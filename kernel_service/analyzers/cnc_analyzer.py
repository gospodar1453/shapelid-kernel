"""
CNC Feature Recognition Modülü — Faz-5
Mesh-based geometrik özellik tespiti (STL/OBJ mesh üzerinden)

Desteklenen teknolojiler:
  - cnc_milling: Freze (pocket, slot, hole, boss, fillet, chamfer)
  - cnc_turning: Torna (cylinder, taper, groove, chamfer, face)
  - edm: Delik/slot erozyon (thin slot, sharp corner, deep pocket)

Tespit edilen özellikler:
  1. Holes (delikler) — cylindrical face clustering + axis analysis
  2. Pockets (cepler) — concave depression detection via curvature
  3. Slots (kanallar) — elongated narrow depressions
  4. Fillets (radüsler) — smooth convex transitions
  5. Chamfers (pahlar) — angled edge transitions
  6. Planar faces (düz yüzeyler) — for facing operations
  7. Cylindrical faces — for turning/boring operations

Not: Bu modül B-rep (STEP/IGES) yerine mesh-based analiz yapar.
Client Portal'daki OCCT Web Worker STEP/IGES → mesh dönüşümünü yapar,
bu modül elde edilen mesh'ten CNC özelliklerini çıkarır.
"""

import trimesh
import numpy as np
from scipy.spatial import cKDTree
from collections import defaultdict
import math


def analyze_cnc(file_path: str, technology: str = "cnc_milling", auto_repair: bool = False) -> dict:
    """
    CNC feature recognition ana fonksiyonu.
    STL/OBJ mesh yükler, geometrik özellikleri tespit eder,
    CNC işleme süresi için gerekli metrikleri hesaplar.
    """
    mesh = trimesh.load(file_path, force="mesh")

    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError("Dosya geçerli bir üçgen ağ içermiyor.")
    if len(mesh.faces) == 0:
        raise ValueError("Mesh boş veya geçersiz.")

    # Auto-repair
    was_watertight = bool(mesh.is_watertight)
    if not was_watertight and auto_repair:
        mesh.merge_vertices()
        mesh.fill_holes()
        mesh.fix_normals()
        trimesh.repair.fix_winding(mesh)
        trimesh.repair.fix_inversion(mesh)
    is_watertight = bool(mesh.is_watertight)

    # Temel geometri
    volume_mm3 = abs(float(mesh.volume)) if mesh.is_volume else abs(float(mesh.convex_hull.volume))
    volume_cm3 = round(volume_mm3 / 1000, 4)
    surface_area_mm2 = float(mesh.area)
    surface_area_cm2 = round(surface_area_mm2 / 100, 4)

    bounds = mesh.bounds
    dimensions = {
        "x_mm": round(float(bounds[1][0] - bounds[0][0]), 2),
        "y_mm": round(float(bounds[1][1] - bounds[0][1]), 2),
        "z_mm": round(float(bounds[1][2] - bounds[0][2]), 2),
    }
    bbox_volume_mm3 = dimensions["x_mm"] * dimensions["y_mm"] * dimensions["z_mm"]
    packing_density = round(volume_mm3 / bbox_volume_mm3, 4) if bbox_volume_mm3 > 0 else 0

    # ── Feature Detection ──
    face_normals = mesh.face_normals
    face_areas = mesh.area_faces
    face_centers = mesh.triangles_center

    # 1. Face classification by normal direction
    planar_faces = _detect_planar_faces(mesh, face_normals, face_areas)
    cylindrical_faces = _detect_cylindrical_faces(mesh, face_normals, face_areas, face_centers)

    # 2. Hole detection from cylindrical faces
    max_part_dim = max(dimensions["x_mm"], dimensions["y_mm"], dimensions["z_mm"])
    holes = _detect_holes(cylindrical_faces, face_centers, face_areas, max_part_dim)

    # 3. Curvature analysis for pockets and slots
    curvature_data = _compute_curvature(mesh)
    pockets = _detect_pockets(mesh, curvature_data, face_centers, face_areas)
    slots = _detect_slots(mesh, curvature_data, face_centers, face_areas, dimensions)

    # 4. Edge analysis — fillets, chamfers, sharp edges
    edges = _analyze_edges(mesh, face_normals)

    # 5. Technology-specific analysis
    if technology == "cnc_turning":
        turning_features = _analyze_turning(mesh, face_normals, face_areas, dimensions)
    else:
        turning_features = None

    # 6. CNC complexity score
    cnc_complexity = _cnc_complexity_score(
        holes, pockets, slots, edges, planar_faces, dimensions, technology
    )

    # 7. Machine time estimation
    machine_time = _estimate_cnc_time(
        holes, pockets, slots, edges, planar_faces, cylindrical_faces,
        dimensions, volume_mm3, technology, mesh
    )

    # 8. Warnings
    warnings = _generate_cnc_warnings(
        holes, pockets, slots, dimensions, is_watertight, technology
    )

    features = {
        "type": "cnc",
        "technology": technology,
        "volume_cm3": volume_cm3,
        "surface_area_cm2": surface_area_cm2,
        "dimensions_mm": dimensions,
        "bounding_box_volume_cm3": round(bbox_volume_mm3 / 1000, 4),
        "packing_density": packing_density,
        "is_watertight": is_watertight,
        "triangle_count": len(mesh.faces),
        # CNC features
        "holes": holes,
        "pockets": pockets,
        "slots": slots,
        "edges": edges,
        "planar_faces": planar_faces,
        "cylindrical_faces": cylindrical_faces,
        "turning_features": turning_features,
        # Metrics
        "cnc_complexity_score": cnc_complexity,
        "estimated_machine_time_min": machine_time["total_time_min"],
        "machine_time_breakdown": machine_time["breakdown"],
        "warnings": warnings,
    }

    return features


