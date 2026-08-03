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
from typing import Optional, List
import tempfile
import os

from analyzers.stl_analyzer import analyze_stl
from analyzers.dxf_analyzer import analyze_dxf
from analyzers.cnc_analyzer import analyze_cnc
from analyzers.nesting import analyze_nesting, get_build_volumes
from pricing.engine import calculate_price
from pricing.cnc_pricing import price_cnc
from pricing.calibration import compute_calibration_factors, apply_calibration, calibration_demo
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


# ── Build Volumes (Faz-6) ─────────────────────────────────────────────

@app.get("/build-volumes")
async def build_volumes(technology: Optional[str] = Query(default=None)):
    """Build volume listesi (3D printing teknolojileri için)."""
    return get_build_volumes(technology)


# ── Nesting (Faz-6) ──────────────────────────────────────────────────

@app.post("/nest")
async def nest_analysis(
    files: List[UploadFile] = File(...),
    technology: str = Form("sls"),
    machine: Optional[str] = Form(None),
    gap_mm: float = Form(2.0),
    quantity_per_part: int = Form(1),
    auto_repair: bool = Form(False),
):
    """
    Nesting analizi — birden fazla parçayı build volume'a yerleştirir.
    SLS/MJF için optimizasyon.
    """
    import trimesh
    meshes = []
    for f in files:
        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in [".stl", ".obj"]:
            raise HTTPException(400, f"Desteklenmeyen format: {ext}")
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            content = f.file.read()
            tmp.write(content)
            tmp_path = tmp.name
        try:
            mesh = trimesh.load(tmp_path)
            if auto_repair and not mesh.is_watertight:
                mesh.fill_holes()
                mesh.fix_normals()
            meshes.append(mesh)
        finally:
            os.unlink(tmp_path)

    result = analyze_nesting(meshes, technology, machine, gap_mm, quantity_per_part)
    return {"status": "ok" if "error" not in result else "error", **result}


@app.post("/nest-price")
async def nest_with_pricing(
    files: List[UploadFile] = File(...),
    technology: str = Form("sls"),
    material: str = Form("pa12"),
    machine: Optional[str] = Form(None),
    gap_mm: float = Form(2.0),
    quantity_per_part: int = Form(1),
    layer_height: float = Form(0.12),
    finish: str = Form("standard"),
    material_price_usd_per_kg: Optional[float] = Form(None),
    auto_repair: bool = Form(False),
):
    """Nesting + fiyatlandırma."""
    import trimesh
    meshes = []
    for f in files:
        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in [".stl", ".obj"]:
            raise HTTPException(400, f"Desteklenmeyen format: {ext}")
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            content = f.file.read()
            tmp.write(content)
            tmp_path = tmp.name
        try:
            mesh = trimesh.load(tmp_path)
            if auto_repair and not mesh.is_watertight:
                mesh.fill_holes()
                mesh.fix_normals()
            meshes.append(mesh)
        finally:
            os.unlink(tmp_path)

    nest_result = analyze_nesting(meshes, technology, machine, gap_mm, quantity_per_part)

    if "error" in nest_result:
        return {"status": "error", "error": nest_result["error"]}

    # Her parça için fiyat hesapla
    part_prices = []
    for mesh in meshes:
        geom = analyze_stl_from_mesh(mesh, technology, material, layer_height, 0.2)
        params = {
            "technology": technology,
            "material": material,
            "quantity": 1,
            "layer_height": layer_height,
            "infill": 0.2,
            "finish": finish,
            "material_price_usd_per_kg": material_price_usd_per_kg,
        }
        price = calculate_price(geom, params)
        part_prices.append(price)

    total_unit = sum(p.get("unit_price", 0) for p in part_prices) * quantity_per_part
    total_all = total_unit * nest_result["parts_placed"] // quantity_per_part if quantity_per_part > 0 else total_unit

    rate = get_pricing_rate(technology)

    return {
        "status": "ok",
        "nesting": nest_result,
        "part_prices": part_prices,
        "total_unit_price": round(total_unit, 2),
        "total_price": round(total_all, 2),
        "total_price_try": round(total_all * rate["pricing_rate"], 2),
        "exchange_rate": rate,
    }


# ── Calibration (Faz-7) ──────────────────────────────────────────────

@app.post("/calibrate")
async def calibrate(
    records: str = Form(...),  # JSON string of calibration records
    tech_material_key: Optional[str] = Form(None),
):
    """
    Kalibrasyon hesapla — CalibrationRecord listesi alır,
    düzeltme katsayıları döndürür.
    """
    import json
    try:
        recs = json.loads(records)
    except json.JSONDecodeError:
        raise HTTPException(400, "records alanı geçerli JSON olmalı")

    result = compute_calibration_factors(recs)
    if tech_material_key:
        result["tech_material_key"] = tech_material_key
    return result


@app.get("/calibration-demo")
async def calibration_demo_endpoint():
    """Demo: synthetic veri ile kalibrasyon gösterimi."""
    return calibration_demo()
