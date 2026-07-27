"""
Faz-2 — Finish / Color / Resolution / Infill / Hardness / Tolerance / Certification

Platform kaynak: app.shapelid.com
  - MaterialFinish entity  → FINISH_RATES
  - MaterialColor entity   → COLOR_RATES
  - SpecOption entity      → RESOLUTION_RATES, INFILL_PRESETS, HARDNESS_RATES
  - pricing/tolerance      → TOLERANCE_RATES

Tüm finish key'leri platform'un MaterialFinish.title değerlerinden türetilmiştir.
Key kuralı: title.lower().strip().replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '').replace('-', '_')

Nihai hesaplama (engine.py içinde):
  unit_price_with_options = unit_price_base
                            × prod(multipliers)
                            + sum(flat_costs) / (1 - take_rate)
"""

from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# FINISH (Yüzey İşlemi) — Kaynak: MaterialFinish entity
# Her key = platform'daki MaterialFinish.title'dan türetilmiş slug
# ─────────────────────────────────────────────────────────────────────────────
FINISH_RATES = {

    # ── GENEL / TÜM TEKNOLOJİLER ──────────────────────────────────────────
    "standard": {
        "multiplier": 1.00, "flat_cost": 0.0,
        "technologies": [],
        "label": "Standard",
    },
    "other": {
        "multiplier": 1.00, "flat_cost": 0.0,
        "technologies": [],
        "label": "Other",
    },
    "custom": {
        "multiplier": 1.00, "flat_cost": 0.0,
        "technologies": [],
        "label": "Custom",
    },
    "as_cast": {
        "multiplier": 1.00, "flat_cost": 0.0,
        "technologies": ["die_casting", "vacuum_casting"],
        "label": "As Cast",
    },

    # ── MEKANİK YÜZEY İŞLEMİ ─────────────────────────────────────────────
    "bead_blast": {
        "multiplier": 1.06, "flat_cost": 0.5,
        "technologies": [
            "cnc_machining", "cnc_milling", "cnc_turning",
            "dmls", "laser", "bending"
        ],
        "label": "Bead Blast",
    },
    "bead_blasting": {
        "multiplier": 1.06, "flat_cost": 0.5,
        "technologies": [
            "cnc_machining", "cnc_milling", "cnc_turning",
            "dmls", "laser", "bending"
        ],
        "label": "Bead Blasting",
    },
    "electropolishing": {
        "multiplier": 1.12, "flat_cost": 6.0,
        "technologies": ["dmls", "cnc_machining", "cnc_milling", "cnc_turning"],
        "label": "Electropolishing",
    },

    # ── KAPLAMA / PLATING ─────────────────────────────────────────────────
    "nickel_plating": {
        "multiplier": 1.14, "flat_cost": 5.0,
        "technologies": ["cnc_machining", "cnc_milling", "cnc_turning", "dmls"],
        "label": "Nickel Plating",
    },
    "electroless_nickel_plating": {
        "multiplier": 1.14, "flat_cost": 5.0,
        "technologies": ["cnc_machining", "cnc_milling", "cnc_turning", "dmls", "laser"],
        "label": "Electroless Nickel Plating",
    },
    "gold_plating": {
        "multiplier": 1.20, "flat_cost": 12.0,
        "technologies": ["cnc_machining", "cnc_milling", "cnc_turning", "dmls"],
        "label": "Gold Plating",
    },
    "silver_plating": {
        "multiplier": 1.16, "flat_cost": 8.0,
        "technologies": ["cnc_machining", "cnc_milling", "cnc_turning", "dmls"],
        "label": "Silver Plating",
    },
    "electrolytic_zinc": {
        "multiplier": 1.08, "flat_cost": 2.5,
        "technologies": ["cnc_machining", "laser", "bending"],
        "label": "Electrolytic Zinc",
    },
    "zinc_coating___galvanising": {
        "multiplier": 1.08, "flat_cost": 3.0,
        "technologies": ["laser", "bending", "cnc_machining"],
        "label": "Zinc Coating / Galvanising",
    },
    "chromate_conversion": {
        "multiplier": 1.07, "flat_cost": 2.0,
        "technologies": ["cnc_machining", "cnc_milling", "cnc_turning"],
        "label": "Chromate Conversion",
    },

    # ── ANODİZİNG ─────────────────────────────────────────────────────────
    "anodising": {
        "multiplier": 1.10, "flat_cost": 3.0,
        "technologies": ["cnc_machining", "cnc_milling", "cnc_turning", "laser", "bending"],
        "label": "Anodising",
    },
    "anodising_hardcoat": {
        "multiplier": 1.14, "flat_cost": 5.0,
        "technologies": ["cnc_machining", "cnc_milling", "cnc_turning"],
        "label": "Anodising Hardcoat",
    },

    # ── TOZ BOYA / PAINT ──────────────────────────────────────────────────
    "powder_coating": {
        "multiplier": 1.12, "flat_cost": 4.0,
        "technologies": ["laser", "bending", "cnc_machining", "cnc_milling", "cnc_turning"],
        "label": "Powder Coating",
    },
    "paint": {
        "multiplier": 1.08, "flat_cost": 2.5,
        "technologies": ["fdm", "sla", "sls", "mjf", "cnc_machining", "laser", "bending"],
        "label": "Paint (RAL)",
    },

    # ── KİMYASAL DÖNÜŞÜM ──────────────────────────────────────────────────
    "passivation": {
        "multiplier": 1.05, "flat_cost": 2.0,
        "technologies": ["dmls", "cnc_machining", "cnc_milling", "cnc_turning"],
        "label": "Passivation",
    },
    "passivate": {
        "multiplier": 1.05, "flat_cost": 2.0,
        "technologies": ["dmls", "cnc_machining", "cnc_milling", "cnc_turning"],
        "label": "Passivate",
    },
    "black_oxide": {
        "multiplier": 1.06, "flat_cost": 2.0,
        "technologies": ["cnc_machining", "cnc_milling", "cnc_turning", "laser", "bending"],
        "label": "Black Oxide",
    },

    # ── ISI İŞLEMİ ────────────────────────────────────────────────────────
    "annealing": {
        "multiplier": 1.08, "flat_cost": 3.0,
        "technologies": ["cnc_machining", "cnc_milling", "cnc_turning", "dmls", "laser"],
        "label": "Annealing",
    },
    "tempering": {
        "multiplier": 1.06, "flat_cost": 2.5,
        "technologies": ["cnc_machining", "cnc_milling", "cnc_turning", "laser"],
        "label": "Tempering",
    },
    "through_hardening": {
        "multiplier": 1.10, "flat_cost": 4.0,
        "technologies": ["cnc_machining", "cnc_milling", "cnc_turning"],
        "label": "Through Hardening",
    },
    "case_hardening": {
        "multiplier": 1.10, "flat_cost": 4.0,
        "technologies": ["cnc_machining", "cnc_milling", "cnc_turning"],
        "label": "Case Hardening",
    },
    "case_hardening_alt": {
        "multiplier": 1.10, "flat_cost": 4.0,
        "technologies": ["cnc_machining", "cnc_milling", "cnc_turning"],
        "label": "Case-Hardening",
    },

    # ── ENJEKSİYON KALIP YÜZEYI (SPI / VDI 3400) ─────────────────────────
    # SPI (Society of Plastics Industry) yüzey standartları — Injection Moulding
    "spi_a_3": {
        "multiplier": 1.30, "flat_cost": 8.0,
        "technologies": ["injection"],
        "label": "SPI A-3 (Yüksek Parlak)",
    },
    "spi_b_2": {
        "multiplier": 1.20, "flat_cost": 5.0,
        "technologies": ["injection"],
        "label": "SPI B-2 (Yarı Parlak)",
    },
    "spi_c_1": {
        "multiplier": 1.12, "flat_cost": 3.0,
        "technologies": ["injection"],
        "label": "SPI C-1 (Mat Pürüzsüz)",
    },
    "spi_c_2": {
        "multiplier": 1.10, "flat_cost": 2.5,
        "technologies": ["injection"],
        "label": "SPI C-2 (Mat)",
    },
    "spi_d_2": {
        "multiplier": 1.06, "flat_cost": 1.5,
        "technologies": ["injection"],
        "label": "SPI D-2 (Kaba Doku)",
    },
    "spi_d_3": {
        "multiplier": 1.04, "flat_cost": 1.0,
        "technologies": ["injection"],
        "label": "SPI D-3 (Kaba)",
    },
    # VDI 3400 — Injection Moulding kalıp dokusu standartları
    "vdi_12": {
        "multiplier": 1.04, "flat_cost": 1.0,
        "technologies": ["injection"],
        "label": "VDI-12 (VDI 3400) — Hafif Pürüzlü",
    },
    "vdi_21": {
        "multiplier": 1.06, "flat_cost": 1.5,
        "technologies": ["injection"],
        "label": "VDI-21 (VDI 3400)",
    },
    "vdi_24": {
        "multiplier": 1.07, "flat_cost": 2.0,
        "technologies": ["injection"],
        "label": "VDI-24 (VDI 3400)",
    },
    "vdi_27": {
        "multiplier": 1.08, "flat_cost": 2.0,
        "technologies": ["injection"],
        "label": "VDI-27 (VDI 3400)",
    },
    "vdi_36": {
        "multiplier": 1.10, "flat_cost": 2.5,
        "technologies": ["injection"],
        "label": "VDI-36 (VDI 3400) — Derin Doku",
    },
    "vdi_42": {
        "multiplier": 1.12, "flat_cost": 3.0,
        "technologies": ["injection"],
        "label": "VDI-42 (VDI 3400) — En Derin Doku",
    },

    # ── 3D BASKI ÖZEL ─────────────────────────────────────────────────────
    "natural": {
        "multiplier": 1.00, "flat_cost": 0.0,
        "technologies": ["sla", "sls", "mjf", "polyjet"],
        "label": "Natural",
    },
    "matte": {
        "multiplier": 1.03, "flat_cost": 0.0,
        "technologies": ["sla"],
        "label": "Matte",
    },
    "strip_and_ship": {
        "multiplier": 0.95, "flat_cost": 0.0,
        "technologies": ["sla"],
        "label": "Strip and Ship (Destek Sökümü)",
    },
    "quick_clear": {
        "multiplier": 1.08, "flat_cost": 1.5,
        "technologies": ["sla"],
        "label": "Quick Clear (SLA Şeffaf)",
    },
    "media_blast": {
        "multiplier": 1.05, "flat_cost": 0.3,
        "technologies": ["sls", "mjf"],
        "label": "Media Blast / Polish",
    },
    # ── FDM / SLS / MJF özel finish'leri ──────────────────────────────────
    "vapor_smoothing": {
        "label": "Vapor Smoothing",
        "multiplier": 1.35,
        "flat_cost": 3.5,
        "technologies": ["fdm", "sls", "mjf"],
        "description": "Solvent buharı ile yüzey pürüzsüzleştirme"
    },
    "dyeing": {
        "label": "Dyeing",
        "multiplier": 1.15,
        "flat_cost": 2.0,
        "technologies": ["sls", "mjf"],
        "description": "SLS/MJF parçaları için boyama"
    },
    "tumble_polishing": {
        "label": "Tumble Polishing",
        "multiplier": 1.12,
        "flat_cost": 1.5,
        "technologies": ["fdm", "sls", "mjf", "sla"],
        "description": "Döner tambur ile yüzey perdahlama"
    },
    "sanding": {
        "label": "Sanding",
        "multiplier": 1.18,
        "flat_cost": 2.0,
        "technologies": ["fdm", "sla", "sls"],
        "description": "Manuel zımpara ile yüzey düzeltme"
    },
    "priming": {
        "label": "Priming",
        "multiplier": 1.10,
        "flat_cost": 1.5,
        "technologies": ["fdm", "sla", "sls", "mjf"],
        "description": "Astar boya uygulama"
    },
    "clear_coating": {
        "label": "Clear Coating",
        "multiplier": 1.12,
        "flat_cost": 1.5,
        "technologies": ["fdm", "sla", "sls"],
        "description": "Şeffaf koruyucu kaplama"
    },
}

