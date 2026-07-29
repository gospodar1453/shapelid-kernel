"""
Fiyat Hesaplama Motoru — Faz-2 + Material Multipliers
Desteklenen teknolojiler: FDM, SLA, SLS, MJF, DMLS, Laser Cutting, Bending

Fiyat kaynağı önceliği:
  1. params["material_price_usd_per_kg"] — Base44 DB'den gelen canlı fiyat
  2. material_rates.py sabit fallback

Material multipliers (Faz-2.1):
  - speed_mult: malzeme bazlı baskı süresi çarpanı
  - material_setup_cost: purge/nozzle wear kurulum maliyeti
  - waste_pct: fire oranı
"""

from .material_rates import MATERIAL_RATES
from .material_multipliers import get_material_multiplier
from .machine_rates import MACHINE_RATES
from .manual_quote import evaluate_manual_quote
from .calibration import apply_calibration
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

    # ── Faz-4: Manual Quote Trigger Değerlendirmesi ──
    mq_result = evaluate_manual_quote(
        geometry   = geometry,
        params     = params,
        unit_price = final_unit_price,
    )

    result = {
        **base_result,
        "unit_price"               : final_unit_price,
        "total_price"              : final_total_price,
        "base_unit_price_no_options": base_result["unit_price"],
        "options"                  : options,
        "options_result"           : options_result,
        "phase"                    : "faz-4",
        "manual_quote"             : mq_result["manual_quote"],
        "auto_price_allowed"       : mq_result["auto_price_allowed"],
        "quote_triggers"           : mq_result["triggers"],
        "quote_warnings"           : mq_result["warnings"],
    }

    # ── Faz-7: ML Kalibrasyon uygula ──
    calibration_factors = params.get("calibration_factors")
    if calibration_factors:
        result = apply_calibration(result, calibration_factors)

    return result


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
        raise ValueError(f"Bilineyen materyal kombinasyonu: {mat_key}")

    machine = MACHINE_RATES.get(technology)
    if not machine:
        raise ValueError(f"Bilinmeyen teknoloji: {technology}")

    # ── Material multipliers (Faz-2.1) ──
    mat_mult = get_material_multiplier(mat_key)
    speed_mult       = mat_mult["speed_mult"]
    mat_setup_cost   = mat_mult["setup_cost"]
    waste_pct        = mat_mult["waste_pct"]

    # ── Hacim hesabı (fire dahil) ──
    if technology == "fdm":
        shell_volume    = surface_area_cm2 * 0.12
        infill_volume   = max(volume_cm3 - shell_volume, 0) * infill
        effective_volume = shell_volume + infill_volume
    else:
        effective_volume = volume_cm3

    # Fire oranını uygula
    effective_volume_with_waste = effective_volume * (1 + waste_pct)

    support_volume = 0
    if technology in ("fdm", "sla"):
        support_volume = support_area_cm2 * 0.1 * 0.5

    # ── Malzeme maliyeti (fire dahil) ──
    material_cost = (effective_volume_with_waste + support_volume) * mat["price_per_cm3"]

    # ── Baskı süresi (malzeme çarpanı ile) ──
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
        bbox_area_cm2      = (dims["x_mm"] * dims["y_mm"]) / 100
        time_per_layer_min = bbox_area_cm2 * 0.008 + 0.5
    else:
        time_per_layer_min = 0.3

    print_time_min = layer_count * time_per_layer_min * speed_mult  # ← malzeme çarpanı
    machine_cost   = (print_time_min / 60) * machine["hourly_rate"]
    setup_cost     = machine["setup_cost"] + mat_setup_cost       # ← malzeme setup

    # ── Post-process ──
    post_process_cost = 0
    if technology == "fdm" and support_ratio > 0.1:
        post_process_cost = support_area_cm2 * 0.05
    elif technology == "sla":
        post_process_cost = surface_area_cm2 * 0.02
    elif technology == "dmls":
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
            "effective_volume_cm3": round(effective_volume_with_waste, 4),
            "support_volume_cm3": round(support_volume, 4),
            "print_time_min"    : round(print_time_min, 2),
            "layer_height_used" : layer_height,
            "infill_used"       : infill,
            "platform_margin_pct": round(PLATFORM_MARGIN * 100, 1),
            "material_speed_mult": speed_mult,
            "material_setup_cost": mat_setup_cost,
            "material_waste_pct": waste_pct,
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
        machine_time_min = (cut_length_m * 1.2 + hole_count * 0.15) * (1 / nesting_eff)
    elif technology == "bending":
        machine_time_min = bend_count * 0.8 + 2.0

    machine_cost   = (machine_time_min / 60) * machine["hourly_rate"]
    setup_cost     = machine["setup_cost"]
    post_process   = max(outer_area_cm2 * 0.002, 0.5)

    unit_cost_raw  = material_cost + machine_cost + setup_cost + post_process
    discount       = _quantity_discount(quantity)
    unit_cost_disc = unit_cost_raw * (1 - discount)
    unit_price     = unit_cost_disc / (1 - PLATFORM_MARGIN)
    total_price    = unit_price * quantity

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
            "post_process_cost" : round(post_process, 4),
            "risk_premium"      : 0,
            "weight_kg"         : round(weight_kg, 4),
            "machine_time_min"  : round(machine_time_min, 2),
            "platform_margin_pct": round(PLATFORM_MARGIN * 100, 1),
        },
        "confidence": _confidence_2d(geometry),
        "routing"   : {"preferred_technology": technology, "alternative": None},
    }