# ─────────────────────────────────────────────
# PLANAR FACE DETECTION
# ─────────────────────────────────────────────

def _detect_planar_faces(mesh, face_normals, face_areas) -> list:
    """
    Düz yüzeyleri tespit eder. Mesh facets (coplanar face groups) kullanır.
    Geniş düz yüzeyler facing operasyonu için önemlidir.
    """
    planar = []

    # trimesh facets: coplanar adjacent face groups
    try:
        facets = mesh.facets
        for facet_idx, facet in enumerate(facets if hasattr(facets, '__iter__') else []):
            if len(facet) < 1:
                continue
            face_indices = facet if isinstance(facet, (list, np.ndarray)) else [facet]
            area = sum(face_areas[i] for i in face_indices if i < len(face_areas))
            if area < 50:  # < 50mm² skip small faces
                continue
            normal = face_normals[face_indices[0]]
            planar.append({
                "area_mm2": round(float(area), 2),
                "normal": [round(float(normal[0]), 3), round(float(normal[1]), 3), round(float(normal[2]), 3)],
                "face_count": len(face_indices),
            })
    except Exception:
        pass

    # Fallback: cluster faces by normal direction
    if not planar:
        planar = _cluster_faces_by_normal(face_normals, face_areas, min_area_mm2=100)

    # Sort by area descending
    planar.sort(key=lambda x: x["area_mm2"], reverse=True)
    return planar[:20]  # Top 20 largest faces


def _cluster_faces_by_normal(face_normals, face_areas, min_area_mm2=100, angle_threshold=5) -> list:
    """Cluster faces by similar normal direction. Returns groups with total area."""
    clusters = []
    used = set()

    for i in range(len(face_normals)):
        if i in used or face_areas[i] < 5:
            continue
        normal_i = face_normals[i]
        group = [i]
        used.add(i)

        for j in range(i + 1, len(face_normals)):
            if j in used or face_areas[j] < 5:
                continue
            dot = float(np.dot(normal_i, face_normals[j]))
            if dot > math.cos(math.radians(angle_threshold)):
                group.append(j)
                used.add(j)

        total_area = sum(face_areas[k] for k in group)
        if total_area >= min_area_mm2:
            clusters.append({
                "area_mm2": round(float(total_area), 2),
                "normal": [round(float(normal_i[0]), 3), round(float(normal_i[1]), 3), round(float(normal_i[2]), 3)],
                "face_count": len(group),
            })

    clusters.sort(key=lambda x: x["area_mm2"], reverse=True)
    return clusters[:20]


# ─────────────────────────────────────────────
# CYLINDRICAL FACE DETECTION
# ─────────────────────────────────────────────

