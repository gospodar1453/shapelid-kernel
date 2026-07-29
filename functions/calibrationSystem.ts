/**
 * ML Kalibrasyon Backend Function — Faz-7
 * 
 * İki fonksiyon:
 * 1. logCalibrationPrediction: kernelAnalyze çağrıldığında tahmini kaydeder
 * 2. runCalibration: produced kayıtları analiz edip faktör hesaplar
 */

import { base44 } from '@base44/core';

/**
 * Bir fiyat tahminini CalibrationRecord olarak kaydeder.
 * kernelAnalyze çağrıldıktan sonra bu fonksiyon çağrılır.
 */
export async function logCalibrationPrediction(data: {
  technology: string;
  material: string;
  quantity: number;
  predicted_unit_price_usd: number;
  predicted_total_price_usd: number;
  volume_cm3: number;
  print_time_min: number;
  breakdown_snapshot: string;  // JSON string
  geometry_fingerprint: string;
}) {
  try {
    const record = await base44.entities.CalibrationRecord.create({
      technology: data.technology,
      material: data.material,
      quantity: data.quantity,
      predicted_unit_price_usd: data.predicted_unit_price_usd,
      predicted_total_price_usd: data.predicted_total_price_usd,
      volume_cm3: data.volume_cm3,
      print_time_min: data.print_time_min,
      breakdown_snapshot: data.breakdown_snapshot,
      geometry_fingerprint: data.geometry_fingerprint,
      status: "predicted",
    });
    return { success: true, record_id: record.id };
  } catch (error) {
    console.error("Calibration prediction log error:", error);
    return { success: false, error: error.message };
  }
}

/**
 * Gerçek üretim maliyetini günceller — sipariş tamamlandığında çağrılır.
 */
export async function updateActualPrice(record_id: string, actual_unit_price_usd: number, actual_total_price_usd?: number, supplier_name?: string, production_notes?: string) {
  try {
    // Sapma hesabı
    const records = await base44.entities.CalibrationRecord.read({
      filter: { id: record_id },
      limit: 1,
    });
    
    if (records.length === 0) {
      return { success: false, error: "Record not found" };
    }
    
    const rec = records[0];
    const predicted = rec.predicted_unit_price_usd || 0;
    const deviation_pct = predicted > 0 ? ((actual_unit_price_usd - predicted) / predicted) * 100 : 0;
    const deviation_direction = Math.abs(deviation_pct) < 0.1 ? "exact" : (actual_unit_price_usd > predicted ? "under" : "over");
    
    const updated = await base44.entities.CalibrationRecord.update(record_id, {
      actual_unit_price_usd,
      actual_total_price_usd: actual_total_price_usd || actual_unit_price_usd * (rec.quantity || 1),
      deviation_pct,
      deviation_direction,
      status: "produced",
      supplier_name,
      production_notes,
    });
    
    return { success: true, deviation_pct, deviation_direction };
  } catch (error) {
    console.error("Update actual price error:", error);
    return { success: false, error: error.message };
  }
}

/**
 * Kalibrasyon çalıştırır — produced status'lu kayıtları analiz eder.
 * Teknoloji + malzeme bazında düzeltme katsayıları hesaplar.
 */
export async function runCalibration() {
  try {
    // Tüm produced kayıtları çek
    const records = await base44.entities.CalibrationRecord.read({
      filter: { status: "produced" },
      limit: 500,
    });
    
    if (records.length === 0) {
      return { success: true, message: "No produced records for calibration", groups: [] };
    }
    
    // Teknoloji + malzeme bazında grupla
    const groups: Record<string, any[]> = {};
    for (const rec of records) {
      const key = `${rec.technology}_${rec.material}`;
      if (!groups[key]) groups[key] = [];
      groups[key].push(rec);
    }
    
    // Mevcut faktörleri çek
    const existingFactors = await base44.entities.CalibrationFactor.read({
      filter: { is_active: true },
      limit: 100,
    });
    
    const factorMap: Record<string, any> = {};
    for (const f of existingFactors) {
      factorMap[f.tech_material_key] = f;
    }
    
    // Her grup için kalibrasyon hesapla
    const results = [];
    for (const [key, groupRecords] of Object.entries(groups)) {
      const [technology, material] = key.split("_");
      
      // Kernel'a gönder (sentetik endpoint yerine lokal hesap)
      const factors = computeFactorsLocal(groupRecords, factorMap[key]);
      
      // DB'ye kaydet/güncelle
      if (factors.sample_count >= 3) {
        if (factorMap[key]) {
          // Update
          await base44.entities.CalibrationFactor.update(factorMap[key].id, {
            material_cost_adjust: factors.material_cost_adjust,
            machine_cost_adjust: factors.machine_cost_adjust,
            setup_cost_adjust: factors.setup_cost_adjust,
            margin_adjust: factors.margin_adjust,
            sample_count: factors.sample_count,
            mean_deviation_pct: factors.mean_deviation_pct,
            std_deviation_pct: factors.std_deviation_pct,
            confidence_score: factors.confidence_score,
            last_calibrated: new Date().toISOString(),
          });
        } else {
          // Create
          await base44.entities.CalibrationFactor.create({
            tech_material_key: key,
            technology,
            material,
            material_cost_adjust: factors.material_cost_adjust,
            machine_cost_adjust: factors.machine_cost_adjust,
            setup_cost_adjust: factors.setup_cost_adjust,
            margin_adjust: factors.margin_adjust,
            sample_count: factors.sample_count,
            mean_deviation_pct: factors.mean_deviation_pct,
            std_deviation_pct: factors.std_deviation_pct,
            confidence_score: factors.confidence_score,
            last_calibrated: new Date().toISOString(),
            is_active: true,
          });
        }
      }
      
      results.push({
        tech_material_key: key,
        technology,
        material,
        ...factors,
      });
    }
    
    return {
      success: true,
      total_records: records.length,
      groups_calibrated: results.filter(r => r.sample_count >= 3).length,
      results,
    };
  } catch (error) {
    console.error("Calibration run error:", error);
    return { success: false, error: error.message };
  }
}

