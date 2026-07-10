"""
DXF Analiz Modülü — Laser Cutting ve Bending için
ezdxf kütüphanesi ile 2D geometri analizi:
- Kesim uzunluğu (toplam kontur)
- Alan (iç ve dış)
- Delik sayısı ve toplam çevresi
- Büküm çizgisi sayısı (BEND_LINE layer'ından)
- Parça bounding box
- Nesting verimliliği tahmini
"""

import ezdxf
from ezdxf.math import Vec2
import math


def analyze_dxf(file_path: str) -> dict:
    try:
        doc = ezdxf.readfile(file_path)
    except ezdxf.DXFStructureError as e:
        raise ValueError(f"DXF dosyası okunamadı: {str(e)}")

    msp = doc.modelspace()

    # Tüm entity'leri topla
    entities = list(msp)

    # Konturları ayır: dış kontur, delikler, büküm çizgileri
    outer_contours = []
    holes = []
    bend_lines = []
    all_cut_lengths = []

    for entity in entities:
        layer = (entity.dxf.layer or "").upper()

        if "BEND" in layer or "BÜKÜ" in layer or "FOLD" in layer:
            # Büküm çizgisi
            length = _get_entity_length(entity)
            if length > 0:
                bend_lines.append({
                    "layer": entity.dxf.layer,
                    "length_mm": round(length, 4)
                })
        elif "HOLE" in layer or "DELIK" in layer or "CUT" in layer:
            # Delik katmanı
            length = _get_entity_length(entity)
            if length > 0:
                holes.append({"length_mm": round(length, 4)})
                all_cut_lengths.append(length)
        else:
            # Genel kesim geometrisi
            length = _get_entity_length(entity)
            if length > 0:
                outer_contours.append({"length_mm": round(length, 4)})
                all_cut_lengths.append(length)

    # Toplam kesim uzunluğu
    total_cut_length_mm = sum(all_cut_lengths)
    total_cut_length_m = round(total_cut_length_mm / 1000, 4)

    # Alan hesaplama (kapalı polyline veya LWPolyline'lardan)
    areas = _calculate_areas(msp)
    outer_area_mm2 = areas["outer"]
    hole_area_mm2 = areas["holes"]
    net_area_mm2 = max(outer_area_mm2 - hole_area_mm2, 0)
    outer_area_cm2 = round(outer_area_mm2 / 100, 4)
    net_area_cm2 = round(net_area_mm2 / 100, 4)

    # Bounding box
    bbox = _get_bounding_box(msp)

    # Nesting verimliliği tahmini
    if bbox["area_mm2"] > 0:
        nesting_efficiency = round(outer_area_mm2 / bbox["area_mm2"], 4)
    else:
        nesting_efficiency = 0

    # Büküm analizi
    bend_count = len(bend_lines)
    total_bend_length_mm = sum(b["length_mm"] for b in bend_lines)

    # Delik analizi
    hole_count = len(holes)
    total_hole_perimeter_mm = sum(h["length_mm"] for h in holes)

    return {
        "type": "2d",
        "total_cut_length_mm": round(total_cut_length_mm, 4),
        "total_cut_length_m": total_cut_length_m,
        "outer_area_cm2": outer_area_cm2,
        "net_area_cm2": net_area_cm2,
        "hole_area_cm2": round(hole_area_mm2 / 100, 4),
        "bounding_box_mm": bbox,
        "nesting_efficiency": nesting_efficiency,
        "bend_count": bend_count,
        "bend_lines": bend_lines,
        "total_bend_length_mm": round(total_bend_length_mm, 4),
        "hole_count": hole_count,
        "total_hole_perimeter_mm": round(total_hole_perimeter_mm, 4),
        "entity_count": len(entities),
        "warnings": _generate_dxf_warnings(total_cut_length_mm, bbox, bend_count),
    }


