"""
Manual Quote Trigger Sistemi — Faz-4
Geometrik karmaşıklık, teknoloji uyumsuzluğu ve adet/boyut eşiklerine göre
otomatik fiyatlandırma yerine manuel teklif sürecine yönlendirme kararı verir.
"""

# BUILD VOLUME LIMITLERI (mm)
BUILD_VOLUME = {
    "fdm":    {"x": 300, "y": 300, "z": 300},
    "sla":    {"x": 335, "y": 200, "z": 300},
    "sls":    {"x": 340, "y": 340, "z": 600},
    "mjf":    {"x": 380, "y": 284, "z": 380},
    "dmls":   {"x": 250, "y": 250, "z": 325},
    "laser":  {"x": 3000, "y": 1500, "z": 0},
    "bending":{"x": 3000, "y": 1500, "z": 0},
    "cnc_milling":  {"x": 1000, "y": 600, "z": 500},
    "cnc_turning":  {"x": 500,  "y": 500, "z": 1000},
    "edm":    {"x": 400, "y": 300, "z": 250},
}

# ADET EŞİKLERİ
QUANTITY_THRESHOLD = {
    "fdm": 500, "sla": 200, "sls": 1000, "mjf": 1000, "dmls": 50,
    "laser": 5000, "bending": 2000, "cnc_milling": 500, "cnc_turning": 500, "edm": 100,
}

# KARMAŞIKLIK EŞİKLERİ
COMPLEXITY_THRESHOLD = {
    "fdm": 80, "sla": 85, "sls": 75, "mjf": 75, "dmls": 65,
    "cnc_milling": 70, "cnc_turning": 60, "edm": 55,
}

# OVERHANG ORANI EŞİKLERİ
SUPPORT_RATIO_THRESHOLD = {
    "fdm": 0.50, "sla": 0.40, "sls": None, "mjf": None, "dmls": 0.35,
}

# İNCE DUVAR EŞİKLERİ (mm)
THIN_WALL_THRESHOLD = {
    "fdm": 0.8, "sla": 0.3, "sls": 0.7, "mjf": 0.5, "dmls": 0.4,
    "cnc_milling": 0.5, "cnc_turning": 0.3, "edm": 0.1, "laser": 0.5, "bending": 0.5,
}

# MİNİMUM FİYAT EŞİKLERİ (USD)
MIN_PRICE_THRESHOLD = {
    "fdm": 1.50, "sla": 2.00, "sls": 8.00, "mjf": 8.00, "dmls": 30.00,
    "laser": 5.00, "bending": 5.00, "cnc_milling": 20.00, "cnc_turning": 15.00, "edm": 50.00,
}

# TEKNOLOJİ UYUMSUZLUK TABLOSU
INCOMPATIBLE_COMBINATIONS = [
    ("pla",      "sls",   "PLA SLS teknolojisiyle uyumlu değil. PA12 veya TPU önerilir."),
    ("pla",      "mjf",   "PLA MJF teknolojisiyle uyumlu değil. PA12 önerilir."),
    ("pla",      "dmls",  "PLA metal 3D baskı için uygulanamaz."),
    ("petg",     "sls",   "PETG SLS ile uyumsuz. PA12 önerilir."),
    ("petg",     "dmls",  "PETG metal 3D baskı için uygulanamaz."),
    ("resin",    "fdm",   "Resin malzeme FDM ile kullanılamaz. SLA/DLP gereklidir."),
    ("resin",    "sls",   "Resin SLS ile kullanılamaz."),
    ("inconel",  "fdm",   "Inconel FDM ile üretilemez. DMLS gereklidir."),
    ("inconel",  "sla",   "Inconel SLA ile üretilemez. DMLS gereklidir."),
    ("titanium", "fdm",   "Titanyum FDM ile üretilemez. DMLS gereklidir."),
    ("titanium", "sla",   "Titanyum SLA ile üretilemez. DMLS gereklidir."),
    ("titanium", "laser", "Titanyum lazer kesimde özel ekipman gerektirir."),
    ("maraging", "fdm",   "Maraging çeliği yalnızca DMLS ile üretilebilir."),
    ("maraging", "sla",   "Maraging çeliği yalnızca DMLS ile üretilebilir."),
    ("tpu",      "sls",   "TPU SLS'de yalnızca özel donanımla işlenebilir."),
]


