/**
 * kernelAnalyze v5 — CNC Auto-Routing + Akıllı Malzeme Eşleştirme
 *
 * v5 değişiklikleri:
 *   - CNC teknolojileri (cnc_milling, cnc_turning, edm) otomatik /analyze-cnc'ye yönlendirilir
 *   - CNC için farklı parametre seti (tolerance, finish odaklı, layer_height/infill yok)
 *   - CNC feature recognition sonuçları döndürülür
 *
 * v4 düzeltmeleri (korunmuştur):
 *   - material_key formatı: tek _ yerine çift __ (DB formatıyla uyumlu)
 *   - Fuzzy match: exact suffix → starts_with → includes sıralaması
 *   - price_unit kontrolü: per_liter için otomatik per_kg dönüşümü
 */

import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

const KERNEL_URL = "https://shapelid-kernel-production.up.railway.app";
const TCMB_URL   = "https://evds2.tcmb.gov.tr/service/evds/series=TP.DK.USD.A&startDate=01-01-2024&endDate=31-12-2026&type=json";

const CNC_TECHNOLOGIES = new Set(["cnc_milling", "cnc_turning", "edm"]);

// ── Kur cache (4 saat) ──────────────────────────────────────────────────
let _kurCache: number | null = null;
let _kurCacheTs = 0;
const KUR_TTL = 4 * 60 * 60 * 1000;

async function getTcmbKur(): Promise<number> {
  if (_kurCache && Date.now() - _kurCacheTs < KUR_TTL) return _kurCache;
  try {
    const res = await fetch(TCMB_URL, {
      headers: { "key": Deno.env.get("TCMB_API_KEY") || "" }
    });
    const data = await res.json();
    const items = data?.items ?? [];
    const latest = items[items.length - 1];
    const kur = parseFloat(latest?.["TP_DK_USD_A"] || "0");
    if (kur > 10) {
      _kurCache = kur * 1.04;
      _kurCacheTs = Date.now();
      return _kurCache;
    }
  } catch (_) {}
  return 47.0 * 1.04;
}

// ── Technology normalizer ────────────────────────────────────────────────
function normalizeTechnology(tech: string): string {
  const t = tech.toLowerCase().trim();
  if (t.includes("fdm") || t.includes("fused") || t.includes("fff"))         return "fdm";
  if (t.includes("sla") || t.includes("stereo") || t.includes("resin"))      return "sla";
  if (t.includes("sls") && !t.includes("dmls"))                               return "sls";
  if (t.includes("mjf") || t.includes("multi jet fusion") || t.includes("hp")) return "mjf";
  if (t.includes("dmls") || t.includes("direct metal") || t.includes("slm"))  return "dmls";
  if (t.includes("polyjet") || t.includes("poly jet"))                        return "polyjet";
  if (t.includes("cnc mill") || t.includes("milling"))                        return "cnc_milling";
  if (t.includes("cnc turn") || t.includes("turning") || t.includes("lathe")) return "cnc_turning";
  if (t.includes("edm") || t.includes("erosion") || t.includes("erozyon"))    return "edm";
  if (t.includes("laser") || t.includes("lazer"))                             return "laser";
  if (t.includes("bend") || t.includes("bük") || t.includes("abkant") || t.includes("sheet metal")) return "bending";
  return t.replace(/\s+/g, "_");
}

// ── Material normalizer ─────────────────────────────────────────────────
function normalizeMaterial(mat: string): string {
  const m = mat.toLowerCase().trim()
    .replace(/\s+/g, "_")
    .replace(/[^a-z0-9_]/g, "")
    .replace(/_+/g, "_");

  const aliases: Record<string, string> = {
    "pla_filament": "pla",
    "pla_plus": "pla",
    "pla": "pla",
    "abs_filament": "abs",
    "abs_fusion_plus": "abs",
    "petg_filament": "petg",
    "tpu_filament": "tpu_flex",
    "tpu": "tpu_flex",
    "standard_resin": "standard_resin",
    "sla_standard_resin": "standard_resin",
    "tough_resin": "tough_resin",
    "sla_tough_resin": "tough_resin",
    "pa12": "pa12",
    "pa12_nylon_tozu_sls": "pa12",
    "pa12_nylon_tozu_mjf": "pa12",
    "ss316l": "ss316l",
    "stainless_steel_316l": "ss316l",
    "mild_steel": "mild_steel",
    "s235_mild_steel_levha": "mild_steel",
    "stainless_steel": "stainless_steel",
    "ss304": "stainless_steel",
    "paslanmaz_celik_304_levha": "stainless_steel",
    "aluminum": "aluminum",
    "aluminum_6061": "aluminum",
    "al6061": "aluminum",
    "aluminyum_6061_levha": "aluminum",
    "copper": "copper",
    "bakir_levha": "copper",
  };
  return aliases[m] ?? m;
}

