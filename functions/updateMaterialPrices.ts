import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

const METALS_DEV_KEY = Deno.env.get("METALS_DEV_API_KEY") || "";

// LME sembol → metals.dev response alanı eşleşmesi
const LME_TO_METALS_DEV: Record<string, string> = {
  "LME-ALU":  "lme_aluminum",
  "LME-XCU":  "lme_copper",
  "LME-NI":   "lme_nickel",
  "STEEL-SC": "lme_aluminum",  // Çelik için LME Alüminyum proxy (yeterince korelasyonlu)
  "STEEL-RE": "lme_aluminum",
};

let _cachedRates: Record<string, number> | null = null;
let _cacheTime = 0;
const CACHE_MS = 4 * 60 * 60 * 1000; // 4 saat

async function fetchAllMetalRates(): Promise<Record<string, number>> {
  const now = Date.now();
  if (_cachedRates && now - _cacheTime < CACHE_MS) return _cachedRates;

  const url = `https://api.metals.dev/v1/latest?api_key=${METALS_DEV_KEY}&currency=USD&unit=kg`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`metals.dev HTTP ${res.status}`);
  const data = await res.json();
  if (data.status !== "success") throw new Error(`metals.dev: ${data.error_message}`);

  _cachedRates = data.metals as Record<string, number>;
  _cacheTime = now;
  return _cachedRates;
}

Deno.serve(async (req) => {
  const base44 = createClientFromRequest(req);
  const now = new Date().toISOString();
  const results: any[] = [];
  const alerts: string[] = [];

  // Tüm metal fiyatlarını tek seferde çek
  let rates: Record<string, number> = {};
  let fetchError = "";
  try {
    rates = await fetchAllMetalRates();
  } catch (e: any) {
    fetchError = e.message;
  }

  // Tüm malzeme kayıtlarını çek
  const materials = await base44.asServiceRole.entities.MaterialPrice.list();

  for (const mat of materials) {
    const d = mat.data;

    // Override aktifse dokunma
    if (d.override_active) {
      results.push({ key: d.material_key, status: "skipped_override" });
      continue;
    }

    // LME sembolü yoksa (plastik/resin) — şimdilik atla
    if (!d.lme_symbol) {
      results.push({ key: d.material_key, status: "no_lme_symbol" });
      continue;
    }

    if (fetchError) {
      results.push({ key: d.material_key, status: "fetch_failed", error: fetchError });
      continue;
    }

    const rateKey = LME_TO_METALS_DEV[d.lme_symbol];
    const lmeCurrent = rateKey ? rates[rateKey] : null;

    if (!lmeCurrent) {
      results.push({ key: d.material_key, status: "symbol_not_found", symbol: d.lme_symbol });
      continue;
    }

    // İlk çalışmada referansı kaydet
    const lmeRef = d.lme_reference_price || lmeCurrent;
    const deltaPct = ((lmeCurrent - lmeRef) / lmeRef) * 100;

    // Yeni fiyat = base_price * (1 + delta%) + buffer
    const bufferFactor = 1 + (d.material_buffer_pct || 6) / 100;
    const newPrice = parseFloat(
      (d.base_price_usd * (1 + deltaPct / 100) * bufferFactor).toFixed(4)
    );

    // Alert threshold kontrolü
    const threshold = d.alert_threshold_pct || 5;
    const absDelta = Math.abs(deltaPct);
    if (absDelta >= threshold) {
      const dir = deltaPct > 0 ? "▲" : "▼";
      alerts.push(
        `⚠️ ${d.material_name}: LME ${dir}${absDelta.toFixed(1)}% değişti → ${(d.current_price_usd || d.base_price_usd).toFixed(4)} → ${newPrice.toFixed(4)} USD/kg`
      );
    }

    // DB'yi güncelle
    await base44.asServiceRole.entities.MaterialPrice.update(mat.id, {
      lme_current_price: lmeCurrent,
      lme_reference_price: lmeRef,
      lme_delta_pct: parseFloat(deltaPct.toFixed(2)),
      current_price_usd: newPrice,
      last_lme_fetch: now,
      last_auto_update: now,
    });

    results.push({
      key: d.material_key,
      status: "updated",
      lme_ref: lmeRef,
      lme_current: lmeCurrent,
      delta_pct: parseFloat(deltaPct.toFixed(2)),
      new_price_usd: newPrice,
    });
  }

  return Response.json({
    success: true,
    timestamp: now,
    fetch_error: fetchError || null,
    updated: results.filter(r => r.status === "updated").length,
    skipped_override: results.filter(r => r.status === "skipped_override").length,
    no_lme: results.filter(r => r.status === "no_lme_symbol").length,
    alerts,
    details: results,
  });
});
