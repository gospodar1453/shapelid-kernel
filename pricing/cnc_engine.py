"""
CNC/EDM Fiyatlandırma Motoru — Faz-5
Shapelid Kernel v3.0.0

Desteklenen teknolojiler:
  - cnc_milling  : 3-eksen VMC, yüzey frezeleme + delik/cep işleme
  - cnc_turning  : 2-3 eksen torna, döner parça
  - edm          : Tel erozyon, hassas kalıp boşluğu

Fiyat formülü:
  unit_price = (material + mrr_machining + setup + post_process) / (1 - margin)

MRR (Material Removal Rate) tabanlı makine süresi hesabı:
  - Milling : MRR = Vc × f_z × z × ae × ap  (cm³/dk)
  - Turning : MRR = Vc × f × ap  (cm³/dk)
  - EDM     : MRR = penetration_rate × cross_section (mm³/dk)
"""

from .machine_rates import MACHINE_RATES
from .manual_quote  import evaluate_manual_quote

PLATFORM_MARGIN = 0.28


# ── Material Removal Rate Sabitleri ────────────────────────────────────────
# Türkiye piyasasındaki ortalama makine + operatör parametreleri

MRR_PARAMS = {
    # CNC Milling (3-eksen VMC)
    # Vc=cutting speed, fz=feed/diş, z=diş sayısı, ae=radial WOC, ap=axial DOC
    "cnc_milling": {
        # Aluminyum (yumuşak)
        "aluminum"      : {"Vc": 200, "fz": 0.05, "z": 4, "ae_ratio": 0.5, "ap_ratio": 0.3},
        # Çelik (genel)
        "steel"         : {"Vc": 100, "fz": 0.03, "z": 4, "ae_ratio": 0.4, "ap_ratio": 0.2},
        "mild_steel"    : {"Vc": 120, "fz": 0.04, "z": 4, "ae_ratio": 0.4, "ap_ratio": 0.25},
        "stainless_steel": {"Vc": 80,  "fz": 0.02, "z": 4, "ae_ratio": 0.35, "ap_ratio": 0.15},
        "ss304"         : {"Vc": 80,  "fz": 0.02, "z": 4, "ae_ratio": 0.35, "ap_ratio": 0.15},
        "ss316l"        : {"Vc": 70,  "fz": 0.018, "z":4, "ae_ratio": 0.30, "ap_ratio": 0.12},
        # Titanyum
        "titanium"      : {"Vc": 50,  "fz": 0.015, "z": 4, "ae_ratio": 0.25, "ap_ratio": 0.10},
        "ti6al4v"       : {"Vc": 45,  "fz": 0.012, "z": 4, "ae_ratio": 0.20, "ap_ratio": 0.08},
        # Bakır
        "copper"        : {"Vc": 150, "fz": 0.04, "z": 4, "ae_ratio": 0.45, "ap_ratio": 0.25},
        # Plastik (CNC frezelenebilir)
        "default"       : {"Vc": 150, "fz": 0.04, "z": 4, "ae_ratio": 0.45, "ap_ratio": 0.25},
    },

    # CNC Turning (2-3 eksen)
    # Vc=yüzey hızı (m/dk), f=ilerleme (mm/dev), ap=talaş derinliği (mm)
    "cnc_turning": {
        "aluminum"      : {"Vc": 250, "f": 0.15, "ap": 2.0},
        "steel"         : {"Vc": 150, "f": 0.10, "ap": 1.5},
        "mild_steel"    : {"Vc": 180, "f": 0.12, "ap": 1.8},
        "stainless_steel": {"Vc": 100, "f": 0.07, "ap": 1.0},
        "ss304"         : {"Vc": 100, "f": 0.07, "ap": 1.0},
        "ss316l"        : {"Vc": 85,  "f": 0.06, "ap": 0.8},
        "titanium"      : {"Vc": 60,  "f": 0.05, "ap": 0.6},
        "ti6al4v"       : {"Vc": 55,  "f": 0.04, "ap": 0.5},
        "copper"        : {"Vc": 200, "f": 0.12, "ap": 1.5},
        "default"       : {"Vc": 150, "f": 0.10, "ap": 1.5},
    },

    # EDM Tel Erozyon
    # penetration_rate: mm/saat cinsinden (malzeme sertliğine bağlı)
    # Kaynak: Mitsubishi Wire EDM referans tablosu
    "edm": {
        # Takım çelikleri (en yaygın EDM malzemesi)
        "tool_steel"    : {"penetration_mm_hr": 80,  "wire_cost_hr": 3.5},
        "h13_steel"     : {"penetration_mm_hr": 75,  "wire_cost_hr": 3.5},
        "d2_steel"      : {"penetration_mm_hr": 70,  "wire_cost_hr": 3.5},
        # Paslanmaz
        "stainless_steel": {"penetration_mm_hr": 65, "wire_cost_hr": 3.0},
        "ss304"         : {"penetration_mm_hr": 65,  "wire_cost_hr": 3.0},
        "ss316l"        : {"penetration_mm_hr": 60,  "wire_cost_hr": 3.0},
        # Alüminyum
        "aluminum"      : {"penetration_mm_hr": 120, "wire_cost_hr": 2.0},
        # Titanyum (EDM'de çok yavaş)
        "titanium"      : {"penetration_mm_hr": 40,  "wire_cost_hr": 5.0},
        # Bakır
        "copper"        : {"penetration_mm_hr": 90,  "wire_cost_hr": 2.5},
        "default"       : {"penetration_mm_hr": 70,  "wire_cost_hr": 3.5},
    },
}

