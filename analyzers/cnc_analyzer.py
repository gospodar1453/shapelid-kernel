"""
CNC Feature Recognition Modülü — Faz-5
Shapelid Kernel v3.0.0

STL mesh üzerinde trimesh + numpy ile geometrik özellik tespiti:

Tespit edilen feature'lar:
  - holes        : silindirik delikler (çap, derinlik, adet)
  - pockets      : cepler (alan, derinlik)
  - flat_faces   : düz yüzeyler (oryantasyon, alan)
  - undercuts    : undercut riski olan yüzeyler
  - thin_walls   : ince duvarlar (min duvar kalınlığı)
  - complexity   : toplam karmaşıklık skoru (CNC workload index)

Çıktı, pricing/engine.py'deki _price_cnc() fonksiyonu tarafından kullanılır.
"""

import numpy as np
import trimesh
from typing import List, Dict, Any


# ── Sabitler ────────────────────────────────────────────────────────────────

# Yüzey normali Z eksenine ne kadar yakınsa "flat face" sayılır (cos açısı)
FLAT_FACE_THRESHOLD  = 0.95   # ~18° tolerans
# Silindirik yüzey tespiti için normal vektör yayılım toleransı
CYLINDER_NORMAL_STD  = 0.15   # düşük std = silindirik yüzey
# Minimum delik çapı (mm) — daha küçük = delik değil
MIN_HOLE_DIAMETER_MM = 0.5
# Undercut eşiği: -Z yönüne bakan yüzey açısı (derece)
UNDERCUT_ANGLE_DEG   = 45.0


def analyze_cnc(file_path: str, technology: str = "cnc_milling") -> dict:
    """
    STL dosyasını analiz eder ve CNC feature'larını döndürür.
    
    Args:
        file_path : STL dosya yolu
        technology: 'cnc_milling' | 'cnc_turning' | 'edm'
    
    Returns:
        dict: feature_summary, setup_complexity, workload_index, warnings
    """
    mesh = trimesh.load(file_path, force="mesh")

    if not isinstance(mesh, trimesh.Trimesh) or len(mesh.faces) == 0:
        raise ValueError("Geçersiz STL dosyası")

    # Temel metrikler
    dims = mesh.bounds
    size = dims[1] - dims[0]  # [x, y, z] mm
    volume_cm3   = abs(float(mesh.volume)) / 1000 if mesh.is_volume else abs(float(mesh.convex_hull.volume)) / 1000
    surface_cm2  = float(mesh.area) / 100

    # ── Feature tespiti ──────────────────────────────────────────────────
    flat_faces   = _detect_flat_faces(mesh)
    holes        = _detect_holes(mesh, size)
    pockets      = _detect_pockets(mesh, flat_faces)
    undercuts    = _detect_undercuts(mesh)
    thin_walls   = _detect_thin_walls(mesh)

    # ── Teknoloji bazlı ek analiz ────────────────────────────────────────
    if technology == "cnc_turning":
        rotational = _analyze_rotational_symmetry(mesh, size)
    else:
        rotational = {"is_rotational": False, "symmetry_score": 0}

    # ── Karmaşıklık skoru (0–100) ────────────────────────────────────────
    workload_index = _calculate_workload_index(
        technology   = technology,
        holes        = holes,
        pockets      = pockets,
        flat_faces   = flat_faces,
        undercuts    = undercuts,
        thin_walls   = thin_walls,
        rotational   = rotational,
        size         = size,
        volume_cm3   = volume_cm3,
    )

    # ── Uyarılar ─────────────────────────────────────────────────────────
    warnings = _generate_cnc_warnings(
        technology = technology,
        holes      = holes,
        undercuts  = undercuts,
        thin_walls = thin_walls,
        size       = size,
        rotational = rotational,
    )

    return {
        "type"              : "cnc",
        "technology"        : technology,
        "volume_cm3"        : round(volume_cm3, 4),
        "surface_area_cm2"  : round(surface_cm2, 4),
        "dimensions_mm"     : {
            "x_mm": round(float(size[0]), 2),
            "y_mm": round(float(size[1]), 2),
            "z_mm": round(float(size[2]), 2),
        },
        "feature_summary"   : {
            "hole_count"        : len(holes),
            "holes"             : holes,
            "pocket_count"      : len(pockets),
            "pockets"           : pockets,
            "flat_face_count"   : len(flat_faces),
            "undercut_count"    : len(undercuts),
            "thin_wall_count"   : len(thin_walls),
            "min_wall_thickness": min([w["thickness_mm"] for w in thin_walls], default=None),
        },
        "rotational_analysis": rotational,
        "workload_index"    : workload_index,
        "setup_complexity"  : _classify_complexity(workload_index),
        "warnings"          : warnings,
        "is_watertight"     : bool(mesh.is_watertight),
    }


