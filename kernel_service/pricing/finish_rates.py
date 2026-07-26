"""
Faz-2 — Finish / Color / Resolution / Hardness Fiyat Etkileri

Her parametre için iki şey tanımlanır:
  - multiplier : birim fiyata yüzdelik etki (1.0 = değişim yok)
  - flat_cost  : birim başına sabit ek maliyet (USD) — kaplama, boyama gibi işlemler için

Nihai hesaplama:
  unit_price_with_options = unit_price_base * multiplier_product + sum(flat_costs)

Teknoloji kısıtlaması:
  Her seçenek hangi teknolojilere uygulanabildiğini "technologies" listesinde belirtir.
  Boş liste → tüm teknolojiler.
"""

# ──────────────────────────────────────────────────────────────
# FİNISH (Yüzey İşlemi)
# ──────────────────────────────────────────────────────────────
FINISH_RATES = {
    # key               : {multiplier, flat_cost, technologies, label_tr}
    "standard"          : {"multiplier": 1.00, "flat_cost": 0.0,  "technologies": [],                        "label": "Standard"},
    "natural"           : {"multiplier": 1.00, "flat_cost": 0.0,  "technologies": ["sla"],                   "label": "Natural"},
    "matte"             : {"multiplier": 1.03, "flat_cost": 0.0,  "technologies": ["sla"],                   "label": "Matte"},
    "vapor_smoothing"   : {"multiplier": 1.08, "flat_cost": 0.5,  "technologies": ["sls", "mjf", "fdm"],     "label": "Vapor Smoothing"},
    "media_blast"       : {"multiplier": 1.05, "flat_cost": 0.3,  "technologies": ["sls", "mjf"],            "label": "Media Blast / Polish"},
    "bead_blast"        : {"multiplier": 1.06, "flat_cost": 0.5,  "technologies": ["cnc_milling", "cnc_turning", "dmls"], "label": "Bead Blast"},
    "anodize_clear"     : {"multiplier": 1.10, "flat_cost": 2.0,  "technologies": ["cnc_milling", "cnc_turning"], "label": "Anodize (Clear)"},
    "anodize_color"     : {"multiplier": 1.12, "flat_cost": 3.0,  "technologies": ["cnc_milling", "cnc_turning"], "label": "Anodize (Color)"},
    "powder_coating"    : {"multiplier": 1.12, "flat_cost": 4.0,  "technologies": ["laser", "bending", "cnc_milling"], "label": "Powder Coating"},
    "nickel_plating"    : {"multiplier": 1.15, "flat_cost": 5.0,  "technologies": ["sls", "mjf", "dmls"],    "label": "Nickel Plating"},
    "painting"          : {"multiplier": 1.08, "flat_cost": 2.5,  "technologies": ["fdm", "sla", "sls", "mjf"], "label": "Painting (RAL)"},
    "sandpaper_300"     : {"multiplier": 1.04, "flat_cost": 0.5,  "technologies": ["fdm", "sla"],            "label": "Sanding (300 grit)"},
    "sandpaper_1000"    : {"multiplier": 1.07, "flat_cost": 1.0,  "technologies": ["fdm", "sla"],            "label": "Sanding (1000 grit)"},
    "passivation"       : {"multiplier": 1.05, "flat_cost": 2.0,  "technologies": ["dmls", "cnc_milling"],   "label": "Passivation"},
    "electropolish"     : {"multiplier": 1.12, "flat_cost": 6.0,  "technologies": ["dmls"],                  "label": "Electropolishing"},
}

