"""
CNC Pricing Module — Faz-5
CNC Turning, CNC Milling, EDM için feature-based fiyatlandırma.

cnc_analyzer'dan gelen feature verisini kullanarak:
  1. Material cost (malzeme maliyeti)
  2. Machine cost (tezgah saati × işlem süresi)
  3. Setup cost (fixture, kalibrasyon)
  4. Tooling cost (takım değiştirme, özel takımlar)
  5. Post-process (deburring, surface finish)

Giriş: CNC analyzer çıktısı (features dict) + params (material, quantity, etc.)
Çıkış: Fiyat dökümü (USD bazlı)
"""

from .machine_rates import MACHINE_RATES
from .material_rates import MATERIAL_RATES

PLATFORM_MARGIN = 0.28

# CNC material rates (from material_rates.py or override)
CNC_MATERIAL_RATES = {
    "aluminum": {"price_per_kg": 3.50, "density_g_cm3": 2.70, "machinability": 1.0},
    "mild_steel": {"price_per_kg": 1.20, "density_g_cm3": 7.85, "machinability": 0.7},
    "stainless_304": {"price_per_kg": 4.50, "density_g_cm3": 8.00, "machinability": 0.5},
    "stainless_316": {"price_per_kg": 5.50, "density_g_cm3": 8.00, "machinability": 0.45},
    "tool_steel": {"price_per_kg": 8.00, "density_g_cm3": 7.85, "machinability": 0.4},
    "brass": {"price_per_kg": 7.00, "density_g_cm3": 8.50, "machinability": 1.2},
    "copper": {"price_per_kg": 9.00, "density_g_cm3": 8.96, "machinability": 0.8},
    "titanium": {"price_per_kg": 45.00, "density_g_cm3": 4.50, "machinability": 0.3},
    "default": {"price_per_kg": 3.00, "density_g_cm3": 7.85, "machinability": 0.7},
}

# Tooling cost estimates (USD per tool/operation)
TOOLING_COSTS = {
    "drill_small": 2.0,    # < 3mm drill bit wear
    "drill_standard": 0.5, # 3-12mm
    "drill_large": 1.0,    # > 12mm boring bar
    "end_mill": 1.5,       # end mill wear per pocket
    "face_mill": 0.8,      # face mill insert wear
    "thread_mill": 3.0,    # thread mill (expensive)
    "edm_wire": 5.0,       # EDM wire consumption per session
}


def price_cnc(geometry: dict, params: dict) -> dict:
    """
    CNC fiyatlandırma ana fonksiyonu.
    geometry: cnc_analyzer.analyze_cnc() çıktısı
    params: {technology, material, quantity, tolerance, ...}
    """
    technology = params.get("technology", "cnc_milling")
    material = params.get("material", "aluminum")
    quantity = max(1, int(params.get("quantity", 1)))
    material_price_kg = params.get("material_price_usd_per_kg")

    # Material rate
    mat = CNC_MATERIAL_RATES.get(material, CNC_MATERIAL_RATES["default"])
    if material_price_kg and material_price_kg > 0:
        mat = {**mat, "price_per_kg": material_price_kg}

    # Machine rate
    machine_key = technology if technology in MACHINE_RATES else "cnc_milling"
    machine = MACHINE_RATES.get(machine_key, MACHINE_RATES["cnc_milling"])

    # ── 1. Material Cost ──
    # Raw stock volume = bounding box + machining allowance
    bbox_vol_cm3 = geometry.get("bounding_box_volume_cm3", 0)
    stock_allowance = 1.1  # 10% extra for stock material
    stock_volume_cm3 = bbox_vol_cm3 * stock_allowance
    stock_weight_kg = (stock_volume_cm3 * mat["density_g_cm3"]) / 1000
    material_cost = stock_weight_kg * mat["price_per_kg"]

    # ── 2. Machine Cost ──
    machine_time_min = geometry.get("estimated_machine_time_min", 30)
    time_breakdown = geometry.get("machine_time_breakdown", {})

    # Adjust machine time by material machinability
    machinability = mat.get("machinability", 0.7)
    adjusted_time = machine_time_min / machinability

    machine_hourly = machine["hourly_rate"]
    machine_cost = (adjusted_time / 60) * machine_hourly

    # ── 3. Setup Cost ──
    setup_cost = machine["setup_cost"]

    # ── 4. Tooling Cost ──
    tooling_cost = _calculate_tooling_cost(geometry, technology)

    # ── 5. Post-Process Cost ──
    post_process_cost = _calculate_post_process(geometry, params)

    # ── 6. Risk Premium ──
    risk_premium = _calculate_risk_premium(geometry, params)

    # ── Total ──
    unit_cost_raw = (
        material_cost + machine_cost + setup_cost +
        tooling_cost + post_process_cost + risk_premium
    )

    # Quantity discount
    discount = _quantity_discount(quantity)
    unit_cost_discounted = unit_cost_raw * (1 - discount)
    unit_price = unit_cost_discounted / (1 - PLATFORM_MARGIN)
    total_price = unit_price * quantity

    # Confidence
    confidence = _cnc_confidence(geometry, params)

    # Routing recommendation
    routing = _cnc_routing(geometry, technology, params)

    return {
        "currency": "USD",
        "unit_price": round(unit_price, 2),
        "total_price": round(total_price, 2),
        "quantity": quantity,
        "quantity_discount_pct": round(discount * 100, 1),
        "price_source": "db_live" if material_price_kg else "static_fallback",
        "breakdown": {
            "material_cost": round(material_cost, 4),
            "machine_cost": round(machine_cost, 4),
            "setup_cost": round(setup_cost, 4),
            "tooling_cost": round(tooling_cost, 4),
            "post_process_cost": round(post_process_cost, 4),
            "risk_premium": round(risk_premium, 4),
            "stock_weight_kg": round(stock_weight_kg, 4),
            "stock_volume_cm3": round(stock_volume_cm3, 4),
            "machine_time_min": round(adjusted_time, 2),
            "raw_machine_time_min": round(machine_time_min, 2),
            "machinability_factor": machinability,
            "platform_margin_pct": round(PLATFORM_MARGIN * 100, 1),
        },
        "time_breakdown": time_breakdown,
        "features_summary": _features_summary(geometry),
        "confidence": confidence,
        "routing": routing,
        "phase": "faz-5",
    }