# ─────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
# ─────────────────────────────────────────────

def _quantity_discount(qty: int) -> float:
    if qty >= 500: return 0.25
    if qty >= 200: return 0.20
    if qty >= 100: return 0.15
    if qty >= 50:  return 0.10
    if qty >= 20:  return 0.07
    if qty >= 10:  return 0.05
    if qty >= 5:   return 0.03
    return 0.0

def _confidence_3d(geometry: dict) -> dict:
    score = 100
    reasons = []
    if not geometry.get("is_watertight", True):
        score -= 30; reasons.append("Mesh watertight değil")
    if geometry.get("complexity_score", 0) > 70:
        score -= 15; reasons.append("Yüksek karmaşıklık")
    if geometry.get("support_ratio", 0) > 0.3:
        score -= 10; reasons.append("Yüksek destek oranı")
    if geometry.get("volume_cm3", 0) < 0.5:
        score -= 10; reasons.append("Çok küçük hacim")
    level = "high" if score >= 80 else ("medium" if score >= 50 else "low")
    return {"score": max(score, 0), "level": level, "recommend_manual_quote": score < 50, "reasons": reasons}

def _confidence_2d(geometry: dict) -> dict:
    score = 100
    reasons = []
    if geometry.get("nesting_efficiency", 1) < 0.5:
        score -= 20; reasons.append("Düşük nesting verimi")
    if geometry.get("hole_count", 0) > 50:
        score -= 15; reasons.append("Çok sayıda delik")
    level = "high" if score >= 80 else ("medium" if score >= 50 else "low")
    return {"score": max(score, 0), "level": level, "recommend_manual_quote": score < 50, "reasons": reasons}

def _routing_recommendation_3d(geometry: dict, technology: str) -> dict:
    volume = geometry.get("volume_cm3", 0)
    dims = geometry.get("dimensions_mm", {})
    max_dim = max(dims.get("x_mm", 0), dims.get("y_mm", 0), dims.get("z_mm", 0))
    complexity = geometry.get("complexity_score", 0)

    alternative = None
    if technology == "fdm" and complexity > 60:
        alternative = "sla"
    elif technology == "sla" and volume > 100:
        alternative = "sls"

    batch = volume < 10 or (volume < 50 and geometry.get("support_ratio", 0) < 0.1)

    notes = ""
    if volume < 5:
        notes = "Küçük parça — toplu sipariş iskonto sağlar"
    elif volume > 500:
        notes = "Büyük parça — baskı süresi uzun"
    elif complexity > 70:
        notes = "Karmaşık geometri — SLA önerilir"
    else:
        notes = "Standart parça"

    return {
        "preferred_technology": technology,
        "alternative": alternative,
        "batch_recommended": batch,
        "notes": notes,
    }
