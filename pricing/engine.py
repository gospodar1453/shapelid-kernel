"""
Fiyat Hesaplama Motoru — Faz-2
Desteklenen teknolojiler: FDM, SLA, SLS, MJF, DMLS, Laser Cutting, Bending

Yeni Faz-2 parametreleri:
  - finish      : yüzey işlemi (standard / vapor_smoothing / anodize_color / ...)
  - color       : renk seçimi (natural_grey / black_dyed / ...)
  - resolution  : çözünürlük/katman kalitesi (draft / standard / fine / ultra / ...)
  - hardness    : TPU shore değeri (shore_45a / shore_85a / ...)
  - tolerance   : boyut toleransı (standard / medium / fine / ultra)
  - certification: sertifika talebi (none / material_cert / first_article / ...)

Fiyat kaynağı önceliği:
  1. params["material_price_usd_per_kg"] — Base44 DB'den gelen canlı fiyat
  2. material_rates.py sabit fallback
"""

from .material_rates import MATERIAL_RATES
from .machine_rates import MACHINE_RATES
from .finish_rates import (
    apply_options,
    resolve_resolution,
    INFILL_PRESETS,
)

# Platform kâr marjı (MoR modeli)
PLATFORM_MARGIN = 0.28


def _resolve_material_rate(mat_key: str, technology: str, override_price_kg: float = None) -> dict:
    base_rate = MATERIAL_RATES.get(mat_key) or MATERIAL_RATES.get(f"default_{technology}", {})
    if override_price_kg is not None and override_price_kg > 0:
        density = base_rate.get("density_g_cm3", 1.24)
        price_per_cm3 = (override_price_kg / 1000) * density
        return {**base_rate, "price_per_kg": override_price_kg, "price_per_cm3": price_per_cm3, "source": "db_live"}
    return {**base_rate, "source": "static_fallback"}


def calculate_price(geometry: dict, params: dict) -> dict:
    technology       = params.get("technology", "fdm")
    material         = params.get("material", "pla")
    quantity         = max(1, int(params.get("quantity", 1)))
    material_price_kg = params.get("material_price_usd_per_kg")

    # ── Faz-2 seçim parametreleri ──
    options = {
        "finish"        : params.get("finish", "standard"),
        "color"         : params.get("color", "none"),
        "resolution"    : params.get("resolution", "standard"),
        "hardness"      : params.get("hardness", "standard"),
        "tolerance"     : params.get("tolerance", "standard"),
        "certification" : params.get("certification", "none"),
    }

    # Resolution seçimi layer_height'ı override edebilir
    res_rate = resolve_resolution(options["resolution"], technology)
    if res_rate.get("layer_height_mm") and not params.get("layer_height_override_disabled"):
        params = {**params, "layer_height": res_rate["layer_height_mm"]}

    # Infill preset çözümle (sparse/standard/solid/full string ise)
    infill_raw = params.get("infill", 0.2)
    if isinstance(infill_raw, str) and infill_raw in INFILL_PRESETS:
        params = {**params, "infill": INFILL_PRESETS[infill_raw]["ratio"]}

    if geometry["type"] == "3d":
        base_result = _price_3d(geometry, params, technology, material, quantity, material_price_kg)
    elif geometry["type"] == "2d":
        base_result = _price_2d(geometry, params, technology, material, quantity, material_price_kg)
    else:
        raise ValueError("Bilinmeyen geometri tipi")

    # ── Faz-2: seçim parametrelerini birim fiyata uygula ──
    options_result = apply_options(
        base_result["unit_price"],
        technology,
        finish        = options.get("finish", "standard"),
        color         = options.get("color", "none"),
        resolution    = options.get("resolution", "standard"),
        infill        = params.get("infill"),
        hardness      = options.get("hardness", "standard"),
        tolerance     = options.get("tolerance", "standard"),
        certification = options.get("certification", "none"),
    )

    final_unit_price  = options_result["unit_price_final"]
    final_total_price = round(final_unit_price * quantity, 2)

    return {
        **base_result,
        "unit_price"               : final_unit_price,
        "total_price"              : final_total_price,
        "base_unit_price_no_options": base_result["unit_price"],
        "options"                  : options,
        "options_result"           : options_result,
        "phase"                    : "faz-2",
    }


# ─────────────────────────────────────────────
# 3D BASKI FİYATLANDIRMASI
# ─────────────────────────────────────────────

