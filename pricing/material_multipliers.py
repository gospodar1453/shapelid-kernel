"""
Malzeme Bazlı Çarpanlar — Fiyat farklılaşması için

material_speed_mult: baskı süresi çarpanı (TPU daha yavaş, CF/GF daha yavaş)
material_setup_cost: malzeme değişimi/purge maliyeti (kompozitler için nozzle wear)
material_waste_pct: fire oranı (% olarak, fire dahil malzeme hesabı)

Key format: {technology}_{material} — TEK alt çizgi (engine.py ile uyumlu)

Kaynak: Türkiye fason baskı piyasa tecrübesi, Temmuz 2026
"""

MATERIAL_MULTIPLIERS = {
    # ── FDM ──────────────────────────────────────────────────────────────
    "fdm_pla": {
        "speed_mult": 1.0,
        "setup_cost": 0.0,
        "waste_pct": 0.05,
        "note": "Standart PLA — hızlı baskı"
    },
    "fdm_pla_matte": {
        "speed_mult": 1.0,
        "setup_cost": 0.0,
        "waste_pct": 0.05,
        "note": "Mat PLA — standart hız"
    },
    "fdm_pla_silk": {
        "speed_mult": 1.05,
        "setup_cost": 0.0,
        "waste_pct": 0.05,
        "note": "İpek PLA — biraz daha yavaş"
    },
    "fdm_abs": {
        "speed_mult": 1.10,
        "setup_cost": 0.50,
        "waste_pct": 0.08,
        "note": "ABS — enclosure gerekli, purge"
    },
    "fdm_asa": {
        "speed_mult": 1.15,
        "setup_cost": 0.50,
        "waste_pct": 0.08,
        "note": "ASA — UV dayanım, enclosure"
    },
    "fdm_tpu_flex": {
        "speed_mult": 1.30,
        "setup_cost": 0.75,
        "waste_pct": 0.10,
        "note": "TPU esnek — yavaş baskı, özel ayar"
    },
    "fdm_tpu_soft": {
        "speed_mult": 1.50,
        "setup_cost": 0.75,
        "waste_pct": 0.12,
        "note": "TPU 87A — çok yavaş, direkt extruder"
    },
    "fdm_pvb": {
        "speed_mult": 1.05,
        "setup_cost": 0.25,
        "waste_pct": 0.05,
        "note": "PVB — standart, alkol buharı cilası"
    },
    "fdm_pc_cf": {
        "speed_mult": 1.20,
        "setup_cost": 1.50,
        "waste_pct": 0.15,
        "note": "PC-CF — yüksek sıcaklık, nozzle aşınması"
    },
    "fdm_pa_gf": {
        "speed_mult": 1.25,
        "setup_cost": 1.50,
        "waste_pct": 0.15,
        "note": "PA12 GF — aşındırıcı, hardened nozzle"
    },
    "fdm_nylon_pa11": {
        "speed_mult": 1.20,
        "setup_cost": 0.75,
        "waste_pct": 0.10,
        "note": "PA11 — nemi önlemek için kurutma"
    },

    # ── SLA ──────────────────────────────────────────────────────────────
    "sla_standard_resin": {
        "speed_mult": 1.0,
        "setup_cost": 0.0,
        "waste_pct": 0.10,
        "note": "Standart reçine"
    },
    "sla_water_washable": {
        "speed_mult": 1.0,
        "setup_cost": 0.0,
        "waste_pct": 0.10,
        "note": "Suyla yıkanabilir reçine"
    },
    "sla_plant_based": {
        "speed_mult": 1.0,
        "setup_cost": 0.0,
        "waste_pct": 0.10,
        "note": "Bitki bazlı reçine"
    },
    "sla_tough_resin": {
        "speed_mult": 1.15,
        "setup_cost": 0.50,
        "waste_pct": 0.12,
        "note": "Tough reçine — daha uzun cure"
    },
    "sla_rigid_engineering": {
        "speed_mult": 1.20,
        "setup_cost": 0.75,
        "waste_pct": 0.12,
        "note": "Rigid/GF reçine — post-cure gerekli"
    },
    "sla_dental_model": {
        "speed_mult": 1.10,
        "setup_cost": 1.00,
        "waste_pct": 0.15,
        "note": "Dental reçine — hassas cure"
    },
    "sla_castable_resin": {
        "speed_mult": 1.15,
        "setup_cost": 1.00,
        "waste_pct": 0.15,
        "note": "Döküm reçine — özel işlem"
    },

    # ── SLS ──────────────────────────────────────────────────────────────
    "sls_pa12": {
        "speed_mult": 1.0,
        "setup_cost": 0.0,
        "waste_pct": 0.15,
        "note": "PA12 standart SLS"
    },
    "sls_pa12_cf": {
        "speed_mult": 1.10,
        "setup_cost": 2.00,
        "waste_pct": 0.20,
        "note": "PA12 CF — aşındırıcı toz"
    },
    "sls_pp": {
        "speed_mult": 1.05,
        "setup_cost": 1.00,
        "waste_pct": 0.18,
        "note": "PP tozu — özel sıcaklık profili"
    },

    # ── MJF ──────────────────────────────────────────────────────────────
    "mjf_pa12": {
        "speed_mult": 1.0,
        "setup_cost": 0.0,
        "waste_pct": 0.15,
        "note": "PA12 MJF standart"
    },

    # ── DMLS ─────────────────────────────────────────────────────────────
    "dmls_ss316l": {
        "speed_mult": 1.0,
        "setup_cost": 0.0,
        "waste_pct": 0.20,
        "note": "316L paslanmaz"
    },
    "dmls_ti64": {
        "speed_mult": 1.15,
        "setup_cost": 5.00,
        "waste_pct": 0.25,
        "note": "Titanyum — argon gaz, yüksek enerji"
    },
}

# Default fallback (malzeme listede yoksa)
DEFAULT_MULTIPLIER = {
    "speed_mult": 1.0,
    "setup_cost": 0.0,
    "waste_pct": 0.10,
    "note": "Default"
}


def get_material_multiplier(material_key: str) -> dict:
    """Verilen material_key için çarpanları döndürür."""
    return MATERIAL_MULTIPLIERS.get(material_key, DEFAULT_MULTIPLIER)
