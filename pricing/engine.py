"""
Fiyat Hesaplama Motoru — Faz-1
Desteklenen teknolojiler: FDM, SLA, SLS, MJF, Laser Cutting, Bending

Fiyat = Malzeme maliyeti + Makine maliyeti + Setup + Destek maliyeti + Miktar iskontosu
Tüm fiyatlar USD cinsinden. TRY dönüşümü API katmanında yapılır.
"""

from .material_rates import MATERIAL_RATES
from .machine_rates import MACHINE_RATES

# Şirket kâr marjı (Xometry benzeri take-rate modeli)
PLATFORM_MARGIN = 0.28  # %28


def calculate_price(geometry: dict, params: dict) -> dict:
    technology = params.get("technology", "fdm")
    material = params.get("material", "pla")
    quantity = max(1, int(params.get("quantity", 1)))

    if geometry["type"] == "3d":
        return _price_3d(geometry, params, technology, material, quantity)
    elif geometry["type"] == "2d":
        return _price_2d(geometry, params, technology, material, quantity)
    else:
        raise ValueError("Bilinmeyen geometri tipi")


# ─────────────────────────────────────────────
# 3D BASKI FİYATLANDIRMASI (FDM / SLA / SLS / MJF)
# ─────────────────────────────────────────────

def _price_3d(geometry, params, technology, material, quantity) -> dict:
    volume_cm3 = geometry["volume_cm3"]
    surface_area_cm2 = geometry["surface_area_cm2"]
    support_area_cm2 = geometry.get("support_area_cm2", 0)
    support_ratio = geometry.get("support_ratio", 0)
    complexity_score = geometry.get("complexity_score", 0)
    dims = geometry["dimensions_mm"]
    is_watertight = geometry.get("is_watertight", True)

    layer_height = float(params.get("layer_height", 0.2))  # mm
    infill = float(params.get("infill", 0.2))              # 0.0-1.0

    mat_key = f"{technology}_{material}"
    mat = MATERIAL_RATES.get(mat_key) or MATERIAL_RATES.get(f"default_{technology}")
    if not mat:
        raise ValueError(f"Bilinmeyen materyal kombinasyonu: {mat_key}")

    machine = MACHINE_RATES.get(technology)
    if not machine:
        raise ValueError(f"Bilinmeyen teknoloji: {technology}")

    # ── Malzeme hacmi ──
    if technology == "fdm":
        # FDM: infill + perimeter (perimeter ~%100 doluluk, 2 duvar)
        shell_thickness_cm = 0.12  # ~2 duvar
        shell_volume = surface_area_cm2 * shell_thickness_cm
        infill_volume = max(volume_cm3 - shell_volume, 0) * infill
        effective_volume = shell_volume + infill_volume
    else:
        # SLA/SLS/MJF: neredeyse tam dolu
        effective_volume = volume_cm3

    # Destek malzeme hacmi (FDM/SLA için)
    support_volume = 0
    if technology in ("fdm", "sla"):
        support_volume = support_area_cm2 * 0.1  # ortalama 1mm yükseklik, %50 doluluk
        support_volume *= 0.5

    # ── Malzeme maliyeti ──
    material_cost = (effective_volume + support_volume) * mat["price_per_cm3"]

    # ── Baskı süresi ──
    layer_count = dims["z_mm"] / layer_height
    if technology == "fdm":
        # FDM: katman başına yaklaşık süre (kompleksite etkili)
        time_per_layer_min = 0.5 + (effective_volume / layer_count) * 0.1
        time_per_layer_min *= (1 + complexity_score / 200)
    elif technology == "sla":
        time_per_layer_min = 0.08  # ~5 saniye/katman cure
    elif technology in ("sls", "mjf"):
        # SLS/MJF: bounding box yüzeyi belirleyici (batch printing)
        bbox_area_cm2 = (dims["x_mm"] * dims["y_mm"]) / 100
        time_per_layer_min = bbox_area_cm2 * 0.002 + 0.1
    else:
        time_per_layer_min = 0.3

    print_time_min = layer_count * time_per_layer_min
    machine_cost = (print_time_min / 60) * machine["hourly_rate"]

    # ── Setup maliyeti ──
    setup_cost = machine["setup_cost"]

    # ── Destek sökme işçiliği ──
    post_process_cost = 0
    if technology == "fdm" and support_ratio > 0.1:
        post_process_cost = support_area_cm2 * 0.05
    elif technology == "sla":
        post_process_cost = surface_area_cm2 * 0.02  # IPA yıkama + UV cure

    # ── Kalite riski primi ──
    risk_premium = 0
    if not is_watertight:
        risk_premium = 2.0  # non-manifold mesh riski

    # ── Birim maliyet ──
    unit_cost_raw = material_cost + machine_cost + setup_cost + post_process_cost + risk_premium

    # ── Miktar iskontosu ──
    discount = _quantity_discount(quantity)
    unit_cost_discounted = unit_cost_raw * (1 - discount)

    # ── Platform marjı ekle ──
    unit_price = unit_cost_discounted / (1 - PLATFORM_MARGIN)
    total_price = unit_price * quantity

    return {
        "currency": "USD",
        "unit_price": round(unit_price, 2),
        "total_price": round(total_price, 2),
        "quantity": quantity,
        "quantity_discount_pct": round(discount * 100, 1),
        "breakdown": {
            "material_cost": round(material_cost, 4),
            "machine_cost": round(machine_cost, 4),
            "setup_cost": round(setup_cost, 4),
            "post_process_cost": round(post_process_cost, 4),
            "risk_premium": round(risk_premium, 4),
            "effective_volume_cm3": round(effective_volume, 4),
            "support_volume_cm3": round(support_volume, 4),
            "print_time_min": round(print_time_min, 2),
            "platform_margin_pct": round(PLATFORM_MARGIN * 100, 1),
        },
        "confidence": _confidence_3d(geometry),
        "routing": _routing_recommendation_3d(geometry, technology),
    }