/**
 * Aktif kalibrasyon faktörlerini döndürür — kernelAnalyze bunu kernel'a paslar.
 */
export async function getActiveCalibrationFactors() {
  try {
    const factors = await base44.entities.CalibrationFactor.read({
      filter: { is_active: true },
      limit: 100,
    });
    
    const factorMap: Record<string, any> = {};
    for (const f of factors) {
      factorMap[f.tech_material_key] = {
        material_cost_adjust: f.material_cost_adjust || 1.0,
        machine_cost_adjust: f.machine_cost_adjust || 1.0,
        setup_cost_adjust: f.setup_cost_adjust || 1.0,
        margin_adjust: f.margin_adjust || 1.0,
        sample_count: f.sample_count || 0,
        confidence_score: f.confidence_score || 0,
      };
    }
    
    return { success: true, factors: factorMap };
  } catch (error) {
    return { success: false, error: error.message, factors: {} };
  }
}

// ── Lokal faktör hesaplama (kernel ile aynı algoritma) ──
function computeFactorsLocal(records: any[], previous?: any) {
  const MIN_SAMPLES = 3;
  const SMOOTHING_ALPHA = 0.3;
  const CLAMP_MIN = 0.5;
  const CLAMP_MAX = 2.0;
  
  const n = records.length;
  if (n < MIN_SAMPLES) {
    return {
      material_cost_adjust: 1.0, machine_cost_adjust: 1.0,
      setup_cost_adjust: 1.0, margin_adjust: 1.0,
      sample_count: n, mean_deviation_pct: 0,
      std_deviation_pct: 0, confidence_score: 0,
    };
  }
  
  const deviations: number[] = [];
  for (const rec of records) {
    const predicted = rec.predicted_unit_price_usd || 0;
    const actual = rec.actual_unit_price_usd || 0;
    if (predicted > 0 && actual > 0) {
      deviations.push(((actual - predicted) / predicted) * 100);
    }
  }
  
  if (deviations.length === 0) {
    return {
      material_cost_adjust: 1.0, machine_cost_adjust: 1.0,
      setup_cost_adjust: 1.0, margin_adjust: 1.0,
      sample_count: n, mean_deviation_pct: 0,
      std_deviation_pct: 0, confidence_score: 0,
    };
  }
  
  const meanDev = deviations.reduce((a, b) => a + b, 0) / deviations.length;
  const variance = deviations.reduce((sum, d) => sum + Math.pow(d - meanDev, 2), 0) / deviations.length;
  const stdDev = Math.sqrt(variance);
  
  const rawMaterial = 1.0 + (meanDev / 100);
  const rawMachine = 1.0 + (meanDev / 100);
  const rawSetup = 1.0 + (meanDev / 100) * 0.5;
  
  const clamp = (v: number, lo = CLAMP_MIN, hi = CLAMP_MAX) => Math.max(lo, Math.min(hi, v));
  
  let matAdj, machAdj, setupAdj, marginAdj;
  if (previous) {
    matAdj = SMOOTHING_ALPHA * rawMaterial + (1 - SMOOTHING_ALPHA) * (previous.material_cost_adjust || 1.0);
    machAdj = SMOOTHING_ALPHA * rawMachine + (1 - SMOOTHING_ALPHA) * (previous.machine_cost_adjust || 1.0);
    setupAdj = SMOOTHING_ALPHA * rawSetup + (1 - SMOOTHING_ALPHA) * (previous.setup_cost_adjust || 1.0);
    marginAdj = 1.0;
  } else {
    matAdj = rawMaterial;
    machAdj = rawMachine;
    setupAdj = rawSetup;
    marginAdj = 1.0;
  }
  
  let confidence = 0;
  if (n >= 20) confidence = 90 - Math.min(30, stdDev);
  else if (n >= 5) confidence = 60 - Math.min(20, stdDev);
  else confidence = 30 - Math.min(15, stdDev);
  confidence = Math.max(0, Math.min(100, confidence));
  
  return {
    material_cost_adjust: Math.round(clamp(matAdj) * 10000) / 10000,
    machine_cost_adjust: Math.round(clamp(machAdj) * 10000) / 10000,
    setup_cost_adjust: Math.round(clamp(setupAdj) * 10000) / 10000,
    margin_adjust: Math.round(clamp(marginAdj, 0.8, 1.5) * 10000) / 10000,
    sample_count: n,
    mean_deviation_pct: Math.round(meanDev * 100) / 100,
    std_deviation_pct: Math.round(stdDev * 100) / 100,
    confidence_score: Math.round(confidence * 10) / 10,
  };
}
