"""
ML Kalibrasyon Sistemi (Faz-7)
Exponential smoothing ile fiyat düzeltme katsayıları.
"""
import math
from typing import Dict, Any, List, Optional

ALPHA = 0.3  # Smoothing factor
MIN_SAMPLES = 3
CLAMP_MIN = 0.5
CLAMP_MAX = 2.0


def _clamp(value: float, lo: float = CLAMP_MIN, hi: float = CLAMP_MAX) -> float:
    return max(lo, min(hi, value))


def _confidence_score(sample_count: int, std_dev_pct: float) -> int:
    """0-100 confidence score based on sample count and variance."""
    count_score = min(100, sample_count * 20)  # 5 samples = 100
    variance_score = max(0, 100 - int(std_dev_pct * 2))
    return int((count_score + variance_score) / 2)


def compute_calibration_factors(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    CalibrationRecord listesinden düzeltme katsayıları hesaplar.

    records: list of dicts with predicted_unit_price_usd, actual_unit_price_usd, etc.
    """
    valid = [r for r in records if r.get("actual_unit_price_usd") and r.get("predicted_unit_price_usd") and r["actual_unit_price_usd"] > 0]

    if len(valid) < MIN_SAMPLES:
        return {
            "status": "insufficient_data",
            "sample_count": len(valid),
            "min_required": MIN_SAMPLES,
            "factors": None,
        }

    # Sapma oranları
    deviations = []
    for r in valid:
        pred = r["predicted_unit_price_usd"]
        act = r["actual_unit_price_usd"]
        dev = (act - pred) / pred  # positive = underestimating
        deviations.append(dev)

    mean_dev = sum(deviations) / len(deviations)
    std_dev = math.sqrt(sum((d - mean_dev) ** 2 for d in deviations) / len(deviations))

    # Exponential smoothing factor
    smoothed_dev = ALPHA * mean_dev + (1 - ALPHA) * mean_dev  # first iteration

    # Düzeltme katsayıları
    correction = 1.0 + smoothed_dev

    factors = {
        "material_cost_adjust": _clamp(correction),
        "machine_cost_adjust": _clamp(correction * 0.9),  # machine less sensitive
        "setup_cost_adjust": _clamp(1.0),  # setup is fixed
        "margin_adjust": _clamp(correction * 0.95),
    }

    confidence = _confidence_score(len(valid), abs(std_dev) * 100)

    return {
        "status": "calibrated",
        "sample_count": len(valid),
        "mean_deviation_pct": round(mean_dev * 100, 2),
        "std_deviation_pct": round(std_dev * 100, 2),
        "smoothed_deviation": round(smoothed_dev, 4),
        "factors": factors,
        "confidence_score": confidence,
        "confidence_level": "high" if confidence >= 70 else "medium" if confidence >= 40 else "low",
    }


def apply_calibration(base_price: float, factors: Optional[Dict[str, float]]) -> float:
    """Kalibrasyon katsayılarını fiyata uygular."""
    if not factors:
        return base_price
    adjusted = base_price * factors.get("material_cost_adjust", 1.0)
    return round(adjusted, 2)


def calibration_demo() -> Dict[str, Any]:
    """Demo: synthetic veri ile kalibrasyon gösterimi."""
    demo_records = [
        {"predicted_unit_price_usd": 10.0, "actual_unit_price_usd": 11.5},
        {"predicted_unit_price_usd": 8.0, "actual_unit_price_usd": 9.2},
        {"predicted_unit_price_usd": 15.0, "actual_unit_price_usd": 16.8},
        {"predicted_unit_price_usd": 12.0, "actual_unit_price_usd": 13.9},
        {"predicted_unit_price_usd": 9.0, "actual_unit_price_usd": 10.1},
    ]
    result = compute_calibration_factors(demo_records)
    result["demo"] = True
    result["demo_records"] = demo_records
    return result