# Alias normalize tablosu — platform'dan gelen title → key eşleştirmesi
FINISH_ALIAS: dict[str, str] = {
    # Platform MaterialFinish.title → FINISH_RATES key
    "Standard": "standard",
    "Other": "other",
    "Custom": "custom",
    "As cast": "as_cast",
    "Bead Blast": "bead_blast",
    "Bead Blasting": "bead_blasting",
    "Electropolishing": "electropolishing",
    "Nickel Plating": "nickel_plating",
    "Electroless Nickel Plating": "electroless_nickel_plating",
    "Gold Plating": "gold_plating",
    "Silver Plating": "silver_plating",
    "Electrolytic Zinc": "electrolytic_zinc",
    "Zinc Coating / Galvanising": "zinc_coating___galvanising",
    "Chromate Conversion": "chromate_conversion",
    "Anodising": "anodising",
    "Anodising Hardcoat": "anodising_hardcoat",
    "Powder Coating": "powder_coating",
    "Paint": "paint",
    "Passivation": "passivation",
    "Passivate": "passivate",
    "Black Oxide": "black_oxide",
    "Annealing": "annealing",
    "Tempering": "tempering",
    "Through Hardening": "through_hardening",
    "Case Hardening": "case_hardening",
    "Case-Hardening": "case_hardening_alt",
    "SPI A-3": "spi_a_3",
    "SPI B-2": "spi_b_2",
    "SPI C-1": "spi_c_1",
    "SPI C-2": "spi_c_2",
    "SPI D-2": "spi_d_2",
    "SPI D-3": "spi_d_3",
    "VDI-12 (VDI 3400)": "vdi_12",
    "VDI-21 (VDI 3400)": "vdi_21",
    "VDI-24 (VDI 3400)": "vdi_24",
    "VDI-27 (VDI 3400)": "vdi_27",
    "VDI-36 (VDI 3400)": "vdi_36",
    "VDI-42 (VDI 3400)": "vdi_42",
    "Natural": "natural",
    "Matte": "matte",
    "Strip and Ship": "strip_and_ship",
    "Quick Clear": "quick_clear",
    "Media Blast": "media_blast",
}


