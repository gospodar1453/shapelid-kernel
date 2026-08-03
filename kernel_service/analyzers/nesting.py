"""
Nesting Optimizasyonu (Faz-6)
SLS/MJF için parça yerleştirme ve hacim verimliliği hesaplama.
"""
import math
import numpy as np
from typing import List, Dict, Any


BUILD_VOLUMES = {
    "sls": {
        "EOS P 396": {"x": 340, "y": 340, "z": 620},
        "EOS P 770": {"x": 700, "y": 580, "z": 750},
    },
    "mjf": {
        "HP Jet Fusion 420": {"x": 380, "y": 280, "z": 380},
        "HP Jet Fusion 580": {"x": 380, "y": 280, "z": 380},
    },
    "fdm": {
        "Bambu X1C": {"x": 256, "y": 256, "z": 256},
        "Prusa MK4": {"x": 250, "y": 210, "z": 220},
    },
    "sla": {
        "Formlabs Form 3": {"x": 145, "y": 145, "z": 185},
        "Formlabs Form 3L": {"x": 300, "y": 335, "z": 200},
    },
    "dmls": {
        "EOS M 290": {"x": 250, "y": 250, "z": 325},
        "SLM 280": {"x": 280, "y": 280, "z": 365},
    },
}


def get_build_volumes(technology: str = None) -> Dict[str, Any]:
    if technology and technology in BUILD_VOLUMES:
        return {technology: BUILD_VOLUMES[technology]}
    return BUILD_VOLUMES


def _grid_pack(parts, build_x, build_y, gap=2.0):
    placements = []
    current_x = gap
    current_y = gap
    row_height = 0
    parts_placed = 0

    for i, part in enumerate(parts):
        pw = part["dim_x"] + gap * 2
        ph = part["dim_y"] + gap * 2

        if current_x + pw > build_x:
            current_x = gap
            current_y += row_height + gap
            row_height = 0

        if current_y + ph > build_y:
            break

        placements.append({
            "part_index": i,
            "x": current_x + gap,
            "y": current_y + gap,
            "rotation": 0,
        })
        current_x += pw
        row_height = max(row_height, ph)
        parts_placed += 1

    util = 0
    if parts_placed > 0:
        util = round(sum(p["dim_x"] * p["dim_y"] for p in parts[:parts_placed]) / (build_x * build_y) * 100, 2)

    return {"placements": placements, "parts_placed": parts_placed, "parts_total": len(parts), "build_utilization_pct": util}


def analyze_nesting(meshes, technology="sls", machine=None, gap_mm=2.0, quantity_per_part=1):
    tech_key = technology.lower().replace(" ", "_")
    if tech_key not in BUILD_VOLUMES:
        return {"error": f"Desteklenmeyen teknoloji: {technology}"}

    machines = BUILD_VOLUMES[tech_key]
    machine_name = machine if machine and machine in machines else list(machines.keys())[0]
    bv = machines[machine_name]

    parts = []
    for i, mesh in enumerate(meshes):
        bounds = mesh.bounds
        dim_x = float(bounds[1][0] - bounds[0][0])
        dim_y = float(bounds[1][1] - bounds[0][1])
        dim_z = float(bounds[1][2] - bounds[0][2])
        vol_cm3 = float(mesh.volume / 1000)
        for q in range(quantity_per_part):
            parts.append({"original_index": i, "copy_index": q, "dim_x": dim_x, "dim_y": dim_y, "dim_z": dim_z, "volume_cm3": vol_cm3})

    max_z = max(p["dim_z"] for p in parts) if parts else 0
    if max_z > bv["z"]:
        return {"error": f"Parça Z ({max_z:.1f}mm) > build Z ({bv['z']}mm)", "machine": machine_name}

    result = _grid_pack(parts, bv["x"], bv["y"], gap_mm)

    total_part_volume = sum(p["volume_cm3"] for p in parts[:result["parts_placed"]])
    build_volume_cm3 = bv["x"] * bv["y"] * bv["z"] / 1000
    volume_util = round(total_part_volume / build_volume_cm3 * 100, 2) if build_volume_cm3 > 0 else 0
    material_saved = round((1 - result["parts_placed"] / max(result["parts_total"], 1)) * 100, 2) if result["parts_total"] > 0 else 0

    return {
        "technology": tech_key, "machine": machine_name,
        "build_volume_mm": {"x": bv["x"], "y": bv["y"], "z": bv["z"]},
        "gap_mm": gap_mm,
        "parts_placed": result["parts_placed"], "parts_total": result["parts_total"],
        "placements": result["placements"],
        "build_utilization_pct": result["build_utilization_pct"],
        "volume_utilization_pct": volume_util,
        "total_part_volume_cm3": round(total_part_volume, 4),
        "build_volume_cm3": round(build_volume_cm3, 2),
        "material_saved_pct": material_saved,
        "max_z_mm": round(max_z, 2),
    }
