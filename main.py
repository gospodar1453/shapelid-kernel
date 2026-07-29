"""
Shapelid Kernel v3.0.0 — Faz-5
Desteklenen teknolojiler:
  3D Baskı : FDM, SLA, SLS, MJF, DMLS
  Sac Metal: Laser Cutting, Bending
  CNC/EDM  : CNC Milling, CNC Turning, EDM  ← YENİ (Faz-5)

Faz-5 eklentileri:
  - CNC Feature Recognition (analyzers/cnc_analyzer.py)
  - MRR tabanlı CNC/EDM fiyatlandırma (pricing/cnc_engine.py)
  - STL → CNC akışı: hole, pocket, flat_face, undercut tespiti
  - cnc_milling / cnc_turning / edm teknolojileri
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import tempfile
import os

from analyzers.stl_analyzer import analyze_stl
from analyzers.dxf_analyzer import analyze_dxf
from analyzers.cnc_analyzer  import analyze_cnc
from pricing.engine import calculate_price
from pricing.cnc_engine import calculate_cnc_price
from pricing.exchange_rate import get_rate_info, get_pricing_rate, get_usd_try
from pricing.finish_rates import (
    FINISH_RATES, COLOR_RATES, RESOLUTION_RATES,
    INFILL_PRESETS, HARDNESS_RATES, TOLERANCE_RATES, CERT_RATES
)

# CNC/EDM teknoloji listesi
CNC_TECHNOLOGIES = {"cnc_milling", "cnc_turning", "edm"}
# Sac metal teknoloji listesi
SHEET_TECHNOLOGIES = {"laser", "bending"}

app = FastAPI(
    title="Shapelid Geometry Kernel",
    version="3.0.0",
    description="Faz-5: CNC/EDM Feature Recognition + MRR tabanlı fiyatlandırma"
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
        "version"       : "3.0.0",
        "phase"         : "faz-5",
        "technologies"  : {
            "3d_printing" : ["fdm", "sla", "sls", "mjf", "dmls"],
            "sheet_metal" : ["laser", "bending"],
            "cnc_edm"     : ["cnc_milling", "cnc_turning", "edm"],
        },
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
):
    ext = os.path.splitext(file.filename)[1].lower()

    # Format kontrolü
    if ext not in [".stl", ".dxf"]:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen format: {ext}. STL veya DXF gerekli."
        )

    # CNC/EDM sadece STL alır
    if technology in CNC_TECHNOLOGIES and ext != ".stl":
        raise HTTPException(
            status_code=400,
            detail=f"{technology} teknolojisi yalnızca STL formatı kabul eder."
        )

    # Sac metal sadece DXF alır
    if technology in SHEET_TECHNOLOGIES and ext != ".dxf":
        raise HTTPException(
            status_code=400,
            detail=f"{technology} teknolojisi yalnızca DXF formatı kabul eder."
        )

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

        # ── Geometrik analiz ─────────────────────────────────────────────
        if technology in CNC_TECHNOLOGIES:
            # Faz-5: STL → CNC feature recognition + CNC fiyatlandırma
            geometry = analyze_stl(tmp_path)        # Temel STL metrikleri
            cnc_features = analyze_cnc(tmp_path, technology)  # CNC feature analizi
            # Feature sonuçlarını geometry'ye entegre et
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

        else:  # .dxf
            geometry = analyze_dxf(tmp_path)
            pricing  = calculate_price(geometry, params)

        # ── Kur dönüşümü ─────────────────────────────────────────────────
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
        },
        "cnc_edm": {
            "cnc_milling": {"description": "CNC Freze (3 eksen VMC)",
                            "materials"  : ["aluminum","mild_steel","stainless_steel","ss304","ss316l","titanium","ti6al4v","copper"],
                            "input_formats": ["stl"],
                            "note"       : "STL üzerinden yaklaşımsal feature tespiti. Daha yüksek doğruluk için STEP önerilir."},
            "cnc_turning": {"description": "CNC Torna (2-3 eksen)",
                            "materials"  : ["aluminum","mild_steel","stainless_steel","ss304","ss316l","titanium","ti6al4v","copper"],
                            "input_formats": ["stl"],
                            "note"       : "Rotasyonel simetri analizi dahil."},
            "edm"        : {"description": "EDM Tel Erozyon",
                            "materials"  : ["tool_steel","h13_steel","d2_steel","stainless_steel","ss304","ss316l","aluminum","titanium","copper"],
                            "input_formats": ["stl"],
                            "note"       : "Yüksek hassasiyet gerektiren kalıp boşlukları için."},
        },
    }


@app.get("/options")
def list_options(technology: str = "fdm"):
    """
    Belirli bir teknoloji için geçerli seçim seçeneklerini döndürür.
    CNC/EDM teknolojileri için ayrı parametre seti döner.
    """
    # CNC/EDM için basitleştirilmiş seçenek seti
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
    """CNC/EDM için seçenek listesi."""
    # Yüzey işlemleri — CNC'ye özgü
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

    # Tolerans seviyeleri — CNC için
    cnc_tolerances = [
        {"key": "standard",  "label": "Standard (±0.1mm)",      "multiplier": 1.0},
        {"key": "medium",    "label": "Medium (±0.05mm)",        "multiplier": 1.20},
        {"key": "fine",      "label": "Fine (±0.025mm)",         "multiplier": 1.50},
        {"key": "ultra",     "label": "Ultra (±0.01mm)",         "multiplier": 2.00},
        {"key": "jig_grade", "label": "Jig Grade (±0.005mm)",    "multiplier": 3.00},
    ]

    # Sertifikasyon
    cnc_certs = [
        {"key": "none",           "label": "Sertifika Yok",            "flat_cost": 0},
        {"key": "material_cert",  "label": "Malzeme Sertifikası (MTC)","flat_cost": 15},
        {"key": "first_article",  "label": "First Article Inspection", "flat_cost": 40},
        {"key": "iso9001",        "label": "ISO 9001 Uyumlu Üretim",   "flat_cost": 60},
        {"key": "as9100",         "label": "AS9100 (Havacılık)",        "flat_cost": 120},
    ]

    # Thread/iç diş seçeneği (CNC'ye özgü)
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
        "note": "STL üzerinden CNC feature tespiti yaklaşımsal. Kesin fiyat için STEP/IGES dosyası önerilir."
    }