# ─────────────────────────────────────────────────────────────────────────────
# COLOR (Renk) — Kaynak: MaterialColor entity
# ─────────────────────────────────────────────────────────────────────────────
COLOR_RATES = {
    # Renk ağırlıklı olarak SLS/MJF boyama veya 3D baskı malzeme rengi
    "natural":          {"multiplier": 1.00, "flat_cost": 0.0, "technologies": [], "label": "Natural"},
    "black":            {"multiplier": 1.00, "flat_cost": 0.0, "technologies": [], "label": "Black"},
    "white":            {"multiplier": 1.00, "flat_cost": 0.0, "technologies": [], "label": "White"},
    "gray":             {"multiplier": 1.00, "flat_cost": 0.0, "technologies": [], "label": "Gray"},
    "light_gray":       {"multiplier": 1.00, "flat_cost": 0.0, "technologies": [], "label": "Light Gray"},
    "dark_gray":        {"multiplier": 1.00, "flat_cost": 0.0, "technologies": [], "label": "Dark Gray"},
    "clear":            {"multiplier": 1.02, "flat_cost": 0.0, "technologies": ["sla", "injection"], "label": "Clear / Transparent"},
    # Boyalı renkler — ek maliyet SLS/MJF boyama için
    "red":              {"multiplier": 1.04, "flat_cost": 0.5, "technologies": ["sls", "mjf", "injection"], "label": "Red"},
    "blue":             {"multiplier": 1.04, "flat_cost": 0.5, "technologies": ["sls", "mjf", "injection"], "label": "Blue"},
    "green":            {"multiplier": 1.04, "flat_cost": 0.5, "technologies": ["sls", "mjf", "injection"], "label": "Green"},
    "yellow":           {"multiplier": 1.04, "flat_cost": 0.5, "technologies": ["sls", "mjf", "injection"], "label": "Yellow"},
    "orange":           {"multiplier": 1.04, "flat_cost": 0.5, "technologies": ["sls", "mjf", "injection"], "label": "Orange"},
    "purple":           {"multiplier": 1.04, "flat_cost": 0.5, "technologies": ["sls", "mjf", "injection"], "label": "Purple"},
    "pink_violet":      {"multiplier": 1.04, "flat_cost": 0.5, "technologies": ["sls", "mjf", "injection"], "label": "Pink / Violet"},
    "brown":            {"multiplier": 1.04, "flat_cost": 0.5, "technologies": ["sls", "mjf", "injection"], "label": "Brown"},
    "tan":              {"multiplier": 1.00, "flat_cost": 0.0, "technologies": [], "label": "Tan / Ivory"},
    "ivory":            {"multiplier": 1.00, "flat_cost": 0.0, "technologies": [], "label": "Ivory"},
    "milky_solid":      {"multiplier": 1.00, "flat_cost": 0.0, "technologies": ["vacuum_casting", "injection"], "label": "Milky Solid"},
    "other":            {"multiplier": 1.05, "flat_cost": 1.0, "technologies": [], "label": "Other (Custom)"},
    "none":             {"multiplier": 1.00, "flat_cost": 0.0, "technologies": [], "label": "N/A"},
}

