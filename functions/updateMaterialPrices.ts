/**
 * updateMaterialPrices — Shapelid MaterialPrice Günlük Fiyat Güncelleyici
 *
 * Kaynaklar:
 *   metals.dev   → Al, Cu, Ni, Zn, Pb (LME spot, USD/kg)   — 1 istek/gün, 100/ay free
 *   Yahoo Finance → HRC Steel futures (USD/short_ton)        — ücretsiz, sınırsız
 *   Yahoo Finance → Brent crude (USD/barrel)                 — plastik model için
 *   TCMB XML     → USD/TRY kuru (referans, gerekirse)        — ücretsiz, sınırsız
 *
 * Çelik modeli:
 *   Yapısal çelik (S235/S355/mild)  = HRC_per_kg × 1.20  (Türkiye marjı)
 *   Galvanized                       = HRC_per_kg × 1.28
 *   SS304 (paslanmaz)                = HRC_per_kg × 1.30 + 0.08 × Ni_per_kg × 1.5
 *   SS316                            = SS304 + 0.02 × Mo_proxy × 1.5
 *   Takım çelikleri (1.2738/1.2709)  = HRC_per_kg × 2.8–4.5 (sabit katsayı)
 *
 * Plastik modeli (Brent bazlı):
 *   fiyat = (base_coeff × brent + fixed_base) × tr_markup
 *   Brent $80 referans; katsayılar piyasa ortalamasına göre kalibre edildi
 */

import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

const METALS_DEV_KEY = Deno.env.get("METALS_DEV_API_KEY") || "";
const YF_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36";
const CACHE_MS = 4 * 60 * 60 * 1000; // 4 saat

// ─── Cache ──────────────────────────────────────────────────────────────────
let _lmeCache: { rates: Record<string, number>; ts: number } | null = null;
let _yfCache:  { hrc: number; brent: number; ts: number } | null = null;

// ─── 1. metals.dev — Al/Cu/Ni/Zn/Pb ────────────────────────────────────────
async function fetchLme(): Promise<Record<string, number>> {
  const now = Date.now();
  if (_lmeCache && now - _lmeCache.ts < CACHE_MS) return _lmeCache.rates;

  const url = `https://api.metals.dev/v1/latest?api_key=${METALS_DEV_KEY}&currency=USD&unit=mt`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`metals.dev HTTP ${res.status}`);
  const data = await res.json();
  if (data.status !== "success") throw new Error(`metals.dev: ${data.error_message}`);

  const rates: Record<string, number> = {};
  for (const [k, v] of Object.entries(data.metals as Record<string, number>)) {
    rates[k] = v / 1000; // /mt → /kg
  }
  _lmeCache = { rates, ts: now };
  return rates;
}

