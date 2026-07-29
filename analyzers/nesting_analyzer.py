"""
Nesting Optimizasyon Modülü — Faz-6
Shapelid Kernel v3.1.0

SLS ve MJF teknolojileri için çoklu parça baskı hacmi yerleştirme (bin packing).

İşlev:
  1. Birden fazla STL parçanın bounding box'larını baskı hacmine sığdırma
  2. Yerleştirme verimliliği (packing efficiency) hesabı
  3. Parça başına düşen maliyet payını (prorata) hesaplama
  4. Makine süresi tek seferde (tüm parçalar için)

Algoritma: Bottom-Left-First (BLF) 3D bin packing — basit ama etkili.
Daha gelişmiş: best-fit decreasing + rotation.

Build volume referansları:
  - SLS (EOS P 396)      : 340 × 340 × 600 mm
  - SLS (Formlabs Fuse 1+): 165 × 165 × 300 mm
  - MJF (HP 5200)        : 380 × 280 × 380 mm
  - MJF (HP 580)         : 215 × 180 × 370 mm
"""

import numpy as np
import trimesh
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field


# ── Makine Build Volume'ları ────────────────────────────────────────────────

BUILD_VOLUMES = {
    "sls": {
        "default"         : {"x": 340, "y": 340, "z": 600, "name": "EOS P 396"},
        "formlabs_fuse1"  : {"x": 165, "y": 165, "z": 300, "name": "Formlabs Fuse 1+"},
        "eos_p770"        : {"x": 700, "y": 380, "z": 580, "name": "EOS P 770"},
    },
    "mjf": {
        "default"         : {"x": 380, "y": 280, "z": 380, "name": "HP Jet Fusion 5200"},
        "hp_580"          : {"x": 215, "y": 180, "z": 370, "name": "HP Jet Fusion 580"},
        "hp_420"          : {"x": 380, "y": 280, "z": 380, "name": "HP Jet Fusion 420"},
    },
    "dmls": {
        "default"         : {"x": 250, "y": 250, "z": 300, "name": "EOS M 290"},
        "slm_280"         : {"x": 280, "y": 280, "z": 365, "name": "SLM 280"},
    },
}

# Minimum parça aralığı (mm) — parçalar birbirine değmesin
MIN_PART_GAP_MM = 2.0
# Toz tabakası kalınlığı (mm) — z ekseni toleransı
POWDER_LAYER_GAP_MM = 3.0


@dataclass
class PartInfo:
    """Tek bir parçanın yerleştirme bilgisi."""
    part_id: str
    dimensions: Tuple[float, float, float]  # x, y, z mm (bounding box)
    volume_cm3: float
    quantity: int = 1
    can_rotate: bool = True
    # Yerleştirme sonucu (BLF sonrası doldurulur)
    position: Tuple[float, float, float] = (0, 0, 0)  # x, y, z offset
    rotation: int = 0  # 0-5: 6 eksen rotasyon
    placed: bool = False


@dataclass
class NestingResult:
    """Nesting sonucu."""
    build_volume: Dict
    parts_placed: List[Dict]
    parts_unplaced: List[Dict]
    total_parts: int
    placed_count: int
    packing_efficiency: float       # 0-1 (hacim verimliliği)
    footprint_efficiency: float     # 0-1 (XY alan verimliliği)
    layers_used: int                 # Z ekseni katman sayısı
    build_height_mm: float
    unused_volume_cm3: float
    nesting_score: float             # 0-100
    warnings: List[Dict] = field(default_factory=list)
    batch_count: int = 1             # Kaç batch gerektiği


