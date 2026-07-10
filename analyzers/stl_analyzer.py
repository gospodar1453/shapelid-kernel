"""
STL Analiz Modülü
trimesh kütüphanesi ile B-Rep benzeri metrikler:
- Hacim (cm³)
- Yüzey alanı (cm²)
- Bounding box boyutları (mm)
- Ağırlık merkezi
- Su geçirmezlik (manifold) kontrolü
- Baskı için tahmini destek yüzey alanı
"""

import trimesh
import numpy as np


def analyze_stl(file_path: str) -> dict:
    mesh = trimesh.load(file_path, force="mesh")

    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError("STL dosyası geçerli bir üçgen ağ içermiyor.")

    if len(mesh.faces) == 0:
        raise ValueError("STL dosyası boş veya geçersiz.")

    # Temel geometri
    volume_mm3 = abs(float(mesh.volume)) if mesh.is_volume else abs(float(mesh.convex_hull.volume))
    volume_cm3 = round(volume_mm3 / 1000, 4)
    surface_area_mm2 = float(mesh.area)
    surface_area_cm2 = round(surface_area_mm2 / 100, 4)

    # Bounding box
    bounds = mesh.bounds
    if bounds is None or bounds.shape != (2, 3):
        # Fallback: vertices'ten hesapla
        verts = mesh.vertices
        bounds = np.array([verts.min(axis=0), verts.max(axis=0)])

    dimensions = {
        "x_mm": round(float(bounds[1][0] - bounds[0][0]), 2),
        "y_mm": round(float(bounds[1][1] - bounds[0][1]), 2),
        "z_mm": round(float(bounds[1][2] - bounds[0][2]), 2),
    }

    # Bounding box hacmi → doluluk oranı (packing density)
    bbox_volume = dimensions["x_mm"] * dimensions["y_mm"] * dimensions["z_mm"]
    packing_density = round(volume_mm3 / bbox_volume, 4) if bbox_volume > 0 else 0

    # Ağırlık merkezi
    centroid = mesh.centroid
    centroid_mm = {
        "x": round(float(centroid[0]), 2),
        "y": round(float(centroid[1]), 2),
        "z": round(float(centroid[2]), 2),
    }

    # Su geçirmezlik kontrolü (manifold) — açık mesh = yazdırma sorunu riski
    is_watertight = bool(mesh.is_watertight)

    # Destek tahmini: Z ekseninde 45°'den fazla sarkan yüzeyler
    support_area_mm2 = _estimate_support_area(mesh)
    support_area_cm2 = round(support_area_mm2 / 100, 4)
    support_ratio = round(support_area_mm2 / surface_area_mm2, 4) if surface_area_mm2 > 0 else 0

    # Kompleksite skoru (0-100): fiyatı etkileyen bir faktör
    complexity_score = _calculate_complexity(mesh, packing_density, support_ratio)

    return {
        "type": "3d",
        "volume_cm3": volume_cm3,
        "surface_area_cm2": surface_area_cm2,
        "dimensions_mm": dimensions,
        "bounding_box_volume_cm3": round(bbox_volume / 1000, 4),
        "packing_density": packing_density,
        "centroid_mm": centroid_mm,
        "triangle_count": len(mesh.faces),
        "is_watertight": is_watertight,
        "support_area_cm2": support_area_cm2,
        "support_ratio": support_ratio,
        "complexity_score": complexity_score,
        "warnings": _generate_warnings(mesh, dimensions, is_watertight),
    }


def _estimate_support_area(mesh: trimesh.Trimesh, threshold_angle: float = 45.0) -> float:
    normals = mesh.face_normals
    z_component = normals[:, 2]
    threshold_cos = np.cos(np.radians(180 - threshold_angle))
    overhang_mask = z_component < threshold_cos
    face_areas = mesh.area_faces
    support_area = float(np.sum(face_areas[overhang_mask]))
    return support_area


def _calculate_complexity(mesh: trimesh.Trimesh, packing_density: float, support_ratio: float) -> int:
    score = 0
    score += int((1 - min(packing_density, 1.0)) * 40)
    score += int(min(support_ratio, 1.0) * 30)
    triangle_score = min(len(mesh.faces) / 100000 * 30, 30)
    score += int(triangle_score)
    return min(score, 100)


def _generate_warnings(mesh, dimensions, is_watertight) -> list:
    warnings = []

    if not is_watertight:
        warnings.append({
            "code": "NON_MANIFOLD",
            "severity": "high",
            "message": "Mesh kapalı değil (manifold değil). Yazdırma öncesi onarım gerekebilir."
        })

    min_dim = min(dimensions["x_mm"], dimensions["y_mm"], dimensions["z_mm"])
    if min_dim < 0.5:
        warnings.append({
            "code": "THIN_WALL",
            "severity": "medium",
            "message": f"Minimum boyut {min_dim}mm. Bazı teknolojilerde üretilemeyebilir."
        })

    max_dim = max(dimensions["x_mm"], dimensions["y_mm"], dimensions["z_mm"])
    if max_dim > 300:
        warnings.append({
            "code": "OVERSIZED",
            "severity": "medium",
            "message": f"Parça boyutu {max_dim}mm. Bazı makinelerin build volume'unu aşıyor olabilir."
        })

    return warnings
