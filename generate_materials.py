import json

missing_materials = [
    # ── 1. DMLS (Direct Metal Laser Sintering) ──
    {
        "material_key": "dmls_316l",
        "material_name": "316L Paslanmaz Çelik Tozu (DMLS)",
        "category": "powder",
        "technology": "dmls",
        "base_price_usd": 80.0,
        "price_unit": "usd_per_kg",
        "notes": "DMLS için Paslanmaz Çelik 316L toz malzeme. Türkiye ithal referanslı."
    },
    {
        "material_key": "dmls_ti64",
        "material_name": "Ti-6Al-4V Titanyum Tozu (DMLS)",
        "category": "powder",
        "technology": "dmls",
        "base_price_usd": 250.0,
        "price_unit": "usd_per_kg",
        "notes": "DMLS için Titanyum Gr5 toz malzeme. Yüksek performanslı havacılık/medikal sınıfı."
    },
    {
        "material_key": "dmls_alsi10mg",
        "material_name": "AlSi10Mg Alüminyum Tozu (DMLS)",
        "category": "powder",
        "technology": "dmls",
        "base_price_usd": 70.0,
        "price_unit": "usd_per_kg",
        "notes": "DMLS için Alüminyum AlSi10Mg toz malzeme."
    },
    {
        "material_key": "dmls_inconel718",
        "material_name": "Inconel 718 Süperalaşım Tozu (DMLS)",
        "category": "powder",
        "technology": "dmls",
        "base_price_usd": 180.0,
        "price_unit": "usd_per_kg",
        "notes": "DMLS için Inconel 718 nikel bazlı süperalaşım toz malzeme."
    },
    
    # ── 2. Polyjet ──
    {
        "material_key": "polyjet_standard",
        "material_name": "Polyjet Standart Reçine (ABS-like)",
        "category": "resin",
        "technology": "polyjet",
        "base_price_usd": 220.0,
        "price_unit": "usd_per_kg",
        "notes": "Polyjet fotopolimer standart ABS-like reçine."
    },
    {
        "material_key": "polyjet_transparent",
        "material_name": "Polyjet Şeffaf Reçine (Transparent)",
        "category": "resin",
        "technology": "polyjet",
        "base_price_usd": 250.0,
        "price_unit": "usd_per_kg",
        "notes": "Polyjet fotopolimer şeffaf/transparent reçine."
    },

    # ── 3. SLS (Naylon Toz Eklemeleri) ──
    {
        "material_key": "sls_pa11",
        "material_name": "PA11 Bio-Nylon Tozu (SLS)",
        "category": "powder",
        "technology": "sls",
        "base_price_usd": 106.38,
        "price_unit": "usd_per_kg",
        "notes": "Biyo-uyumlu PA11 SLS toz malzeme (5000 TRY/kg @ 47 TRY/USD)."
    },
    {
        "material_key": "sls_tpu",
        "material_name": "TPU Esnek Tozu (SLS)",
        "category": "powder",
        "technology": "sls",
        "base_price_usd": 127.66,
        "price_unit": "usd_per_kg",
        "notes": "Esnek parçalar için TPU SLS toz malzeme (6000 TRY/kg @ 47 TRY/USD)."
    },

    # ── 4. HP Multi Jet Fusion (MJF Eklemeleri) ──
    {
        "material_key": "mjf_pa12gb",
        "material_name": "PA12 Cam Dolgulu Tozu (MJF)",
        "category": "powder",
        "technology": "mjf",
        "base_price_usd": 122.34,
        "price_unit": "usd_per_kg",
        "notes": "Cam dolgulu mukavemeti yüksek PA12 GB MJF toz malzeme (5750 TRY/kg @ 47 TRY/USD)."
    },

    # ── 5. FDM (Filament Eklemeleri) ──
    {
        "material_key": "fdm_asa",
        "material_name": "ASA Filament (FDM)",
        "category": "plastic_3d",
        "technology": "fdm",
        "base_price_usd": 19.15,
        "price_unit": "usd_per_kg",
        "notes": "UV ve dış ortam koşullarına dayanıklı ASA filament (900 TRY/kg @ 47 TRY/USD)."
    },
    {
        "material_key": "fdm_nylon",
        "material_name": "Nylon Filament (FDM)",
        "category": "plastic_3d",
        "technology": "fdm",
        "base_price_usd": 25.53,
        "price_unit": "usd_per_kg",
        "notes": "Yüksek mekanik mukavemetli Nylon (PA) filament (1200 TRY/kg @ 47 TRY/USD)."
    },

    # ── 6. CNC Milling (Freze Blok) ──
    {
        "material_key": "cnc_milling_aluminum",
        "material_name": "Alüminyum 6061 Blok (CNC Freze)",
        "category": "metal_sheet",
        "technology": "cnc_milling",
        "base_price_usd": 4.50,
        "price_unit": "usd_per_kg",
        "notes": "CNC Freze için Alüminyum 6061 ham blok malzeme."
    },
    {
        "material_key": "cnc_milling_steel",
        "material_name": "S235 Karbon Çelik Blok (CNC Freze)",
        "category": "metal_sheet",
        "technology": "cnc_milling",
        "base_price_usd": 1.10,
        "price_unit": "usd_per_kg",
        "notes": "CNC Freze için S235 yapısal çelik ham blok malzeme."
    },
    {
        "material_key": "cnc_milling_stainless",
        "material_name": "Paslanmaz Çelik 304 Blok (CNC Freze)",
        "category": "metal_sheet",
        "technology": "cnc_milling",
        "base_price_usd": 3.50,
        "price_unit": "usd_per_kg",
        "notes": "CNC Freze için korozyona dayanıklı Paslanmaz Çelik 304 ham blok malzeme."
    },
    {
        "material_key": "cnc_milling_pom",
        "material_name": "POM Delrin Blok (CNC Freze)",
        "category": "plastic_3d",
        "technology": "cnc_milling",
        "base_price_usd": 4.50,
        "price_unit": "usd_per_kg",
        "notes": "CNC Freze için POM (Delrin) mühendislik plastiği blok malzeme."
    },
    {
        "material_key": "cnc_milling_peek",
        "material_name": "PEEK Blok (CNC Freze)",
        "category": "plastic_3d",
        "technology": "cnc_milling",
        "base_price_usd": 150.0,
        "price_unit": "usd_per_kg",
        "notes": "CNC Freze için ultra performanslı PEEK plastik blok malzeme."
    },

    # ── 7. CNC Turning (Torna Çubuk) ──
    {
        "material_key": "cnc_turning_aluminum",
        "material_name": "Alüminyum 6061 Çubuk (CNC Torna)",
        "category": "metal_sheet",
        "technology": "cnc_turning",
        "base_price_usd": 4.50,
        "price_unit": "usd_per_kg",
        "notes": "CNC Torna için Alüminyum 6061 dairesel çubuk malzeme."
    },
    {
        "material_key": "cnc_turning_steel",
        "material_name": "S235 Karbon Çelik Çubuk (CNC Torna)",
        "category": "metal_sheet",
        "technology": "cnc_turning",
        "base_price_usd": 1.10,
        "price_unit": "usd_per_kg",
        "notes": "CNC Torna için S235 karbon çeliği dairesel çubuk malzeme."
    },
    {
        "material_key": "cnc_turning_stainless",
        "material_name": "Paslanmaz Çelik 304 Çubuk (CNC Torna)",
        "category": "metal_sheet",
        "technology": "cnc_turning",
        "base_price_usd": 3.50,
        "price_unit": "usd_per_kg",
        "notes": "CNC Torna için Paslanmaz Çelik 304 dairesel çubuk malzeme."
    },
    {
        "material_key": "cnc_turning_pom",
        "material_name": "POM Delrin Çubuk (CNC Torna)",
        "category": "plastic_3d",
        "technology": "cnc_turning",
        "base_price_usd": 4.50,
        "price_unit": "usd_per_kg",
        "notes": "CNC Torna için POM (Delrin) plastik dairesel çubuk malzeme."
    },
    {
        "material_key": "cnc_turning_brass",
        "material_name": "Pirinç MS58 Çubuk (CNC Torna)",
        "category": "metal_sheet",
        "technology": "cnc_turning",
        "base_price_usd": 9.50,
        "price_unit": "usd_per_kg",
        "notes": "CNC Torna için Pirinç (Sarı) MS58 çubuk malzeme (440 TRY/kg @ 47 TRY/USD)."
    },

    # ── 8. EDM Services ──
    {
        "material_key": "edm_steel",
        "material_name": "Takım Çeliği Blok (EDM)",
        "category": "metal_sheet",
        "technology": "edm",
        "base_price_usd": 1.50,
        "price_unit": "usd_per_kg",
        "notes": "EDM Tel Erozyon için karbon/takım çeliği blok malzeme."
    },
    {
        "material_key": "edm_copper",
        "material_name": "Bakır Elektrot Blok (EDM)",
        "category": "metal_sheet",
        "technology": "edm",
        "base_price_usd": 8.50,
        "price_unit": "usd_per_kg",
        "notes": "EDM Tel Erozyon ve hızlı delik delme için bakır elektrot malzeme."
    },

    # ── 9. Laser Cutting (Sac Levha Eklemeleri) ──
    {
        "material_key": "laser_brass",
        "material_name": "Pirinç Levha (Laser)",
        "category": "metal_sheet",
        "technology": "laser",
        "base_price_usd": 4.26,
        "price_unit": "usd_per_kg",
        "notes": "Lazer kesim ve büküm için Pirinç levha malzeme (200 TRY/kg @ 47 TRY/USD)."
    },
    {
        "material_key": "laser_ss316",
        "material_name": "Paslanmaz Çelik 316L Levha (Laser)",
        "category": "metal_sheet",
        "technology": "laser",
        "base_price_usd": 3.19,
        "price_unit": "usd_per_kg",
        "notes": "Marine sınıf korozyon dayanımlı Paslanmaz Çelik 316L levha malzeme (150 TRY/kg @ 47 TRY/USD)."
    },

    # ── 10. SLA (Reçine Eklemeleri) ──
    {
        "material_key": "sla_flexible_resin",
        "material_name": "SLA Flexible Reçine",
        "category": "resin",
        "technology": "sla",
        "base_price_usd": 53.20,
        "price_unit": "usd_per_kg",
        "notes": "SLA için esnek ve kauçuk benzeri elastik reçine (2500 TRY/kg @ 47 TRY/USD)."
    },
    {
        "material_key": "sla_castable_resin",
        "material_name": "SLA Döküm Reçinesi (Castable)",
        "category": "resin",
        "technology": "sla",
        "base_price_usd": 85.11,
        "price_unit": "usd_per_kg",
        "notes": "Hassas döküm uygulamaları için döküm reçinesi (4000 TRY/kg @ 47 TRY/USD)."
    }
]

print(json.dumps(missing_materials, indent=2, ensure_ascii=False))
