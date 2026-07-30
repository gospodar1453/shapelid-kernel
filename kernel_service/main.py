"""
Shapelid Kernel Faz-2 Mikroservisi
Desteklenen teknolojiler: FDM, SLA, SLS, MJF, DMLS, Laser Cutting, Bending

Faz-2 eklentileri:
  - finish, color, resolution, hardness, tolerance, certification parametreleri
  - apply_options() ile çarpan + sabit maliyet entegrasyonu
  - /options endpoint — teknoloji bazlı geçerli seçim listesi
  - auto_repair parametresi — non-manifold mesh otomatik onarımı

Kur riski önlemleri:
  A) %4 kur tamponu (pricing_rate = TCMB * 1.04)
  B) Teklif geçerlilik süresi (valid_until)
  C) DB'den canlı malzeme fiyatı (material_price_usd_per_kg parametresi)
  D) İç hesap USD, müşteriye TRY gösterim
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import tempfile
import os

from analyzers.stl_analyzer import analyze_stl
from analyzers.dxf_analyzer import analyze_dxf
from pricing.engine import calculate_price
from pricing.exchange_rate import get_rate_info, get_pricing_rate, get_usd_try
from pricing.finish_rates import (
    FINISH_RATES, COLOR_RATES, RESOLUTION_RATES,
    INFILL_PRESETS, HARDNESS_RATES, TOLERANCE_RATES, CERT_RATES
)

app = FastAPI(
    title="Shapelid Geometry Kernel",
    version="2.1.0",
    description="Faz-2: finish/color/resolution/hardness/tolerance/cert + auto mesh repair"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status"        : "ok",
        "version"       : "2.1.0",
        "phase"         : "faz-2",
        "exchange_rate" : get_rate_info(),
    }


@app.get("/exchange-rate")
def exchange_rate(force_refresh: bool = False):
    if force_refresh:
        get_usd_try(force_refresh=True)
    return get_rate_info()


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    # ── Temel parametreler ──
    technology              : str            = "fdm",
    material                : str            = "pla",
    quantity                : int            = 1,
    layer_height            : float          = 0.2,
    infill                  : float          = 0.2,
    material_thickness      : float          = 2.0,
    # ── Faz-2 seçim parametreleri ──
    finish                  : str            = "standard",
    color                   : str            = "none",
    resolution              : str            = "standard",
    hardness                : str            = "standard",
    tolerance               : str            = "standard",
    certification           : str            = "none",
    # ── Canlı DB fiyatı ──
    material_price_usd_per_kg: Optional[float] = Query(default=None),
    # ── Mesh onarımı ──
    auto_repair             : bool           = False,
):
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in [".stl", ".dxf"]:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen format: {ext}. Faz-2 yalnızca STL ve DXF kabul eder."
        )

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Geometrik analiz (auto_repair parametresi STL için geçerli)
        if ext == ".stl":
            geometry = analyze_stl(tmp_path, auto_repair=auto_repair)
        else:
            geometry = analyze_dxf(tmp_path)

        # Fiyat hesaplama
        params = {
            "technology"               : technology,
            "material"                 : material,
            "quantity"                 : quantity,
            "layer_height"             : layer_height,
            "infill"                   : infill,
            "material_thickness"       : material_thickness,
            # Faz-2 options
            "finish"                   : finish,
            "color"                    : color,
            "resolution"               : resolution,
            "hardness"                 : hardness,
            "tolerance"                : tolerance,
            "certification"            : certification,
            # Canlı DB fiyatı
            "material_price_usd_per_kg": material_price_usd_per_kg,
        }
        pricing = calculate_price(geometry, params)

        # Kur
        rate         = get_pricing_rate(technology)
        pricing_rate = rate["pricing_rate"]

        pricing_try = {
            "unit_price_try"  : round(pricing["unit_price"]  * pricing_rate, 2),
            "total_price_try" : round(pricing["total_price"] * pricing_rate, 2),
            "valid_until"     : rate["valid_until"],
            "valid_hours"     : rate["valid_hours"],
            "exchange_rate"   : {
                "tcmb_rate"   : rate["tcmb_rate"],
                "pricing_rate": pricing_rate,
                "buffer_pct"  : rate["buffer_pct"],
                "source"      : rate["source"],
                "fetched_at"  : rate["fetched_at"],
            },
        }

        return {
            "file"        : file.filename,
            "format"      : ext,
            "technology"  : technology,
            "material"    : material,
            "quantity"    : quantity,
            "options"     : {
                "finish"       : finish,
                "color"        : color,
                "resolution"   : resolution,
                "hardness"     : hardness,
                "tolerance"    : tolerance,
                "certification": certification,
            },
            "geometry"    : geometry,
            "pricing"     : pricing,
            "pricing_try" : pricing_try,
        }

    finally:
        os.unlink(tmp_path)


@app.get("/technologies")
def list_technologies():
    return {
        "3d_printing": {
            "fdm" : {"description": "Fused Deposition Modeling",
                     "materials"  : ["pla","abs","petg","tpu","asa"],
                     "input_formats": ["stl"]},
            "sla" : {"description": "Stereolithography",
                     "materials"  : ["standard_resin","tough_resin","flexible_resin","castable_resin"],
                     "input_formats": ["stl"]},
            "sls" : {"description": "Selective Laser Sintering",
                     "materials"  : ["pa12","pa11","tpu"],
                     "input_formats": ["stl"]},
            "mjf" : {"description": "HP Multi Jet Fusion",
                     "materials"  : ["pa12","pa12gb"],
                     "input_formats": ["stl"]},
            "dmls": {"description": "Direct Metal Laser Sintering",
                     "materials"  : ["316l","ti64"],
                     "input_formats": ["stl"]},
        },
        "sheet_metal": {
            "laser"  : {"description": "Laser Cutting",
                        "materials"  : ["mild_steel","stainless_steel","aluminum","copper","brass","galvanized_steel"],
                        "input_formats": ["dxf"]},
            "bending": {"description": "Sheet Metal Bending",
                        "materials"  : ["mild_steel","stainless_steel","aluminum"],
                        "input_formats": ["dxf"]},
        }
    }


@app.get("/options")
def list_options(technology: str = "fdm"):
    """
    Belirli bir teknoloji için geçerli seçim seçeneklerini döndürür.
    Frontend bu endpoint'i kullanarak dinamik dropdown listesi oluşturur.
    """
    def _filter(rate_dict: dict, tech: str) -> list:
        result = []
        for key, val in rate_dict.items():
            allowed = val.get("technologies", [])
            if not allowed or tech in allowed:
                result.append({
                    "key"        : key,
                    "label"      : val.get("label", key),
                    "multiplier" : val.get("multiplier", 1.0),
                    "flat_cost"  : val.get("flat_cost", 0.0),
                })
        return result

    return {
        "technology"   : technology,
        "finish"       : _filter(FINISH_RATES, technology),
        "color"        : _filter(COLOR_RATES, technology),
        "resolution"   : _filter(RESOLUTION_RATES, technology),
        "hardness"     : _filter(HARDNESS_RATES, technology),
        "tolerance"    : _filter(TOLERANCE_RATES, technology),
        "certification": [{"key": k, "label": v["label"], "flat_cost": v["flat_cost"]}
                          for k, v in CERT_RATES.items()],
        "infill_presets": [{"key": k, "label": v["label"], "ratio": v["ratio"]}
                           for k, v in INFILL_PRESETS.items()],
    }