# ──────────────────────────────────────────────────────────────
# COLOR (Renk) — ağırlıklı olarak SLS/MJF/Polyjet için
# ──────────────────────────────────────────────────────────────
COLOR_RATES = {
    # MJF / SLS renk seçenekleri
    "natural_grey"      : {"multiplier": 1.00, "flat_cost": 0.0,  "technologies": ["sls", "mjf"],            "label": "Natural Grey"},
    "black_dyed"        : {"multiplier": 1.04, "flat_cost": 0.5,  "technologies": ["sls", "mjf"],            "label": "Black (Dyed)"},
    "white_dyed"        : {"multiplier": 1.04, "flat_cost": 0.5,  "technologies": ["sls", "mjf"],            "label": "White (Dyed)"},
    "color_dyed"        : {"multiplier": 1.06, "flat_cost": 1.0,  "technologies": ["sls", "mjf"],            "label": "Custom Color (Dyed)"},
    # FDM filament rengi — filament fiyatına yansır, ek maliyet yok
    "filament_color"    : {"multiplier": 1.00, "flat_cost": 0.0,  "technologies": ["fdm"],                   "label": "Filament Color (no cost)"},
    # SLA reçine rengi
    "resin_color"       : {"multiplier": 1.02, "flat_cost": 0.0,  "technologies": ["sla"],                   "label": "Colored Resin"},
    # Metal — renk yok
    "none"              : {"multiplier": 1.00, "flat_cost": 0.0,  "technologies": [],                        "label": "N/A"},
}

# ──────────────────────────────────────────────────────────────
# RESOLUTION / LAYER HEIGHT (3D baskı kalite seviyesi)
# Katman yüksekliği zaten baskı süresini doğrudan etkiliyor.
# Buradaki çarpan setup/işçilik kalitesini yansıtır (makine süresine ek).
# ──────────────────────────────────────────────────────────────
RESOLUTION_RATES = {
    # key        : {multiplier, layer_height_mm, technologies, label}
    "draft"      : {"multiplier": 0.90, "layer_height_mm": 0.30, "technologies": ["fdm"],              "label": "Draft (0.30mm)"},
    "standard"   : {"multiplier": 1.00, "layer_height_mm": 0.20, "technologies": ["fdm"],              "label": "Standard (0.20mm)"},
    "fine"       : {"multiplier": 1.10, "layer_height_mm": 0.12, "technologies": ["fdm"],              "label": "Fine (0.12mm)"},
    "ultra"      : {"multiplier": 1.25, "layer_height_mm": 0.06, "technologies": ["fdm"],              "label": "Ultra (0.06mm)"},
    # SLA
    "sla_50"     : {"multiplier": 1.00, "layer_height_mm": 0.05, "technologies": ["sla"],              "label": "Standard (0.05mm)"},
    "sla_25"     : {"multiplier": 1.20, "layer_height_mm": 0.025,"technologies": ["sla"],              "label": "High Res (0.025mm)"},
    # SLS/MJF — layer height sabit, sadece "standart" var
    "sls_std"    : {"multiplier": 1.00, "layer_height_mm": 0.10, "technologies": ["sls", "mjf"],       "label": "Standard (0.10mm)"},
    # DMLS
    "dmls_std"   : {"multiplier": 1.00, "layer_height_mm": 0.03, "technologies": ["dmls"],             "label": "Standard (0.03mm)"},
    "dmls_fine"  : {"multiplier": 1.20, "layer_height_mm": 0.02, "technologies": ["dmls"],             "label": "Fine (0.02mm)"},
}

# ──────────────────────────────────────────────────────────────
# INFILL (Dolgu) — sadece FDM
# Çarpan yok — infill oranı doğrudan hacim hesabına girer (engine.py).
# Burada sadece "kalite etiketi" → float oranı eşlemesi var.
# ──────────────────────────────────────────────────────────────
INFILL_PRESETS = {
    "sparse"     : {"ratio": 0.10, "label": "Sparse (%10) — prototip"},
    "standard"   : {"ratio": 0.20, "label": "Standard (%20) — genel kullanım"},
    "solid"      : {"ratio": 0.40, "label": "Solid (%40) — dayanıklı parça"},
    "full"       : {"ratio": 1.00, "label": "Full (%100) — maksimum güç"},
}