def _detect_cylindrical_faces(mesh, face_normals, face_areas, face_centers) -> list:
    """
    Silindirik yüzeyleri tespit eder. Normal vektörlerinin düzlem
    üzerinde çembersel pattern oluşturduğu yüzey gruplarını arar.

    Yaklaşım: Komşu face'lerin normal'lerinin bir eksene dik olduğunu
    ve normals'ın çembersel bir pattern oluşturduğunu kontrol eder.
    """
    cylindrical = []

    # Group faces by approximate axis direction
    # A cylindrical surface has normals perpendicular to its axis
    # So we cluster by the component of normals along potential axes

    # Check 3 main axes + their combinations
    candidate_axes = [
        np.array([1, 0, 0], dtype=float),
        np.array([0, 1, 0], dtype=float),
        np.array([0, 0, 1], dtype=float),
    ]

    # Also check dominant axes from the mesh
    try:
        pca = mesh.principal_inertia_axes  # (3, 3) array
        for i in range(min(3, len(pca))):
            candidate_axes.append(np.abs(pca[i]))
    except Exception:
        pass

    for axis in candidate_axes:
        axis = axis / (np.linalg.norm(axis) + 1e-10)

        # Faces whose normals are nearly perpendicular to this axis → potential cylindrical
        perpendicularity = np.abs(np.dot(face_normals, axis))
        cyl_mask = perpendicularity < 0.15  # Normal nearly perpendicular to axis
        cyl_indices = np.where(cyl_mask)[0]

        if len(cyl_indices) < 10:
            continue

        # Cluster these faces by position along the axis
        axis_projections = np.dot(face_centers[cyl_indices], axis)
        radial_vectors = face_centers[cyl_indices] - np.outer(axis_projections, axis)
        radial_distances = np.linalg.norm(radial_vectors, axis=1)

        # Group by similar radial distance → same cylinder radius
        if len(radial_distances) == 0:
            continue

        # Cluster radial distances
        sorted_indices = np.argsort(radial_distances)
        clusters = []
        current_cluster = [sorted_indices[0]]

        for k in range(1, len(sorted_indices)):
            idx = sorted_indices[k]
            prev_idx = current_cluster[-1]
            if radial_distances[idx] - radial_distances[prev_idx] < 0.5:  # 0.5mm grouping
                current_cluster.append(idx)
            else:
                clusters.append(current_cluster)
                current_cluster = [idx]
        clusters.append(current_cluster)

        for cluster in clusters:
            if len(cluster) < 5:
                continue
            cluster_areas = face_areas[cyl_indices[cluster]]
            total_area = float(np.sum(cluster_areas))
            if total_area < 30:  # < 30mm² too small
                continue

            avg_radius = float(np.mean(radial_distances[cluster]))
            if avg_radius < 0.5:  # Too small radius
                continue

            axis_length = float(np.max(axis_projections[cluster]) - np.min(axis_projections[cluster]))

            cylindrical.append({
                "radius_mm": round(avg_radius, 3),
                "diameter_mm": round(avg_radius * 2, 3),
                "length_mm": round(axis_length, 2),
                "area_mm2": round(total_area, 2),
                "face_count": len(cluster),
                "axis": [round(float(axis[0]), 3), round(float(axis[1]), 3), round(float(axis[2]), 3)],
            })

    # Deduplicate by similar radius+length
    unique = []
    for cyl in cylindrical:
        is_dup = False
        for u in unique:
            if (abs(cyl["radius_mm"] - u["radius_mm"]) < 0.3 and
                abs(cyl["length_mm"] - u["length_mm"]) < 1.0):
                is_dup = True
                break
        if not is_dup:
            unique.append(cyl)

    unique.sort(key=lambda x: x["area_mm2"], reverse=True)
    return unique[:30]


# ─────────────────────────────────────────────
# HOLE DETECTION
# ─────────────────────────────────────────────

def _detect_holes(cylindrical_faces, face_centers, face_areas, max_part_dim: float = 100) -> list:
    """
    Silindirik yüzeylerden delikleri tespit eder.
    Küçük yarıçaplı silindirik yüzeyler delik olarak sınıflandırılır.
    Parça boyutundan daha büyük silindirler dış yüzeydir, delik değildir.
    """
    holes = []

    for cyl in cylindrical_faces:
        radius = cyl["radius_mm"]
        length = cyl["length_mm"]

        # Hole criteria: diameter must be smaller than the part's max dimension
        # If diameter > 80% of the part's max dimension, it's likely an outer surface
        if cyl["diameter_mm"] > max_part_dim * 0.8:
            continue

        # Also skip if radius > 30mm (unusual hole size)
        if radius > 30:
            continue

        # Classify hole type by depth/radius ratio
        depth_ratio = length / (2 * radius) if radius > 0 else 0

        if depth_ratio > 5:
            hole_type = "deep_hole"
        elif depth_ratio > 2:
            hole_type = "blind_hole"
        elif length > 0.5:
            hole_type = "through_hole"
        else:
            hole_type = "shallow_hole"

        # Estimate machining complexity
        # Small diameter + deep = high complexity
        complexity = 0
        if radius < 1:
            complexity += 3  # < 2mm diameter — micro drilling
        elif radius < 2.5:
            complexity += 2  # < 5mm — small hole
        elif radius < 10:
            complexity += 1  # standard drilling
        else:
            complexity += 2  # large diameter — boring

        if depth_ratio > 5:
            complexity += 3  # deep hole drilling is hard
        elif depth_ratio > 3:
            complexity += 2

        # Determine if through or blind
        is_through = depth_ratio > 0.5 and hole_type in ("through_hole", "deep_hole")

        holes.append({
            "id": f"hole_{len(holes)+1}",
            "diameter_mm": cyl["diameter_mm"],
            "radius_mm": round(radius, 3),
            "depth_mm": round(length, 2),
            "type": hole_type,
            "is_through": is_through,
            "complexity": complexity,
            "area_mm2": cyl["area_mm2"],
            "est_drill_time_min": _estimate_drill_time(radius, length, is_through),
        })

    return holes


