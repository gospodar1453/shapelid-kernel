import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

// ─── ENV ────────────────────────────────────────────────────────────────────
const METALS_DEV_KEY = Deno.env.get("METALS_DEV_API_KEY") || "";
const FRED_API_KEY   = Deno.env.get("FRED_API_KEY") || "";

// ─── LME → metals.dev field (fiyatlar /mt gelir → /1000 = kg) ──────────────
// Çelik (LME_ST) ve Titanyum (LME_TI) artık ayrı kaynaklardan çekiliyor
const LME_SYMBOL_MAP: Record<string, string> = {
  "LME_AL": "lme_aluminum",
  "LME_CU": "lme_copper",
  "LME_NI": "lme_nickel",
  "LME_ZN": "lme_zinc",
  "LME_PB": "lme_lead",
  // Eski tire-format fallback
  "LME-ALU": "lme_aluminum",
  "LME-XCU": "lme_copper",
  "LME-NI":  "lme_nickel",
  "LME-ZN":  "lme_zinc",
  "LME-PB":  "lme_lead",
};

// FRED series ID'leri → hangi LME_ST alt kategorisi için
// WPS102 = Hot Rolled Steel (ABD PPI endeksi, USD/100 lbs → kg'a çevriyoruz)
const FRED_SERIES: Record<string, string> = {
  "FRED_STEEL": "WPS102",  // Producer Price Index: Steel Mill Products
};

// Plasticker material codes
const PLASTICKER_CODES: Record<string, string> = {
  "PLAS_ABS":    "ABS",
  "PLAS_PC":     "PC",
  "PLAS_PA6":    "PA 6",
  "PLAS_PA66":   "PA 6.6",
  "PLAS_PP":     "PP",
  "PLAS_HDPE":   "HDPE",
  "PLAS_LDPE":   "LDPE",
  "PLAS_POM":    "POM",
  "PLAS_PET":    "PET",
  "PLAS_PVC":    "PVC",
};

// ─── CACHE ──────────────────────────────────────────────────────────────────
let _lmeRates: Record<string, number> | null = null;
let _lmeCacheTime = 0;
let _fredRates: Record<string, number> | null = null;
let _fredCacheTime = 0;
let _plastickerRates: Record<string, number> | null = null;
let _plastickerCacheTime = 0;
const CACHE_MS = 4 * 60 * 60 * 1000; // 4 saat

// ─── 1. metals.dev LME fiyatları ────────────────────────────────────────────
async function fetchLmeRatesPerKg(): Promise<Record<string, number>> {
  const now = Date.now();
  if (_lmeRates && now - _lmeCacheTime < CACHE_MS) return _lmeRates;

  const url = `https://api.metals.dev/v1/latest?api_key=${METALS_DEV_KEY}&currency=USD&unit=mt`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`metals.dev HTTP ${res.status}`);
  const data = await res.json();
  if (data.status !== "success") throw new Error(`metals.dev: ${data.error_message || "unknown"}`);

  const perKg: Record<string, number> = {};
  for (const [k, v] of Object.entries(data.metals as Record<string, number>)) {
    perKg[k] = v / 1000;
  }
  _lmeRates = perKg;
  _lmeCacheTime = now;
  return perKg;
}

// ─── 2. FRED API — Çelik fiyatı ─────────────────────────────────────────────
// WPS102: PPI Steel Mill Products (Index 1982=100)
// Bu bir endeks, ham fiyat değil. Çelik için USD/ton baz fiyatını
// endeks değişimine göre ayarlamak için kullanıyoruz.
async function fetchFredSteelIndex(): Promise<number | null> {
  const now = Date.now();
  if (_fredRates && now - _fredCacheTime < CACHE_MS) return _fredRates["WPS102"] ?? null;
  if (!FRED_API_KEY) return null;

  try {
    const url = `https://api.stlouisfed.org/fred/series/observations?series_id=WPS102&api_key=${FRED_API_KEY}&sort_order=desc&limit=2&file_type=json`;
    const res = await fetch(url);
    if (!res.ok) return null;
    const data = await res.json();
    const obs = data.observations || [];
    // En son geçerli değeri al (bazı aylar "." olabilir)
    for (const o of obs) {
      const val = parseFloat(o.value);
      if (!isNaN(val)) {
        _fredRates = { "WPS102": val };
        _fredCacheTime = now;
        return val;
      }
    }
  } catch (_) { /* sessizce geç */ }
  return null;
}