def analyze_nesting(
    parts: List[Dict[str, Any]],
    technology: str = "sls",
    machine_variant: str = "default",
) -> NestingResult:
    """
    Birden fazla parçayı baskı hacmine yerleştirir.

    Args:
        parts: [{ part_id, dimensions_mm: {x,y,z}, volume_cm3, quantity }]
        technology: "sls" | "mjf" | "dmls"
        machine_variant: "default" | "formlabs_fuse1" | "hp_580" | vb.

    Returns:
        NestingResult: yerleştirme analizi
    """
    build = BUILD_VOLUMES.get(technology, {}).get(machine_variant)
    if not build:
        build = BUILD_VOLUMES.get(technology, {}).get("default", {"x": 300, "y": 300, "z": 400})

    bx, by, bz = build["x"], build["y"], build["z"]

    # ── Parça listesini hazırla ────────────────────────────────────────────
    part_list = []
    for p in parts:
        dims = p.get("dimensions_mm", p.get("dimensions", {}))
        dx = float(dims.get("x_mm", dims.get("x", 50)))
        dy = float(dims.get("y_mm", dims.get("y", 50)))
        dz = float(dims.get("z_mm", dims.get("z", 50)))
        vol = float(p.get("volume_cm3", 0))
        qty = int(p.get("quantity", 1))

        for i in range(qty):
            part_list.append(PartInfo(
                part_id=f"{p.get('part_id', 'part')}_{i}" if qty > 1 else p.get("part_id", "part"),
                dimensions=(dx, dy, dz),
                volume_cm3=vol,
                quantity=1,
                can_rotate=p.get("can_rotate", True),
            ))

    # ── Parçaları boyuta göre büyükten küçüğe sırala (best-fit decreasing) ─
    part_list.sort(key=lambda p: p.volume_cm3, reverse=True)

    # ── 3D Bin Packing (BLF algoritması) ──────────────────────────────────
    placed = []
    unplaced = []
    occupied_regions = []  # [(x1,y1,z1, x2,y2,z2), ...]

    batch_parts = part_list.copy()
    batch_count = 1
    batches = []

    while batch_parts:
        batch_placed = []
        batch_unplaced = []
        occupied_regions = []

        for part in batch_parts:
            pos = _find_position(part, occupied_regions, bx, by, bz)
            if pos:
                part.position = pos
                part.placed = True
                x, y, z = pos
                dx, dy, dz = _rotate_dims(part)
                occupied_regions.append((x, y, z, x + dx + MIN_PART_GAP_MM,
                                        y + dy + MIN_PART_GAP_MM, z + dz + POWDER_LAYER_GAP_MM))
                batch_placed.append(part)
            else:
                batch_unplaced.append(part)

        batches.append(batch_placed)

        if batch_unplaced:
            batch_count += 1
            batch_parts = batch_unplaced
            # Bir sonraki batch için yerleştirilmeyenleri tekrar dene
            if batch_count > 10:  # Güvenlik limiti
                unplaced.extend(batch_unplaced)
                break
        else:
            batch_parts = []

    # Tüm batch'lerden yerleştirilenleri topla
    all_placed = []
    for batch in batches:
        all_placed.extend(batch)

    # ── Verimlilik hesabı ─────────────────────────────────────────────────
    total_part_volume = sum(p.volume_cm3 for p in all_placed)
    build_volume_cm3 = (bx * by * bz) / 1000

    # En yüksek batch'in build height'ı
    max_height_mm = 0
    for p in all_placed:
        x, y, z = p.position
        dx, dy, dz = _rotate_dims(p)
        max_height_mm = max(max_height_mm, z + dz)

    used_height_mm = max_height_mm if all_placed else 0
    used_volume_cm3 = (bx * by * used_height_mm) / 1000 if used_height_mm > 0 else 0

    packing_eff = round(total_part_volume / build_volume_cm3, 4) if build_volume_cm3 > 0 else 0
    footprint_eff = round(total_part_volume / used_volume_cm3, 4) if used_volume_cm3 > 0 else 0

    layers_used = int(used_height_mm / 0.1) if used_height_mm > 0 else 0  # 100µm layer

    # Nesting score (0-100)
    nesting_score = _nesting_score(packing_eff, footprint_eff, len(all_placed), len(unplaced))

    # ── Uyarılar ──────────────────────────────────────────────────────────
    warnings = _generate_warnings(
        technology=technology,
        build=build,
        packing_eff=packing_eff,
        unplaced_count=len(unplaced),
        batch_count=batch_count,
        max_part_dims=max(part_list, key=lambda p: max(p.dimensions)).dimensions if part_list else (0,0,0),
    )

    # ── Sonuç dict'leri ───────────────────────────────────────────────────
    placed_dicts = []
    for p in all_placed:
        placed_dicts.append({
            "part_id"   : p.part_id,
            "position_mm": {"x": round(p.position[0], 1), "y": round(p.position[1], 1), "z": round(p.position[2], 1)},
            "dimensions_mm": {"x": round(_rotate_dims(p)[0], 1), "y": round(_rotate_dims(p)[1], 1), "z": round(_rotate_dims(p)[2], 1)},
            "volume_cm3": p.volume_cm3,
            "rotation"  : p.rotation,
        })

    unplaced_dicts = [{"part_id": p.part_id, "dimensions_mm": {"x": p.dimensions[0], "y": p.dimensions[1], "z": p.dimensions[2]}}
                      for p in unplaced]

    return NestingResult(
        build_volume={"x": bx, "y": by, "z": bz, "name": build.get("name", "Unknown")},
        parts_placed=placed_dicts,
        parts_unplaced=unplaced_dicts,
        total_parts=len(part_list),
        placed_count=len(all_placed),
        packing_efficiency=packing_eff,
        footprint_efficiency=footprint_eff,
        layers_used=layers_used,
        build_height_mm=round(used_height_mm, 1),
        unused_volume_cm3=round(build_volume_cm3 - total_part_volume, 2),
        nesting_score=nesting_score,
        warnings=warnings,
        batch_count=batch_count,
    )