def _estimate_drill_time(radius_mm: float, depth_mm: float, is_through: bool) -> float:
    """
    Delik delme süresi tahmini (dakika).
    Peck drilling for deep holes, simple drilling for shallow.
    """
    # Feed rate: ~100mm/min for small holes, ~200mm/min for larger
    feed_rate = 80 + min(radius_mm * 15, 120)  # mm/min
    plunge_time = depth_mm / feed_rate

    # Peck drilling: retract + re-plunge for deep holes
    if depth_mm / (2 * radius_mm) > 3:
        peck_count = int(depth_mm / (3 * radius_mm))
        peck_overhead = peck_count * 0.15  # 9s per peck cycle
    else:
        peck_overhead = 0

    # Through holes need breakthrough time
    breakthrough = 0.1 if is_through else 0

    # Tool change/positioning
    positioning = 0.2

    return round(plunge_time + peck_overhead + breakthrough + positioning, 3)


# ─────────────────────────────────────────────
# CURVATURE ANALYSIS
# ─────────────────────────────────────────────

def _compute_curvature(mesh) -> dict:
    """
    Mesh yüzey eğriliğini hesaplar.
    Concave (çöküntü) ve convex (çıkıntı) bölgeleri tespit etmek için.
    """
    try:
        # trimesh discrete gaussian curvature
        gaussian = trimesh.curvature.discrete_gaussian_curvature_measure(
            mesh, mesh.vertices, radius=2.0
        )
        mean_curv = trimesh.curvature.discrete_mean_curvature_measure(
            mesh, mesh.vertices, radius=2.0
        )

        # Per-face curvature (average of vertex curvatures)
        face_curvature = np.mean(np.abs(mean_curv[mesh.faces]), axis=1)

        return {
            "gaussian": gaussian,
            "mean": mean_curv,
            "face_curvature": face_curvature,
            "mean_threshold": float(np.percentile(np.abs(mean_curv), 75)),
            "face_threshold": float(np.percentile(face_curvature, 80)),
        }
    except Exception:
        return {
            "gaussian": None,
            "mean": None,
            "face_curvature": np.zeros(len(mesh.faces)),
            "mean_threshold": 0,
            "face_threshold": 0,
        }


# ─────────────────────────────────────────────
# POCKET DETECTION
# ─────────────────────────────────────────────