# Alias — platform MaterialColor.title → COLOR_RATES key
COLOR_ALIAS: dict[str, str] = {
    "Natural": "natural", "Black": "black", "White": "white",
    "Gray": "gray", "Grey": "gray", "Light Gray": "light_gray",
    "Dark Gray": "dark_gray", "Clear": "clear", "Clear / Transparent": "clear",
    "Red": "red", "Blue": "blue", "Green": "green", "Yellow": "yellow",
    "Orange": "orange", "Purple": "purple", "Pink/Violet": "pink_violet",
    "Brown": "brown", "Tan": "tan", "Ivory": "ivory",
    "Milky Solid": "milky_solid", "Other": "other",
}


# ─────────────────────────────────────────────────────────────────────────────
# RESOLUTION / LAYER HEIGHT — Kaynak: SpecOption.resolution (Additive Mfg)
# Platform'daki değerler: "High", "Standard", "Draft"
# ─────────────────────────────────────────────────────────────────────────────
RESOLUTION_RATES = {
    # FDM
    "draft":    {"multiplier": 0.90, "layer_height_mm": 0.30, "technologies": ["fdm"],         "label": "Draft (0.30 mm)"},
    "standard": {"multiplier": 1.00, "layer_height_mm": 0.20, "technologies": ["fdm"],         "label": "Standard (0.20 mm)"},
    "high":     {"multiplier": 1.12, "layer_height_mm": 0.12, "technologies": ["fdm"],         "label": "High (0.12 mm)"},
    "ultra":    {"multiplier": 1.28, "layer_height_mm": 0.06, "technologies": ["fdm"],         "label": "Ultra Fine (0.06 mm)"},
    # SLA
    "sla_standard": {"multiplier": 1.00, "layer_height_mm": 0.05, "technologies": ["sla"],    "label": "Standard (0.05 mm)"},
    "sla_high":     {"multiplier": 1.22, "layer_height_mm": 0.025,"technologies": ["sla"],    "label": "High (0.025 mm)"},
    # SLS / MJF
    "sls_standard": {"multiplier": 1.00, "layer_height_mm": 0.10, "technologies": ["sls", "mjf"], "label": "Standard (0.10 mm)"},
    # DMLS
    "dmls_standard":{"multiplier": 1.00, "layer_height_mm": 0.03, "technologies": ["dmls"],   "label": "Standard (0.03 mm)"},
    "dmls_high":    {"multiplier": 1.22, "layer_height_mm": 0.02, "technologies": ["dmls"],   "label": "High (0.02 mm)"},
    # Polyjet (çok yüksek çözünürlük)
    "polyjet_std":  {"multiplier": 1.00, "layer_height_mm": 0.016,"technologies": ["polyjet"],"label": "Standard (16μm)"},
    "polyjet_high": {"multiplier": 1.15, "layer_height_mm": 0.014,"technologies": ["polyjet"],"label": "High (14μm)"},
}

