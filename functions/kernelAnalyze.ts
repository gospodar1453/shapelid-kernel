/**
 * kernelAnalyze — STL/DXF dosyasını analiz eder ve fiyat hesaplar.
 *
 * Fiyat akışı:
 *   1. MaterialPrice entity'sinden güncel malzeme fiyatını çeker (DB)
 *   2. Override veya current_price_usd'yi kernel'a material_price_usd_per_kg olarak gönderir
 *   3. Kernel geometrik analiz yapar + fiyat hesaplar
 *   4. TCMB kurunu çeker, TRY karşılığını ekler
 */

import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

const KERNEL_URL = "https://shapelid-kernel-production.up.railway.app";
const TCMB_URL   = "https://evds2.tcmb.gov.tr/service/evds/series=TP.DK.USD.A&startDate=01-01-2024&endDate=31-12-2026&type=json";

// ── Kur cache (4 saat) ──────────────────────────────────────────────────
let _kurCache: number | null = null;
let _kurCacheTs = 0;
const KUR_TTL = 4 * 60 * 60 * 1000;

async function getTcmbKur(): Promise<number> {
  if (_kurCache && Date.now() - _kurCacheTs < KUR_TTL) return _kurCache;
  try {
    // TCMB EVDS API — TP.DK.USD.A = USD/TRY Döviz Alış
    const res = await fetch(TCMB_URL, { headers: { "key": Deno.env.get("TCMB_API_KEY") || "" } });
    const data = await res.json();
    const items = data?.items ?? [];
    const latest = items[items.length - 1];
    const kur = parseFloat(latest?.["TP_DK_USD_A"] || "0");
    if (kur > 10) {
      _kurCache = kur * 1.04; // %4 buffer
      _kurCacheTs = Date.now();
      return _kurCache;
    }
  } catch (_) {}
  // Fallback: sabit kur
  return 47.0 * 1.04;
}

// ── Malzeme fiyatını DB'den çek ─────────────────────────────────────────
async function getMaterialPriceFromDB(
  base44: any,
  technology: string,
  material: string
): Promise<number | null> {
  try {
    const matKey = `${technology}_${material}`;
    const resp = await base44.asServiceRole.entities.MaterialPrice.list();
    const items = Array.isArray(resp) ? resp : (resp?.items ?? resp?.data ?? []);
    const found = items.find((m: any) => (m.data ?? m).material_key === matKey);
    if (!found) return null;
    const d = found.data ?? found;
    if (d.override_active && d.override_price_usd) return d.override_price_usd;
    return d.current_price_usd || d.base_price_usd || null;
  } catch (_) {
    return null;
  }
}

Deno.serve(async (req) => {
  // Health check
  if (req.method === "GET") {
    const res = await fetch(`${KERNEL_URL}/health`);
    const data = await res.json();
    return Response.json(data);
  }

  const base44 = createClientFromRequest(req);
  const body = await req.json();

  const {
    fileBase64,
    fileName,
    technology = "fdm",
    material = "pla",
    quantity = 1,
    layer_height = 0.2,
    infill = 0.2,
    material_thickness = 2.0,
  } = body;

  if (!fileBase64 || !fileName) {
    return Response.json({ error: "fileBase64 ve fileName zorunlu" }, { status: 400 });
  }

  // DB'den canlı malzeme fiyatını çek
  const dbPrice = await getMaterialPriceFromDB(base44, technology, material);

  // Base64 → binary
  const binaryStr = atob(fileBase64);
  const bytes = new Uint8Array(binaryStr.length);
  for (let i = 0; i < binaryStr.length; i++) bytes[i] = binaryStr.charCodeAt(i);
  const blob = new Blob([bytes]);

  // FormData
  const form = new FormData();
  form.append("file", blob, fileName);

  const url = new URL(`${KERNEL_URL}/analyze`);
  url.searchParams.set("technology", technology);
  url.searchParams.set("material", material);
  url.searchParams.set("quantity", String(quantity));
  url.searchParams.set("layer_height", String(layer_height));
  url.searchParams.set("infill", String(infill));
  url.searchParams.set("material_thickness", String(material_thickness));
  // DB fiyatını kernel'a gönder
  if (dbPrice !== null) {
    url.searchParams.set("material_price_usd_per_kg", String(dbPrice));
  }

  const res = await fetch(url.toString(), { method: "POST", body: form });
  const data = await res.json();

  if (!res.ok) {
    return Response.json(data, { status: res.status });
  }

  // TCMB kurunu çek ve TRY fiyatlarını ekle
  const kurTRY = await getTcmbKur();

  const unitPriceUSD  = data.pricing?.unit_price  ?? 0;
  const totalPriceUSD = data.pricing?.total_price ?? 0;

  return Response.json({
    ...data,
    pricing: {
      ...data.pricing,
      // TRY karşılıkları (buffer dahil kur)
      unit_price_try:  parseFloat((unitPriceUSD  * kurTRY).toFixed(2)),
      total_price_try: parseFloat((totalPriceUSD * kurTRY).toFixed(2)),
      exchange_rate:   parseFloat(kurTRY.toFixed(4)),
      price_source:    data.pricing?.price_source ?? (dbPrice ? "db_live" : "static_fallback"),
      material_price_usd_per_kg_used: dbPrice,
    },
  });
});