# ── Feature Detection Fonksiyonları ─────────────────────────────────────────

def _detect_flat_faces(mesh: trimesh.Trimesh) -> List[Dict]:
    """
    Düz yüzeyler: normal vektörü ağırlıklı ortalama yönlere yakın olan yüzey grupları.
    Çıkış eksenleri: +Z, -Z, +X, -X, +Y, -Y (6 ana yüz yönü)
    """
    normals = mesh.face_normals  # (N, 3)
    areas   = mesh.area_faces    # (N,)

    principal_axes = np.array([
        [0, 0,  1],   # +Z (top)
        [0, 0, -1],   # -Z (bottom)
        [1, 0,  0],   # +X
        [-1, 0,  0],  # -X
        [0,  1,  0],  # +Y
        [0, -1,  0],  # -Y
    ], dtype=float)

    axis_names = ["+Z", "-Z", "+X", "-X", "+Y", "-Y"]
    flat_faces = []

    for ax, name in zip(principal_axes, axis_names):
        dots = np.abs(normals @ ax)
        mask = dots > FLAT_FACE_THRESHOLD
        if mask.sum() > 0:
            area_sum = float(areas[mask].sum()) / 100  # mm² → cm²
            flat_faces.append({
                "axis"      : name,
                "area_cm2"  : round(area_sum, 4),
                "face_count": int(mask.sum()),
            })

    return flat_faces


def _detect_holes(mesh: trimesh.Trimesh, size: np.ndarray) -> List[Dict]:
    """
    Delik tespiti: silindirik yüzey kümeleri arar.
    Yaklaşım: edge loop analizi + normal vektör yayılımı
    """
    holes = []

    # Boundary edge'leri (sadece 1 face'e ait edge'ler) bul
    try:
        boundary_edges = trimesh.graph.connected_component_labels(mesh.edges_unique)
    except Exception:
        boundary_edges = []

    # Alternatif: yüzey normal kümelenmesi ile silindirik grup tespiti
    normals = mesh.face_normals
    areas   = mesh.area_faces

    # Her face'in XY düzlemine projeksiyonu — silindirik yüzeyler radyal normal'e sahip
    # Normal XY bileşeninin büyüklüğü silindirik yüzeylerde yüksek olur
    n_xy_magnitude = np.sqrt(normals[:, 0]**2 + normals[:, 1]**2)
    cylindrical_mask = n_xy_magnitude > 0.85  # XY ağırlıklı normal = lateral yüzey

    # Silindirik yüzeyleri bounding box merkezinden uzaklığa göre grupla
    mesh_center_xy = np.array([
        float(mesh.bounds[0][0] + size[0]/2),
        float(mesh.bounds[0][1] + size[1]/2),
    ])

    if cylindrical_mask.sum() > 0:
        # Silindirik yüzeylerin ağırlık merkezi
        face_centers = mesh.triangles_center[cylindrical_mask]
        cyl_area     = float(areas[cylindrical_mask].sum())

        # Basit: silindirik yüzey alanından tahmini delik çapı
        # Lateral alan = π × d × h → d = area / (π × h)
        est_height = float(size[2]) * 0.3  # tahmini
        if est_height > 0:
            est_diameter = cyl_area / (np.pi * est_height * 10)  # mm
            if est_diameter >= MIN_HOLE_DIAMETER_MM:
                holes.append({
                    "type"          : "cylindrical",
                    "est_diameter_mm": round(est_diameter, 2),
                    "est_depth_mm"  : round(est_height, 2),
                    "area_cm2"      : round(cyl_area / 100, 4),
                    "confidence"    : "medium",  # STL'den kesin tespit zor
                })

    # Mesh'in karmaşıklığına göre ek delik tahmini (istatistiksel)
    # Topologi: her non-manifold edge = potansiyel delik
    if not mesh.is_watertight:
        holes.append({
            "type"           : "topology_implied",
            "est_diameter_mm": None,
            "est_depth_mm"   : None,
            "area_cm2"       : None,
            "confidence"     : "low",
            "note"           : "Non-watertight mesh — gerçek STEP analizi önerilir",
        })

    return holes


