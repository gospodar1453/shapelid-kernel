import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

const METALS_DEV_KEY = Deno.env.get("METALS_DEV_API_KEY") || "";

// DB'deki lme_symbol değerleri → metals.dev field adı (fiyatlar mt cinsinden gelir, /1000 → kg)
const LME_SYMBOL_MAP: Record<string, string> = {
  "LME_AL":  "lme_aluminum",   // Alüminyum (die casting, bending, cnc al)
  "LME_CU":  "lme_copper",     // Bakır, pirinç
  "LME_NI":  "lme_nickel",     // Nikel, Inconel
  "LME_ZN":  "lme_zinc",       // Çinko
  "LME_PB":  "lme_lead",       // Kurşun
  "LME_ST":  "lme_aluminum",   // Çelik — LME steel spot yok, Al ile proxy
  "LME_TI":  "lme_aluminum",   // Titanyum — LME'de yok, proxy olarak Al kullan (conservative)
  // Eski format fallback (tire ile)
  "LME-ALU": "lme_aluminum",
  "LME-XCU": "lme_copper",
  "LME-NI":  "lme_nickel",
  "LME-ZN":  "lme_zinc",
  "LME-PB":  "lme_lead",
};

let _cachedRates: Record<string, number> | null = null;
let _cacheTime = 0;
const CACHE_MS = 4 * 60 * 60 * 1000; // 4 saat

async function fetchMetalRatesPerKg(): Promise<Record<string, number>> {
  const now = Date.now();
  if (_cachedRates && now - _cacheTime < CACHE_MS) return _cachedRates;

  const url = `https://api.metals.dev/v1/latest?api_key=${METALS_DEV_KEY}&currency=USD&unit=mt`;
  const res = await fetch(url, { headers: { "Accept": "application/json" } });
  if (!res.ok) throw new Error(`metals.dev HTTP ${res.status}`);
  const data = await res.json();
  if (data.status !== "success") throw new Error(`metals.dev: ${data.error_message || "unknown"}`);

  // mt → kg dönüşümü
  const perKg: Record<string, number> = {};
  for (const [k, v] of Object.entries(data.metals as Record<string, number>)) {
    perKg[k] = v / 1000;
  }
  _cachedRates = perKg;
  _cacheTime = now;
  return perKg;
}

Deno.serve(async (req) => {
  const base44 = createClientFromRequest(req);
  const now = new Date().toISOString();
  const results: any[] = [];
  const alerts: string[] = [];

  // ── Metal fiyatlarını çek ──────────────────────────────────────────
  let rates: Record<string, number> = {};
  let fetchError = "";
  try {
    rates = await fetchMetalRatesPerKg();
  } catch (e: any) {
    fetchError = e.message;
  }

  // ── Tüm MaterialPrice kayıtlarını çek ──────────────────────────────
  let materials: any[] = [];
  try {
    const resp = await base44.asServiceRole.entities.MaterialPrice.list();
    if (Array.isArray(resp)) {
      materials = resp;
    } else if (Array.isArray(resp?.items)) {
      materials = resp.items;
    } else if (Array.isArray(resp?.data)) {
      materials = resp.data;
    }
  } catch (e: any) {
    return Response.json({ success: false, error: `Entity list failed: ${e.message}` }, { status: 500 });
  }

  for (const mat of materials) {
    const id = mat.id ?? mat._id;
    const d = mat.data ?? mat;

    if (!id) {
      results.push({ status: "no_id" });
      continue;
    }

    // Override aktifse dokunma
    if (d.override_active) {
      results.push({ key: d.material_key, status: "skipped_override" });
      continue;
    }

    // LME sembolü yoksa (plastik/resin) — atla
    if (!d.lme_symbol) {
      results.push({ key: d.material_key, status: "no_lme_symbol" });
      continue;
    }

    if (fetchError) {
      results.push({ key: d.material_key, status: "fetch_failed", error: fetchError });
      continue;
    }

    const rateKey = LME_SYMBOL_MAP[d.lme_symbol];
    const lmeCurrent = rateKey ? rates[rateKey] : null;

    if (!lmeCurrent) {
      results.push({
        key: d.material_key,
        status: "symbol_not_found",
        symbol: d.lme_symbol,
        tried_key: rateKey,
      });
      continue;
    }

    // İlk çalışmada referans fiyatı set et
    const lmeRef = d.lme_reference_price || lmeCurrent;
    const deltaPct = ((lmeCurrent - lmeRef) / lmeRef) * 100;

    // Yeni fiyat = base_price × (1 + delta%)
    const newPrice = parseFloat((d.base_price_usd * (1 + deltaPct / 100)).toFixed(4));

    // %5 değişim alerti
    const threshold = d.alert_threshold_pct || 5;
    if (Math.abs(deltaPct) >= threshold) {
      const dir = deltaPct > 0 ? "▲" : "▼";
      alerts.push(
        `⚠️ ${d.material_name}: LME ${dir}${Math.abs(deltaPct).toFixed(1)}% | $${(d.current_price_usd ?? d.base_price_usd).toFixed(4)} → $${newPrice.toFixed(4)}/kg`
      );
    }

    // DB güncelle
    await base44.asServiceRole.entities.MaterialPrice.update(id, {
      lme_current_price: parseFloat(lmeCurrent.toFixed(6)),
      lme_reference_price: parseFloat(lmeRef.toFixed(6)),
      lme_delta_pct: parseFloat(deltaPct.toFixed(2)),
      current_price_usd: newPrice,
      last_lme_fetch: now,
      last_auto_update: now,
    });

    results.push({
      key: d.material_key,
      material: d.material_name,
      status: "updated",
      lme_symbol: d.lme_symbol,
      lme_ref: parseFloat(lmeRef.toFixed(4)),
      lme_now: parseFloat(lmeCurrent.toFixed(4)),
      delta_pct: parseFloat(deltaPct.toFixed(2)),
      old_price: d.current_price_usd ?? d.base_price_usd,
      new_price: newPrice,
    });
  }

  const updated   = results.filter(r => r.status === "updated");
  const noLme     = results.filter(r => r.status === "no_lme_symbol");
  const overrides = results.filter(r => r.status === "skipped_override");
  const failed    = results.filter(r => ["fetch_failed","symbol_not_found","no_id"].includes(r.status));

  return Response.json({
    success: true,
    timestamp: now,
    fetch_error: fetchError || null,
    summary: {
      total: materials.length,
      updated: updated.length,
      no_lme_symbol: noLme.length,
      skipped_override: overrides.length,
      failed: failed.length,
      alerts: alerts.length,
    },
    alerts,
    updated_details: updated,
    failed_details: failed,
  });
});