# ─────────────────────────────────────────────
# SAC METAL FİYATLANDIRMASI (LASER / BENDING)
# ─────────────────────────────────────────────

def _price_2d(geometry, params, technology, material, quantity) -> dict:
    cut_length_m = geometry["total_cut_length_m"]
    net_area_cm2 = geometry["net_area_cm2"]
    outer_area_cm2 = geometry["outer_area_cm2"]
    hole_count = geometry.get("hole_count", 0)
    bend_count = geometry.get("bend_count", 0)
    nesting_eff = geometry.get("nesting_efficiency", 0.7)

    thickness_mm = float(params.get("material_thickness", 2.0))

    mat_key = f"laser_{material}"
    mat = MATERIAL_RATES.get(mat_key) or MATERIAL_RATES.get(f"default_laser")
    machine = MACHINE_RATES.get("laser")

    # ── Malzeme maliyeti (ağırlık bazlı) ──
    density = mat.get("density_g_cm3", 7.85)  # g/cm³
    volume_cm3 = (outer_area_cm2 * thickness_mm) / 10  # mm→cm
    weight_kg = (volume_cm3 * density) / 1000
    material_cost = weight_kg * mat["price_per_kg"]

    # ── Lazer kesim maliyeti ──
    if technology == "laser":
        # Kesim hızı kalınlığa göre azalır
        cut_speed_m_min = max(0.5, 5.0 - (thickness_mm - 1) * 0.6)
        cut_time_min = cut_length_m / cut_speed_m_min
        # Delik piercing süresi (her delik ~3-8 sn)
        pierce_time_min = hole_count * (0.05 + thickness_mm * 0.01)
        machine_time_min = cut_time_min + pierce_time_min
        machine_cost = (machine_time_min / 60) * machine["hourly_rate"]

    elif technology == "bending":
        # Bending: büküm başına setup + çalışma
        bend_time_min = bend_count * (1.5 + thickness_mm * 0.3)
        bend_time_min = max(bend_time_min, 5)
        machine_cost = (bend_time_min / 60) * MACHINE_RATES["bending"]["hourly_rate"]
    else:
        machine_cost = 0

    # ── Setup ──
    setup_cost = machine["setup_cost"] if technology == "laser" else MACHINE_RATES["bending"]["setup_cost"]

    # ── Nesting verimsizliği maliyeti ──
    # Düşük nesting → atık malzeme artıyor
    waste_factor = max(0, 0.3 - nesting_eff) * 0.5
    waste_cost = material_cost * waste_factor

    # ── Birim maliyet ──
    unit_cost_raw = material_cost + machine_cost + setup_cost + waste_cost

    discount = _quantity_discount(quantity)
    unit_cost_discounted = unit_cost_raw * (1 - discount)
    unit_price = unit_cost_discounted / (1 - PLATFORM_MARGIN)
    total_price = unit_price * quantity

    return {
        "currency": "USD",
        "unit_price": round(unit_price, 2),
        "total_price": round(total_price, 2),
        "quantity": quantity,
        "quantity_discount_pct": round(discount * 100, 1),
        "breakdown": {
            "material_cost": round(material_cost, 4),
            "machine_cost": round(machine_cost, 4),
            "setup_cost": round(setup_cost, 4),
            "waste_cost": round(waste_cost, 4),
            "weight_kg": round(weight_kg, 4),
            "cut_time_min": round(machine_time_min if technology == "laser" else bend_count * 1.5, 2),
            "platform_margin_pct": round(PLATFORM_MARGIN * 100, 1),
        },
        "confidence": _confidence_2d(geometry, thickness_mm),
        "routing": _routing_recommendation_2d(geometry, technology, bend_count),
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
    """Otomatik fiyat güven skoru — düşükse manuel teklif öner"""
    score = 100
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
    recommend_manual = score < 50

    return {
        "score": max(score, 0),
        "level": level,
        "recommend_manual_quote": recommend_manual,
        "reasons": reasons,
    }


def _confidence_2d(geometry: dict, thickness_mm: float) -> dict:
    score = 100
    reasons = []

    if geometry.get("total_cut_length_mm", 0) == 0:
        score -= 50
        reasons.append("Geçerli geometri bulunamadı")
    if thickness_mm > 20:
        score -= 25
        reasons.append(f"Kalın malzeme ({thickness_mm}mm) — lazer sınırı aşılıyor olabilir")
    if geometry.get("bend_count", 0) > 8:
        score -= 20
        reasons.append(f"{geometry['bend_count']} büküm tespit edildi")

    level = "high" if score >= 75 else "medium" if score >= 50 else "low"

    return {
        "score": max(score, 0),
        "level": level,
        "recommend_manual_quote": score < 50,
        "reasons": reasons,
    }


def _routing_recommendation_3d(geometry, technology) -> dict:
    """Parçayı hangi üretici profiline yönlendireceğimizi öner"""
    dims = geometry["dimensions_mm"]
    volume = geometry["volume_cm3"]

    if technology == "fdm":
        if volume > 500:
            return {"tier": "industrial", "note": "Büyük hacimli FDM — endüstriyel yazıcı gerekli"}
        return {"tier": "standard", "note": "Standart FDM üreticisi"}
    elif technology == "sls":
        return {"tier": "industrial", "note": "SLS — minimum batch lot kontrolü yapılmalı"}
    elif technology in ("sla",):
        return {"tier": "precision", "note": "SLA — hassas boyut toleransı üreticisi"}
    return {"tier": "standard", "note": technology.upper()}


def _routing_recommendation_2d(geometry, technology, bend_count) -> dict:
    thickness_implied = "thin"  # DXF'te thickness bilgisi params'tan geliyor
    if bend_count > 5:
        return {"tier": "precision", "note": f"{bend_count} büküm — abkant uzmanı gerekli"}
    return {"tier": "standard", "note": f"Standart {technology} üreticisi"}