def _calculate_tooling_cost(geometry: dict, technology: str) -> float:
    """
    Takım maliyeti: delik, cep, kanal için takım aşınması.
    """
    cost = 0.0

    holes = geometry.get("holes", [])
    for hole in holes:
        if hole["diameter_mm"] < 3:
            cost += TOOLING_COSTS["drill_small"] * hole["complexity"]
        elif hole["diameter_mm"] > 12:
            cost += TOOLING_COSTS["drill_large"]
        else:
            cost += TOOLING_COSTS["drill_standard"]

    pockets = geometry.get("pockets", [])
    for pocket in pockets:
        cost += TOOLING_COSTS["end_mill"] * pocket["complexity"]

    slots = geometry.get("slots", [])
    for slot in slots:
        cost += TOOLING_COSTS["end_mill"]
        if slot["type"] == "thin_slot":
            cost += TOOLING_COSTS["edm_wire"]

    if technology == "edm":
        cost += TOOLING_COSTS["edm_wire"]

    return round(cost, 4)


def _calculate_post_process(geometry: dict, params: dict) -> float:
    """
    Post-process: deburring, surface finishing, cleaning.
    """
    cost = 2.0  # Base deburring/cleaning

    # Sharp edges need deburring
    edges = geometry.get("edges", {})
    sharp = edges.get("sharp_edges", 0)
    cost += min(sharp * 0.05, 10)

    # Tolerance affects finishing time
    tolerance = params.get("tolerance", "standard")
    if tolerance == "fine":
        cost += 5.0
    elif tolerance == "ultra":
        cost += 15.0

    # Surface finish
    finish = params.get("finish", "standard")
    if finish in ("polished", "mirror"):
        cost += 10.0
    elif finish in ("anodized", "plated"):
        cost += 8.0

    return round(cost, 4)


def _calculate_risk_premium(geometry: dict, params: dict) -> float:
    """
    Risk primi: kompleks parçalar için ek güvenlik marjı.
    """
    premium = 0.0

    complexity = geometry.get("cnc_complexity_score", 0)
    if complexity > 70:
        premium += 8.0
    elif complexity > 50:
        premium += 4.0

    # Non-watertight mesh → uncertain geometry
    if not geometry.get("is_watertight", True):
        premium += 3.0

    # Tight tolerance + high complexity = high risk
    tolerance = params.get("tolerance", "standard")
    if tolerance == "ultra" and complexity > 40:
        premium += 5.0

    # Titanium is hard to machine — higher risk
    material = params.get("material", "")
    if "titanium" in material.lower():
        premium += 5.0

    return round(premium, 4)


def _quantity_discount(quantity: int) -> float:
    if quantity >= 1000: return 0.30
    if quantity >= 500:  return 0.25
    if quantity >= 100:  return 0.20
    if quantity >= 50:   return 0.15
    if quantity >= 10:   return 0.10
    if quantity >= 5:    return 0.05
    return 0.0


