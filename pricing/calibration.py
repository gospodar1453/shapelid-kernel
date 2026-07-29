"""
ML Kalibrasyon Modülü — Faz-7

Gerçek üretim verileriyle fiyat tahminlerini kalibre eder.

Çalışma prensibi:
  1. Her /analyze çağrısında fiyat tahmini kaydedilir (CalibrationRecord)
  2. Üretim tamamlandığında gerçek maliyet kaydedilir
  3. Sapma analizi: (actual - predicted) / predicted
  4. Düzeltme katsayıları hesaplanır ve engine'e uygulanır

Kalibrasyon katsayıları:
  - material_cost_adjust: malzeme maliyeti düzeltme çarpanı
  - machine_cost_adjust: makine maliyeti düzeltme çarpanı
  - setup_cost_adjust: setup maliyeti düzeltme çarpanı
  - margin_adjust: platform marjı düzeltme çarpanı

Algoritma:
  - Min 3 kayıt gerekli (güven aralığı için)
  - Exponential smoothing: α=0.3 (yeni veri %30 ağırlık)
  - Clamp: [0.5, 2.0] — aşırı düzeltme engellenir
  - Confidence: sample_count ve std_dev'a bağlı
"""

import json
import math
from typing import Dict, Optional, List
from datetime import datetime


# ── Konfigürasyon ────────────────────────────────────────────────────────────

MIN_SAMPLES = 3          # Kalibrasyon için min kayıt
SMOOTHING_ALPHA = 0.3    # Yeni veri ağırlığı (0.3 = %30 yeni, %70 eski)
CLAMP_MIN = 0.5          # Min düzeltme çarpanı
CLAMP_MAX = 2.0          # Max düzeltme çarpanı
CONFIDENCE_THRESHOLD_LOW = 5     # 5'ten az kayıt → low confidence
CONFIDENCE_THRESHOLD_HIGH = 20   # 20+ kayıt → high confidence


def clamp(value: float, lo: float = CLAMP_MIN, hi: float = CLAMP_MAX) -> float:
    """Düzeltme çarpanını güvenli aralığa sıkıştırır."""
    return max(lo, min(hi, value))


def compute_deviation(predicted: float, actual: float) -> dict:
    """
    Tahmin vs gerçek sapma hesabı.
    
    Returns:
        {
            "deviation_pct": float,      # (actual - predicted) / predicted * 100
            "deviation_direction": str,  # "under" | "over" | "exact"
            "ratio": float,              # actual / predicted
        }
    """
    if predicted <= 0:
        return {"deviation_pct": 0.0, "deviation_direction": "exact", "ratio": 1.0}
    
    deviation = (actual - predicted) / predicted * 100
    ratio = actual / predicted
    
    if abs(deviation) < 0.1:
        direction = "exact"
    elif actual > predicted:
        direction = "under"  # Tahmin düşük → yetersiz fiyat
    else:
        direction = "over"  # Tahmin yüksek → fazla fiyat
    
    return {
        "deviation_pct": round(deviation, 2),
        "deviation_direction": direction,
        "ratio": round(ratio, 4),
    }