# Malzeme yoğunlukları (g/cm³)
MATERIAL_DENSITIES = {
    "aluminum"       : 2.70,
    "steel"          : 7.85,
    "mild_steel"     : 7.85,
    "stainless_steel": 8.00,
    "ss304"          : 8.00,
    "ss316l"         : 8.00,
    "titanium"       : 4.43,
    "ti6al4v"        : 4.43,
    "copper"         : 8.96,
    "tool_steel"     : 7.80,
    "h13_steel"      : 7.80,
    "d2_steel"       : 7.70,
    "default"        : 7.85,
}

# Stok malzeme fire oranları (blank → finished part)
STOCK_REMOVAL_RATIOS = {
    "cnc_milling": 0.55,   # Ortalama %55 talaş (%45 net parça)
    "cnc_turning": 0.45,   # Torna daha verimli — %45 talaş
    "edm"        : 0.05,   # EDM neredeyse sıfır fire
}


def calculate_cnc_price(geometry: dict, params: dict) -> dict:
    """
    Ana CNC/EDM fiyat hesaplama fonksiyonu.
    pricing/engine.py tarafından çağrılır.
    """
    technology     = params.get("technology", "cnc_milling")
    material       = params.get("material", "aluminum")
    quantity       = max(1, int(params.get("quantity", 1)))
    material_price_kg = params.get("material_price_usd_per_kg")

    volume_cm3   = geometry.get("volume_cm3", 0)
    surface_cm2  = geometry.get("surface_area_cm2", 0)
    dims         = geometry.get("dimensions_mm", {"x_mm": 50, "y_mm": 50, "z_mm": 50})
    workload_idx = geometry.get("workload_index", 30)
    holes        = geometry.get("feature_summary", {}).get("holes", [])
    pockets      = geometry.get("feature_summary", {}).get("pockets", [])
    undercuts    = geometry.get("feature_summary", {}).get("undercuts", [])

    # ── 1. Stok malzeme maliyeti ──────────────────────────────────────────
    removal_ratio  = STOCK_REMOVAL_RATIOS.get(technology, 0.50)
    stock_volume_cm3 = volume_cm3 / (1 - removal_ratio)  # Blank boyutu

    density = MATERIAL_DENSITIES.get(material, MATERIAL_DENSITIES["default"])
    stock_weight_kg = (stock_volume_cm3 * density) / 1000

    # Malzeme fiyatı: DB'den veya varsayılan
    if material_price_kg and material_price_kg > 0:
        mat_price_per_kg = material_price_kg
        price_source = "db_live"
    else:
        mat_price_per_kg = _default_material_price(material)
        price_source = "static_fallback"

    material_cost = stock_weight_kg * mat_price_per_kg

    # ── 2. Makine süresi (MRR tabanlı) ───────────────────────────────────
    machining_time_min, mrr_details = _calculate_machining_time(
        technology   = technology,
        material     = material,
        volume_cm3   = volume_cm3,
        dims         = dims,
        workload_idx = workload_idx,
        holes        = holes,
        pockets      = pockets,
    )

    machine_rate = MACHINE_RATES.get(technology, MACHINE_RATES["cnc_milling"])
    machine_cost = (machining_time_min / 60) * machine_rate["hourly_rate"]

    # ── 3. Setup maliyeti ─────────────────────────────────────────────────
    setup_cost = _calculate_setup_cost(
        technology   = technology,
        machine_rate = machine_rate,
        undercuts    = undercuts,
        complexity   = workload_idx,
    )

    # ── 4. Post-process maliyeti ──────────────────────────────────────────
    post_process_cost = _calculate_post_process(
        technology = technology,
        volume_cm3 = volume_cm3,
        surface_cm2 = surface_cm2,
        finish     = params.get("finish", "standard"),
    )

    # ── 5. EDM tel maliyeti (ekstra) ──────────────────────────────────────
    wire_cost = 0
    if technology == "edm":
        edm_params = MRR_PARAMS["edm"].get(material, MRR_PARAMS["edm"]["default"])
        wire_cost  = (machining_time_min / 60) * edm_params["wire_cost_hr"]

    # ── 6. Adet iskontosu ─────────────────────────────────────────────────
    discount = _quantity_discount_cnc(quantity, technology)

    # ── 7. Birim fiyat ────────────────────────────────────────────────────
    unit_cost_raw = material_cost + machine_cost + setup_cost + post_process_cost + wire_cost
    unit_cost     = unit_cost_raw * (1 - discount)
    unit_price    = unit_cost / (1 - PLATFORM_MARGIN)
    total_price   = unit_price * quantity

    # ── 8. Manual Quote değerlendirme ────────────────────────────────────
    mq_result = evaluate_manual_quote(
        geometry   = {**geometry, "type": "cnc"},
        params     = params,
        unit_price = unit_price,
    )

    return {
        "currency"         : "USD",
        "unit_price"       : round(unit_price, 2),
        "total_price"      : round(total_price, 2),
        "quantity"         : quantity,
        "quantity_discount_pct": round(discount * 100, 1),
        "price_source"     : price_source,
        "phase"            : "faz-5",
        "manual_quote"     : mq_result["manual_quote"],
        "auto_price_allowed": mq_result["auto_price_allowed"],
        "quote_triggers"   : mq_result["triggers"],
        "quote_warnings"   : mq_result["warnings"],
        "breakdown": {
            "material_cost"     : round(material_cost, 4),
            "machine_cost"      : round(machine_cost, 4),
            "setup_cost"        : round(setup_cost, 4),
            "post_process_cost" : round(post_process_cost, 4),
            "wire_cost"         : round(wire_cost, 4),
            "stock_weight_kg"   : round(stock_weight_kg, 4),
            "machining_time_min": round(machining_time_min, 2),
            "stock_removal_ratio": removal_ratio,
            "platform_margin_pct": round(PLATFORM_MARGIN * 100, 1),
            "mrr_details"       : mrr_details,
        },
        "confidence"       : _confidence_cnc(workload_idx, geometry),
        "routing"          : _routing_recommendation_cnc(geometry, technology),
    }