def _detect_pockets(mesh, curvature_data, face_centers, face_areas) -> list:
    """
    Cep (pocket) tespiti — yüzeyde çöküntü oluşturan bölgeler.
    Concave curvature + volume analysis ile.
    """
    pockets = []

    face_curv = curvature_data.get("face_curvature", np.array([]))
    if len(face_curv) == 0:
        return pockets

    threshold = curvature_data.get("face_threshold", 0)
    if threshold == 0:
        return pockets

    # High curvature faces → potential pocket boundaries
    high_curv_mask = face_curv > threshold
    high_curv_indices = np.where(high_curv_mask)[0]

    if len(high_curv_indices) < 10:
        return pockets

    # Cluster high-curvature faces by proximity
    if len(high_curv_indices) > 0:
        centers = face_centers[high_curv_indices]
        clusters = _cluster_by_proximity(centers, max_distance=15.0)

        for cluster_indices in clusters:
            if len(cluster_indices) < 5:
                continue
            cluster_faces = high_curv_indices[cluster_indices]
            cluster_area = float(np.sum(face_areas[cluster_faces]))
            cluster_center = np.mean(face_centers[cluster_faces], axis=0)

            # Estimate pocket depth from curvature intensity
            avg_curv = float(np.mean(face_curv[cluster_faces]))
            est_depth = min(avg_curv * 10, 50)  # rough depth estimate

            # Pocket dimensions
            cluster_pts = face_centers[cluster_faces]
            extent = np.max(cluster_pts, axis=0) - np.min(cluster_pts, axis=0)
            width = float(extent[0])
            height = float(extent[1])

            # Classify pocket type
            aspect_ratio = max(width, height) / (min(width, height) + 0.001)
            if aspect_ratio > 4:
                pocket_type = "slot_pocket"
            elif est_depth > 15:
                pocket_type = "deep_pocket"
            elif cluster_area > 500:
                pocket_type = "large_pocket"
            else:
                pocket_type = "standard_pocket"

            # Estimate milling time
            milling_time = _estimate_pocket_mill_time(
                cluster_area, est_depth, pocket_type
            )

            pockets.append({
                "id": f"pocket_{len(pockets)+1}",
                "type": pocket_type,
                "area_mm2": round(cluster_area, 2),
                "estimated_depth_mm": round(est_depth, 2),
                "width_mm": round(width, 2),
                "height_mm": round(height, 2),
                "est_mill_time_min": milling_time,
                "complexity": 2 if est_depth > 10 else 1,
            })

    pockets.sort(key=lambda x: x["area_mm2"], reverse=True)
    return pockets[:15]


def _estimate_pocket_mill_time(area_mm2: float, depth_mm: float, pocket_type: str) -> float:
    """
    Cep frezeleme süresi tahmini (dakika).
    MRR (Material Removal Rate) based estimation.
    """
    # Volume to remove
    volume_mm3 = area_mm2 * depth_mm

    # MRR for CNC milling: ~1000-3000 mm³/min (depends on material, tool, etc.)
    # Conservative: 1500 mm³/min for aluminum, 800 for steel
    mrr = 1200  # mm³/min average
    if pocket_type == "deep_pocket":
        mrr *= 0.6  # Slower for deep pockets
    elif pocket_type == "slot_pocket":
        mrr *= 0.8

    rough_time = volume_mm3 / mrr

    # Finish pass: ~20% of area at slower rate
    finish_time = (area_mm2 * 0.2) / 200  # mm²/min finish rate

    # Tool changes / positioning
    overhead = 0.5

    return round(rough_time + finish_time + overhead, 3)


# ─────────────────────────────────────────────
# SLOT DETECTION
# ─────────────────────────────────────────────

def _detect_slots(mesh, curvature_data, face_centers, face_areas, dimensions) -> list:
    """
    Kanal (slot) tespiti — dar ve uzun çöküntü bölgeleri.
    EDM için özellikle önemli (ince kanallar).
    """
    slots = []

    face_curv = curvature_data.get("face_curvature", np.array([]))
    if len(face_curv) == 0:
        return slots

    threshold = curvature_data.get("face_threshold", 0)
    if threshold == 0:
        return slots

    # High curvature + elongated clusters → slots
    high_curv_mask = face_curv > threshold * 1.2
    high_curv_indices = np.where(high_curv_mask)[0]

    if len(high_curv_indices) < 5:
        return slots

    centers = face_centers[high_curv_indices]
    clusters = _cluster_by_proximity(centers, max_distance=10.0)

    for cluster_indices in clusters:
        if len(cluster_indices) < 3:
            continue
        cluster_faces = high_curv_indices[cluster_indices]
        cluster_area = float(np.sum(face_areas[cluster_faces]))

        cluster_pts = face_centers[cluster_faces]
        extent = np.max(cluster_pts, axis=0) - np.min(cluster_pts, axis=0)
        length = float(max(extent))
        width = float(min(extent[extent > 0])) if np.any(extent > 0) else 0

        if width == 0:
            continue

        aspect_ratio = length / width
        if aspect_ratio < 3:
            continue  # Not elongated enough for a slot

        est_depth = float(np.mean(face_curv[cluster_faces])) * 5

        slot_type = "thin_slot" if width < 2 else "standard_slot"

        slots.append({
            "id": f"slot_{len(slots)+1}",
            "type": slot_type,
            "length_mm": round(length, 2),
            "width_mm": round(width, 2),
            "estimated_depth_mm": round(est_depth, 2),
            "area_mm2": round(cluster_area, 2),
            "est_mill_time_min": round(length / 50 + 0.3, 3),  # ~50mm/min slot milling
            "complexity": 3 if slot_type == "thin_slot" else 1,
        })

    slots.sort(key=lambda x: x["length_mm"], reverse=True)
    return slots[:10]