def _detect_pockets(mesh: trimesh.Trimesh, flat_faces: List[Dict]) -> List[Dict]:
    """
    Cep (pocket) tahmini: iç düz yüzeyler + çevreleyen duvarlar kombinasyonu.
    STL'de kesin cep tespiti zor — yaklaşımsal.
    """
    pockets = []

    # -Z (alt) yönündeki düz yüzeyler hariç, iç düz yüzeyler cep adayı
    # Basit yaklaşım: +X, -X, +Y, -Y eksenindeki küçük flat face'ler cep tabanı
    for face in flat_faces:
        if face["axis"] in ("+X", "-X", "+Y", "-Y") and face["area_cm2"] < 50:
            pockets.append({
                "type"    : "side_pocket",
                "axis"    : face["axis"],
                "area_cm2": face["area_cm2"],
                "confidence": "low",
            })

    return pockets


def _detect_undercuts(mesh: trimesh.Trimesh) -> List[Dict]:
    """
    Undercut tespiti: -Z yönüne bakan ve Z ekseninden belirli açıda eğik yüzeyler.
    3-eksen CNC'de bu yüzeyler işlenemez.
    """
    normals = mesh.face_normals
    areas   = mesh.area_faces

    # -Z bileşeni yüksek + XY bileşeni var = undercut adayı
    neg_z_mask = normals[:, 2] < -np.cos(np.radians(UNDERCUT_ANGLE_DEG))
    xy_mask    = np.sqrt(normals[:, 0]**2 + normals[:, 1]**2) > 0.2

    undercut_mask = neg_z_mask & xy_mask

    undercuts = []
    if undercut_mask.sum() > 0:
        area_sum = float(areas[undercut_mask].sum()) / 100
        undercuts.append({
            "face_count"  : int(undercut_mask.sum()),
            "area_cm2"    : round(area_sum, 4),
            "severity"    : "high" if area_sum > 5 else "medium",
            "note"        : "5-eksen CNC veya özel fixture gerekebilir",
        })

    return undercuts


def _detect_thin_walls(mesh: trimesh.Trimesh) -> List[Dict]:
    """
    İnce duvar tahmini: packing density düşük + yüzey/hacim oranı yüksek bölgeler.
    Kesin tespit STEP gerektirir; STL'de yaklaşımsal.
    """
    thin_walls = []

    volume_mm3   = abs(float(mesh.volume)) if mesh.is_volume else abs(float(mesh.convex_hull.volume))
    surface_mm2  = float(mesh.area)

    if volume_mm3 > 0:
        # Yüzey/hacim oranı: ince parçalarda yüksek
        sv_ratio = surface_mm2 / volume_mm3

        # Eğer oran > 2.0 mm⁻¹ → potansiyel ince duvar
        if sv_ratio > 2.0:
            est_thickness = round(2.0 / sv_ratio * 10, 2)  # mm cinsinden tahmin
            thin_walls.append({
                "thickness_mm"  : est_thickness,
                "sv_ratio"      : round(sv_ratio, 4),
                "confidence"    : "medium",
                "note"          : f"Tahmini duvar kalınlığı: {est_thickness}mm — kesin tespit için STEP gerekli",
            })

    return thin_walls