# ── MRR Hesap Fonksiyonları ─────────────────────────────────────────────────

def _calculate_machining_time(
    technology: str, material: str, volume_cm3: float,
    dims: dict, workload_idx: float,
    holes: list, pockets: list,
) -> tuple:
    """Makine süresini dakika cinsinden hesaplar. (süre, detay_dict)"""

    if technology == "cnc_milling":
        return _milling_time(material, volume_cm3, dims, workload_idx, holes, pockets)
    elif technology == "cnc_turning":
        return _turning_time(material, volume_cm3, dims, workload_idx)
    elif technology == "edm":
        return _edm_time(material, volume_cm3, dims, workload_idx)
    else:
        # Fallback: saatlik ücret × basit tahmin
        time = max(volume_cm3 / 5, 10)
        return time, {"method": "fallback"}


def _milling_time(material, volume_cm3, dims, workload_idx, holes, pockets) -> tuple:
    """
    CNC Freze süresi — MRR tabanlı.
    MRR (cm³/dk) = Vc × fz × z × ae × ap / (π × D × 10)
    D: takım çapı (varsayılan 10mm)
    """
    p = MRR_PARAMS["cnc_milling"].get(material, MRR_PARAMS["cnc_milling"]["default"])

    D_mm    = 10.0  # takım çapı
    n_rpm   = (p["Vc"] * 1000) / (np.pi * D_mm)  # devir/dk
    Vf_mm_min = p["fz"] * p["z"] * n_rpm  # ilerleme hızı mm/dk

    # Kaldırılacak hacim (talaş)
    removal_ratio = STOCK_REMOVAL_RATIOS["cnc_milling"]
    chip_volume_cm3 = volume_cm3 * (removal_ratio / (1 - removal_ratio))

    ae_mm = D_mm * p["ae_ratio"]  # radyal paso
    ap_mm = D_mm * p["ap_ratio"]  # eksenel paso

    # MRR = Vf × ae × ap (mm³/dk) → cm³/dk
    mrr_cm3_min = (Vf_mm_min * ae_mm * ap_mm) / 1000

    # Temel işleme süresi
    base_time_min = chip_volume_cm3 / mrr_cm3_min if mrr_cm3_min > 0 else 30

    # Karmaşıklık çarpanı
    complexity_mult = 1 + (workload_idx / 100) * 1.5

    # Delik ve cep katkısı
    hole_time  = len(holes) * 2.5   # Her delik ~2.5 dk
    pocket_time = len(pockets) * 8  # Her cep ~8 dk

    total_time = base_time_min * complexity_mult + hole_time + pocket_time

    return round(total_time, 2), {
        "method"        : "mrr_milling",
        "n_rpm"         : round(n_rpm, 1),
        "feed_rate_mm_min": round(Vf_mm_min, 1),
        "mrr_cm3_min"   : round(mrr_cm3_min, 4),
        "chip_volume_cm3": round(chip_volume_cm3, 4),
        "complexity_mult": round(complexity_mult, 3),
        "hole_time_min" : round(hole_time, 2),
        "pocket_time_min": round(pocket_time, 2),
    }


