"""
Malzeme Fiyat Tablosu — USD bazlı
Kaynak: piyasa ortalamaları (2026 Q1)
Düzenli olarak güncellenmelidir.
"""

MATERIAL_RATES = {
    # ── FDM ──
    "fdm_pla":      {"price_per_cm3": 0.025, "name": "PLA"},
    "fdm_abs":      {"price_per_cm3": 0.028, "name": "ABS"},
    "fdm_petg":     {"price_per_cm3": 0.030, "name": "PETG"},
    "fdm_tpu":      {"price_per_cm3": 0.045, "name": "TPU (Esnek)"},
    "fdm_asa":      {"price_per_cm3": 0.032, "name": "ASA (UV Dayanımlı)"},
    "default_fdm":  {"price_per_cm3": 0.025, "name": "FDM Standart"},

    # ── SLA ──
    "sla_standard_resin":  {"price_per_cm3": 0.15, "name": "Standart Reçine"},
    "sla_tough_resin":     {"price_per_cm3": 0.20, "name": "Dayanıklı Reçine"},
    "sla_flexible_resin":  {"price_per_cm3": 0.22, "name": "Esnek Reçine"},
    "sla_castable_resin":  {"price_per_cm3": 0.35, "name": "Döküm Reçine"},
    "default_sla":         {"price_per_cm3": 0.15, "name": "SLA Standart"},

    # ── SLS ──
    "sls_pa12":   {"price_per_cm3": 0.18, "name": "PA12 (Nylon 12)"},
    "sls_pa11":   {"price_per_cm3": 0.20, "name": "PA11 (Bio-Nylon)"},
    "sls_tpu":    {"price_per_cm3": 0.25, "name": "TPU Esnek (SLS)"},
    "default_sls":{"price_per_cm3": 0.18, "name": "SLS Standart"},

    # ── MJF ──
    "mjf_pa12":    {"price_per_cm3": 0.20, "name": "PA12 MJF"},
    "mjf_pa12gb":  {"price_per_cm3": 0.22, "name": "PA12 Cam Dolgulu MJF"},
    "default_mjf": {"price_per_cm3": 0.20, "name": "MJF Standart"},

    # ── Lazer Kesim / Bending — ağırlık bazlı (USD/kg) ──
    "laser_mild_steel":      {"price_per_kg": 1.20, "density_g_cm3": 7.85, "name": "Yumuşak Çelik (S235)"},
    "laser_stainless_steel": {"price_per_kg": 4.50, "density_g_cm3": 7.93, "name": "Paslanmaz Çelik (304)"},
    "laser_aluminum":        {"price_per_kg": 3.80, "density_g_cm3": 2.70, "name": "Alüminyum (6061)"},
    "laser_copper":          {"price_per_kg": 9.50, "density_g_cm3": 8.96, "name": "Bakır"},
    "laser_brass":           {"price_per_kg": 7.80, "density_g_cm3": 8.50, "name": "Pirinç"},
    "default_laser":         {"price_per_kg": 1.20, "density_g_cm3": 7.85, "name": "Lazer Standart"},
}
