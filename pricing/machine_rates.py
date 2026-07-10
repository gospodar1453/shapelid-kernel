"""
Makine Saatlik Maliyet Tablosu — USD bazlı
Kaynak: Türkiye piyasa araştırması, Temmuz 2026
Kur referansı: 1 USD = 47 TRY

Maliyet kalemleri:
- Amortisman (makine ömrü 7-10 yıl)
- Enerji (kWh × Türkiye sanayi elektrik ~3.5 TL/kWh)
- Bakım/onarım (%8-12 yıllık)
- Operatör işçiliği (Türkiye OSB ortalama)
- Sarf malzeme (gaz, soğutucu, vs.)

Saatlik ücretler, Türkiye'deki fason imalatçı piyasa ortalamalarına göre kalibre edilmiştir.
"""

USD_TRY_REF = 47.0

MACHINE_RATES = {
    # ── FDM ──────────────────────────────────────────────────────────────
    # Türkiye'de FDM servisi rekabetçi — masa üstü makineler yaygın
    # Piyasa saatlik: 100–300 TL/saat → $2.13–$6.38/saat | ortalama ~150 TL/saat
    "fdm": {
        "hourly_rate": 3.20,       # ~150 TL/saat → $3.20/saat (Prusa/Bambu Lab seviyesi)
        "hourly_rate_try": 150,
        "setup_cost": 1.50,        # ~70 TL (plaka hazırlık + kalibrasyon)
        "setup_cost_try": 70,
        "name": "FDM Yazıcı",
        "note": "Masa üstü FDM (Prusa/Bambu/Creality tipi)"
    },

    # ── SLA ──────────────────────────────────────────────────────────────
    # SLA servisi az, reçine+UV işlemi ekstra — ortalama ~300 TL/saat
    "sla": {
        "hourly_rate": 6.40,       # ~300 TL/saat → $6.38/saat
        "hourly_rate_try": 300,
        "setup_cost": 2.50,        # ~117 TL (reçine hazırlık + destek yapısı)
        "setup_cost_try": 117,
        "name": "SLA Yazıcı",
        "note": "MSLA/LCD veya DLP tabanlı"
    },

    # ── SLS ──────────────────────────────────────────────────────────────
    # Endüstriyel SLS — Türkiye'de az sayıda servis merkezi
    # Avrupa fiyatı ~€80-120/saat; Türkiye'de ~€50-70/saat (~$55-75)
    "sls": {
        "hourly_rate": 55.00,      # ~2.585 TL/saat → $55/saat (EOS/Formlabs Fuse)
        "hourly_rate_try": 2585,
        "setup_cost": 35.00,       # ~1.645 TL (toz yükleme + ısınma ~45 dk)
        "setup_cost_try": 1645,
        "name": "SLS Sistemi",
        "note": "Endüstriyel SLS (EOS/3D Systems tipi)"
    },

    # ── MJF ──────────────────────────────────────────────────────────────
    # HP MJF — Türkiye'de çok az var, Avrupa fiyatlarına yakın
    "mjf": {
        "hourly_rate": 65.00,      # ~3.055 TL/saat → $65/saat (HP Jet Fusion 5200)
        "hourly_rate_try": 3055,
        "setup_cost": 40.00,       # ~1.880 TL
        "setup_cost_try": 1880,
        "name": "HP MJF Sistemi",
        "note": "HP Jet Fusion serisi"
    },

    # ── DMLS ─────────────────────────────────────────────────────────────
    # Metal 3D baskı — Türkiye'de neredeyse yok, fiyat Avrupa referanslı
    "dmls": {
        "hourly_rate": 120.00,     # ~5.640 TL/saat (EOS M290 tipi)
        "hourly_rate_try": 5640,
        "setup_cost": 80.00,       # build plate hazırlık + argon gaz
        "setup_cost_try": 3760,
        "name": "DMLS Metal 3D Baskı",
        "note": "EOS/SLM Solutions tipi — Avrupa referanslı"
    },

    # ── FİBER LAZER KESİM ────────────────────────────────────────────────
    # Türkiye piyasa: 3kW → 800-1.200 TL/saat | 6kW → 1.500-2.200 TL/saat
    # Ortalama 3-4kW makine ~1.000 TL/saat → $21.28/saat
    "laser": {
        "hourly_rate": 21.30,      # ~1.000 TL/saat → $21.28/saat (3kW fiber lazer)
        "hourly_rate_try": 1000,
        "setup_cost": 6.40,        # ~300 TL (program yükleme + malzeme yerleştirme)
        "setup_cost_try": 300,
        "name": "Fiber Lazer Kesim (3kW)",
        "note": "Bersa/Baykal/Ermaksan 3kW fiber lazer — Temmuz 2026"
    },

    # ── ABKANT PRES (BENDING) ────────────────────────────────────────────
    # Türkiye piyasa: CNC abkant ~800-2.000 TL/saat | ortalama ~1.200 TL/saat
    "bending": {
        "hourly_rate": 25.50,      # ~1.200 TL/saat → $25.53/saat
        "hourly_rate_try": 1200,
        "setup_cost": 8.50,        # ~400 TL (kalıp kurulum + program)
        "setup_cost_try": 400,
        "name": "CNC Abkant Pres",
        "note": "Baykal/Ermaksan CNC abkant — Temmuz 2026"
    },

    # ── CNC TORNA ────────────────────────────────────────────────────────
    # Türkiye piyasa: 2-3 eksen CNC torna ~500-2.000 TL/saat | ortalama ~900 TL/saat
    "cnc_turning": {
        "hourly_rate": 19.15,      # ~900 TL/saat → $19.15/saat
        "hourly_rate_try": 900,
        "setup_cost": 12.75,       # ~600 TL (takım kurulum + referans alma)
        "setup_cost_try": 600,
        "name": "CNC Torna (2-3 eksen)",
        "note": "Türkmaksan/Doosan tipi — Temmuz 2026"
    },

    # ── CNC FREZE ────────────────────────────────────────────────────────
    # Türkiye piyasa: 3 eksen VMC ~700-3.000 TL/saat | ortalama ~1.400 TL/saat
    "cnc_milling": {
        "hourly_rate": 29.80,      # ~1.400 TL/saat → $29.79/saat
        "hourly_rate_try": 1400,
        "setup_cost": 17.00,       # ~800 TL (fixture + sıfırlama)
        "setup_cost_try": 800,
        "name": "CNC Freze (3 eksen VMC)",
        "note": "Haas/Mazak/DMG Mori tipi — Temmuz 2026"
    },

    # ── EDM ──────────────────────────────────────────────────────────────
    # Tel erozyon — özel, pahalı işlem
    "edm": {
        "hourly_rate": 35.00,      # ~1.645 TL/saat (tel erozyonu)
        "hourly_rate_try": 1645,
        "setup_cost": 25.00,       # ~1.175 TL (tel germe + program)
        "setup_cost_try": 1175,
        "name": "EDM Tel Erozyon",
        "note": "Mitsubishi/Fanuc tel erozyon — Temmuz 2026"
    },
}
