"""
Malzeme Bazlı Çarpanlar — Fiyat farklılaşması için

material_speed_mult: baskı süresi çarpanı (TPU daha yavaş, CF/GF daha yavaş)
material_setup_cost: malzeme değişimi/purge maliyeti (kompozitler için nozzle wear)
material_waste_pct: fire oranı (% olarak, fire dahil malzeme hesabı)

Kaynak: Türkiye fason baskı piyasa tecrübesi, Temmuz 2026
"""

MATERIAL_MULTIPLIERS = {
    # ── FDM ──────────────────────────────────────────────────────────────
    "fdm__pla": {
        "speed_mult": 1.0,
        "setup_cost": 0.0,
        "waste_pct": 0.05,
        "note": "Standart PLA — hızlı baskı"
    },
    "fdm__pla_matte": {
        "speed_mult": 1.0,
        "setup_cost": 0.0,
        "waste_pct": 0.05,
        "note": "Mat PLA — standart hız"
    },
    "fdm__pla_silk": {
        "speed_mult": 1.05,
        "setup_cost": 0.0,
        "waste_pct": 0.05,
        "note": "İpek PLA — biraz daha yavaş"
    },
    "fdm__abs": {
        "speed_mult": 1.10,
        "setup_cost": 0.50,
        "waste_pct": 0.08,
        "note": "ABS — enclosure gerekli, purge"
    },
    "fdm__asa": {
        "speed_mult": 1.15,
        "setup_cost": 0.50,
        "waste_pct": 0.08,
        "note": "ASA — UV dayanım, enclosure"
    },
    "fdm__tpu_flex": {
        "speed_mult": 1.30,
        "setup_cost": 0.75,
        "waste_pct": 0.10,
        "note": "TPU esnek — yavaş baskı, özel ayar"
    },
    "fdm__tpu_soft": {
        "speed_mult": 1.50,
        "setup_cost": 0.75,
        "waste_pct": 0.12,
        "note": "TPU 87A — çok yavaş, direkt extruder"
    },
    "fdm__pvb": {
        "speed_mult": 1.05,
        "setup_cost": 0.25,
        "waste_pct": 0.05,
        "note": "PVB — standart, alkol buharı cilası"
    },
    "fdm__pc_cf": {
        "speed_mult": 1.20,
        "setup_cost": 1.50,
        "waste_pct": 0.15,
        "note": "PC-CF — yüksek sıcaklık, nozzle aşınması"
    },
    "fdm__pa_gf": {
        "speed_mult": 1.25,
        "setup_cost": 1.50,
        "waste_pct": 0.15,
        "note": "PA12 GF — aşındırıcı, hardened nozzle"
    },
    "fdm__nylon_pa11": {
        "speed_mult": 1.20,
        "setup_cost": 0.75,
        "waste_pct": 0.10,
        "note": "PA11 — nemi önlemek için kurutma"
    },

    # ── SLA ──────────────────────────────────────────────────────────────
    "sla__standard_resin": {
        "speed_mult": 1.0,
        "setup_cost": 0.0,
        "waste_pct": 0.10,
        "note": "Standart reçine"
    },
    "sla__water_washable": {
        "speed_mult": 1.0,
        "setup_cost": 0.0,
        "waste_pct": 0.10,
        "note": "Suyla yıkanabilir reçine"
    },
    "sla__plant_based": {
        "speed_mult": 1.0,
        "setup_cost": 0.0,
        "waste_pct": 0.10,
        "note": "Bitki bazlı reçine"
    },
    "sla__tough_resin": {
        "speed_mult": 1.15,
        "setup_cost": 0.50,
        "waste_pct": 0.12,
        "note": "Tough reçine — daha uzun cure"
    },
    "sla__rigid_engineering": {
        "speed_mult": 1.20,
        "setup_cost": 0.75,
        "waste_pct": 0.12,
        "note": "Rigid/GF reçine — post-cure gerekli"
    },
    "sla__dental_model": {
        "speed_mult": 1.10,
        "setup_cost": 1.00,
        "waste_pct": 0.15,
        "note": "Dental reçine — hassas cure"
    },
    "sla__castable_resin": {
        "speed_mult": 1.15,
        "setup_cost": 1.00,
        "waste_pct": 0.15,
        "note": "Döküm reçine — özel işlem"
    },

    # ── SLS ──────────────────────────────────────────────────────────────
    "sls__pa12": {
        "speed_mult": 1.0,
        "setup_cost": 0.0,
        "waste_pct": 0.15,
        "note": "PA12 standart SLS"
    },
    "sls__pa12_cf": {
        "speed_mult": 1.10,
        "setup_cost": 2.00,
        "waste_pct": 0.20,
        "note": "PA12 CF — aşındırıcı toz"
    },
    "sls__pp": {
        "speed_mult": 1.05,
        "setup_cost": 1.00,
        "waste_pct": 0.18,
        "note": "PP tozu — özel sıcaklık profili"
    },

    # ── MJF ──────────────────────────────────────────────────────────────
    "mjf__pa12": {
        "speed_mult": 1.0,
        "setup_cost": 0.0,
        "waste_pct": 0.15,
        "note": "PA12 MJF standart"
    },

    # ── DMLS ─────────────────────────────────────────────────────────────
    "dmls__ss316l": {
        "speed_mult": 1.0,
        "setup_cost": 0.0,
        "waste_pct": 0.20,
        "note": "316L paslanmaz"
    },
    "dmls__ti64": {
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