# ──────────────────────────────────────────────────────────────
# HARDNESS / SHORE (TPU/Esnek malzemeler için)
# Shore değeri, malzeme seçimini yönlendirir — farklı hardness = farklı material_key
# Burada sadece çarpan farkı modellenir (daha sert TPU genelde daha pahalı)
# ──────────────────────────────────────────────────────────────
HARDNESS_RATES = {
    # key          : {multiplier, shore_a, technologies, material_hint, label}
    "shore_45a"    : {"multiplier": 1.00, "shore_a": 45,  "technologies": ["fdm", "sls"],  "material_hint": "tpu",    "label": "Shore 45A (çok yumuşak)"},
    "shore_60a"    : {"multiplier": 1.00, "shore_a": 60,  "technologies": ["fdm", "sls"],  "material_hint": "tpu",    "label": "Shore 60A (yumuşak)"},
    "shore_85a"    : {"multiplier": 1.02, "shore_a": 85,  "technologies": ["fdm", "sls"],  "material_hint": "tpu",    "label": "Shore 85A (orta)"},
    "shore_95a"    : {"multiplier": 1.05, "shore_a": 95,  "technologies": ["fdm", "sls"],  "material_hint": "tpu",    "label": "Shore 95A (sert esnek)"},
    "standard"     : {"multiplier": 1.00, "shore_a": None, "technologies": [],             "material_hint": None,     "label": "Standard (sabit malzeme)"},
}

# ──────────────────────────────────────────────────────────────
# TOLERANCE CLASS (CNC, Laser için)
# ──────────────────────────────────────────────────────────────
TOLERANCE_RATES = {
    "standard"   : {"multiplier": 1.00, "tolerance_mm": 0.5,  "technologies": [],                              "label": "Standard (±0.5mm)"},
    "medium"     : {"multiplier": 1.10, "tolerance_mm": 0.2,  "technologies": ["laser", "cnc_milling"],        "label": "Medium (±0.2mm)"},
    "fine"       : {"multiplier": 1.25, "tolerance_mm": 0.1,  "technologies": ["cnc_milling", "cnc_turning"],  "label": "Fine (±0.1mm)"},
    "ultra"      : {"multiplier": 1.45, "tolerance_mm": 0.05, "technologies": ["cnc_milling", "cnc_turning"],  "label": "Ultra (±0.05mm)"},
}

# ──────────────────────────────────────────────────────────────
# CERTIFICATIONS / QUALITY EXTRAS
# ──────────────────────────────────────────────────────────────
CERT_RATES = {
    "none"           : {"multiplier": 1.00, "flat_cost": 0.0,  "label": "Sertifika yok"},
    "material_cert"  : {"multiplier": 1.00, "flat_cost": 8.0,  "label": "Malzeme Sertifikası (CoC)"},
    "first_article"  : {"multiplier": 1.00, "flat_cost": 25.0, "label": "First Article Inspection (FAI)"},
    "iso_inspection" : {"multiplier": 1.00, "flat_cost": 50.0, "label": "ISO Boyutsal Rapor"},
}


# ──────────────────────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
# ──────────────────────────────────────────────────────────────

def resolve_finish(finish_key: str, technology: str) -> dict:
    """Finish seçimini çöz — teknoloji uyumunu kontrol et."""
    rate = FINISH_RATES.get(finish_key, FINISH_RATES["standard"])
    allowed = rate["technologies"]
    if allowed and technology not in allowed:
        # Uyumsuz seçim → standard'a düş, uyarı ekle
        return {**FINISH_RATES["standard"], "warning": f"'{finish_key}' bu teknoloji için geçerli değil, Standard uygulandı"}
    return rate

def resolve_color(color_key: str, technology: str) -> dict:
    rate = COLOR_RATES.get(color_key, COLOR_RATES["none"])
    allowed = rate["technologies"]
    if allowed and technology not in allowed:
        return {**COLOR_RATES["none"], "warning": f"'{color_key}' bu teknoloji için geçerli değil"}
    return rate

def resolve_resolution(res_key: str, technology: str) -> dict:
    rate = RESOLUTION_RATES.get(res_key, RESOLUTION_RATES.get("standard", {}))
    if not rate:
        return {"multiplier": 1.0, "layer_height_mm": 0.2}
    allowed = rate.get("technologies", [])
    if allowed and technology not in allowed:
        return {"multiplier": 1.0, "layer_height_mm": 0.2, "warning": f"'{res_key}' bu teknoloji için geçerli değil"}
    return rate