def evaluate_manual_quote(geometry: dict, params: dict, unit_price: float = None) -> dict:
    technology    = params.get("technology", "fdm").lower()
    material      = params.get("material", "").lower()
    quantity      = int(params.get("quantity", 1))
    dims          = geometry.get("dimensions_mm", {})
    support_ratio = geometry.get("support_ratio", 0)
    complexity    = geometry.get("complexity_score", 0)

    triggers = []
    warnings = []

    # 1. Build volume
    bv = BUILD_VOLUME.get(technology)
    if bv and dims:
        for axis in ["x", "y", "z"]:
            limit = bv.get(axis, 0)
            val   = dims.get(f"{axis}_mm", 0)
            if limit > 0 and val > limit:
                triggers.append({
                    "code": "BUILD_VOLUME_EXCEEDED", "severity": "critical",
                    "message": f"Parça {axis.upper()} ekseninde {val}mm — {technology.upper()} limiti {limit}mm.",
                })

    # 2. Adet
    qty_limit = QUANTITY_THRESHOLD.get(technology)
    if qty_limit and quantity > qty_limit:
        triggers.append({
            "code": "QUANTITY_EXCEEDED", "severity": "high",
            "message": f"{quantity} adet {technology.upper()} için yüksek (eşik: {qty_limit}). Alternatif üretim değerlendirilebilir.",
        })

    # 3. Geometrik karmaşıklık
    cplx_limit = COMPLEXITY_THRESHOLD.get(technology, 80)
    if complexity >= cplx_limit:
        triggers.append({
            "code": "HIGH_COMPLEXITY", "severity": "high",
            "message": f"Geometrik karmaşıklık {complexity}/100 — {technology.upper()} eşiği {cplx_limit}.",
        })

    # 4. Overhang / destek oranı
    sr_limit = SUPPORT_RATIO_THRESHOLD.get(technology)
    if sr_limit is not None and support_ratio > sr_limit:
        triggers.append({
            "code": "HIGH_SUPPORT_RATIO", "severity": "high",
            "message": f"Overhang oranı %{round(support_ratio*100,1)} — {technology.upper()} eşiği %{round(sr_limit*100):.0f}.",
        })

    # 5. İnce duvar
    min_dim = min(dims.get("x_mm", 999), dims.get("y_mm", 999), dims.get("z_mm", 999))
    tw_limit = THIN_WALL_THRESHOLD.get(technology)
    if tw_limit and min_dim < tw_limit:
        sev = "high" if min_dim < tw_limit * 0.5 else "medium"
        entry = {
            "code": "THIN_WALL", "severity": sev,
            "message": f"Min boyut {min_dim}mm — {technology.upper()} min duvar {tw_limit}mm.",
        }
        triggers.append(entry) if sev == "high" else warnings.append(entry)

    # 6. Teknoloji uyumsuzluğu
    for mat_kw, tech_kw, msg in INCOMPATIBLE_COMBINATIONS:
        if mat_kw in material and tech_kw == technology:
            triggers.append({
                "code": "INCOMPATIBLE_COMBINATION", "severity": "critical",
                "message": msg,
            })

    # 7. Non-manifold uyarı
    if not geometry.get("is_watertight", True):
        warnings.append({
            "code": "NON_MANIFOLD", "severity": "medium",
            "message": "Mesh kapalı değil (non-manifold). Baskı öncesi onarım gerekebilir.",
        })

    # 8. Minimum fiyat
    if unit_price is not None:
        min_price = MIN_PRICE_THRESHOLD.get(technology, 1.0)
        if unit_price < min_price:
            warnings.append({
                "code": "BELOW_MIN_PRICE", "severity": "low",
                "message": f"Birim fiyat ${unit_price:.2f} — minimum eşik ${min_price:.2f}.",
            })

    manual_quote = any(t["severity"] in ("critical", "high") for t in triggers)

    return {
        "manual_quote":        manual_quote,
        "auto_price_allowed":  not manual_quote,
        "trigger_count":       len(triggers),
        "warning_count":       len(warnings),
        "triggers":            triggers,
        "warnings":            warnings,
    }
