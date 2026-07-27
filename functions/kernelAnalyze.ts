/**
 * kernelAnalyze v3 — Faz-2 + Akıllı Malzeme Eşleştirme
 *
 * Değişiklikler v3:
 *   - getMaterialPriceFromDB: exact key → technology fuzzy → en yakın eşleşme sıralaması
 *   - material_key_used response'a eklendi (debug için)
 *   - Tüm MaterialPrice kayıtları cache'lendi (tek list() çağrısı)
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
// Frontend'den gelen technology string'ini MaterialPrice.technology alanına eşler
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

// ── Material normalizer ──────────────────────────────────────────────────
// Material adından MaterialPrice.material_key suffix'ini üretir
function normalizeMaterial(mat: string): string {
  const m = mat.toLowerCase().trim()
    .replace(/\s+/g, "_")
    .replace(/[^a-z0-9_]/g, "")
    .replace(/_+/g, "_");
  
  // Kısa takma adlar
  const aliases: Record<string, string> = {
    "pla_filament": "pla", "pla_plus": "pla", "pla+": "pla",
    "abs_filament": "abs", "abs_fusion_plus": "abs",
    "petg_filament": "petg",
    "tpu_filament": "tpu", "tpu_flex": "tpu",
    "sla_standard_resin": "standard_resin", "standard_resin": "standard_resin",
    "sla_tough_resin": "tough_resin", "tough_resin": "tough_resin",
    "pa12_nylon_tozu_sls": "pa12", "pa12": "pa12",
    "pa12_nylon_tozu_mjf": "pa12",
    "ss316l": "ss316l", "stainless_steel_316l": "ss316l",
    "s235_mild_steel_levha": "mild_steel", "mild_steel": "mild_steel",
    "paslanmaz_celik_304_levha": "stainless_steel", "ss304": "stainless_steel",
    "aluminyum_6061_levha": "aluminum", "aluminum_6061": "aluminum", "al6061": "aluminum",
    "bakir_levha": "copper", "copper": "copper",
  };
  return aliases[m] ?? m;
}

// ── Malzeme fiyatını DB'den çek (akıllı eşleştirme) ────────────────────
async function getMaterialPriceFromDB(
  base44: any,
  technology: string,
  material: string
): Promise<{ price: number | null; key_used: string }> {
  try {
    const resp = await base44.asServiceRole.entities.MaterialPrice.list();
    const items = Array.isArray(resp) ? resp : (resp?.items ?? resp?.data ?? []);
    const records = items.map((m: any) => m.data ?? m);

    const techNorm = normalizeTechnology(technology);
    const matNorm  = normalizeMaterial(material);

    // 1. Exact match: material_key === `${techNorm}_${matNorm}`
    const exactKey = `${techNorm}_${matNorm}`;
    let found = records.find((r: any) => r.material_key === exactKey);

    // 2. Technology match + material substring
    if (!found) {
      const techRecords = records.filter((r: any) => r.technology === techNorm);
      found = techRecords.find((r: any) =>
        r.material_key?.includes(matNorm) || matNorm.includes(r.material_key?.split("_").slice(1).join("_"))
      );
    }

    // 3. Sadece technology'ye göre ilk kayıt (fallback içinde fallback)
    if (!found) {
      found = records.find((r: any) => r.technology === techNorm);
    }

    if (!found) return { price: null, key_used: "no_match" };

    const d = found;
    const price = (d.override_active && d.override_price_usd)
      ? d.override_price_usd
      : (d.current_price_usd || d.base_price_usd || null);

    return { price, key_used: d.material_key };
  } catch (_) {
    return { price: null, key_used: "error" };
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
    // Temel parametreler
    technology          = "fdm",
    material            = "pla",
    quantity            = 1,
    layer_height        = 0.2,
    infill              = 0.2,
    material_thickness  = 2.0,
    // ── Faz-2: seçim parametreleri ──
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

  // DB'den canlı malzeme fiyatını çek (akıllı eşleştirme)
  const { price: dbPrice, key_used: keyUsed } = await getMaterialPriceFromDB(base44, technology, material);

  // Base64 → binary
  const binaryStr = atob(fileBase64);
  const bytes = new Uint8Array(binaryStr.length);
  for (let i = 0; i < binaryStr.length; i++) bytes[i] = binaryStr.charCodeAt(i);
  const blob = new Blob([bytes]);

  // FormData
  const form = new FormData();
  form.append("file", blob, fileName);

  const url = new URL(`${KERNEL_URL}/analyze`);
  // Temel
  url.searchParams.set("technology",         normalizeTechnology(technology));
  url.searchParams.set("material",           normalizeMaterial(material));
  url.searchParams.set("quantity",           String(quantity));
  url.searchParams.set("layer_height",       String(layer_height));
  url.searchParams.set("infill",             String(infill));
  url.searchParams.set("material_thickness", String(material_thickness));
  // Faz-2 options
  url.searchParams.set("finish",             finish);
  url.searchParams.set("color",              color);
  url.searchParams.set("resolution",         resolution);
  url.searchParams.set("hardness",           hardness);
  url.searchParams.set("tolerance",          tolerance);
  url.searchParams.set("certification",      certification);
  // DB fiyatı
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

  return Response.json({
    ...data,
    pricing: {
      ...data.pricing,
      unit_price_try  : parseFloat((unitPriceUSD  * kurTRY).toFixed(2)),
      total_price_try : parseFloat((totalPriceUSD * kurTRY).toFixed(2)),
      exchange_rate   : parseFloat(kurTRY.toFixed(4)),
      price_source    : dbPrice ? "db_live" : "static_fallback",
      material_price_usd_per_kg_used: dbPrice,
      material_key_matched: keyUsed,
    },
  });
});