def _features_summary(geometry: dict) -> dict:
    """Feature özeti — UI'da gösterilecek"""
    holes = geometry.get("holes", [])
    pockets = geometry.get("pockets", [])
    slots = geometry.get("slots", [])
    edges = geometry.get("edges", {})
    turning = geometry.get("turning_features")

    summary = {
        "hole_count": len(holes),
        "pocket_count": len(pockets),
        "slot_count": len(slots),
        "total_features": len(holes) + len(pockets) + len(slots),
        "sharp_edges": edges.get("sharp_edges", 0),
        "fillets": edges.get("fillets", 0),
        "chamfers": edges.get("chamfers", 0),
        "complexity_score": geometry.get("cnc_complexity_score", 0),
        "complexity_level": _complexity_level(geometry.get("cnc_complexity_score", 0)),
    }

    if turning:
        summary["turning"] = {
            "is_turning_candidate": turning.get("is_turning_candidate", False),
            "roundness_score": turning.get("roundness_score", 0),
            "length_mm": turning.get("length_mm", 0),
            "max_diameter_mm": turning.get("max_diameter_mm", 0),
        }

    # List notable features
    notable = []
    for h in holes[:3]:
        notable.append(f"Delik Ø{h['diameter_mm']}mm × {h['depth_mm']}mm ({h['type']})")
    for p in pockets[:3]:
        notable.append(f"Cep {p['width_mm']}×{p['height_mm']}mm ({p['type']})")
    for s in slots[:2]:
        notable.append(f"Kanal {s['width_mm']}×{s['length_mm']}mm ({s['type']})")
    summary["notable_features"] = notable

    return summary


def _complexity_level(score: int) -> str:
    if score >= 70: return "very_high"
    if score >= 50: return "high"
    if score >= 30: return "medium"
    if score >= 15: return "low"
    return "simple"


def _cnc_confidence(geometry: dict, params: dict) -> dict:
    """Fiyat güven skoru."""
    score = 100
    reasons = []

    if not geometry.get("is_watertight", True):
        score -= 25
        reasons.append("Mesh kapalı değil — feature tespiti etkilenebilir")

    complexity = geometry.get("cnc_complexity_score", 0)
    if complexity > 70:
        score -= 20
        reasons.append("Çok yüksek geometrik kompleksite")
    elif complexity > 50:
        score -= 10
        reasons.append("Yüksek geometrik kompleksite")

    holes = geometry.get("holes", [])
    deep_holes = [h for h in holes if h["type"] == "deep_hole"]
    if deep_holes:
        score -= 15
        reasons.append(f"{len(deep_holes)} derin delik — fiyat tahmini düşük güven")

    material = params.get("material", "")
    if "titanium" in material.lower():
        score -= 10
        reasons.append("Titanyum işleme parametreleri değişken")

    level = "high" if score >= 75 else "medium" if score >= 50 else "low"
    return {
        "score": max(score, 0),
        "level": level,
        "recommend_manual_quote": score < 50,
        "reasons": reasons,
    }


def _cnc_routing(geometry: dict, technology: str, params: dict) -> dict:
    """Üretim yönlendirme önerisi."""
    complexity = geometry.get("cnc_complexity_score", 0)
    dims = geometry.get("dimensions_mm", {})
    max_dim = max(dims.get("x_mm", 0), dims.get("y_mm", 0), dims.get("z_mm", 0))

    routing = {
        "preferred_technology": technology,
        "machine_class": "3_axis" if complexity < 50 else "4_axis",
        "notes": [],
    }

    # Recommend 5-axis for very complex parts
    if complexity > 80:
        routing["machine_class"] = "5_axis"
        routing["notes"].append("5-eksen tezgah önerilir — yüksek kompleksite")

    # EDM recommendation for thin slots
    slots = geometry.get("slots", [])
    thin_slots = [s for s in slots if s["type"] == "thin_slot"]
    if thin_slots:
        routing["alternative"] = "edm"
        routing["notes"].append(f"{len(thin_slots)} ince kanal — EDM alternatifi")

    # Large part
    if max_dim > 300:
        routing["notes"].append(f"Parça {max_dim}mm — büyük tezgah kapasitesi gerekli")

    # Turning recommendation
    if technology != "cnc_turning":
        turning = geometry.get("turning_features")
        if turning and turning.get("is_turning_candidate"):
            routing["alternative"] = "cnc_turning"
            routing["notes"].append("Parça silindirik — tornalama daha ekonomik olabilir")

    # Batch recommendation
    volume = geometry.get("volume_cm3", 0)
    if volume < 10:
        routing["batch_recommended"] = True
        routing["notes"].append("Küçük parça — toplu siparişte setup maliyeti düşer")

    routing["notes"] = routing["notes"] if routing["notes"] else None
    return routing