# Platform SpecOption.resolution alanı virgülle ayrılmış string → parse edip ilk değeri kullanırız
RESOLUTION_ALIAS: dict[str, str] = {
    "Draft": "draft", "Standard": "standard",
    "High": "high", "Ultra": "ultra",
    "High, Standard": "high",  # SpecOption çift değer geldiğinde → en yükseği al
    "Standard, Standard": "standard",
}


# ─────────────────────────────────────────────────────────────────────────────
# INFILL (Dolgu Oranı) — Kaynak: SpecOption.infill
# Platform'daki değerler: "UltraLight, Light, Solid"
# Oranlar engine.py'daki hacim hesabına girer (doğrudan multiplier değil)
# ─────────────────────────────────────────────────────────────────────────────
INFILL_PRESETS = {
    "ultralight": {"ratio": 0.08, "label": "UltraLight (%8) — Hafif prototip"},
    "light":      {"ratio": 0.15, "label": "Light (%15) — Hafif kullanım"},
    "standard":   {"ratio": 0.20, "label": "Standard (%20) — Genel kullanım"},
    "solid":      {"ratio": 0.40, "label": "Solid (%40) — Dayanıklı parça"},
    "full":       {"ratio": 1.00, "label": "Full (%100) — Maksimum güç"},
}