# ─────────────────────────────────────────────
# EDGE ANALYSIS — FILLETS, CHAMFERS, SHARP EDGES
# ─────────────────────────────────────────────

def _analyze_edges(mesh, face_normals) -> dict:
    """
    Kenar analizi: sharp edges, fillets, chamfers.
    Komşu face normal'leri arasındaki açıya göre sınıflandırma.
    """
    sharp_count = 0
    fillet_count = 0
    chamfer_count = 0
    smooth_count = 0

    # Get face adjacency (shared edges)
    try:
        adjacency = mesh.face_adjacency  # list of (face_i, face_j) pairs
        adjacency_angles = mesh.face_adjacency_angles  # angles in radians

        for angle in adjacency_angles:
            angle_deg = math.degrees(float(angle))
            if angle_deg < 5:
                smooth_count += 1  # Tangent — smooth surface
            elif angle_deg < 15:
                fillet_count += 1  # Small angle → fillet
            elif angle_deg < 45:
                chamfer_count += 1  # Medium angle → chamfer
            else:
                sharp_count += 1  # Sharp corner
    except Exception:
        pass

    total_edges = sharp_count + fillet_count + chamfer_count + smooth_count

    return {
        "sharp_edges": sharp_count,
        "fillets": fillet_count,
        "chamfers": chamfer_count,
        "smooth_edges": smooth_count,
        "total_edges": total_edges,
        "edge_density": round(total_edges / max(len(mesh.faces), 1) * 3, 4),
    }


# ─────────────────────────────────────────────
# TURNING-SPECIFIC ANALYSIS
# ─────────────────────────────────────────────

def _analyze_turning(mesh, face_normals, face_areas, dimensions) -> dict:
    """
    CNC Torna için rotasyonel simetri analizi.
    Parçanın bir eksene göre simetrik olup olmadığını kontrol eder.
    """
    # Check if part is roughly cylindrical (turning candidate)
    x, y, z = dimensions["x_mm"], dimensions["y_mm"], dimensions["z_mm"]

    # Determine which axis is the rotation axis (longest dimension)
    dims_sorted = sorted([(x, "x"), (y, "y"), (z, "z")], key=lambda d: d[0], reverse=True)
    length_axis = dims_sorted[0][1]
    length = dims_sorted[0][0]

    # The other two dimensions should be similar (circular cross-section)
    other_dims = [d[0] for d in dims_sorted[1:]]
    diameter = max(other_dims)
    roundness = 1 - abs(other_dims[0] - other_dims[1]) / (max(other_dims) + 0.001)

    is_turning_candidate = (
        roundness > 0.7 and  # Fairly round cross-section
        length > diameter * 0.5  # At least somewhat elongated
    )

    # Estimate turning operations
    # Facing: 2 operations (both ends)
    facing_ops = 2 if is_turning_candidate else 0
    facing_time = facing_ops * 0.5  # 30s per face

    # Roughing: remove material to create profile
    # Based on bounding box vs actual volume ratio
    bbox_vol = x * y * z
    actual_vol = abs(float(mesh.volume))
    material_to_remove = max(bbox_vol - actual_vol, 0)
    roughing_time = material_to_remove / 2000 if is_turning_candidate else 0  # 2000mm³/min

    # Finishing: profile the entire length
    finishing_time = length / 100 if is_turning_candidate else 0  # 100mm/min

    # Threading (if applicable — can't detect from mesh, estimate from features)
    threading_time = 0  # Would need user input

    return {
        "is_turning_candidate": is_turning_candidate,
        "rotation_axis": length_axis,
        "length_mm": round(length, 2),
        "max_diameter_mm": round(diameter, 2),
        "roundness_score": round(roundness, 3),
        "operations": {
            "facing_count": facing_ops,
            "facing_time_min": round(facing_time, 3),
            "roughing_time_min": round(roughing_time, 3),
            "finishing_time_min": round(finishing_time, 3),
            "threading_time_min": round(threading_time, 3),
        },
        "total_turning_time_min": round(facing_time + roughing_time + finishing_time + threading_time, 3),
    }


# ─────────────────────────────────────────────
# CNC COMPLEXITY SCORE
# ─────────────────────────────────────────────