def _price_3d(geometry, params, technology, material, quantity, material_price_kg) -> dict:
    volume_cm3       = geometry["volume_cm3"]
    surface_area_cm2 = geometry["surface_area_cm2"]
    support_area_cm2 = geometry.get("support_area_cm2", 0)
    support_ratio    = geometry.get("support_ratio", 0)
    complexity_score = geometry.get("complexity_score", 0)
    dims             = geometry["dimensions_mm"]
    is_watertight    = geometry.get("is_watertight", True)

    layer_height = float(params.get("layer_height", 0.2))
    infill       = float(params.get("infill", 0.2))

    mat_key = f"{technology}_{material}"
    mat     = _resolve_material_rate(mat_key, technology, material_price_kg)
    if not mat:
        raise ValueError(f"Bilinmeyen materyal kombinasyonu: {mat_key}")

    machine = MACHINE_RATES.get(technology)
    if not machine:
        raise ValueError(f"Bilinmeyen teknoloji: {technology}")

    # ── Hacim hesabı ──
    if technology == "fdm":
        shell_volume    = surface_area_cm2 * 0.12
        infill_volume   = max(volume_cm3 - shell_volume, 0) * infill
        effective_volume = shell_volume + infill_volume
    else:
        effective_volume = volume_cm3

    support_volume = 0
    if technology in ("fdm", "sla"):
        support_volume = support_area_cm2 * 0.1 * 0.5

    # ── Malzeme maliyeti ──
    material_cost = (effective_volume + support_volume) * mat["price_per_cm3"]

    # ── Baskı süresi ──
    layer_count = dims["z_mm"] / layer_height

    if technology == "fdm":
        time_per_layer_min = 0.5 + (effective_volume / layer_count) * 0.1
        time_per_layer_min *= (1 + complexity_score / 200)
    elif technology == "sla":
        time_per_layer_min = 0.08
    elif technology in ("sls", "mjf"):
        bbox_area_cm2      = (dims["x_mm"] * dims["y_mm"]) / 100
        time_per_layer_min = bbox_area_cm2 * 0.002 + 0.1
    elif technology == "dmls":
        # DMLS: çok yavaş — 30µm katman, metal sinterleme
        bbox_area_cm2      = (dims["x_mm"] * dims["y_mm"]) / 100
        time_per_layer_min = bbox_area_cm2 * 0.008 + 0.5
    else:
        time_per_layer_min = 0.3

    print_time_min = layer_count * time_per_layer_min
    machine_cost   = (print_time_min / 60) * machine["hourly_rate"]
    setup_cost     = machine["setup_cost"]

    # ── Post-process ──
    post_process_cost = 0
    if technology == "fdm" and support_ratio > 0.1:
        post_process_cost = support_area_cm2 * 0.05
    elif technology == "sla":
        post_process_cost = surface_area_cm2 * 0.02
    elif technology == "dmls":
        # DMLS: stres giderme + platten removal standart
        post_process_cost = 15.0

    # ── Risk primi ──
    risk_premium = 0
    if not is_watertight:
        risk_premium = 2.0

    unit_cost_raw        = material_cost + machine_cost + setup_cost + post_process_cost + risk_premium
    discount             = _quantity_discount(quantity)
    unit_cost_discounted = unit_cost_raw * (1 - discount)
    unit_price           = unit_cost_discounted / (1 - PLATFORM_MARGIN)
    total_price          = unit_price * quantity

    return {
        "currency"              : "USD",
        "unit_price"            : round(unit_price, 2),
        "total_price"           : round(total_price, 2),
        "quantity"              : quantity,
        "quantity_discount_pct" : round(discount * 100, 1),
        "price_source"          : mat.get("source", "static_fallback"),
        "breakdown": {
            "material_cost"     : round(material_cost, 4),
            "machine_cost"      : round(machine_cost, 4),
            "setup_cost"        : round(setup_cost, 4),
            "post_process_cost" : round(post_process_cost, 4),
            "risk_premium"      : round(risk_premium, 4),
            "effective_volume_cm3": round(effective_volume, 4),
            "support_volume_cm3": round(support_volume, 4),
            "print_time_min"    : round(print_time_min, 2),
            "layer_height_used" : layer_height,
            "infill_used"       : infill,
            "platform_margin_pct": round(PLATFORM_MARGIN * 100, 1),
        },
        "confidence": _confidence_3d(geometry),
        "routing"   : _routing_recommendation_3d(geometry, technology),
    }


# ─────────────────────────────────────────────
# SAC METAL FİYATLANDIRMASI (LASER / BENDING)
# ─────────────────────────────────────────────