def _turning_time(material, volume_cm3, dims, workload_idx) -> tuple:
    """
    CNC Torna süresi — MRR tabanlı.
    MRR (cm³/dk) = π × D × ap × f × n / 1000
    """
    p = MRR_PARAMS["cnc_turning"].get(material, MRR_PARAMS["cnc_turning"]["default"])

    D_mm    = max(dims.get("x_mm", 50), dims.get("y_mm", 50))  # çap tahmini
    n_rpm   = (p["Vc"] * 1000) / (np.pi * D_mm)  # devir/dk

    # MRR = π × D × ap × f × n / 1000 (cm³/dk)
    mrr_cm3_min = (np.pi * D_mm * p["ap"] * p["f"] * n_rpm) / 1_000_000 * 1000

    removal_ratio  = STOCK_REMOVAL_RATIOS["cnc_turning"]
    chip_volume_cm3 = volume_cm3 * (removal_ratio / (1 - removal_ratio))

    base_time_min = chip_volume_cm3 / mrr_cm3_min if mrr_cm3_min > 0 else 20
    complexity_mult = 1 + (workload_idx / 100) * 0.8  # Torna daha az karmaşık

    total_time = base_time_min * complexity_mult

    return round(total_time, 2), {
        "method"           : "mrr_turning",
        "diameter_mm"      : round(D_mm, 2),
        "n_rpm"            : round(n_rpm, 1),
        "mrr_cm3_min"      : round(mrr_cm3_min, 4),
        "chip_volume_cm3"  : round(chip_volume_cm3, 4),
        "complexity_mult"  : round(complexity_mult, 3),
    }


def _edm_time(material, volume_cm3, dims, workload_idx) -> tuple:
    """
    EDM Tel Erozyon süresi — penetrasyon hızı tabanlı.
    Kesim uzunluğu = bounding box çevresi × yükseklik
    """
    p = MRR_PARAMS["edm"].get(material, MRR_PARAMS["edm"]["default"])

    # Kesim yüksekliği (iş parçası yüksekliği)
    cut_height_mm = dims.get("z_mm", 20)

    # Tahmini kesim uzunluğu (çevre tahmini bounding box'tan)
    perimeter_mm = 2 * (dims.get("x_mm", 50) + dims.get("y_mm", 50))

    # Penetrasyon hızı → mm/saat
    pen_rate = p["penetration_mm_hr"]

    # Kesim süresi: uzunluk × yükseklik / penetrasyon alanı (basitleştirilmiş)
    # Tel EDM'de süre = toplam kesim yüzeyi alanı / penetrasyon hızı
    cut_area_mm2 = perimeter_mm * cut_height_mm  # mm²
    pen_rate_area = pen_rate * cut_height_mm     # mm²/saat (basitleştirilmiş)

    base_time_hr = cut_area_mm2 / pen_rate_area if pen_rate_area > 0 else 2
    base_time_min = base_time_hr * 60

    complexity_mult = 1 + (workload_idx / 100) * 1.2

    total_time = base_time_min * complexity_mult

    return round(total_time, 2), {
        "method"          : "edm_penetration",
        "cut_height_mm"   : cut_height_mm,
        "perimeter_mm"    : round(perimeter_mm, 2),
        "penetration_mm_hr": pen_rate,
        "complexity_mult" : round(complexity_mult, 3),
    }


