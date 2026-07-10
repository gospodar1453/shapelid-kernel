"""
Malzeme Fiyat Tablosu — USD bazlı
Kaynak: Türkiye piyasa araştırması, Temmuz 2026
Kur referansı: 1 USD = 47 TRY (TCMB, 10 Temmuz 2026)

Güncelleme notu:
- FDM filamentler: filamentmarketim.com, trendyol, hepsiburada (gerçek satış fiyatları)
- SLA reçine: anycubic, elegoo Türkiye satıcıları
- SLS/MJF PA12: endüstriyel toz tedarikçi ortalaması
- Metal: celikfiyatlari.com, borufiyatlari.com.tr (Temmuz 2026)

Revizyon periyodu: 3 ayda bir (kur + emtia değişimlerine göre)
"""

# USD/TRY referans kuru (TCMB - otomatik kur sistemi devreye girene kadar)
USD_TRY_REF = 47.0

MATERIAL_RATES = {
    # ── FDM ──────────────────────────────────────────────────────────────
    # Türkiye piyasa: 550–700 TL/kg | yoğunluk: 1.24 g/cm³
    "fdm_pla": {
        "price_per_cm3": 0.0158,   # ~600 TL/kg → $12.77/kg → $0.0158/cm³
        "price_try_per_kg": 600,
        "density_g_cm3": 1.24,
        "name": "PLA",
        "source": "filamentmarketim.com, Temmuz 2026"
    },
    # Türkiye piyasa: ~750 TL/kg | yoğunluk: 1.05 g/cm³
    "fdm_abs": {
        "price_per_cm3": 0.0168,   # ~750 TL/kg → $15.96/kg → $0.0168/cm³
        "price_try_per_kg": 750,
        "density_g_cm3": 1.05,
        "name": "ABS",
        "source": "filamentmarketim.com, Temmuz 2026"
    },
    # Türkiye piyasa: ~600 TL/kg | yoğunluk: 1.27 g/cm³
    "fdm_petg": {
        "price_per_cm3": 0.0162,   # ~600 TL/kg → $12.77/kg → $0.0162/cm³
        "price_try_per_kg": 600,
        "density_g_cm3": 1.27,
        "name": "PETG",
        "source": "filamentmarketim.com, Temmuz 2026"
    },
    # Türkiye piyasa: ~1.100 TL/kg | yoğunluk: 1.21 g/cm³
    "fdm_tpu": {
        "price_per_cm3": 0.0283,   # ~1.100 TL/kg → $23.41/kg → $0.0283/cm³
        "price_try_per_kg": 1100,
        "density_g_cm3": 1.21,
        "name": "TPU (Esnek)",
        "source": "filamentmarketim.com, Temmuz 2026"
    },
    # Türkiye piyasa: ~900 TL/kg | yoğunluk: 1.07 g/cm³
    "fdm_asa": {
        "price_per_cm3": 0.0205,   # ~900 TL/kg → $19.16/kg → $0.0205/cm³
        "price_try_per_kg": 900,
        "density_g_cm3": 1.07,
        "name": "ASA (UV Dayanımlı)",
        "source": "filamentmarketim.com, Temmuz 2026"
    },
    "default_fdm": {
        "price_per_cm3": 0.0158,
        "price_try_per_kg": 600,
        "density_g_cm3": 1.24,
        "name": "FDM Standart (PLA)"
    },

    # ── SLA ──────────────────────────────────────────────────────────────
    # Türkiye piyasa: ~750 TL/kg | yoğunluk: ~1.10 g/cm³
    "sla_standard_resin": {
        "price_per_cm3": 0.0176,   # ~750 TL/kg → $15.96/kg → $0.0176/cm³
        "price_try_per_kg": 750,
        "density_g_cm3": 1.10,
        "name": "Standart Reçine",
        "source": "Anycubic/Elegoo Türkiye satıcıları, Temmuz 2026"
    },
    # Türkiye piyasa: ~1.150 TL/kg (ABS-Like/Tough)
    "sla_tough_resin": {
        "price_per_cm3": 0.0269,   # ~1.150 TL/kg → $24.48/kg → $0.0269/cm³
        "price_try_per_kg": 1150,
        "density_g_cm3": 1.10,
        "name": "Dayanıklı Reçine (Tough/ABS-Like)",
        "source": "Anycubic Tough Pro, Temmuz 2026"
    },
    # Türkiye piyasa: ~2.500 TL/kg (Flexible/Elastic reçine)
    "sla_flexible_resin": {
        "price_per_cm3": 0.0585,   # ~2.500 TL/kg → $53.21/kg → $0.0585/cm³
        "price_try_per_kg": 2500,
        "density_g_cm3": 1.10,
        "name": "Esnek Reçine (Flexible)",
        "source": "Siraya/Formlabs Türkiye, Temmuz 2026"
    },
    # Döküm reçine — endüstriyel, ~4.000 TL/kg tahmini
    "sla_castable_resin": {
        "price_per_cm3": 0.0974,   # ~4.000 TL/kg → $85.11/kg → $0.0974/cm³ (kuyumculuk reçine)
        "price_try_per_kg": 4000,
        "density_g_cm3": 1.10,
        "name": "Döküm Reçine (Castable)",
        "source": "Endüstriyel tahmin, Temmuz 2026"
    },
    "default_sla": {
        "price_per_cm3": 0.0176,
        "price_try_per_kg": 750,
        "density_g_cm3": 1.10,
        "name": "SLA Standart Reçine"
    },

    # ── SLS ──────────────────────────────────────────────────────────────
    # Türkiye piyasa: ~4.500 TL/kg (endüstriyel PA12 toz) | yoğunluk: 0.95 g/cm³
    "sls_pa12": {
        "price_per_cm3": 0.0910,   # ~4.500 TL/kg → $95.79/kg → $0.0910/cm³
        "price_try_per_kg": 4500,
        "density_g_cm3": 0.95,
        "name": "PA12 (Nylon 12) SLS",
        "source": "Endüstriyel SLS toz tedarikçi ortalaması, Temmuz 2026"
    },
    # PA11 bio-nylon — biraz daha pahalı
    "sls_pa11": {
        "price_per_cm3": 0.1050,   # ~5.000 TL/kg → $106.38/kg → $0.1050/cm³
        "price_try_per_kg": 5000,
        "density_g_cm3": 1.01,
        "name": "PA11 (Bio-Nylon) SLS",
        "source": "Endüstriyel tahmin, Temmuz 2026"
    },
    # TPU SLS tozu — esnek, nadir, pahalı
    "sls_tpu": {
        "price_per_cm3": 0.1350,   # ~6.000 TL/kg → $127.66/kg → $0.1350/cm³
        "price_try_per_kg": 6000,
        "density_g_cm3": 1.21,
        "name": "TPU Esnek (SLS)",
        "source": "Endüstriyel tahmin, Temmuz 2026"
    },
    "default_sls": {
        "price_per_cm3": 0.0910,
        "price_try_per_kg": 4500,
        "density_g_cm3": 0.95,
        "name": "SLS Standart (PA12)"
    },

    # ── MJF ──────────────────────────────────────────────────────────────
    # HP MJF toz — SLS'den biraz daha pahalı
    "mjf_pa12": {
        "price_per_cm3": 0.1011,   # ~5.000 TL/kg → $106.38/kg → $0.1011/cm³
        "price_try_per_kg": 5000,
        "density_g_cm3": 0.95,
        "name": "PA12 MJF",
        "source": "HP MJF endüstriyel toz, Temmuz 2026"
    },
    "mjf_pa12gb": {
        "price_per_cm3": 0.1150,   # cam dolgulu, ~%15 zam
        "price_try_per_kg": 5750,
        "density_g_cm3": 1.10,
        "name": "PA12 Cam Dolgulu MJF",
        "source": "Endüstriyel tahmin, Temmuz 2026"
    },
    "default_mjf": {
        "price_per_cm3": 0.1011,
        "price_try_per_kg": 5000,
        "density_g_cm3": 0.95,
        "name": "MJF Standart (PA12)"
    },

    # ── DMLS / Metal 3D Baskı ────────────────────────────────────────────
    # Türkiye'de DMLS servisi yok denecek kadar az — fiyat servis bazlı
    # Toz malzeme maliyeti kg başına (Avrupa referanslı, +%20 ithalat marjı)
    "dmls_316l": {
        "price_per_cm3": 0.85,     # ~40 TL/g → paslanmaz çelik toz
        "price_try_per_kg": 40000,
        "density_g_cm3": 7.98,
        "name": "316L Paslanmaz Çelik (DMLS)",
        "source": "Avrupa DMLS toz referansı +%20, Temmuz 2026"
    },
    "dmls_ti64": {
        "price_per_cm3": 1.20,     # titanyum toz — çok pahalı
        "price_try_per_kg": 70000,
        "density_g_cm3": 4.43,
        "name": "Ti-6Al-4V Titanyum (DMLS)",
        "source": "Avrupa DMLS toz referansı +%20, Temmuz 2026"
    },
    "default_dmls": {
        "price_per_cm3": 0.85,
        "price_try_per_kg": 40000,
        "density_g_cm3": 7.98,
        "name": "DMLS Standart (316L)"
    },

    # ── LAZER KESİM / BENDING — ağırlık bazlı (USD/kg) ──────────────────
    # Türkiye piyasa: S235 ince levha 21-29 TL/kg → ortalama ~25 TL/kg → $0.53/kg
    "laser_mild_steel": {
        "price_per_kg": 0.53,      # ~25 TL/kg → $0.53/kg
        "price_try_per_kg": 25,
        "density_g_cm3": 7.85,
        "name": "Yumuşak Çelik S235/ST37",
        "source": "celikfiyatlari.com, Temmuz 2026"
    },
    # Türkiye piyasa: 304 paslanmaz ~100 TL/kg → $2.13/kg
    "laser_stainless_steel": {
        "price_per_kg": 2.13,      # ~100 TL/kg → $2.13/kg
        "price_try_per_kg": 100,
        "density_g_cm3": 7.93,
        "name": "Paslanmaz Çelik 304",
        "source": "celikfiyatlari.com, Temmuz 2026"
    },
    # Türkiye piyasa: 6061 alüminyum levha ~95 TL/kg → $2.02/kg
    "laser_aluminum": {
        "price_per_kg": 2.02,      # ~95 TL/kg → $2.02/kg
        "price_try_per_kg": 95,
        "density_g_cm3": 2.70,
        "name": "Alüminyum 6061",
        "source": "Metal tedarikçi ortalaması, Temmuz 2026"
    },
    # Türkiye piyasa: bakır ~280 TL/kg → $5.96/kg
    "laser_copper": {
        "price_per_kg": 5.96,      # ~280 TL/kg → $5.96/kg
        "price_try_per_kg": 280,
        "density_g_cm3": 8.96,
        "name": "Bakır",
        "source": "Metal tedarikçi tahmini, Temmuz 2026"
    },
    # Türkiye piyasa: pirinç ~200 TL/kg → $4.26/kg
    "laser_brass": {
        "price_per_kg": 4.26,      # ~200 TL/kg → $4.26/kg
        "price_try_per_kg": 200,
        "density_g_cm3": 8.50,
        "name": "Pirinç",
        "source": "Metal tedarikçi tahmini, Temmuz 2026"
    },
    # Galvanizli çelik — S235'e yakın ama biraz pahalı
    "laser_galvanized_steel": {
        "price_per_kg": 0.64,      # ~30 TL/kg → $0.64/kg
        "price_try_per_kg": 30,
        "density_g_cm3": 7.85,
        "name": "Galvanizli Çelik",
        "source": "Metal tedarikçi tahmini, Temmuz 2026"
    },
    "default_laser": {
        "price_per_kg": 0.53,
        "price_try_per_kg": 25,
        "density_g_cm3": 7.85,
        "name": "Lazer Standart (S235)"
    },
}