INFILL_ALIAS: dict[str, str] = {
    "UltraLight": "ultralight", "ultralight": "ultralight",
    "Light": "light",           "light": "light",
    "Standard": "standard",     "standard": "standard",
    "Solid": "solid",           "solid": "solid",
    "Full": "full",             "full": "full",
}


# ─────────────────────────────────────────────────────────────────────────────
# HARDNESS / SHORE — Kaynak: SpecOption.hardness (TPU/Elastomer malzemeleri)
# ─────────────────────────────────────────────────────────────────────────────
HARDNESS_RATES = {
    "shore_40a":  {"multiplier": 1.00, "shore_a": 40,  "technologies": ["fdm", "sls", "injection"], "label": "Shore 40A (Çok Yumuşak)"},
    "shore_45a":  {"multiplier": 1.00, "shore_a": 45,  "technologies": ["fdm", "sls", "injection"], "label": "Shore 45A"},
    "shore_60a":  {"multiplier": 1.00, "shore_a": 60,  "technologies": ["fdm", "sls", "injection"], "label": "Shore 60A (Yumuşak)"},
    "shore_70a":  {"multiplier": 1.02, "shore_a": 70,  "technologies": ["fdm", "sls", "injection"], "label": "Shore 70A"},
    "shore_85a":  {"multiplier": 1.02, "shore_a": 85,  "technologies": ["fdm", "sls", "injection"], "label": "Shore 85A (Orta)"},
    "shore_95a":  {"multiplier": 1.05, "shore_a": 95,  "technologies": ["fdm", "sls", "injection"], "label": "Shore 95A (Sert Esnek)"},
    "standard":   {"multiplier": 1.00, "shore_a": None, "technologies": [],                          "label": "Standard"},
}