// ─── 3. Plasticker.de — Plastik hammadde fiyatları ──────────────────────────
// Plasticker aylık Avrupa spot fiyatlarını HTML sayfada yayınlar
async function fetchPlastickerRates(): Promise<Record<string, number>> {
  const now = Date.now();
  if (_plastickerRates && now - _plastickerCacheTime < CACHE_MS) return _plastickerRates;

  try {
    const url = "https://plasticker.de/preise/pms_en.php?show=ok&region=eu";
    const res = await fetch(url, {
      headers: { "User-Agent": "Mozilla/5.0 (compatible; PriceBot/1.0)" }
    });
    if (!res.ok) return {};
    const html = await res.text();

    // Fiyatları parse et: "ABS  1.95 - 2.10 EUR/kg" formatından orta değeri al
    const rates: Record<string, number> = {};
    // Plasticker'daki tablo satırları: material | low | high EUR/kg
    const rows = html.match(/<tr[^>]*>[\s\S]*?<\/tr>/gi) || [];
    for (const row of rows) {
      // Metin içeriğini çıkar
      const text = row.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
      // "ABS 1.85 2.05" gibi bir pattern ara
      const m = text.match(/^([A-Z][A-Z0-9\s\.\/\-]+?)\s+([\d]+\.[\d]+)\s+([\d]+\.[\d]+)/);
      if (m) {
        const material = m[1].trim();
        const low  = parseFloat(m[2]);
        const high = parseFloat(m[3]);
        if (!isNaN(low) && !isNaN(high)) {
          rates[material] = (low + high) / 2; // Orta değer, EUR/kg
        }
      }
    }

    // EUR → USD (yaklaşık 1.08 sabit, TCMB'den çekilebilir ama basit tutalım)
    const EUR_USD = 1.08;
    const ratesUsd: Record<string, number> = {};
    for (const [k, v] of Object.entries(rates)) {
      ratesUsd[k] = parseFloat((v * EUR_USD).toFixed(4));
    }

    if (Object.keys(ratesUsd).length > 0) {
      _plastickerRates = ratesUsd;
      _plastickerCacheTime = now;
    }
    return ratesUsd;
  } catch (_) {
    return {};
  }
}