def _rotate_dims(part: PartInfo) -> Tuple[float, float, float]:
    """Rotasyon uygulandıktan sonra boyutları döndür."""
    dx, dy, dz = part.dimensions
    rot = part.rotation
    # 6 eksen rotasyon kombinasyonu
    if rot == 0: return (dx, dy, dz)
    elif rot == 1: return (dy, dx, dz)   # X-Y swap
    elif rot == 2: return (dx, dz, dy)   # Y-Z swap
    elif rot == 3: return (dz, dy, dx)   # X-Z swap
    elif rot == 4: return (dy, dz, dx)   # rotate 120°
    else: return (dz, dx, dy)            # rotate 240°


def _find_position(part: PartInfo, occupied: List[Tuple], bx: float, by: float, bz: float) -> Tuple[float, float, float] | None:
    """
    Bottom-Left-First: en düşük (x, y, z) pozisyonu ara.
    Parça için 6 rotasyon kombinasyonunu dener.
    """
    # Rotasyon sırası: en düşük taban alanı önce (dz'yi max yap, taban alanı min)
    if part.can_rotate:
        rotations = [2, 4, 5, 3, 1, 0]  # Z'yi max yapacak sıra
    else:
        rotations = [0]

    for rot in rotations:
        part.rotation = rot
        dx, dy, dz = _rotate_dims(part)

        # Hacim kontrolü
        if dx > bx or dy > by or dz > bz:
            continue

        # Grid tabanlı arama (10mm adım)
        step = 10.0
        for z in np.arange(0, bz - dz + 1, step):
            for y in np.arange(0, by - dy + 1, step):
                for x in np.arange(0, bx - dx + 1, step):
                    if _is_free(x, y, z, dx, dy, dz, occupied):
                        return (float(x), float(y), float(z))

    return None


def _is_free(x: float, y: float, z: float, dx: float, dy: float, dz: float,
             occupied: List[Tuple]) -> bool:
    """Verilen bölge boş mu? (AABB çakışma kontrolü)."""
    x2, y2, z2 = x + dx, y + dy, z + dz
    for ox1, oy1, oz1, ox2, oy2, oz2 in occupied:
        # Çakışma yoksa continue
        if x2 <= ox1 or x >= ox2 or y2 <= oy1 or y >= oy2 or z2 <= oz1 or z >= oz2:
            continue
        return False
    return True


def _nesting_score(packing_eff: float, footprint_eff: float, placed: int, unplaced: int) -> float:
    """Nesting kalite skoru (0-100)."""
    score = 0.0
    # Packing efficiency %50 ağırlık
    score += min(packing_eff * 100, 100) * 0.50
    # Footprint efficiency %30 ağırlık
    score += min(footprint_eff * 100, 100) * 0.30
    # Yerleştirme oranı %20 ağırlık
    total = placed + unplaced
    if total > 0:
        score += (placed / total) * 100 * 0.20
    return round(score, 1)


def _generate_warnings(technology: str, build: Dict, packing_eff: float,
                       unplaced_count: int, batch_count: int,
                       max_part_dims: Tuple) -> List[Dict]:
    warnings = []

    # Düşük packing efficiency
    if packing_eff < 0.05:
        warnings.append({
            "code"    : "LOW_PACKING_EFFICIENCY",
            "severity": "medium",
            "message" : f"Packing efficiency çok düşük (%{packing_eff*100:.1f}). Parça boyutları build volume'a göre çok küçük.",
        })

    # Yerleştirilemeyen parçalar
    if unplaced_count > 0:
        warnings.append({
            "code"    : "PARTS_UNPLACED",
            "severity": "high",
            "message" : f"{unplaced_count} parça build volume'a sığmadı. Daha büyük makine veya batch gerekli.",
        })

    # Çok sayıda batch
    if batch_count > 3:
        warnings.append({
            "code"    : "TOO_MANY_BATCHES",
            "severity": "medium",
            "message" : f"{batch_count} batch gerekiyor. Maliyet artar — daha verimli nesting öner.",
        })

    # Parça build volume'dan büyük
    bx, by, bz = build["x"], build["y"], build["z"]
    mx, my, mz = max_part_dims
    if mx > bx or my > by or mz > bz:
        warnings.append({
            "code"    : "PART_EXCEEDS_BUILD_VOLUME",
            "severity": "critical",
            "message" : f"En büyük parça ({mx}×{my}×{mz}mm) build volume'u ({bx}×{by}×{bz}mm) aşıyor.",
        })

    return warnings