def resolve_hardness(hardness_key: str, technology: str) -> dict:
    rate = HARDNESS_RATES.get(hardness_key, HARDNESS_RATES["standard"])
    allowed = rate["technologies"]
    if allowed and technology not in allowed:
        return {**HARDNESS_RATES["standard"], "warning": f"'{hardness_key}' bu teknoloji için geçerli değil"}
    return rate

def resolve_tolerance(tol_key: str, technology: str) -> dict:
    rate = TOLERANCE_RATES.get(tol_key, TOLERANCE_RATES["standard"])
    allowed = rate["technologies"]
    if allowed and technology not in allowed:
        return {**TOLERANCE_RATES["standard"], "warning": f"'{tol_key}' bu teknoloji için geçerli değil"}
    return rate

def resolve_cert(cert_key: str) -> dict:
    return CERT_RATES.get(cert_key, CERT_RATES["none"])


def apply_options(base_unit_price: float, technology: str, options: dict) -> dict:
    """
    Tüm seçim parametrelerini birim fiyata uygula.
    options: {finish, color, resolution, hardness, tolerance, certification}
    Döndürür: {final_unit_price, total_multiplier, total_flat, warnings, breakdown}
    """
    warnings = []
    breakdown = {}

    # Her parametre
    finish_r   = resolve_finish(options.get("finish", "standard"), technology)
    color_r    = resolve_color(options.get("color", "none"), technology)
    res_r      = resolve_resolution(options.get("resolution", "standard"), technology)
    hard_r     = resolve_hardness(options.get("hardness", "standard"), technology)
    tol_r      = resolve_tolerance(options.get("tolerance", "standard"), technology)
    cert_r     = resolve_cert(options.get("certification", "none"))

    # Uyarıları topla
    for r, name in [(finish_r,"finish"),(color_r,"color"),(res_r,"resolution"),(hard_r,"hardness"),(tol_r,"tolerance")]:
        if r.get("warning"):
            warnings.append(r["warning"])

    # Toplam çarpan
    total_multiplier = (
        finish_r.get("multiplier", 1.0) *
        color_r.get("multiplier", 1.0) *
        res_r.get("multiplier", 1.0) *
        hard_r.get("multiplier", 1.0) *
        tol_r.get("multiplier", 1.0)
    )

    # Toplam sabit ek maliyet
    total_flat = (
        finish_r.get("flat_cost", 0.0) +
        color_r.get("flat_cost", 0.0) +
        cert_r.get("flat_cost", 0.0)
    )

    # MoR modeli: ek maliyetleri de margin üzerinden fiyatlandır
    final_unit_price = (base_unit_price * total_multiplier) + (total_flat / (1 - 0.28))

    breakdown = {
        "finish"         : {"key": options.get("finish","standard"),        "multiplier": finish_r.get("multiplier",1.0), "flat": finish_r.get("flat_cost",0.0)},
        "color"          : {"key": options.get("color","none"),             "multiplier": color_r.get("multiplier",1.0),  "flat": color_r.get("flat_cost",0.0)},
        "resolution"     : {"key": options.get("resolution","standard"),    "multiplier": res_r.get("multiplier",1.0),    "layer_height_override": res_r.get("layer_height_mm")},
        "hardness"       : {"key": options.get("hardness","standard"),      "multiplier": hard_r.get("multiplier",1.0)},
        "tolerance"      : {"key": options.get("tolerance","standard"),     "multiplier": tol_r.get("multiplier",1.0)},
        "certification"  : {"key": options.get("certification","none"),     "flat": cert_r.get("flat_cost",0.0)},
        "total_multiplier": round(total_multiplier, 4),
        "total_flat_cost" : round(total_flat, 4),
    }

    return {
        "final_unit_price": round(final_unit_price, 2),
        "base_unit_price" : round(base_unit_price, 2),
        "total_multiplier": round(total_multiplier, 4),
        "total_flat_usd"  : round(total_flat, 4),
        "warnings"        : warnings,
        "options_breakdown": breakdown,
    }