// ─── ANA HANDLER ────────────────────────────────────────────────────────────
Deno.serve(async (req) => {
  const base44 = createClientFromRequest(req);
  const now = new Date().toISOString();
  const results: any[] = [];
  const alerts: string[] = [];
  const sources: Record<string, string> = {};

  // Paralel olarak tüm kaynakları çek
  const [lmeRates, fredIndex, plastickerRates] = await Promise.allSettled([
    fetchLmeRatesPerKg(),
    fetchFredSteelIndex(),
    fetchPlastickerRates(),
  ]);

  const lme = lmeRates.status === "fulfilled" ? lmeRates.value : {};
  const fredVal = fredIndex.status === "fulfilled" ? fredIndex.value : null;
  const plasticker = plastickerRates.status === "fulfilled" ? plastickerRates.value : {};

  sources["lme"]        = lmeRates.status === "fulfilled" ? "ok" : (lmeRates.reason?.message || "failed");
  sources["fred"]       = fredIndex.status === "fulfilled" ? (fredVal ? `index=${fredVal}` : "no_key") : "failed";
  sources["plasticker"] = plastickerRates.status === "fulfilled" ? `${Object.keys(plasticker).length} items` : "failed";

  // FRED steel index baz fiyatı: WPS102 indeksi değişimini USD/ton'a çevir
  // Baz: WPS102 ~ 350 index = ~700 USD/ton çelik (2023 ortası referans)
  // Çelik kg fiyatı = (fredVal / 350) * 0.70  (USD/kg)
  let steelPricePerKg: number | null = null;
  if (fredVal) {
    steelPricePerKg = parseFloat(((fredVal / 350) * 0.70).toFixed(4));
    sources["steel_kg"] = `$${steelPricePerKg}/kg (FRED WPS102=${fredVal})`;
  }

  // Tüm MaterialPrice kayıtlarını çek
  let materials: any[] = [];
  try {
    const resp = await base44.asServiceRole.entities.MaterialPrice.list();
    materials = Array.isArray(resp) ? resp
      : Array.isArray(resp?.items) ? resp.items
      : Array.isArray(resp?.data) ? resp.data : [];
  } catch (e: any) {
    return Response.json({ success: false, error: `Entity list failed: ${e.message}` }, { status: 500 });
  }

  for (const mat of materials) {
    const id = mat.id ?? mat._id;
    const d  = mat.data ?? mat;
    if (!id) { results.push({ status: "no_id" }); continue; }
    if (d.override_active) { results.push({ key: d.material_key, status: "skipped_override" }); continue; }
    if (!d.lme_symbol) { results.push({ key: d.material_key, status: "no_lme_symbol" }); continue; }

    let lmeCurrent: number | null = null;
    let priceSource = "";

    // ── Çelik → FRED ────────────────────────────────────────────────────────
    if (d.lme_symbol === "LME_ST" || d.lme_symbol === "STEEL-SC" || d.lme_symbol === "STEEL-RE") {
      if (steelPricePerKg) {
        lmeCurrent = steelPricePerKg;
        priceSource = "fred_wps102";
      } else {
        // FRED yoksa mevcut fiyatı koru
        results.push({ key: d.material_key, status: "fred_unavailable", symbol: d.lme_symbol });
        continue;
      }
    }
    // ── Titanyum → override bekleniyor, geç ─────────────────────────────────
    else if (d.lme_symbol === "LME_TI") {
      results.push({ key: d.material_key, status: "titanium_manual_override_needed" });
      continue;
    }
    // ── Plastik → Plasticker ─────────────────────────────────────────────────
    else if (d.lme_symbol && d.lme_symbol.startsWith("PLAS_")) {
      const plasCode = PLASTICKER_CODES[d.lme_symbol];
      if (plasCode && plasticker[plasCode]) {
        lmeCurrent = plasticker[plasCode];
        priceSource = "plasticker";
      } else {
        results.push({ key: d.material_key, status: "plasticker_not_found", symbol: d.lme_symbol });
        continue;
      }
    }
    // ── Diğer metaller → metals.dev ─────────────────────────────────────────
    else {
      const rateKey = LME_SYMBOL_MAP[d.lme_symbol];
      if (rateKey && lme[rateKey]) {
        lmeCurrent = lme[rateKey];
        priceSource = "metals_dev";
      } else {
        results.push({ key: d.material_key, status: "symbol_not_found", symbol: d.lme_symbol });
        continue;
      }
    }

    // Fiyat hesapla
    const lmeRef   = d.lme_reference_price || lmeCurrent;
    const deltaPct = ((lmeCurrent - lmeRef) / lmeRef) * 100;
    const newPrice = parseFloat((d.base_price_usd * (1 + deltaPct / 100)).toFixed(4));

    // %5 alert
    const threshold = d.alert_threshold_pct || 5;
    if (Math.abs(deltaPct) >= threshold) {
      const dir = deltaPct > 0 ? "▲" : "▼";
      alerts.push(`⚠️ ${d.material_name}: ${priceSource} ${dir}${Math.abs(deltaPct).toFixed(1)}% | $${(d.current_price_usd ?? d.base_price_usd).toFixed(4)} → $${newPrice}/kg`);
    }

    await base44.asServiceRole.entities.MaterialPrice.update(id, {
      lme_current_price:   parseFloat(lmeCurrent.toFixed(6)),
      lme_reference_price: parseFloat(lmeRef.toFixed(6)),
      lme_delta_pct:       parseFloat(deltaPct.toFixed(2)),
      current_price_usd:   newPrice,
      last_lme_fetch:      now,
      last_auto_update:    now,
    });

    results.push({
      key:       d.material_key,
      material:  d.material_name,
      status:    "updated",
      source:    priceSource,
      lme_ref:   parseFloat(lmeRef.toFixed(4)),
      lme_now:   parseFloat(lmeCurrent.toFixed(4)),
      delta_pct: parseFloat(deltaPct.toFixed(2)),
      old_price: d.current_price_usd ?? d.base_price_usd,
      new_price: newPrice,
    });
  }

  const updated   = results.filter(r => r.status === "updated");
  const noLme     = results.filter(r => r.status === "no_lme_symbol");
  const overrides = results.filter(r => r.status === "skipped_override");
  const failed    = results.filter(r => !["updated","no_lme_symbol","skipped_override"].includes(r.status));

  return Response.json({
    success:   true,
    timestamp: now,
    sources,
    summary: {
      total:            materials.length,
      updated:          updated.length,
      no_lme_symbol:    noLme.length,
      skipped_override: overrides.length,
      failed:           failed.length,
      alerts:           alerts.length,
    },
    alerts,
    updated_by_source: {
      metals_dev:  updated.filter(r => r.source === "metals_dev").length,
      fred_steel:  updated.filter(r => r.source === "fred_wps102").length,
      plasticker:  updated.filter(r => r.source === "plasticker").length,
    },
    failed_details: failed,
  });
});