def _price_2d(geometry, params, technology, material, quantity, material_price_kg) -> dict:
    cut_length_m  = geometry["total_cut_length_m"]
    outer_area_cm2 = geometry["outer_area_cm2"]
    hole_count    = geometry.get("hole_count", 0)
    bend_count    = geometry.get("bend_count", 0)
    nesting_eff   = geometry.get("nesting_efficiency", 0.7)
    thickness_mm  = float(params.get("material_thickness", 2.0))

    mat_key = f"laser_{material}"
    mat     = _resolve_material_rate(mat_key, "laser", material_price_kg)
    machine = MACHINE_RATES.get("laser")

    density    = mat.get("density_g_cm3", 7.85)
    volume_cm3 = (outer_area_cm2 * thickness_mm) / 10
    weight_kg  = (volume_cm3 * density) / 1000
    material_cost = weight_kg * mat["price_per_kg"]

    machine_time_min = 0
    if technology == "laser":
        cut_speed_m_min  = max(0.5, 5.0 - (thickness_mm - 1) * 0.6)
        cut_time_min     = cut_length_m / cut_speed_m_min
        pierce_time_min  = hole_count * (0.05 + thickness_mm * 0.01)
        machine_time_min = cut_time_min + pierce_time_min
        machine_cost     = (machine_time_min / 60) * machine["hourly_rate"]
    elif technology == "bending":
        bend_time_min    = max(bend_count * (1.5 + thickness_mm * 0.3), 5)
        machine_time_min = bend_time_min
        machine_cost     = (bend_time_min / 60) * MACHINE_RATES["bending"]["hourly_rate"]
    else:
        machine_cost = 0

    setup_cost  = machine["setup_cost"] if technology == "laser" else MACHINE_RATES["bending"]["setup_cost"]
    waste_factor = max(0, 0.3 - nesting_eff) * 0.5
    waste_cost  = material_cost * waste_factor

    unit_cost_raw        = material_cost + machine_cost + setup_cost + waste_cost
    discount             = _quantity_discount(quantity)
    unit_cost_discounted = unit_cost_raw * (1 - discount)
    unit_price           = unit_cost_discounted / (1 - PLATFORM_MARGIN)
    total_price          = unit_price * quantity

    return {
        "currency"              : "USD",
        "unit_price"            : round(unit_price, 2),
        "total_price"           : round(total_price, 2),
        "quantity"              : quantity,
        "quantity_discount_pct" : round(discount * 100, 1),
        "price_source"          : mat.get("source", "static_fallback"),
        "breakdown": {
            "material_cost"     : round(material_cost, 4),
            "machine_cost"      : round(machine_cost, 4),
            "setup_cost"        : round(setup_cost, 4),
            "waste_cost"        : round(waste_cost, 4),
            "weight_kg"         : round(weight_kg, 4),
            "cut_time_min"      : round(machine_time_min, 2),
            "thickness_mm"      : thickness_mm,
            "platform_margin_pct": round(PLATFORM_MARGIN * 100, 1),
        },
        "confidence": _confidence_2d(geometry, thickness_mm),
        "routing"   : _routing_recommendation_2d(geometry, technology, bend_count),
    }


# ─────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
# ─────────────────────────────────────────────

def _quantity_discount(quantity: int) -> float:
    if quantity >= 1000: return 0.30
    if quantity >= 500:  return 0.25
    if quantity >= 100:  return 0.20
    if quantity >= 50:   return 0.15
    if quantity >= 10:   return 0.10
    if quantity >= 5:    return 0.05
    return 0.0


def _confidence_3d(geometry: dict) -> dict:
    score   = 100
    reasons = []
    if not geometry.get("is_watertight", True):
        score -= 30
        reasons.append("Mesh manifold değil")
    if geometry.get("complexity_score", 0) > 70:
        score -= 20
        reasons.append("Yüksek geometrik kompleksite")
    if geometry.get("support_ratio", 0) > 0.4:
        score -= 15
        reasons.append("Yoğun destek yapısı gerekiyor")
    level = "high" if score >= 75 else "medium" if score >= 50 else "low"
    return {"score": max(score, 0), "level": level, "recommend_manual_quote": score < 50, "reasons": reasons}


def _confidence_2d(geometry: dict, thickness_mm: float) -> dict:
    score   = 100
    reasons = []
    if geometry.get("total_cut_length_mm", 0) == 0:
        score -= 50
        reasons.append("Geçerli geometri bulunamadı")
    if thickness_mm > 20:
        score -= 25
        reasons.append(f"Kalın malzeme ({thickness_mm}mm)")
    level = "high" if score >= 75 else "medium" if score >= 50 else "low"
    return {"score": max(score, 0), "level": level, "recommend_manual_quote": score < 50, "reasons": reasons}


def _routing_recommendation_3d(geometry: dict, technology: str) -> dict:
    volume     = geometry.get("volume_cm3", 0)
    complexity = geometry.get("complexity_score", 0)
    return {
        "preferred_technology": technology,
        "alternative"         : "sls" if technology == "fdm" and complexity > 60 else None,
        "batch_recommended"   : volume < 5,
        "notes"               : "Küçük parça — toplu sipariş iskonto sağlar" if volume < 5 else None,
    }


def _routing_recommendation_2d(geometry: dict, technology: str, bend_count: int) -> dict:
    return {
        "preferred_technology": technology,
        "combined_process"    : bend_count > 0 and technology == "laser",
        "notes"               : "Lazer + bükme kombine sipariş önerilir" if bend_count > 0 else None,
    }
