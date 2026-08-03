"""
Shapelid Geometry Kernel — v4.0.0 (Faz-5)
Desteklenen teknolojiler: FDM, SLA, SLS, MJF, DMLS, Laser Cutting, Bending,
                          CNC Turning, CNC Milling, EDM

Faz-5 eklentileri:
  - CNC Feature Recognition (cnc_analyzer.py)
  - CNC Pricing (cnc_pricing.py)
  - /analyze-cnc endpoint — STEP/IGES/STL kabul eder, CNC özellik tespiti yapar
  - /features endpoint — feature-only analysis (fiyat hesabı olmadan)

Geriye dönük uyumlu: /analyze endpoint'i hala STL + DXF kabul eder (3D printing / sheet metal)
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import tempfile
import os

from analyzers.stl_analyzer import analyze_stl
from analyzers.dxf_analyzer import analyze_dxf
from analyzers.cnc_analyzer import analyze_cnc
from pricing.engine import calculate_price
from pricing.cnc_pricing import price_cnc
from pricing.exchange_rate import get_rate_info, get_pricing_rate, get_usd_try
from pricing.finish_rates import (
    FINISH_RATES, COLOR_RATES, RESOLUTION_RATES,
    INFILL_PRESETS, HARDNESS_RATES, TOLERANCE_RATES, CERT_RATES
)

app = FastAPI(
    title="Shapelid Geometry Kernel",
    version="4.0.0",
    description="Faz-5: CNC feature recognition + STEP/IGES + all 11 technologies"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# CNC technologies
CNC_TECHNOLOGIES = {"cnc_turning", "cnc_milling", "edm"}
# All supported file formats
SUPPORTED_FORMATS_3D = {".stl", ".obj", ".step", ".stp", ".iges", ".igs"}
CNC_FORMATS = {".stl", ".obj", ".step", ".stp", ".iges", ".igs"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "4.0.0",
        "phase": "faz-5",
        "exchange_rate": get_rate_info(),
    }


@app.get("/exchange-rate")
def exchange_rate(force_refresh: bool = False):
    if force_refresh:
        get_usd_try(force_refresh=True)
    return get_rate_info()


# ─────────────────────────────────────────────
# 3D PRINTING / SHEET METAL ANALYSIS (existing)
# ─────────────────────────────────────────────

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
    auto_repair             : bool           = False,
):
    ext = os.path.splitext(file.filename)[1].lower()

    # Route CNC technologies to /analyze-cnc
    if technology in CNC_TECHNOLOGIES:
        return await _analyze_cnc_impl(
            file, technology, material, quantity,
            tolerance, finish, material_price_usd_per_kg, auto_repair
        )

    if ext not in [".stl", ".dxf"]:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen format: {ext}. /analyze STL ve DXF kabul eder. CNC için /analyze-cnc kullanın."
        )

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        if ext == ".stl":
            geometry = analyze_stl(tmp_path, auto_repair=auto_repair)
        else:
            geometry = analyze_dxf(tmp_path)

        params = {
            "technology": technology, "material": material, "quantity": quantity,
            "layer_height": layer_height, "infill": infill,
            "material_thickness": material_thickness,
            "finish": finish, "color": color, "resolution": resolution,
            "hardness": hardness, "tolerance": tolerance,
            "certification": certification,
            "material_price_usd_per_kg": material_price_usd_per_kg,
        }
        pricing = calculate_price(geometry, params)

        rate = get_pricing_rate(technology)
        pricing_rate = rate["pricing_rate"]
        pricing_try = {
            "unit_price_try": round(pricing["unit_price"] * pricing_rate, 2),
            "total_price_try": round(pricing["total_price"] * pricing_rate, 2),
            "valid_until": rate["valid_until"],
            "valid_hours": rate["valid_hours"],
            "exchange_rate": {
                "tcmb_rate": rate["tcmb_rate"],
                "pricing_rate": pricing_rate,
                "buffer_pct": rate["buffer_pct"],
                "source": rate["source"],
                "fetched_at": rate["fetched_at"],
            },
        }

        return {
            "file": file.filename, "format": ext,
            "technology": technology, "material": material, "quantity": quantity,
            "options": {
                "finish": finish, "color": color, "resolution": resolution,
                "hardness": hardness, "tolerance": tolerance, "certification": certification,
            },
            "geometry": geometry, "pricing": pricing, "pricing_try": pricing_try,
        }

    finally:
        os.unlink(tmp_path)


# ─────────────────────────────────────────────
# CNC FEATURE RECOGNITION + PRICING (Faz-5)
# ─────────────────────────────────────────────

@app.post("/analyze-cnc")
async def analyze_cnc_endpoint(
    file: UploadFile = File(...),
    technology              : str            = Form("cnc_milling"),
    material                : str            = Form("aluminum"),
    quantity                : int            = Form(1),
    tolerance               : str            = Form("standard"),
    finish                  : str            = Form("standard"),
    material_price_usd_per_kg: Optional[float] = Form(default=None),
    auto_repair             : bool           = Form(False),
):
    """
    CNC Feature Recognition + Pricing endpoint.
    STEP/IGES/STL/OBJ dosyalarını kabul eder.

    1. Mesh yükle (STL/OBJ direkt, STEP/IGES için OCCT worker)
    2. CNC feature tespiti (hole, pocket, slot, fillet, chamfer)
    3. Machine time estimation (feature-based)
    4. Fiyat hesabı (material + machine + tooling + setup)
    """
    return await _analyze_cnc_impl(
        file, technology, material, quantity,
        tolerance, finish, material_price_usd_per_kg, auto_repair
    )


@app.post("/features")
async def features_only(
    file: UploadFile = File(...),
    technology              : str            = Form("cnc_milling"),
    auto_repair             : bool           = Form(False),
):
    """
    Sadece feature tespiti — fiyat hesabı olmadan.
    UI'da hızlı önizleme için kullanılır.
    """
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in CNC_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen format: {ext}. Kabul edilenler: {', '.join(CNC_FORMATS)}"
        )

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        features = analyze_cnc(tmp_path, technology=technology, auto_repair=auto_repair)
        return {
            "file": file.filename,
            "format": ext,
            "technology": technology,
            "features": features,
        }
    finally:
        os.unlink(tmp_path)


async def _analyze_cnc_impl(
    file: UploadFile,
    technology: str,
    material: str,
    quantity: int,
    tolerance: str,
    finish: str,
    material_price_usd_per_kg: Optional[float],
    auto_repair: bool,
):
    """CNC analiz + fiyatlandırma ortak implementation."""
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in CNC_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen format: {ext}. CNC için kabul edilenler: {', '.join(CNC_FORMATS)}"
        )

    # STEP/IGES için şu an mesh gerekiyor (OCCT client-side yapıldığı için
    # kernel'a STL/OBJ gelmesi beklenir, ama STEP/IGES de kabul edilir —
    # trimesh STEP'i mesh olarak yükleyebilir)
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # CNC feature recognition
        geometry = analyze_cnc(tmp_path, technology=technology, auto_repair=auto_repair)

        # CNC pricing
        params = {
            "technology": technology,
            "material": material,
            "quantity": quantity,
            "tolerance": tolerance,
            "finish": finish,
            "material_price_usd_per_kg": material_price_usd_per_kg,
        }
        pricing = price_cnc(geometry, params)

        # Exchange rate
        rate = get_pricing_rate(technology)
        pricing_rate = rate["pricing_rate"]
        pricing_try = {
            "unit_price_try": round(pricing["unit_price"] * pricing_rate, 2),
            "total_price_try": round(pricing["total_price"] * pricing_rate, 2),
            "valid_until": rate["valid_until"],
            "valid_hours": rate["valid_hours"],
            "exchange_rate": {
                "tcmb_rate": rate["tcmb_rate"],
                "pricing_rate": pricing_rate,
                "buffer_pct": rate["buffer_pct"],
                "source": rate["source"],
                "fetched_at": rate["fetched_at"],
            },
        }

        return {
            "file": file.filename,
            "format": ext,
            "technology": technology,
            "material": material,
            "quantity": quantity,
            "geometry": geometry,
            "features_summary": pricing.get("features_summary", {}),
            "pricing": pricing,
            "pricing_try": pricing_try,
        }

    finally:
        os.unlink(tmp_path)


# ─────────────────────────────────────────────
# ENDPOINTS (existing)
# ─────────────────────────────────────────────

@app.get("/technologies")
def list_technologies():
    return {
        "3d_printing": {
            "fdm": {"description": "Fused Deposition Modeling",
                     "materials": ["pla", "abs", "petg", "tpu", "asa"],
                     "input_formats": ["stl"]},
            "sla": {"description": "Stereolithography",
                     "materials": ["standard_resin", "tough_resin", "flexible_resin", "castable_resin"],
                     "input_formats": ["stl"]},
            "sls": {"description": "Selective Laser Sintering",
                     "materials": ["pa12", "pa11", "tpu"],
                     "input_formats": ["stl"]},
            "mjf": {"description": "HP Multi Jet Fusion",
                     "materials": ["pa12", "pa12gb"],
                     "input_formats": ["stl"]},
            "dmls": {"description": "Direct Metal Laser Sintering",
                     "materials": ["316l", "ti64"],
                     "input_formats": ["stl"]},
        },
        "sheet_metal": {
            "laser": {"description": "Laser Cutting",
                        "materials": ["mild_steel", "stainless_steel", "aluminum", "copper", "brass", "galvanized_steel"],
                        "input_formats": ["dxf"]},
            "bending": {"description": "Sheet Metal Bending",
                        "materials": ["mild_steel", "stainless_steel", "aluminum"],
                        "input_formats": ["dxf"]},
        },
        "cnc": {
            "cnc_turning": {"description": "CNC Turning (2-3 axis)",
                            "materials": ["aluminum", "mild_steel", "stainless_304", "stainless_316",
                                           "brass", "copper", "titanium", "tool_steel"],
                            "input_formats": ["stl", "step", "stp", "iges", "igs"]},
            "cnc_milling": {"description": "CNC Milling (3-5 axis)",
                            "materials": ["aluminum", "mild_steel", "stainless_304", "stainless_316",
                                           "brass", "copper", "titanium", "tool_steel"],
                            "input_formats": ["stl", "step", "stp", "iges", "igs"]},
            "edm": {"description": "EDM (Wire/Sinker)",
                    "materials": ["aluminum", "mild_steel", "stainless_304", "stainless_316",
                                  "tool_steel", "titanium"],
                    "input_formats": ["stl", "step", "stp", "iges", "igs"]},
        },
    }


@app.get("/options")
def list_options(technology: str = "fdm"):
    def _filter(rate_dict: dict, tech: str) -> list:
        result = []
        for key, val in rate_dict.items():
            allowed = val.get("technologies", [])
            if not allowed or tech in allowed:
                result.append({
                    "key": key,
                    "label": val.get("label", key),
                    "multiplier": val.get("multiplier", 1.0),
                    "flat_cost": val.get("flat_cost", 0.0),
                })
        return result

    return {
        "technology": technology,
        "finish": _filter(FINISH_RATES, technology),
        "color": _filter(COLOR_RATES, technology),
        "resolution": _filter(RESOLUTION_RATES, technology),
        "hardness": _filter(HARDNESS_RATES, technology),
        "tolerance": _filter(TOLERANCE_RATES, technology),
        "certification": [{"key": k, "label": v["label"], "flat_cost": v["flat_cost"]}
                          for k, v in CERT_RATES.items()],
        "infill_presets": [{"key": k, "label": v["label"], "ratio": v["ratio"]}
                           for k, v in INFILL_PRESETS.items()],
    }