def _cnc_complexity_score(holes, pockets, slots, edges, planar_faces, dimensions, technology) -> int:
    """
    CNC kompleksite skoru (0-100).
    Feature sayısı, çeşitliliği ve boyutu baz alınır.
    """
    score = 0

    # Hole complexity
    for hole in holes:
        score += hole["complexity"] * 2
    score = min(score, 30)  # Holes max 30 points

    # Pocket complexity
    for pocket in pockets:
        score += pocket["complexity"] * 3
    score = min(score, 50)  # Cumulative max 50 (holes+pockets)

    # Slot complexity
    for slot in slots:
        score += slot["complexity"] * 2
    score = min(score, 60)

    # Edge complexity
    edge_density = edges.get("edge_density", 0)
    score += int(edge_density * 20)
    score = min(score, 80)

    # Size complexity (large parts are harder to machine precisely)
    max_dim = max(dimensions["x_mm"], dimensions["y_mm"], dimensions["z_mm"])
    if max_dim > 200:
        score += 10
    elif max_dim > 100:
        score += 5
    score = min(score, 90)

    # Sharp edges add complexity (need more tool changes)
    sharp = edges.get("sharp_edges", 0)
    if sharp > 50:
        score += 10
    elif sharp > 20:
        score += 5
    score = min(score, 100)

    return score


# ─────────────────────────────────────────────
# MACHINE TIME ESTIMATION
# ─────────────────────────────────────────────

def _estimate_cnc_time(holes, pockets, slots, edges, planar_faces,
                       cylindrical_faces, dimensions, volume_mm3, technology, mesh) -> dict:
    """
    Toplam CNC işleme süresi tahmini.
    Her feature tipi için ayrı süre hesabı + setup + overhead.
    """
    breakdown = {}
    total = 0

    # 1. Setup time (fixture, zero setting, tool loading)
    setup_time = 10  # 10 min base setup
    if technology == "cnc_turning":
        setup_time = 8  # Turning setup is faster (chuck/jaw)
    elif technology == "edm":
        setup_time = 15  # EDM setup (wire threading, alignment)

    breakdown["setup_min"] = setup_time
    total += setup_time

    # 2. Hole drilling time
    hole_time = sum(h["est_drill_time_min"] for h in holes)
    breakdown["hole_drilling_min"] = round(hole_time, 2)
    total += hole_time

    # 3. Pocket milling time
    pocket_time = sum(p["est_mill_time_min"] for p in pockets)
    breakdown["pocket_milling_min"] = round(pocket_time, 2)
    total += pocket_time

    # 4. Slot milling time
    slot_time = sum(s["est_mill_time_min"] for s in slots)
    breakdown["slot_milling_min"] = round(slot_time, 2)
    total += slot_time

    # 5. Facing time (largest planar face)
    if planar_faces:
        largest_face_area = planar_faces[0]["area_mm2"]
        facing_time = largest_face_area / 5000  # ~5000mm²/min facing rate
    else:
        facing_time = 2.0  # Minimum facing
    breakdown["facing_min"] = round(facing_time, 2)
    total += facing_time

    # 6. Contour/edge milling time
    edge_count = edges.get("total_edges", 0)
    # Contour milling: ~0.18s per edge (most edges are interior mesh edges, not machined contours)
    # Only sharp edges need actual machining — use a much smaller multiplier
    sharp_edges = edges.get("sharp_edges", 0)
    contour_time = sharp_edges * 0.005 + edge_count * 0.001  # 0.3s per sharp, 0.06s per total edge
    breakdown["contour_milling_min"] = round(contour_time, 2)
    total += contour_time

    # 7. Finishing time (surface finish)
    surface_area = float(mesh.area)
    finishing_time = surface_area / 3000  # ~3000mm²/min finish pass
    breakdown["finishing_min"] = round(finishing_time, 2)
    total += finishing_time

    # 8. Technology-specific time
    if technology == "cnc_turning":
        turning_data = _analyze_turning(mesh, mesh.face_normals, mesh.area_faces, dimensions)
        turning_time = turning_data["total_turning_time_min"]
        breakdown["turning_operations_min"] = turning_time
        total = max(total, turning_time + setup_time)

    elif technology == "edm":
        # EDM is slower — wire cutting speed ~2-5mm²/min
        # For wire EDM, estimate based on cut length
        cut_area = sum(s["area_mm2"] for s in slots) + sum(p["area_mm2"] for p in pockets)
        edm_time = max(cut_area / 3, 5)  # min 5 min
        breakdown["edm_cutting_min"] = round(edm_time, 2)
        total += edm_time

    # 9. Tool changes (estimated from feature variety)
    tool_change_count = len(set(h["diameter_mm"] for h in holes)) + \
                        len(set(p["type"] for p in pockets)) + \
                        len(set(s["type"] for s in slots))
    tool_change_time = tool_change_count * 0.5  # 30s per change
    breakdown["tool_changes_min"] = round(tool_change_time, 2)
    total += tool_change_time

    # 10. QC / inspection time
    qc_time = 2 + len(holes) * 0.1 + len(pockets) * 0.2
    breakdown["qc_min"] = round(qc_time, 2)
    total += qc_time

    return {
        "total_time_min": round(total, 2),
        "breakdown": {k: round(v, 2) for k, v in breakdown.items()},
    }