# ── Yardımcı Fonksiyonlar ────────────────────────────────────────────────────

def _default_material_price(material: str) -> float:
    """Statik fallback malzeme fiyatı (USD/kg)."""
    defaults = {
        "aluminum"       : 3.50,
        "steel"          : 1.20,
        "mild_steel"     : 1.00,
        "stainless_steel": 3.80,
        "ss304"          : 3.80,
        "ss316l"         : 5.50,
        "titanium"       : 35.00,
        "ti6al4v"        : 40.00,
        "copper"         : 9.50,
        "tool_steel"     : 4.00,
        "default"        : 2.50,
    }
    return defaults.get(material, defaults["default"])


def _calculate_setup_cost(technology, machine_rate, undercuts, complexity) -> float:
    base_setup = machine_rate.get("setup_cost", 15.0)
    # Undercut = ek fixture/setup
    if undercuts:
        base_setup *= 2.0
    # Çok karmaşık = daha uzun setup
    if complexity > 70:
        base_setup *= 1.5
    return round(base_setup, 2)


def _calculate_post_process(technology, volume_cm3, surface_cm2, finish) -> float:
    """Post-process maliyeti."""
    base = 0
    if technology in ("cnc_milling", "cnc_turning"):
        # Deburring (çapak alma) standart
        base = surface_cm2 * 0.02
        if finish in ("anodize", "anodize_color", "hard_anodize"):
            base += surface_cm2 * 0.15
        elif finish in ("polish", "mirror_polish"):
            base += surface_cm2 * 0.25
        elif finish == "powder_coat":
            base += surface_cm2 * 0.10
    elif technology == "edm":
        # EDM zaten hassas yüzey — minimum post-process
        base = 5.0
    return round(max(base, 2.0), 2)


def _quantity_discount_cnc(quantity: int, technology: str) -> float:
    """CNC için adet iskontosu — 3D baskıdan daha agresif."""
    if quantity <= 1:
        return 0.0
    elif quantity <= 5:
        return 0.05
    elif quantity <= 20:
        return 0.12
    elif quantity <= 100:
        return 0.20
    else:
        return 0.28


def _confidence_cnc(workload_idx: float, geometry: dict) -> dict:
    """Fiyat güvenilirlik skoru."""
    # STL'den CNC feature tespiti yaklaşımsal — orta güven
    base_confidence = 0.65

    if geometry.get("is_watertight"):
        base_confidence += 0.10

    # Düşük karmaşıklık = daha güvenilir
    if workload_idx < 30:
        base_confidence += 0.10

    score = min(base_confidence, 0.85)
    label = "high" if score > 0.75 else "medium" if score > 0.55 else "low"

    return {
        "score": round(score, 2),
        "label": label,
        "note" : "STL'den feature tespiti yaklaşımsal. STEP dosyası daha yüksek doğruluk sağlar.",
    }


def _routing_recommendation_cnc(geometry: dict, technology: str) -> dict:
    """Üretim routing önerisi."""
    rotational = geometry.get("rotational_analysis", {})
    undercuts  = geometry.get("feature_summary", {}).get("undercut_count", 0)
    workload   = geometry.get("workload_index", 30)

    if rotational.get("is_rotational") and technology != "cnc_turning":
        return {"recommended": "cnc_turning", "reason": "Rotasyonel simetri tespit edildi — torna daha verimli"}
    if undercuts > 0:
        return {"recommended": "cnc_5axis", "reason": "Undercut var — 5-eksen CNC veya özel fixture gerekli"}
    if workload > 80:
        return {"recommended": "manual_quote", "reason": "Yüksek karmaşıklık — manuel değerlendirme önerilir"}

    return {"recommended": technology, "reason": "Mevcut teknoloji uygun"}


import numpy as np
