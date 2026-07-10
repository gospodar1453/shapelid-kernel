"""
Shapelid Kernel Faz-1 Mikroservisi
Desteklenen teknolojiler: Laser Cutting, Bending, FDM, SLA, SLS, MJF
Girdi formatları: STL (3D), DXF (2D)

Kur riski önlemleri:
  A) %4 kur tamponu (pricing_rate = TCMB * 1.04)
  B) Teklif geçerlilik süresi (valid_until)
  D) İç hesap USD, müşteriye TRY gösterim
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from analyzers.stl_analyzer import analyze_stl
from analyzers.dxf_analyzer import analyze_dxf
from pricing.engine import calculate_price
from pricing.exchange_rate import get_rate_info, get_pricing_rate, usd_to_try, get_usd_try

app = FastAPI(
    title="Shapelid Geometry Kernel",
    version="1.2.0",
    description="Faz-1: STL/DXF bazlı fiyatlandırma — TCMB kuru, %4 tampon, geçerlilik süresi"
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
        "status": "ok",
        "version": "1.2.0",
        "phase": "faz-1",
        "exchange_rate": get_rate_info(),
    }


@app.get("/exchange-rate")
def exchange_rate(force_refresh: bool = False):
    """
    TCMB'den güncel kur bilgisi.
    - usd_try: ham TCMB kuru
    - usd_try_buffered: fiyatlamada kullanılan kur (%4 tamponlu)
    - validity_hours_by_technology: teknoloji bazlı teklif geçerlilik süreleri
    force_refresh=true ile 4h cache bypass edilebilir.
    """
    if force_refresh:
        get_usd_try(force_refresh=True)
    return get_rate_info()


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    technology: str = "fdm",          # fdm | sla | sls | mjf | laser | bending
    material: str = "pla",
    quantity: int = 1,
    layer_height: float = 0.2,
    infill: float = 0.2,
    material_thickness: float = 2.0,
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
        else:
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

        # Kur bilgisi — tamponu uygulanmış (A önlemi)
        rate = get_pricing_rate(technology)
        pricing_rate = rate["pricing_rate"]   # TCMB * 1.04

        # TRY dönüşümü (D önlemi: müşteriye sadece TRY)
        unit_price_try  = round(pricing["unit_price"]  * pricing_rate, 2)
        total_price_try = round(pricing["total_price"] * pricing_rate, 2)

        # B önlemi: geçerlilik süresi
        pricing_try = {
            "unit_price_try":  unit_price_try,
            "total_price_try": total_price_try,
            "valid_until":     rate["valid_until"],   # ISO UTC
            "valid_hours":     rate["valid_hours"],
            "exchange_rate": {
                "tcmb_rate":    rate["tcmb_rate"],
                "pricing_rate": pricing_rate,
                "buffer_pct":   rate["buffer_pct"],
                "source":       rate["source"],
                "fetched_at":   rate["fetched_at"],
            },
        }

        return {
            "file":       file.filename,
            "format":     ext,
            "technology": technology,
            "material":   material,
            "quantity":   quantity,
            "geometry":   geometry,
            "pricing":    pricing,          # USD (iç hesap)
            "pricing_try": pricing_try,     # TRY (müşteriye gösterim)
        }

    finally:
        os.unlink(tmp_path)


@app.get("/technologies")
def list_technologies():
    """Desteklenen teknoloji ve materyal kombinasyonları"""
    return {
        "3d_printing": {
            "fdm":  {"description": "Fused Deposition Modeling",
                     "materials": ["pla", "abs", "petg", "tpu", "asa"],
                     "input_formats": ["stl"]},
            "sla":  {"description": "Stereolithography",
                     "materials": ["standard_resin", "tough_resin", "flexible_resin", "castable_resin"],
                     "input_formats": ["stl"]},
            "sls":  {"description": "Selective Laser Sintering",
                     "materials": ["pa12", "pa11", "tpu"],
                     "input_formats": ["stl"]},
            "mjf":  {"description": "HP Multi Jet Fusion",
                     "materials": ["pa12", "pa12gb"],
                     "input_formats": ["stl"]},
        },
        "sheet_metal": {
            "laser":   {"description": "Laser Cutting",
                        "materials": ["mild_steel", "stainless_steel", "aluminum", "copper", "brass", "galvanized_steel"],
                        "input_formats": ["dxf"]},
            "bending": {"description": "Sheet Metal Bending",
                        "materials": ["mild_steel", "stainless_steel", "aluminum"],
                        "input_formats": ["dxf"]},
        }
    }