// ── Malzeme fiyatını DB'den çek ───────────────────────────────────────
async function getMaterialPriceFromDB(
  base44: any,
  technology: string,
  material: string
): Promise<{ price: number | null; key_used: string; price_unit: string }> {
  try {
    const resp = await base44.asServiceRole.entities.MaterialPrice.list();
    const items = Array.isArray(resp) ? resp : (resp?.items ?? resp?.data ?? []);
    const records = items.map((m: any) => m.data ?? m);

    const techNorm = normalizeTechnology(technology);
    const matNorm  = normalizeMaterial(material);

    // 1. Exact match: material_key === `${techNorm}__${matNorm}` (ÇİFT alt çizgi!)
    const exactKey = `${techNorm}__${matNorm}`;
    let found = records.find((r: any) => r.material_key === exactKey);

    // 2. Technology match + exact suffix
    if (!found) {
      const techRecords = records.filter((r: any) => r.technology === techNorm);
      found = techRecords.find((r: any) =>
        r.material_key?.endsWith(`__${matNorm}`)
      );
    }

    // 3. Technology match + material_key includes matNorm
    if (!found) {
      const techRecords = records.filter((r: any) => r.technology === techNorm);
      found = techRecords.find((r: any) =>
        r.material_key?.includes(matNorm)
      );
    }

    // 4. Sadece technology'ye göre ilk kayıt (son fallback)
    if (!found) {
      found = records.find((r: any) => r.technology === techNorm);
    }

    if (!found) return { price: null, key_used: "no_match", price_unit: "per_kg" };

    const d = found;
    const price = (d.override_active && d.override_price_usd)
      ? d.override_price_usd
      : (d.current_price_usd || d.base_price_usd || null);

    return { price, key_used: d.material_key, price_unit: d.price_unit || "per_kg" };
  } catch (e) {
    return { price: null, key_used: "error", price_unit: "per_kg" };
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
    technology          = "fdm",
    material            = "pla",
    quantity            = 1,
    layer_height        = 0.2,
    infill              = 0.2,
    material_thickness  = 2.0,
    finish              = "standard",
    color               = "none",
    resolution          = "standard",
    hardness            = "standard",
    tolerance           = "standard",
    certification       = "none",
  } = body;

  if (!fileBase64 || !fileName) {
    return Response.json({ error: "fileBase64 ve fileName zorunlu" }, { status: 400 });
  }

  // Normalize technology
  const techNorm = normalizeTechnology(technology);
  const matNorm = normalizeMaterial(material);

  // DB'den canlı malzeme fiyatını çek
  const { price: dbPrice, key_used: keyUsed, price_unit: priceUnit } = await getMaterialPriceFromDB(base44, technology, material);

  // Base64 → binary
  const binaryStr = atob(fileBase64);
  const bytes = new Uint8Array(binaryStr.length);
  for (let i = 0; i < binaryStr.length; i++) bytes[i] = binaryStr.charCodeAt(i);
  const blob = new Blob([bytes]);

  // FormData
  const form = new FormData();
  form.append("file", blob, fileName);

  // ── CNC routing: CNC teknolojileri /analyze-cnc'ye ──
  const isCNC = CNC_TECHNOLOGIES.has(techNorm);

  const url = new URL(`${KERNEL_URL}${isCNC ? "/analyze-cnc" : "/analyze"}`);
  url.searchParams.set("technology", techNorm);
  url.searchParams.set("material", matNorm);
  url.searchParams.set("quantity", String(quantity));

  if (isCNC) {
    // CNC parametreleri
    url.searchParams.set("tolerance", tolerance);
    url.searchParams.set("finish", finish);
  } else {
    // 3D printing / sheet metal parametreleri
    url.searchParams.set("layer_height",       String(layer_height));
    url.searchParams.set("infill",             String(infill));
    url.searchParams.set("material_thickness", String(material_thickness));
    url.searchParams.set("finish",             finish);
    url.searchParams.set("color",              color);
    url.searchParams.set("resolution",         resolution);
    url.searchParams.set("hardness",           hardness);
    url.searchParams.set("tolerance",           tolerance);
    url.searchParams.set("certification",      certification);
  }

  // DB fiyatı — kernel'a per_kg olarak pasla
  if (dbPrice !== null) {
    url.searchParams.set("material_price_usd_per_kg", String(dbPrice));
  }

  const res = await fetch(url.toString(), { method: "POST", body: form });
  const data = await res.json();

  if (!res.ok) {
    return Response.json(data, { status: res.status });
  }

  const kurTRY        = await getTcmbKur();
  const unitPriceUSD  = data.pricing?.unit_price  ?? 0;
  const totalPriceUSD = data.pricing?.total_price ?? 0;

  const response: any = {
    ...data,
    pricing: {
      ...data.pricing,
      unit_price_try  : parseFloat((unitPriceUSD  * kurTRY).toFixed(2)),
      total_price_try : parseFloat((totalPriceUSD * kurTRY).toFixed(2)),
      exchange_rate   : parseFloat(kurTRY.toFixed(4)),
      price_source    : dbPrice ? "db_live" : "static_fallback",
      material_price_usd_per_kg_used: dbPrice,
      material_key_matched: keyUsed,
      price_unit: priceUnit,
    },
  };

  // CNC: feature summary'yi ekle
  if (isCNC && data.features_summary) {
    response.features = data.features_summary;
  }

  return Response.json(response);
});
