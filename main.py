"""
Shapelid Kernel Faz-1 Mikroservisi
Desteklenen teknolojiler: Laser Cutting, Bending, FDM, SLA, SLS, MJF
Girdi formatları: STL (3D), DXF (2D)
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from analyzers.stl_analyzer import analyze_stl
from analyzers.dxf_analyzer import analyze_dxf
from pricing.engine import calculate_price
from pricing.exchange_rate import get_rate_info, usd_to_try, get_usd_try

app = FastAPI(
    title="Shapelid Geometry Kernel",
    version="1.1.0",
    description="Faz-1: STL ve DXF bazlı otomatik fiyatlandırma motoru — Türkiye piyasası kalibrasyonu"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    rate = get_rate_info()
    return {
        "status": "ok",
        "version": "1.1.0",
        "phase": "faz-1",
        "exchange_rate": rate,
    }


@app.get("/exchange-rate")
def exchange_rate(force_refresh: bool = False):
    """
    TCMB'den güncel USD/TRY ve EUR/TRY kurlarını döndür.
    force_refresh=true ile cache bypass edilebilir.
    """
    if force_refresh:
        get_usd_try(force_refresh=True)
    return get_rate_info()


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    technology: str = "fdm",          # fdm | sla | sls | mjf | laser | bending
    material: str = "pla",            # pla | abs | petg | resin | pa12 | stainless_steel | mild_steel | aluminum
    quantity: int = 1,
    layer_height: float = 0.2,        # mm — sadece 3D baskı için
    infill: float = 0.2,              # 0.0-1.0 — sadece FDM için
    material_thickness: float = 2.0,  # mm — sadece laser/bending için
):
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in [".stl", ".dxf"]:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen format: {ext}. Faz-1 yalnızca STL ve DXF kabul eder."
        )

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Geometrik analiz
        if ext == ".stl":
            geometry = analyze_stl(tmp_path)
        elif ext == ".dxf":
            geometry = analyze_dxf(tmp_path)

        # Fiyat hesaplama (USD)
        params = {
            "technology": technology,
            "material": material,
            "quantity": quantity,
            "layer_height": layer_height,
            "infill": infill,
            "material_thickness": material_thickness,
        }
        pricing = calculate_price(geometry, params)

        # TRY dönüşümü — TCMB kuru ile
        rate_info = get_rate_info()
        usd_try = rate_info["usd_try"]

        pricing_try = {
            "unit_price_try": round(pricing["unit_price"] * usd_try, 2),
            "total_price_try": round(pricing["total_price"] * usd_try, 2),
            "exchange_rate": {
                "usd_try": usd_try,
                "source": rate_info["source"],
                "fetched_at": rate_info["fetched_at"],
            }
        }

        return {
            "file": file.filename,
            "format": ext,
            "technology": technology,
            "material": material,
            "geometry": geometry,
            "pricing": pricing,
            "pricing_try": pricing_try,
            "quantity": quantity,
        }

    finally:
        os.unlink(tmp_path)


@app.get("/technologies")
def list_technologies():
    """Desteklenen teknoloji ve materyal kombinasyonları"""
    return {
        "3d_printing": {
            "fdm": {
                "description": "Fused Deposition Modeling",
                "materials": ["pla", "abs", "petg", "tpu", "asa"],
                "input_formats": ["stl"]
            },
            "sla": {
                "description": "Stereolithography",
                "materials": ["standard_resin", "tough_resin", "flexible_resin", "castable_resin"],
                "input_formats": ["stl"]
            },
            "sls": {
                "description": "Selective Laser Sintering",
                "materials": ["pa12", "pa11", "tpu"],
                "input_formats": ["stl"]
            },
            "mjf": {
                "description": "HP Multi Jet Fusion",
                "materials": ["pa12", "pa12gb"],
                "input_formats": ["stl"]
            },
        },
        "sheet_metal": {
            "laser": {
                "description": "Laser Cutting",
                "materials": ["mild_steel", "stainless_steel", "aluminum", "copper", "brass", "galvanized_steel"],
                "input_formats": ["dxf"]
            },
            "bending": {
                "description": "Sheet Metal Bending",
                "materials": ["mild_steel", "stainless_steel", "aluminum"],
                "input_formats": ["dxf"]
            },
        }
    }