// ─── 2. Yahoo Finance — HRC Steel + Brent ────────────────────────────────────
async function fetchYahoo(): Promise<{ hrc: number; brent: number }> {
  const now = Date.now();
  if (_yfCache && now - _yfCache.ts < CACHE_MS) return _yfCache;

  async function yfGet(sym: string): Promise<number> {
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${sym}?interval=1d&range=2d`;
    const res = await fetch(url, { headers: { "User-Agent": YF_UA } });
    if (!res.ok) throw new Error(`Yahoo ${sym} HTTP ${res.status}`);
    const d = await res.json();
    const price = d?.chart?.result?.[0]?.meta?.regularMarketPrice;
    if (!price) throw new Error(`Yahoo ${sym}: no price`);
    return price;
  }

  const [hrcRaw, brent] = await Promise.all([yfGet("HRC=F"), yfGet("BZ=F")]);
  const hrc = hrcRaw / 907.185; // USD/short_ton → USD/kg
  _yfCache = { hrc, brent, ts: now };
  return { hrc, brent };
}

// ─── Çelik fiyat modeli ──────────────────────────────────────────────────────
function steelPrice(materialKey: string, hrc: number, ni: number): number | null {
  const key = materialKey.toLowerCase();

  // Yapısal / mild çelik
  if (/mild_steel|s235|s355|1\.0038|1\.0570|1\.0330|1\.0511|structural|galvanized|galvanised/.test(key)) {
    const base = hrc * 1.20; // %20 Türkiye marjı
    if (/galvan/.test(key)) return base * 1.07; // galvaniz kaplama ek maliyet
    return base;
  }

  // Paslanmaz 304 serisi (8% Ni içeriği)
  if (/ss304|304l?|1\.4301|1\.4307|x5crni|x2crni(?!mo)|303|1\.4305/.test(key)) {
    return hrc * 1.30 + 0.08 * ni * 1.5;
  }

  // Paslanmaz 316 serisi (10% Ni + 2% Mo)
  if (/ss316|316l?|1\.4401|1\.4404|1\.4571|x5crnimo|x2crnimo|v4a/.test(key)) {
    const ss304 = hrc * 1.30 + 0.08 * ni * 1.5;
    const mo_proxy = 25.0; // Mo ~$25/kg sabit (LME'de yok)
    return ss304 + 0.025 * mo_proxy * 1.5;
  }

  // Takım çelikleri (1.2738 plastik kalıp, 1.2709 maraging)
  if (/1\.2738|1\.2709|maraging|tool_steel|mold_steel|ms1/.test(key)) {
    return hrc * 3.5;
  }

  // Alaşımlı çelik (25CrMo4, 42CrMo4, 4130, C45)
  if (/4130|c45|25crmo|42crmo|1\.7218|1\.7225|1\.0503|alloy_steel/.test(key)) {
    return hrc * 1.60;
  }

  // "Any available" fallback
  if (/any_available/.test(key)) {
    if (/stainless/.test(key)) return hrc * 1.30 + 0.08 * ni * 1.5;
    return hrc * 1.20;
  }

  return null; // eşleşme yok
}

// ─── Plastik fiyat modeli (Brent bazlı) ─────────────────────────────────────
// Katsayılar Türkiye ithalat fiyatlarına (~Brent $80 referans) göre kalibre edildi
const PLASTIC_MODEL: Record<string, { coeff: number; base: number; markup: number }> = {
  // Temel poliolefinler
  "pp":          { coeff: 0.012, base: 0.85, markup: 1.25 },
  "hdpe":        { coeff: 0.013, base: 0.90, markup: 1.25 },
  "ldpe":        { coeff: 0.012, base: 0.85, markup: 1.25 },
  "lldpe":       { coeff: 0.012, base: 0.88, markup: 1.25 },
  "pet":         { coeff: 0.011, base: 0.80, markup: 1.20 },
  "pvc":         { coeff: 0.010, base: 0.75, markup: 1.20 },
  "ps":          { coeff: 0.014, base: 0.95, markup: 1.30 },
  "hips":        { coeff: 0.015, base: 1.00, markup: 1.30 },
  // Mühendislik plastikleri
  "abs":         { coeff: 0.018, base: 1.25, markup: 1.35 },
  "pc":          { coeff: 0.022, base: 1.65, markup: 1.40 },
  "pmma":        { coeff: 0.020, base: 1.50, markup: 1.38 },
  "acrylic":     { coeff: 0.020, base: 1.50, markup: 1.38 },
  "pom":         { coeff: 0.020, base: 1.50, markup: 1.45 },
  "delrin":      { coeff: 0.020, base: 1.50, markup: 1.45 },
  "pbt":         { coeff: 0.018, base: 1.35, markup: 1.38 },
  "pet_gf":      { coeff: 0.016, base: 1.20, markup: 1.35 },
  "nylon6":      { coeff: 0.016, base: 1.60, markup: 1.40 }, // Caprolactam türevi
  "pa6":         { coeff: 0.016, base: 1.60, markup: 1.40 },
  "nylon66":     { coeff: 0.018, base: 1.80, markup: 1.42 },
  "pa66":        { coeff: 0.018, base: 1.80, markup: 1.42 },
  "pa6_gf":      { coeff: 0.015, base: 1.90, markup: 1.38 },
  "tpe":         { coeff: 0.020, base: 2.00, markup: 1.40 },
  "tpu":         { coeff: 0.022, base: 2.20, markup: 1.42 },
  "tpv":         { coeff: 0.018, base: 1.80, markup: 1.38 },
  "tpe_elastomer": { coeff: 0.020, base: 2.00, markup: 1.40 },
  // Yüksek performans
  "pps":         { coeff: 0.025, base: 4.50, markup: 1.30 },
  "pei":         { coeff: 0.030, base: 22.0, markup: 1.15 },
  "ultem":       { coeff: 0.030, base: 22.0, markup: 1.15 },
  "peek":        { coeff: 0.050, base: 60.0, markup: 1.10 },
  "pc_abs":      { coeff: 0.020, base: 1.45, markup: 1.38 },
  "pc_pbt":      { coeff: 0.021, base: 1.55, markup: 1.38 },
  "pc_pmma":     { coeff: 0.021, base: 1.55, markup: 1.38 },
  // 3D baskı filamentleri (premium, filament fiyatı granülden ~3-5× pahalı)
  "pla":         { coeff: 0.012, base: 1.20, markup: 3.50 },
  "petg":        { coeff: 0.013, base: 1.10, markup: 3.20 },
  "asa":         { coeff: 0.018, base: 1.35, markup: 3.50 },
  "abs_fusion":  { coeff: 0.018, base: 1.30, markup: 3.50 },
  "abs_esd":     { coeff: 0.018, base: 1.35, markup: 4.00 },
  "peek_like":   { coeff: 0.045, base: 55.0, markup: 1.15 },
  "tpu_flex":    { coeff: 0.022, base: 2.50, markup: 3.80 },
  "uhmwpe":      { coeff: 0.013, base: 1.10, markup: 2.80 },
  // Resinler (SLA/DLP) — petrol bazlı ama çok daha az korelasyon, yüksek sabit baz
  "standard_resin":    { coeff: 0.010, base: 22.0, markup: 1.10 },
  "standard_black":    { coeff: 0.010, base: 22.0, markup: 1.10 },
  "standard_grey":     { coeff: 0.010, base: 22.0, markup: 1.10 },
  "standard_white":    { coeff: 0.010, base: 22.0, markup: 1.10 },
  "standard_transparent": { coeff: 0.010, base: 24.0, markup: 1.10 },
  "photopolymer":      { coeff: 0.010, base: 22.0, markup: 1.10 },
  "rubber_like":       { coeff: 0.012, base: 28.0, markup: 1.10 },
  "castable":          { coeff: 0.010, base: 35.0, markup: 1.10 },
  // Vacuum casting resinleri
  "pr700":    { coeff: 0.005, base: 17.0, markup: 1.05 },
  "pr2000":   { coeff: 0.005, base: 19.0, markup: 1.05 },
  "pra794":   { coeff: 0.005, base: 18.0, markup: 1.05 },
  "prf100":   { coeff: 0.005, base: 21.0, markup: 1.05 },
  "prc1819":  { coeff: 0.005, base: 23.0, markup: 1.05 },
  "pr777":    { coeff: 0.005, base: 14.0, markup: 1.05 },
  // SLS/MJF tozları
  "pa12":     { coeff: 0.018, base: 50.0, markup: 1.20 },
  "pa11":     { coeff: 0.020, base: 55.0, markup: 1.20 },
  "nylon12":  { coeff: 0.018, base: 50.0, markup: 1.20 },
  "nylon11":  { coeff: 0.020, base: 55.0, markup: 1.20 },
  "pa12_gf":  { coeff: 0.015, base: 55.0, markup: 1.15 },
};

function plasticPrice(materialKey: string, brent: number): number | null {
  const key = materialKey.toLowerCase().replace(/[^a-z0-9_]/g, "_").replace(/_+/g, "_");
  const calc = (m: { coeff: number; base: number; markup: number }) =>
    parseFloat(((m.coeff * brent + m.base) * m.markup).toFixed(4));
  if (/pa12|pa_12|nylon_?12/.test(key)) return calc({ coeff: 0.018, base: 50.0, markup: 1.20 });
  if (/pa11|pa_11|nylon_?11/.test(key)) return calc({ coeff: 0.020, base: 55.0, markup: 1.20 });
  if (/nylon_?6(?!6)|pa_?6(?!6|_gf|cf)/.test(key)) return calc({ coeff: 0.016, base: 1.60, markup: 1.40 });
  if (/nylon_?66|pa_?66/.test(key))                  return calc({ coeff: 0.018, base: 1.80, markup: 1.42 });
  if (/pa6_?gf|pa_?6.*gf/.test(key))                 return calc({ coeff: 0.015, base: 1.90, markup: 1.38 });
  if (key.includes("peek_like"))  return calc({ coeff: 0.045, base: 55.0, markup: 1.15 });
  if (key.includes("peek"))       return calc({ coeff: 0.050, base: 60.0, markup: 1.10 });
  if (key.includes("pei") || key.includes("ultem")) return calc({ coeff: 0.030, base: 22.0, markup: 1.15 });
  if (key.includes("pps"))        return calc({ coeff: 0.025, base: 4.50, markup: 1.30 });
  if (key.includes("petg"))       return calc({ coeff: 0.013, base: 1.10, markup: 3.20 });
  if (key.includes("pet"))        return calc({ coeff: 0.011, base: 0.80, markup: 1.20 });
  if (key.includes("pc_abs"))     return calc({ coeff: 0.020, base: 1.45, markup: 1.38 });
  if (key.includes("pc_pbt"))     return calc({ coeff: 0.021, base: 1.55, markup: 1.38 });
  if (key.includes("pc_pmma"))    return calc({ coeff: 0.021, base: 1.55, markup: 1.38 });
  if (key.includes("pc"))         return calc({ coeff: 0.022, base: 1.65, markup: 1.40 });
  if (key.includes("pmma") || key.includes("acrylic")) return calc({ coeff: 0.020, base: 1.50, markup: 1.38 });
  if (key.includes("pom") || key.includes("delrin"))   return calc({ coeff: 0.020, base: 1.50, markup: 1.45 });
  if (key.includes("pbt"))        return calc({ coeff: 0.018, base: 1.35, markup: 1.38 });
  if (key.includes("abs_fusion")) return calc({ coeff: 0.018, base: 1.30, markup: 3.50 });
  if (key.includes("abs_esd"))    return calc({ coeff: 0.018, base: 1.35, markup: 4.00 });
  if (key.includes("abs"))        return calc({ coeff: 0.018, base: 1.25, markup: 1.35 });
  if (key.includes("asa"))        return calc({ coeff: 0.018, base: 1.35, markup: 3.50 });
  if (key.includes("hips"))       return calc({ coeff: 0.015, base: 1.00, markup: 1.30 });
  if (key.includes("pvc"))        return calc({ coeff: 0.010, base: 0.75, markup: 1.20 });
  if (key.includes("hdpe"))       return calc({ coeff: 0.013, base: 0.90, markup: 1.25 });
  if (key.includes("ldpe"))       return calc({ coeff: 0.012, base: 0.85, markup: 1.25 });
  if (key.includes("lldpe"))      return calc({ coeff: 0.012, base: 0.88, markup: 1.25 });
  if (key.includes("uhmw"))       return calc({ coeff: 0.013, base: 1.10, markup: 2.80 });
  if (key.includes("pp"))         return calc({ coeff: 0.012, base: 0.85, markup: 1.25 });
  if (key.includes("pla"))        return calc({ coeff: 0.012, base: 1.20, markup: 3.50 });
  if (key.includes("tpu_flex"))   return calc({ coeff: 0.022, base: 2.50, markup: 3.80 });
  if (key.includes("tpu"))        return calc({ coeff: 0.022, base: 2.20, markup: 1.42 });
  if (key.includes("tpe"))        return calc({ coeff: 0.020, base: 2.00, markup: 1.40 });
  if (key.includes("tpv"))        return calc({ coeff: 0.018, base: 1.80, markup: 1.38 });
  if (key.includes("hips") || key.includes("ps") || key.includes("polystyrene")) return calc({ coeff: 0.014, base: 0.95, markup: 1.30 });
  if (key.includes("pr700"))   return calc({ coeff: 0.005, base: 17.0, markup: 1.05 });
  if (key.includes("pr2000"))  return calc({ coeff: 0.005, base: 19.0, markup: 1.05 });
  if (key.includes("pra794"))  return calc({ coeff: 0.005, base: 18.0, markup: 1.05 });
  if (key.includes("prf100"))  return calc({ coeff: 0.005, base: 21.0, markup: 1.05 });
  if (key.includes("prc1819")) return calc({ coeff: 0.005, base: 23.0, markup: 1.05 });
  if (key.includes("pr777"))   return calc({ coeff: 0.005, base: 14.0, markup: 1.05 });
  if (key.includes("cristal_hri")) return calc({ coeff: 0.005, base: 23.0, markup: 1.05 });
  if (key.includes("resin") || key.includes("photopolymer") || key.includes("rubber_like"))
    return calc({ coeff: 0.010, base: 22.0, markup: 1.10 });
  if (/powder|_sls_|_mjf_/.test(key)) return calc({ coeff: 0.018, base: 50.0, markup: 1.20 });
  if (key.includes("filament") || key.includes("fdm")) return calc({ coeff: 0.012, base: 1.20, markup: 3.50 });
  return null;
}


// ─── ANA HANDLER ────────────────────────────────────────────────────────────
Deno.serve(async (req) => {
  const base44 = createClientFromRequest(req);
  const now = new Date().toISOString();
  const results: any[] = [];
  const alerts: string[] = [];

  // Paralel veri çekimi
  const [lmeResult, yfResult] = await Promise.allSettled([fetchLme(), fetchYahoo()]);

  const lme    = lmeResult.status    === "fulfilled" ? lmeResult.value    : {};
  const yf     = yfResult.status     === "fulfilled" ? yfResult.value     : null;
  const hrc    = yf?.hrc    ?? null; // USD/kg
  const brent  = yf?.brent  ?? null; // USD/barrel
  const ni     = lme["lme_nickel"] ?? 17.43; // fallback

  const sources = {
    lme:    lmeResult.status === "fulfilled" ? `ok (Al=${lme["lme_aluminum"]?.toFixed(4)})` : `FAILED: ${(lmeResult as any).reason?.message}`,
    hrc:    yf ? `$${(hrc! * 907.185).toFixed(0)}/short_ton` : `FAILED: ${(yfResult as any).reason?.message}`,
    brent:  yf ? `$${brent}/barrel` : "FAILED",
  };

  // LME sembol haritası (metals.dev field isimleri)
  const LME_MAP: Record<string, string> = {
    "LME_AL": "lme_aluminum",
    "LME_CU": "lme_copper",
    "LME_NI": "lme_nickel",
    "LME_ZN": "lme_zinc",
    "LME_PB": "lme_lead",
  };

  // MaterialPrice kayıtlarını çek
  let materials: any[] = [];
  try {
    const resp = await base44.asServiceRole.entities.MaterialPrice.list();
    materials = Array.isArray(resp) ? resp
      : Array.isArray(resp?.items) ? resp.items
      : Array.isArray(resp?.data)  ? resp.data : [];
  } catch (e: any) {
    return Response.json({ success: false, error: e.message }, { status: 500 });
  }

  for (const mat of materials) {
    const id = mat.id ?? mat._id;
    const d  = mat.data ?? mat;
    if (!id) continue;

    // Override aktifse dokunma
    if (d.override_active) {
      results.push({ key: d.material_key, status: "skipped_override" });
      continue;
    }

    let newPrice: number | null = null;
    let source = "";
    let lmeCurrent: number | null = null;

    // ── Titanyum → override bekleniyor, atla ────────────────────────────────
    if (d.lme_symbol === "LME_TI") {
      results.push({ key: d.material_key, status: "titanium_skip" });
      continue;
    }

    // ── LME metalleri (Al/Cu/Ni/Zn/Pb) → metals.dev ────────────────────────
    if (d.lme_symbol && LME_MAP[d.lme_symbol]) {
      const rateKey = LME_MAP[d.lme_symbol];
      if (lme[rateKey]) {
        lmeCurrent = lme[rateKey];
        const lmeRef   = d.lme_reference_price || lmeCurrent;
        const deltaPct = ((lmeCurrent - lmeRef) / lmeRef) * 100;
        newPrice = parseFloat((d.base_price_usd * (1 + deltaPct / 100)).toFixed(4));
        source = "metals_dev";

        if (Math.abs(deltaPct) >= (d.alert_threshold_pct ?? 5)) {
          alerts.push(`⚠️ ${d.material_name}: LME ${deltaPct > 0 ? "▲" : "▼"}${Math.abs(deltaPct).toFixed(1)}% → $${newPrice}/kg`);
        }

        await base44.asServiceRole.entities.MaterialPrice.update(id, {
          lme_current_price:   parseFloat(lmeCurrent.toFixed(6)),
          lme_reference_price: parseFloat((d.lme_reference_price || lmeCurrent).toFixed(6)),
          lme_delta_pct:       parseFloat(deltaPct.toFixed(2)),
          current_price_usd:   newPrice,
          last_lme_fetch:      now,
          last_auto_update:    now,
        });
        results.push({ key: d.material_key, material: d.material_name, status: "updated",
          source, old: d.current_price_usd, new: newPrice, delta_pct: parseFloat(deltaPct.toFixed(2)) });
        continue;
      }
    }

    // ── Çelik → Yahoo HRC modeli ─────────────────────────────────────────────
    if (d.lme_symbol === "LME_ST" || d.category?.includes("metal")) {
      if (hrc !== null) {
        const computed = steelPrice(d.material_key, hrc, ni);
        if (computed !== null) {
          newPrice = computed;
          source = "yahoo_hrc";
          const oldP = d.current_price_usd ?? d.base_price_usd;
          const deltaPct = oldP > 0 ? ((newPrice - oldP) / oldP) * 100 : 0;

          if (Math.abs(deltaPct) >= (d.alert_threshold_pct ?? 5)) {
            alerts.push(`⚠️ ${d.material_name}: HRC ${deltaPct > 0 ? "▲" : "▼"}${Math.abs(deltaPct).toFixed(1)}% → $${newPrice}/kg`);
          }

          await base44.asServiceRole.entities.MaterialPrice.update(id, {
            lme_current_price:  parseFloat(hrc.toFixed(6)),
            lme_delta_pct:      parseFloat(deltaPct.toFixed(2)),
            current_price_usd:  newPrice,
            last_lme_fetch:     now,
            last_auto_update:   now,
          });
          results.push({ key: d.material_key, material: d.material_name, status: "updated",
            source, old: oldP, new: newPrice, delta_pct: parseFloat(deltaPct.toFixed(2)) });
          continue;
        }
      }
    }

    // ── Plastik / Resin / 3D Filament → Brent modeli ────────────────────────
    if (!d.lme_symbol && brent !== null) {
      const computed = plasticPrice(d.material_key, brent);
      if (computed !== null) {
        newPrice = computed;
        source = "yahoo_brent";
        const oldP = d.current_price_usd ?? d.base_price_usd;
        const deltaPct = oldP > 0 ? ((newPrice - oldP) / oldP) * 100 : 0;

        if (Math.abs(deltaPct) >= (d.alert_threshold_pct ?? 5)) {
          alerts.push(`⚠️ ${d.material_name}: Brent ${deltaPct > 0 ? "▲" : "▼"}${Math.abs(deltaPct).toFixed(1)}% → $${newPrice}/kg`);
        }

        await base44.asServiceRole.entities.MaterialPrice.update(id, {
          lme_current_price:  parseFloat(brent.toFixed(4)),
          lme_delta_pct:      parseFloat(deltaPct.toFixed(2)),
          current_price_usd:  newPrice,
          last_lme_fetch:     now,
          last_auto_update:   now,
        });
        results.push({ key: d.material_key, material: d.material_name, status: "updated",
          source, old: oldP, new: newPrice, delta_pct: parseFloat(deltaPct.toFixed(2)) });
        continue;
      }
    }

    // Hiçbir kaynak eşleşmedi
    results.push({ key: d.material_key, status: "no_source_match", symbol: d.lme_symbol, category: d.category });
  }

  // Özet
  const updated   = results.filter(r => r.status === "updated");
  const skipped   = results.filter(r => r.status === "skipped_override");
  const noMatch   = results.filter(r => r.status === "no_source_match");

  return Response.json({
    success: true,
    timestamp: now,
    sources,
    market: { hrc_usd_kg: hrc ? parseFloat(hrc.toFixed(4)) : null, brent_usd_barrel: brent, ni_usd_kg: ni },
    summary: {
      total: materials.length,
      updated: updated.length,
      skipped_override: skipped.length,
      no_match: noMatch.length,
      alerts: alerts.length,
    },
    updated_by_source: {
      metals_dev:   updated.filter(r => r.source === "metals_dev").length,
      yahoo_hrc:    updated.filter(r => r.source === "yahoo_hrc").length,
      yahoo_brent:  updated.filter(r => r.source === "yahoo_brent").length,
    },
    alerts,
    no_match_details: noMatch,
  });
});