# ─────────────────────────────────────────────
# PROXIMITY CLUSTERING HELPER
# ─────────────────────────────────────────────

def _cluster_by_proximity(points: np.ndarray, max_distance: float = 10.0) -> list:
    """
    Noktaları spatial proximity'e göre kümele.
    DBSCAN-like basit clustering.
    """
    if len(points) == 0:
        return []
    if len(points) == 1:
        return [np.array([0])]

    tree = cKDTree(points)
    visited = set()
    clusters = []

    for i in range(len(points)):
        if i in visited:
            continue
        # Find all neighbors within max_distance
        neighbors = tree.query_ball_point(points[i], max_distance)
        cluster = []
        queue = list(neighbors)

        while queue:
            j = queue.pop(0)
            if j in visited:
                continue
            visited.add(j)
            cluster.append(j)
            new_neighbors = tree.query_ball_point(points[j], max_distance)
            for n in new_neighbors:
                if n not in visited:
                    queue.append(n)

        if len(cluster) >= 1:
            clusters.append(np.array(cluster))

    return clusters


# ─────────────────────────────────────────────
# WARNINGS
# ─────────────────────────────────────────────

def _generate_cnc_warnings(holes, pockets, slots, dimensions, is_watertight, technology) -> list:
    warnings = []

    if not is_watertight:
        warnings.append({
            "code": "NON_MANIFOLD",
            "severity": "medium",
            "message": "Mesh kapalı değil. CNC toolpath hesabı etkilenebilir."
        })

    # Deep hole warning
    for h in holes:
        if h["type"] == "deep_hole":
            warnings.append({
                "code": "DEEP_HOLE",
                "severity": "high",
                "message": f"Derin delik tespit edildi: Ø{h['diameter_mm']}mm × {h['depth_mm']}mm derinlik. Özel takım gerekebilir."
            })
            break  # One warning is enough

    # Micro hole warning
    for h in holes:
        if h["diameter_mm"] < 1.0:
            warnings.append({
                "code": "MICRO_HOLE",
                "severity": "high",
                "message": f"Mikro delik tespit edildi: Ø{h['diameter_mm']}mm. Standart CNC takımı ile zor olabilir."
            })
            break

    # Thin slot warning (EDM candidate)
    for s in slots:
        if s["type"] == "thin_slot":
            warnings.append({
                "code": "THIN_SLOT_EDM",
                "severity": "medium",
                "message": f"İnce kanal tespit edildi: {s['width_mm']}mm genişlik. EDM önerilir."
            })
            break

    # Oversized part
    max_dim = max(dimensions["x_mm"], dimensions["y_mm"], dimensions["z_mm"])
    if max_dim > 500:
        warnings.append({
            "code": "OVERSIZED",
            "severity": "high",
            "message": f"Parça {max_dim}mm — büyük CNC tezgahı gerekiyor."
        })
    elif max_dim > 300:
        warnings.append({
            "code": "LARGE_PART",
            "severity": "medium",
            "message": f"Parça {max_dim}mm — bazı tezgahların stroke limitini zorluyor."
        })

    # High pocket count
    if len(pockets) > 5:
        warnings.append({
            "code": "MANY_POCKETS",
            "severity": "medium",
            "message": f"{len(pockets)} cep tespit edildi. İşleme süresi uzun olabilir."
        })

    # Turning-specific
    if technology == "cnc_turning":
        roundness = max(dimensions["x_mm"], dimensions["y_mm"]) / (min(dimensions["x_mm"], dimensions["y_mm"]) + 0.001)
        if roundness > 1.5:
            warnings.append({
                "code": "NON_CYLINDRICAL",
                "severity": "high",
                "message": "Parça silindirik değil — tornalamada multi-axis veya frezleme gerekebilir."
            })

    return warnings