def _analyze_rotational_symmetry(mesh: trimesh.Trimesh, size: np.ndarray) -> Dict:
    """
    CNC Turning için: parça rotasyonel simetri analizi.
    Z ekseni etrafında simetrik = torna işlemi uygun.
    """
    # Bounding box en-boy oranı: uzun/silindirik parça → turning
    x, y, z = float(size[0]), float(size[1]), float(size[2])
    aspect_ratio = z / max(x, y) if max(x, y) > 0 else 1

    # XY kesit daireselliği: x ≈ y ise silindirik
    xy_roundness = min(x, y) / max(x, y) if max(x, y) > 0 else 0

    # Normal vektörlerinin XY düzlemindeki dağılımı
    normals = mesh.face_normals
    n_z_abs = np.abs(normals[:, 2])
    radial_pct = float((n_z_abs < 0.3).mean())  # radyal normal'e sahip yüzey oranı

    is_rotational = (
        xy_roundness > 0.75 and
        aspect_ratio > 1.0  and
        radial_pct > 0.3
    )

    symmetry_score = round(
        (xy_roundness * 40 + min(aspect_ratio / 5, 1) * 30 + radial_pct * 30),
        1
    )

    return {
        "is_rotational"  : is_rotational,
        "symmetry_score" : min(symmetry_score, 100),
        "aspect_ratio"   : round(aspect_ratio, 2),
        "xy_roundness"   : round(xy_roundness, 4),
        "radial_surface_pct": round(radial_pct, 4),
        "note": "Torna uyumu yüksek" if is_rotational else "Freze uyumu daha uygun olabilir",
    }


def _calculate_workload_index(
    technology: str,
    holes: List, pockets: List, flat_faces: List,
    undercuts: List, thin_walls: List,
    rotational: Dict, size: np.ndarray, volume_cm3: float,
) -> float:
    """
    CNC İşleme İş Yükü İndeksi (0–100).
    Fiyatlandırma motorunda makine süresi çarpanı olarak kullanılır.
    """
    score = 20.0  # Baz puan (basit parça)

    # Boyut katkısı (büyük parça = daha uzun işleme)
    volume_factor = min(volume_cm3 / 100, 1.0)  # 100 cm³ = max katkı
    score += volume_factor * 15

    # Feature katkıları
    score += min(len(holes) * 5, 20)        # Her delik +5 (max 20)
    score += min(len(pockets) * 8, 24)      # Her cep +8 (max 24)
    score += min(len(undercuts) * 10, 20)   # Her undercut +10 (max 20)
    score += min(len(thin_walls) * 5, 10)   # İnce duvar +5 (max 10)

    # Teknoloji özgün düzeltme
    if technology == "cnc_turning" and rotational.get("is_rotational"):
        score *= 0.7   # Torna = daha hızlı (simetrik)
    elif technology == "edm":
        score *= 1.3   # EDM çok yavaş

    return round(min(score, 100), 1)


def _classify_complexity(workload_index: float) -> str:
    if workload_index < 25:
        return "simple"
    elif workload_index < 50:
        return "moderate"
    elif workload_index < 75:
        return "complex"
    else:
        return "very_complex"


def _generate_cnc_warnings(
    technology: str, holes: List, undercuts: List,
    thin_walls: List, size: np.ndarray, rotational: Dict
) -> List[Dict]:
    warnings = []

    # Non-manifold → STEP önerisi
    for h in holes:
        if h.get("confidence") == "low":
            warnings.append({
                "code"    : "STL_GEOMETRY_ESTIMATE",
                "severity": "medium",
                "message" : "STL formatında feature tespiti yaklaşımsal. Kesin fiyat için STEP/IGES dosyası önerilir.",
            })
            break

    # Undercut uyarısı
    if undercuts:
        warnings.append({
            "code"    : "UNDERCUT_DETECTED",
            "severity": "high",
            "message" : f"Undercut bölgeler tespit edildi ({sum(u['face_count'] for u in undercuts)} yüzey). 5-eksen CNC veya özel fixture gerekebilir.",
        })

    # İnce duvar
    for tw in thin_walls:
        if tw["thickness_mm"] < 0.5:
            warnings.append({
                "code"    : "THIN_WALL_RISK",
                "severity": "high",
                "message" : f"Tahmini duvar kalınlığı {tw['thickness_mm']}mm — CNC işlemede titreşim/kırılma riski.",
            })

    # Torna uyumsuzluğu
    if technology == "cnc_turning" and not rotational.get("is_rotational"):
        warnings.append({
            "code"    : "NOT_ROTATIONAL",
            "severity": "medium",
            "message" : "Parça rotasyonel simetri taşımıyor. CNC Freze daha uygun olabilir.",
        })

    # EDM büyük parça
    if technology == "edm":
        if float(size[0]) > 400 or float(size[1]) > 300 or float(size[2]) > 250:
            warnings.append({
                "code"    : "BUILD_VOLUME_EXCEEDED",
                "severity": "critical",
                "message" : "EDM makine hacmi aşıldı (400×300×250mm). Manuel teklif gerekli.",
            })

    return warnings