# ─────────────────────────────────────────────────────────────────────────────
# TOLERANCE CLASS — CNC / Laser için işleme hassasiyeti
# ─────────────────────────────────────────────────────────────────────────────
TOLERANCE_RATES = {
    "standard": {
        "multiplier": 1.00, "tolerance_mm": 0.5,
        "technologies": [],
        "label": "Standard (±0.5 mm)",
    },
    "medium": {
        "multiplier": 1.10, "tolerance_mm": 0.2,
        "technologies": ["laser", "bending", "cnc_machining", "cnc_milling", "cnc_turning", "sls", "mjf", "fdm"],
        "label": "Medium (±0.2 mm)",
    },
    "fine": {
        "multiplier": 1.25, "tolerance_mm": 0.1,
        "technologies": ["cnc_machining", "cnc_milling", "cnc_turning", "sls", "mjf", "dmls"],
        "label": "Fine (±0.1 mm)",
    },
    "ultra": {
        "multiplier": 1.45, "tolerance_mm": 0.05,
        "technologies": ["cnc_machining", "cnc_milling", "cnc_turning", "dmls"],
        "label": "Ultra (±0.05 mm)",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# CERTIFICATIONS / KALİTE EKSTRALERİ
# ─────────────────────────────────────────────────────────────────────────────
CERT_RATES = {
    "none":           {"multiplier": 1.00, "flat_cost": 0.0,  "label": "Sertifika Yok"},
    "material_cert":  {"multiplier": 1.00, "flat_cost": 8.0,  "label": "Malzeme Sertifikası (CoC)"},
    "first_article":  {"multiplier": 1.00, "flat_cost": 25.0, "label": "First Article Inspection (FAI)"},
    "iso_inspection": {"multiplier": 1.00, "flat_cost": 50.0, "label": "ISO Boyutsal Rapor"},
}


# ─────────────────────────────────────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
# ─────────────────────────────────────────────────────────────────────────────

def _normalize(raw: str) -> str:
    """Platform'dan gelen ham string'i key formatına çevir."""
    return (raw or "").strip().lower() \
        .replace(" ", "_").replace("/", "_").replace("-", "_") \
        .replace("(", "").replace(")", "").replace(",", "")


def resolve_finish(finish_input: str, technology: str) -> dict:
    """
    finish_input: platform MaterialFinish.title VEYA FINISH_RATES key
    technology  : kernel teknoloji kodu (fdm, sla, cnc_machining, ...)
    """
    # 1. Önce alias tablosunda ara (platform title → key)
    key = FINISH_ALIAS.get(finish_input) or _normalize(finish_input)
    rate = FINISH_RATES.get(key) or FINISH_RATES.get(finish_input)

    if rate is None:
        return {**FINISH_RATES["standard"],
                "warning": f"Finish '{finish_input}' tanımsız → Standard uygulandı"}

    allowed = rate.get("technologies", [])
    if allowed and technology not in allowed:
        return {**FINISH_RATES["standard"],
                "warning": f"'{finish_input}' {technology} için geçerli değil → Standard uygulandı"}

    return rate


def resolve_color(color_input: str, technology: str) -> dict:
    key = COLOR_ALIAS.get(color_input) or _normalize(color_input)
    rate = COLOR_RATES.get(key) or COLOR_RATES.get(color_input)

    if rate is None:
        return COLOR_RATES["none"]

    allowed = rate.get("technologies", [])
    if allowed and technology not in allowed:
        return COLOR_RATES["none"]

    return rate


def resolve_resolution(res_input: str, technology: str) -> dict:
    # SpecOption'dan virgüllü string gelebilir → ilk değeri al
    first = (res_input or "").split(",")[0].strip()
    key = RESOLUTION_ALIAS.get(first) or RESOLUTION_ALIAS.get(res_input) or _normalize(first)
    rate = RESOLUTION_RATES.get(key)

    if rate is None:
        # Teknolojiye göre default döndür
        defaults = {
            "fdm": "standard", "sla": "sla_standard",
            "sls": "sls_standard", "mjf": "sls_standard",
            "dmls": "dmls_standard", "polyjet": "polyjet_std",
        }
        return RESOLUTION_RATES.get(defaults.get(technology, "standard"),
                                    RESOLUTION_RATES["standard"])

    allowed = rate.get("technologies", [])
    if allowed and technology not in allowed:
        return RESOLUTION_RATES.get("standard", list(RESOLUTION_RATES.values())[0])

    return rate


def resolve_infill(infill_input: str) -> dict:
    # SpecOption'dan virgüllü string gelebilir → son değeri al (en yüksek olan)
    last = (infill_input or "standard").split(",")[-1].strip()
    key = INFILL_ALIAS.get(last) or INFILL_ALIAS.get(infill_input) or _normalize(last)
    return INFILL_PRESETS.get(key, INFILL_PRESETS["standard"])


def resolve_hardness(hardness_input: str, technology: str) -> dict:
    key = _normalize(hardness_input) if hardness_input else "standard"
    rate = HARDNESS_RATES.get(key, HARDNESS_RATES["standard"])
    allowed = rate.get("technologies", [])
    if allowed and technology not in allowed:
        return HARDNESS_RATES["standard"]
    return rate


def resolve_tolerance(tolerance_input: str, technology: str) -> dict:
    key = _normalize(tolerance_input) if tolerance_input else "standard"
    rate = TOLERANCE_RATES.get(key, TOLERANCE_RATES["standard"])
    allowed = rate.get("technologies", [])
    if allowed and technology not in allowed:
        return TOLERANCE_RATES["standard"]
    return rate


def resolve_certification(cert_input: str) -> dict:
    key = _normalize(cert_input) if cert_input else "none"
    return CERT_RATES.get(key, CERT_RATES["none"])


def apply_options(
    base_unit_price: float,
    technology: str,
    finish: str = "standard",
    color: str = "none",
    resolution: str = "standard",
    infill: Optional[str] = None,
    hardness: str = "standard",
    tolerance: str = "standard",
    certification: str = "none",
    take_rate: float = 0.28,
) -> dict:
    """
    Tüm seçenekleri uygular ve nihai birim fiyatı döndürür.

    Hesaplama:
      base × (finish_mult × color_mult × res_mult × hardness_mult × tol_mult)
      + flat_costs / (1 - take_rate)

    Returns: {
        "unit_price_final": float,
        "multiplier_total": float,
        "flat_cost_total": float,
        "breakdown": dict,
        "warnings": list[str],
    }
    """
    warnings = []

    f_rate  = resolve_finish(finish, technology)
    c_rate  = resolve_color(color, technology)
    r_rate  = resolve_resolution(resolution, technology)
    h_rate  = resolve_hardness(hardness, technology)
    t_rate  = resolve_tolerance(tolerance, technology)
    ct_rate = resolve_certification(certification)

    # Infill sadece FDM için hacim hesabına etki eder; burada multiplier olarak modellenmez
    infill_rate = resolve_infill(infill) if infill else None

    for rate in [f_rate, c_rate, r_rate, h_rate, t_rate]:
        if "warning" in rate:
            warnings.append(rate["warning"])

    mult = (
        f_rate.get("multiplier", 1.0)
        * c_rate.get("multiplier", 1.0)
        * r_rate.get("multiplier", 1.0)
        * h_rate.get("multiplier", 1.0)
        * t_rate.get("multiplier", 1.0)
    )

    flat = (
        f_rate.get("flat_cost", 0.0)
        + c_rate.get("flat_cost", 0.0)
        + ct_rate.get("flat_cost", 0.0)
    )

    unit_final = base_unit_price * mult + flat / max(1 - take_rate, 0.01)

    return {
        "unit_price_final": round(unit_final, 4),
        "multiplier_total": round(mult, 4),
        "flat_cost_total": round(flat, 4),
        "breakdown": {
            "finish":         {"key": finish,        "mult": f_rate.get("multiplier"),  "flat": f_rate.get("flat_cost"),  "label": f_rate.get("label")},
            "color":          {"key": color,          "mult": c_rate.get("multiplier"),  "flat": c_rate.get("flat_cost"),  "label": c_rate.get("label")},
            "resolution":     {"key": resolution,     "mult": r_rate.get("multiplier"),  "layer_mm": r_rate.get("layer_height_mm"), "label": r_rate.get("label")},
            "hardness":       {"key": hardness,       "mult": h_rate.get("multiplier"),  "label": h_rate.get("label")},
            "tolerance":      {"key": tolerance,      "mult": t_rate.get("multiplier"),  "tol_mm": t_rate.get("tolerance_mm"), "label": t_rate.get("label")},
            "certification":  {"key": certification,  "flat": ct_rate.get("flat_cost"),  "label": ct_rate.get("label")},
            "infill":         infill_rate,
        },
        "warnings": warnings,
    }


# ─────────────────────────────────────────────────────────────────────────────
# /options endpoint için dropdown verisi üretici
# ─────────────────────────────────────────────────────────────────────────────

def get_options_for_technology(technology: str) -> dict:
    """
    Verilen teknoloji için geçerli seçenek listelerini döndürür.
    Client Portal dropdown'larını beslemek için kullanılır.
    """
    def _filter(table: dict) -> list[dict]:
        result = []
        for key, val in table.items():
            allowed = val.get("technologies", [])
            if not allowed or technology in allowed:
                result.append({"key": key, "label": val.get("label", key)})
        return result

    return {
        "technology": technology,
        "finishes":    _filter(FINISH_RATES),
        "colors":      _filter(COLOR_RATES),
        "resolutions": _filter(RESOLUTION_RATES),
        "hardness":    _filter(HARDNESS_RATES),
        "tolerances":  _filter(TOLERANCE_RATES),
        "infills":     [{"key": k, "label": v["label"]} for k, v in INFILL_PRESETS.items()]
                       if technology == "fdm" else [],
        "certifications": [{"key": k, "label": v["label"]} for k, v in CERT_RATES.items()],
    }
