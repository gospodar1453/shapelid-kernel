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

app = FastAPI(
    title="Shapelid Geometry Kernel",
    version="1.0.0",
    description="Faz-1: STL ve DXF bazlı otomatik fiyatlandırma motoru"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0", "phase": "faz-1"}


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    technology: str = "fdm",         # fdm | sla | sls | mjf | laser | bending
    material: str = "pla",           # pla | abs | petg | resin | pa12 | stainless_steel | mild_steel | aluminum
    quantity: int = 1,
    layer_height: float = 0.2,       # mm — sadece 3D baskı için
    infill: float = 0.2,             # 0.0-1.0 — sadece FDM için
    material_thickness: float = 2.0, # mm — sadece laser/bending için
):
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in [".stl", ".dxf"]:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen format: {ext}. Faz-1 yalnızca STL ve DXF kabul eder."
        )

    # Dosyayı geçici olarak kaydet
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

        # Fiyat hesaplama
        params = {
            "technology": technology,
            "material": material,
            "quantity": quantity,
            "layer_height": layer_height,
            "infill": infill,
            "material_thickness": material_thickness,
        }
        pricing = calculate_price(geometry, params)

        return {
            "file": file.filename,
            "format": ext,
            "technology": technology,
            "material": material,
            "geometry": geometry,
            "pricing": pricing,
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
                "materials": ["mild_steel", "stainless_steel", "aluminum", "copper", "brass"],
                "input_formats": ["dxf"]
            },
            "bending": {
                "description": "Sheet Metal Bending",
                "materials": ["mild_steel", "stainless_steel", "aluminum"],
                "input_formats": ["dxf"]
            },
        }
    }