def compute_calibration_factors(records: List[dict], previous_factors: Optional[dict] = None) -> dict:
    """
    Bir grup CalibrationRecord'dan düzeltme katsayıları hesaplar.
    
    Args:
        records: "produced" status'lu CalibrationRecord listesi
                 Her kayıtta: predicted_unit_price_usd, actual_unit_price_usd,
                             breakdown_snapshot (JSON string)
        previous_factors: Önceki kalibrasyon katsayıları (smoothing için)
    
    Returns:
        {
            "material_cost_adjust": float,
            "machine_cost_adjust": float,
            "setup_cost_adjust": float,
            "margin_adjust": float,
            "sample_count": int,
            "mean_deviation_pct": float,
            "std_deviation_pct": float,
            "confidence_score": float,  # 0-100
        }
    """
    n = len(records)
    
    # Default (kalibrasyon yok)
    default = {
        "material_cost_adjust": 1.0,
        "machine_cost_adjust": 1.0,
        "setup_cost_adjust": 1.0,
        "margin_adjust": 1.0,
        "sample_count": n,
        "mean_deviation_pct": 0.0,
        "std_deviation_pct": 0.0,
        "confidence_score": 0.0,
    }
    
    if n < MIN_SAMPLES:
        return default
    
    deviations = []
    material_ratios = []
    machine_ratios = []
    setup_ratios = []
    
    for rec in records:
        predicted = rec.get("predicted_unit_price_usd", 0)
        actual = rec.get("actual_unit_price_usd", 0)
        
        if predicted <= 0 or actual <= 0:
            continue
        
        dev = compute_deviation(predicted, actual)
        deviations.append(dev["deviation_pct"])
        
        # Breakdown'dan bileşen oranlarını çıkar
        try:
            bd = json.loads(rec.get("breakdown_snapshot", "{}"))
            pred_material = bd.get("material_cost", 0)
            pred_machine = bd.get("machine_cost", 0)
            pred_setup = bd.get("setup_cost", 0)
            pred_total = predicted
            
            # Oran: actual'ın bileşenlere nasıl dağıldığını tahmin et
            # Basit model: toplam sapmayı bileşenlere orantılı dağıt
            total_ratio = actual / predicted
            if pred_material > 0:
                material_ratios.append(total_ratio)
            if pred_machine > 0:
                machine_ratios.append(total_ratio)
            if pred_setup > 0:
                setup_ratios.append(total_ratio)
        except (json.JSONDecodeError, TypeError):
            pass
    
    if not deviations:
        return default
    
    # İstatistik
    mean_dev = sum(deviations) / len(deviations)
    variance = sum((d - mean_dev) ** 2 for d in deviations) / len(deviations)
    std_dev = math.sqrt(variance)
    
    # Ham düzeltme çarpanları
    # Eğer ortalama sapma +%20 (tahmin düşük) → çarpan 1.20 olmalı
    raw_material = 1.0 + (mean_dev / 100)
    raw_machine = 1.0 + (mean_dev / 100)
    raw_setup = 1.0 + (mean_dev / 100) * 0.5  # Setup'a %50 daha az düzeltme (sabit maliyet)
    raw_margin = 1.0  # Marj düzeltmesi şu ankapalı
    
    # Exponential smoothing
    alpha = SMOOTHING_ALPHA
    if previous_factors:
        prev = previous_factors
        material_adjust = alpha * raw_material + (1 - alpha) * prev.get("material_cost_adjust", 1.0)
        machine_adjust = alpha * raw_machine + (1 - alpha) * prev.get("machine_cost_adjust", 1.0)
        setup_adjust = alpha * raw_setup + (1 - alpha) * prev.get("setup_cost_adjust", 1.0)
        margin_adjust = alpha * raw_margin + (1 - alpha) * prev.get("margin_adjust", 1.0)
    else:
        material_adjust = raw_material
        machine_adjust = raw_machine
        setup_adjust = raw_setup
        margin_adjust = raw_margin
    
    # Clamp
    material_adjust = clamp(material_adjust)
    machine_adjust = clamp(machine_adjust)
    setup_adjust = clamp(setup_adjust)
    margin_adjust = clamp(margin_adjust, 0.8, 1.5)  # Marj için daha dar aralık
    
    # Confidence skoru
    if n >= CONFIDENCE_THRESHOLD_HIGH:
        confidence = 90.0 - min(30.0, std_dev)  # Yüksek std_dev → düşük confidence
    elif n >= CONFIDENCE_THRESHOLD_LOW:
        confidence = 60.0 - min(20.0, std_dev)
    else:
        confidence = 30.0 - min(15.0, std_dev)
    
    confidence = max(0.0, min(100.0, confidence))
    
    return {
        "material_cost_adjust": round(material_adjust, 4),
        "machine_cost_adjust": round(machine_adjust, 4),
        "setup_cost_adjust": round(setup_adjust, 4),
        "margin_adjust": round(margin_adjust, 4),
        "sample_count": n,
        "mean_deviation_pct": round(mean_dev, 2),
        "std_deviation_pct": round(std_dev, 2),
        "confidence_score": round(confidence, 1),
    }


def apply_calibration(pricing: dict, factors: dict) -> dict:
    """
    Hesaplanan fiyatı kalibrasyon katsayılarıyla düzeltir.
    
    Engine.py'de calculate_price() sonrası çağrılır.
    """
    if not factors:
        return pricing
    
    bd = pricing.get("breakdown", {})
    
    # Bileşenleri düzelt
    orig_material = bd.get("material_cost", 0)
    orig_machine = bd.get("machine_cost", 0)
    orig_setup = bd.get("setup_cost", 0)
    
    adj_material = orig_material * factors.get("material_cost_adjust", 1.0)
    adj_machine = orig_machine * factors.get("machine_cost_adjust", 1.0)
    adj_setup = orig_setup * factors.get("setup_cost_adjust", 1.0)
    
    bd["material_cost"] = round(adj_material, 4)
    bd["machine_cost"] = round(adj_machine, 4)
    bd["setup_cost"] = round(adj_setup, 4)
    bd["calibration_applied"] = True
    bd["calibration_factors"] = {
        "material": factors.get("material_cost_adjust", 1.0),
        "machine": factors.get("machine_cost_adjust", 1.0),
        "setup": factors.get("setup_cost_adjust", 1.0),
        "confidence": factors.get("confidence_score", 0),
        "samples": factors.get("sample_count", 0),
    }
    
    # Toplam fiyatı yeniden hesapla
    # Fiyat formülü: (material + machine + setup + post_process + risk) / (1 - margin)
    # Margin sabit (28%) — margin_adjust şu an kapalı
    margin_pct = bd.get("platform_margin_pct", 28.0) / 100.0
    
    new_subtotal = adj_material + adj_machine + adj_setup + bd.get("post_process_cost", 0) + bd.get("risk_premium", 0)
    new_unit_price = new_subtotal / (1 - margin_pct)
    
    pricing["unit_price"] = round(new_unit_price, 2)
    pricing["total_price"] = round(new_unit_price * pricing.get("quantity", 1), 2)
    pricing["breakdown"] = bd
    pricing["calibrated"] = True
    
    return pricing


def geometry_fingerprint(geometry: dict) -> str:
    """
    Geometri için kısa fingerprint üretir.
    Aynı parça tekrar yüklendiğinde eşleştirme için.
    """
    parts = [
        f"v{geometry.get('volume_cm3', 0):.2f}",
        f"s{geometry.get('surface_area_cm2', 0):.2f}",
        f"b{geometry.get('bounding_box', {}).get('x', 0):.0f}x{geometry.get('bounding_box', {}).get('y', 0):.0f}x{geometry.get('bounding_box', {}).get('z', 0):.0f}",
        f"t{geometry.get('technology', '')}",
    ]
    return "_".join(parts)