def _get_entity_length(entity) -> float:
    """Entity türüne göre uzunluk hesaplar"""
    dxftype = entity.dxftype()

    try:
        if dxftype == "LINE":
            start = Vec2(entity.dxf.start[:2])
            end = Vec2(entity.dxf.end[:2])
            return (end - start).magnitude

        elif dxftype in ("CIRCLE",):
            return 2 * math.pi * entity.dxf.radius

        elif dxftype == "ARC":
            radius = entity.dxf.radius
            start_angle = math.radians(entity.dxf.start_angle)
            end_angle = math.radians(entity.dxf.end_angle)
            if end_angle < start_angle:
                end_angle += 2 * math.pi
            return radius * (end_angle - start_angle)

        elif dxftype in ("LWPOLYLINE", "POLYLINE"):
            if hasattr(entity, "get_points"):
                points = list(entity.get_points())
            elif hasattr(entity, "points"):
                points = list(entity.points())
            else:
                return 0

            if len(points) < 2:
                return 0

            total = 0
            pts2d = [Vec2(p[:2]) for p in points]
            for i in range(len(pts2d) - 1):
                total += (pts2d[i + 1] - pts2d[i]).magnitude

            if entity.is_closed:
                total += (pts2d[-1] - pts2d[0]).magnitude

            return total

        elif dxftype == "SPLINE":
            # Spline için yaklaşık uzunluk (örnekleme)
            if hasattr(entity, "flattening"):
                pts = list(entity.flattening(0.01))
                total = 0
                for i in range(len(pts) - 1):
                    p1, p2 = Vec2(pts[i][:2]), Vec2(pts[i + 1][:2])
                    total += (p2 - p1).magnitude
                return total

        elif dxftype == "ELLIPSE":
            # Ramanujan yaklaşımı
            a = entity.dxf.major_axis.magnitude
            b = a * entity.dxf.ratio
            h = ((a - b) ** 2) / ((a + b) ** 2)
            return math.pi * (a + b) * (1 + (3 * h) / (10 + math.sqrt(4 - 3 * h)))

    except Exception:
        pass

    return 0


def _calculate_areas(msp) -> dict:
    """Kapalı polyline'ların alanını hesaplar"""
    outer_area = 0
    hole_area = 0

    for entity in msp:
        dxftype = entity.dxftype()
        layer = (entity.dxf.layer or "").upper()

        try:
            if dxftype == "LWPOLYLINE" and entity.is_closed:
                pts = [Vec2(p[:2]) for p in entity.get_points()]
                area = abs(_polygon_area(pts))
                if "HOLE" in layer or "DELIK" in layer:
                    hole_area += area
                else:
                    outer_area = max(outer_area, area)

            elif dxftype == "CIRCLE":
                r = entity.dxf.radius
                area = math.pi * r * r
                if "HOLE" in layer or "DELIK" in layer:
                    hole_area += area

        except Exception:
            pass

    return {"outer": outer_area, "holes": hole_area}


def _polygon_area(points: list) -> float:
    """Shoelace formülü"""
    n = len(points)
    if n < 3:
        return 0
    area = 0
    for i in range(n):
        j = (i + 1) % n
        area += points[i].x * points[j].y
        area -= points[j].x * points[i].y
    return area / 2


def _get_bounding_box(msp) -> dict:
    """Tüm geometrinin bounding box'ı"""
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")

    for entity in msp:
        try:
            dxftype = entity.dxftype()
            if dxftype == "LINE":
                for pt in [entity.dxf.start, entity.dxf.end]:
                    min_x = min(min_x, pt[0]); max_x = max(max_x, pt[0])
                    min_y = min(min_y, pt[1]); max_y = max(max_y, pt[1])
            elif dxftype == "CIRCLE":
                cx, cy = entity.dxf.center[:2]
                r = entity.dxf.radius
                min_x = min(min_x, cx - r); max_x = max(max_x, cx + r)
                min_y = min(min_y, cy - r); max_y = max(max_y, cy + r)
            elif dxftype == "LWPOLYLINE":
                for pt in entity.get_points():
                    min_x = min(min_x, pt[0]); max_x = max(max_x, pt[0])
                    min_y = min(min_y, pt[1]); max_y = max(max_y, pt[1])
        except Exception:
            pass

    if min_x == float("inf"):
        return {"x_mm": 0, "y_mm": 0, "area_mm2": 0}

    x = round(max_x - min_x, 4)
    y = round(max_y - min_y, 4)
    return {"x_mm": x, "y_mm": y, "area_mm2": round(x * y, 4)}


def _generate_dxf_warnings(cut_length_mm, bbox, bend_count) -> list:
    warnings = []

    if cut_length_mm == 0:
        warnings.append({
            "code": "NO_GEOMETRY",
            "severity": "high",
            "message": "DXF dosyasında ölçülebilir geometri bulunamadı."
        })

    if bbox.get("x_mm", 0) > 3000 or bbox.get("y_mm", 0) > 1500:
        warnings.append({
            "code": "OVERSIZED_SHEET",
            "severity": "medium",
            "message": "Parça standart sac metal tabla boyutunu aşıyor (3000x1500mm)."
        })

    if bend_count > 12:
        warnings.append({
            "code": "COMPLEX_BENDING",
            "severity": "low",
            "message": f"{bend_count} büküm tespit edildi. Manuel teklif önerilir."
        })

    return warnings
