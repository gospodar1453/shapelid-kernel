"""
Shapelid Kernel v3.1.0 — Faz-6
Desteklenen teknolojiler:
  3D Baskı : FDM, SLA, SLS, MJF, DMLS
  Sac Metal: Laser Cutting, Bending
  CNC/EDM  : CNC Milling, CNC Turning, EDM
  Nesting  : SLS/MJF/DMLS batch nesting + prorata pricing  ← YENİ (Faz-6)

Faz-6 eklentileri:
  - /nest endpoint: çoklu parça batch yerleştirme + verimlilik
  - /nest-price endpoint: batch fiyatlandırma + prorata dağıtım
  - Savings hesabı: ayrı baskı vs batch baskı karşılaştırması
  - Build volume database: EOS P 396, HP 5200, Formlabs Fuse 1+, vb.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import tempfile
import os
import json

from analyzers.stl_analyzer import analyze_stl
from analyzers.dxf_analyzer import analyze_dxf
from analyzers.cnc_analyzer  import analyze_cnc
from analyzers.nesting_analyzer import analyze_nesting, BUILD_VOLUMES
from pricing.engine import calculate_price
from pricing.cnc_engine import calculate_cnc_price
from pricing.nesting_engine import calculate_nesting_price
from pricing.exchange_rate import get_rate_info, get_pricing_rate, get_usd_try
from pricing.finish_rates import (
    FINISH_RATES, COLOR_RATES, RESOLUTION_RATES,
    INFILL_PRESETS, HARDNESS_RATES, TOLERANCE_RATES, CERT_RATES
)

# Teknoloji kategorileri
CNC_TECHNOLOGIES = {"cnc_milling", "cnc_turning", "edm"}
SHEET_TECHNOLOGIES = {"laser", "bending"}
NESTING_TECHNOLOGIES = {"sls", "mjf", "dmls"}

app = FastAPI(
    title="Shapelid Geometry Kernel",
    version="3.1.0",
    description="Faz-6: Nesting Optimizasyonu + SLS/MJF batch pricing"
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
        "version"       : "3.1.0",
        "phase"         : "faz-6",
        "technologies"  : {
            "3d_printing" : ["fdm", "sla", "sls", "mjf", "dmls"],
            "sheet_metal" : ["laser", "bending"],
            "cnc_edm"     : ["cnc_milling", "cnc_turning", "edm"],
            "nesting"     : list(NESTING_TECHNOLOGIES),
        },
        "exchange_rate" : get_rate_info(),
    }


@app.get("/exchange-rate")
def exchange_rate(force_refresh: bool = False):
    if force_refresh:
        get_usd_try(force_refresh=True)
    return get_rate_info()


# ── /analyze (mevcut — değişiklik yok) ─────────────────────────────────────

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    technology              : str            = "fdm",
    material                : str            = "pla",
    quantity                : int            = 1,
    layer_height            : float          = 0.2,
    infill                  : float          = 0.2,
    material_thickness      : float          = 2.0,
    finish                  : str            = "standard",
    color                   : str            = "none",
    resolution              : str            = "standard",
    hardness                : str            = "standard",
    tolerance               : str            = "standard",
    certification           : str            = "none",
    material_price_usd_per_kg: Optional[float] = Query(default=None),
):
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in [".stl", ".dxf"]:
        raise HTTPException(status_code=400, detail=f"Desteklenmeyen format: {ext}. STL veya DXF gerekli.")

    if technology in CNC_TECHNOLOGIES and ext != ".stl":
        raise HTTPException(status_code=400, detail=f"{technology} yalnızca STL kabul eder.")

    if technology in SHEET_TECHNOLOGIES and ext != ".dxf":
        raise HTTPException(status_code=400, detail=f"{technology} yalnızca DXF kabul eder.")

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        params = {
            "technology"               : technology,
            "material"                 : material,
            "quantity"                 : quantity,
            "layer_height"             : layer_height,
            "infill"                   : infill,
            "material_thickness"       : material_thickness,
            "finish"                   : finish,
            "color"                    : color,
            "resolution"               : resolution,
            "hardness"                 : hardness,
            "tolerance"                : tolerance,
            "certification"            : certification,
            "material_price_usd_per_kg": material_price_usd_per_kg,
        }

        if technology in CNC_TECHNOLOGIES:
            geometry = analyze_stl(tmp_path)
            cnc_features = analyze_cnc(tmp_path, technology)
            geometry = {
                **geometry,
                "type"             : "cnc",
                "technology"       : technology,
                "feature_summary"  : cnc_features["feature_summary"],
                "rotational_analysis": cnc_features.get("rotational_analysis", {}),
                "workload_index"   : cnc_features["workload_index"],
                "setup_complexity" : cnc_features["setup_complexity"],
                "warnings"         : geometry.get("warnings", []) + cnc_features.get("warnings", []),
            }
            pricing = calculate_cnc_price(geometry, params)
        elif ext == ".stl":
            geometry = analyze_stl(tmp_path)
            pricing  = calculate_price(geometry, params)
        else:
            geometry = analyze_dxf(tmp_path)
            pricing  = calculate_price(geometry, params)

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
            "file"       : file.filename,
            "format"     : ext,
            "technology" : technology,
            "material"   : material,
            "quantity"   : quantity,
            "options"    : {
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


# ── /nest — Nesting analizi (Faz-6 YENİ) ─────────────────────────────────────

class NestPart(BaseModel):
    part_id: str
    dimensions_mm: dict        # {x, y, z}
    volume_cm3: float
    quantity: int = 1
    can_rotate: bool = True

class NestRequest(BaseModel):
    parts: List[NestPart]
    technology: str = "sls"
    machine_variant: str = "default"

@app.post("/nest")
def nest_analysis(req: NestRequest):
    """
    Birden fazla parçayı SLS/MJF/DMLS build volume'una yerleştirir.
    Verimlilik, batch sayısı ve yerleştirme koordinatlarını döndürür.
    """
    if req.technology not in NESTING_TECHNOLOGIES:
        raise HTTPException(
            status_code=400,
            detail=f"Nesting yalnızca {NESTING_TECHNOLOGIES} teknolojileri için desteklenir."
        )

    parts_data = [
        {
            "part_id"     : p.part_id,
            "dimensions_mm": p.dimensions_mm,
            "volume_cm3"  : p.volume_cm3,
            "quantity"    : p.quantity,
            "can_rotate"  : p.can_rotate,
        }
        for p in req.parts
    ]

    result = analyze_nesting(parts_data, req.technology, req.machine_variant)

    # Dataclass → dict
    return {
        "build_volume"       : result.build_volume,
        "parts_placed"       : result.parts_placed,
        "parts_unplaced"     : result.parts_unplaced,
        "total_parts"        : result.total_parts,
        "placed_count"       : result.placed_count,
        "packing_efficiency" : result.packing_efficiency,
        "footprint_efficiency": result.footprint_efficiency,
        "layers_used"        : result.layers_used,
        "build_height_mm"    : result.build_height_mm,
        "unused_volume_cm3"  : result.unused_volume_cm3,
        "nesting_score"      : result.nesting_score,
        "warnings"           : result.warnings,
        "batch_count"        : result.batch_count,
    }


# ── /nest-price — Nesting + Fiyatlandırma (Faz-6 YENİ) ───────────────────────

class NestPriceRequest(BaseModel):
    parts: List[NestPart]
    technology: str = "sls"
    machine_variant: str = "default"
    material: str = "pa12"
    material_price_usd_per_kg: Optional[float] = None

@app.post("/nest-price")
def nest_with_pricing(req: NestPriceRequest):
    """
    Nesting analizi + batch fiyatlandırma.
    Ayrı baskı vs batch baskı tasarruf karşılaştırması döndürür.
    """
    if req.technology not in NESTING_TECHNOLOGIES:
        raise HTTPException(
            status_code=400,
            detail=f"Nesting yalnızca {NESTING_TECHNOLOGIES} teknolojileri için desteklenir."
        )

    parts_data = [
        {
            "part_id"     : p.part_id,
            "dimensions_mm": p.dimensions_mm,
            "volume_cm3"  : p.volume_cm3,
            "quantity"    : p.quantity,
            "can_rotate"  : p.can_rotate,
        }
        for p in req.parts
    ]

    # 1. Nesting analizi
    nest_result = analyze_nesting(parts_data, req.technology, req.machine_variant)

    # 2. Fiyatlandırma
    nest_dict = {
        "build_volume"       : nest_result.build_volume,
        "parts_placed"        : nest_result.parts_placed,
        "batch_count"         : nest_result.batch_count,
        "build_height_mm"     : nest_result.build_height_mm,
        "packing_efficiency"  : nest_result.packing_efficiency,
    }

    pricing = calculate_nesting_price(
        nesting_result    = nest_dict,
        parts             = parts_data,
        technology        = req.technology,
        material_price_kg = req.material_price_usd_per_kg,
    )

    # 3. Kur dönüşümü
    rate = get_pricing_rate(req.technology)
    pricing_rate = rate["pricing_rate"]

    return {
        "nesting": {
            "build_volume"       : nest_result.build_volume,
            "placed_count"        : nest_result.placed_count,
            "unplaced_count"      : len(nest_result.parts_unplaced),
            "packing_efficiency"  : nest_result.packing_efficiency,
            "footprint_efficiency": nest_result.footprint_efficiency,
            "nesting_score"       : nest_result.nesting_score,
            "batch_count"         : nest_result.batch_count,
            "build_height_mm"     : nest_result.build_height_mm,
            "parts_placed"        : nest_result.parts_placed,
            "parts_unplaced"      : nest_result.parts_unplaced,
            "warnings"            : nest_result.warnings,
        },
        "pricing": {
            **pricing,
            "total_price_try": round(pricing["total_price"] * pricing_rate, 2),
        },
        "exchange_rate": {
            "tcmb_rate"   : rate["tcmb_rate"],
            "pricing_rate": pricing_rate,
            "buffer_pct"  : rate["buffer_pct"],
        },
    }


# ── /technologies (güncellendi — nesting info eklendi) ──────────────────────

@app.get("/technologies")
def list_technologies():
    return {
        "3d_printing": {
            "fdm" : {"description": "Fused Deposition Modeling", "materials": ["pla","abs","petg","tpu","asa"], "input_formats": ["stl"]},
            "sla" : {"description": "Stereolithography", "materials": ["standard_resin","tough_resin","flexible_resin","castable_resin"], "input_formats": ["stl"]},
            "sls" : {"description": "Selective Laser Sintering", "materials": ["pa12","pa11","tpu"], "input_formats": ["stl"], "nesting": True},
            "mjf" : {"description": "HP Multi Jet Fusion", "materials": ["pa12","pa12gb"], "input_formats": ["stl"], "nesting": True},
            "dmls": {"description": "Direct Metal Laser Sintering", "materials": ["316l","ti64"], "input_formats": ["stl"], "nesting": True},
        },
        "sheet_metal": {
            "laser"  : {"description": "Laser Cutting", "materials": ["mild_steel","stainless_steel","aluminum","copper","brass","galvanized_steel"], "input_formats": ["dxf"]},
            "bending": {"description": "Sheet Metal Bending", "materials": ["mild_steel","stainless_steel","aluminum"], "input_formats": ["dxf"]},
        },
        "cnc_edm": {
            "cnc_milling": {"description": "CNC Freze (3 eksen VMC)", "materials": ["aluminum","mild_steel","stainless_steel","ss304","ss316l","titanium","ti6al4v","copper"], "input_formats": ["stl"]},
            "cnc_turning": {"description": "CNC Torna (2-3 eksen)", "materials": ["aluminum","mild_steel","stainless_steel","ss304","ss316l","titanium","ti6al4v","copper"], "input_formats": ["stl"]},
            "edm"        : {"description": "EDM Tel Erozyon", "materials": ["tool_steel","h13_steel","d2_steel","stainless_steel","ss304","ss316l","aluminum","titanium","copper"], "input_formats": ["stl"]},
        },
        "nesting": {
            "supported_technologies": list(NESTING_TECHNOLOGIES),
            "build_volumes": BUILD_VOLUMES,
        },
    }


# ── /build-volumes (Faz-6 YENİ) ──────────────────────────────────────────────

@app.get("/build-volumes")
def list_build_volumes(technology: Optional[str] = None):
    """Makine build volume boyutlarını döndürür."""
    if technology:
        return {
            "technology"    : technology,
            "build_volumes"  : BUILD_VOLUMES.get(technology, {}),
        }
    return {"build_volumes": BUILD_VOLUMES}


# ── /options (mevcut — değişiklik yok) ──────────────────────────────────────

@app.get("/options")
def list_options(technology: str = "fdm"):
    if technology in CNC_TECHNOLOGIES:
        return _cnc_options(technology)

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


def _cnc_options(technology: str) -> dict:
    cnc_finishes = [
        {"key": "standard",       "label": "Standard (As Machined)",  "multiplier": 1.0,  "flat_cost": 0},
        {"key": "deburr",         "label": "Deburr & Edge Break",     "multiplier": 1.05, "flat_cost": 2},
        {"key": "polish",         "label": "Surface Polish (Ra 0.8)", "multiplier": 1.20, "flat_cost": 8},
        {"key": "mirror_polish",  "label": "Mirror Polish (Ra 0.2)",  "multiplier": 1.40, "flat_cost": 20},
        {"key": "anodize",        "label": "Anodize (Alüminyum)",     "multiplier": 1.15, "flat_cost": 15},
        {"key": "anodize_color",  "label": "Color Anodize",           "multiplier": 1.25, "flat_cost": 20},
        {"key": "hard_anodize",   "label": "Hard Anodize (Type III)", "multiplier": 1.35, "flat_cost": 25},
        {"key": "powder_coat",    "label": "Powder Coating",          "multiplier": 1.20, "flat_cost": 18},
        {"key": "zinc_plate",     "label": "Zinc Plating",            "multiplier": 1.15, "flat_cost": 12},
        {"key": "nickel_plate",   "label": "Nickel Plating",          "multiplier": 1.25, "flat_cost": 22},
        {"key": "black_oxide",    "label": "Black Oxide",             "multiplier": 1.10, "flat_cost": 8},
        {"key": "passivation",    "label": "Passivation (SS)",        "multiplier": 1.08, "flat_cost": 10},
    ]
    cnc_tolerances = [
        {"key": "standard",  "label": "Standard (±0.1mm)",   "multiplier": 1.0},
        {"key": "medium",    "label": "Medium (±0.05mm)",     "multiplier": 1.20},
        {"key": "fine",      "label": "Fine (±0.025mm)",      "multiplier": 1.50},
        {"key": "ultra",     "label": "Ultra (±0.01mm)",      "multiplier": 2.00},
        {"key": "jig_grade", "label": "Jig Grade (±0.005mm)", "multiplier": 3.00},
    ]
    cnc_certs = [
        {"key": "none",           "label": "Sertifika Yok",            "flat_cost": 0},
        {"key": "material_cert",  "label": "Malzeme Sertifikası (MTC)","flat_cost": 15},
        {"key": "first_article",  "label": "First Article Inspection", "flat_cost": 40},
        {"key": "iso9001",        "label": "ISO 9001 Uyumlu Üretim",   "flat_cost": 60},
        {"key": "as9100",         "label": "AS9100 (Havacılık)",        "flat_cost": 120},
    ]
    thread_options = [
        {"key": "none",      "label": "Diş Yok"},
        {"key": "metric",    "label": "Metrik Diş (M2-M64)"},
        {"key": "inch_unc",  "label": "İnç Diş (UNC/UNF)"},
        {"key": "pipe",      "label": "Boru Dişi (BSP/NPT)"},
    ]

    return {
        "technology"    : technology,
        "finish"        : cnc_finishes,
        "tolerance"     : cnc_tolerances,
        "certification" : cnc_certs,
        "thread_options": thread_options,
        "materials"     : [
            {"key": "aluminum",        "label": "Aluminyum 6061"},
            {"key": "mild_steel",      "label": "Çelik S235/S355"},
            {"key": "stainless_steel", "label": "Paslanmaz 304"},
            {"key": "ss316l",          "label": "Paslanmaz 316L"},
            {"key": "titanium",        "label": "Titanyum Grade 5 (Ti-6Al-4V)"},
            {"key": "copper",          "label": "Bakır"},
            {"key": "tool_steel",      "label": "Takım Çeliği (EDM)"},
            {"key": "h13_steel",       "label": "H13 Sıcak İş Çeliği"},
        ] if technology == "edm" else [
            {"key": "aluminum",        "label": "Aluminyum 6061"},
            {"key": "mild_steel",      "label": "Çelik S235/S355"},
            {"key": "stainless_steel", "label": "Paslanmaz 304"},
            {"key": "ss316l",          "label": "Paslanmaz 316L"},
            {"key": "titanium",        "label": "Titanyum Grade 5 (Ti-6Al-4V)"},
            {"key": "copper",          "label": "Bakır"},
        ],
        "note": "STL üzerinden CNC feature tespiti yaklaşıksal. Kesin fiyat için STEP/IGES dosyası önerilir."
    }
