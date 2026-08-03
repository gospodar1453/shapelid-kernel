/**
 * kernelAnalyzeCNC v1.0 — CNC Feature Recognition + Pricing (Faz-5)
 *
 * Client Portal'dan gelen CNC analiz isteklerini Railway'deki
 * /analyze-cnc endpoint'ine yönlendirir.
 *
 * Akış:
 *   1. Client Portal → fileBase64 + technology + material + quantity
 *   2. MaterialPrice DB'den canlı malzeme fiyatı çek
 *   3. Railway /analyze-cnc → feature tespiti + fiyat hesabı
 *   4. TRY dönüşümü + features_summary ile geri dön
 *
 * Desteklenen teknolojiler: cnc_milling, cnc_turning, edm
 * Desteklenen formatlar: STL, OBJ, STEP, IGES
 */

import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

const KERNEL_URL = "https://shapelid-kernel-production.up.railway.app";

// ── Kur cache (4 saat) ──────────────────────────────────────────────────
let _kurCache: number | null = null;
let _kurCacheTs = 0;
const KUR_TTL = 4 * 60 * 60 * 1000;

async function getTcmbKur(): Promise<number> {
  if (_kurCache && Date.now() - _kurCacheTs < KUR_TTL) return _kurCache;
  try {
    const res = await fetch(
      "https://evds2.tcmb.gov.tr/service/evds/series=TP.DK.USD.A&startDate=01-01-2024&endDate=31-12-2026&type=json",
      { headers: { "key": Deno.env.get("TCMB_API_KEY") || "" } }
    );
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

// ── CNC Technology normalizer ───────────────────────────────────────────
function normalizeTechnology(tech: string): string {
  const t = tech.toLowerCase().trim();
  if (t.includes("cnc mill") || t.includes("milling") || t.includes("freze")) return "cnc_milling";
  if (t.includes("cnc turn") || t.includes("turning") || t.includes("lathe") || t.includes("torna")) return "cnc_turning";
  if (t.includes("edm") || t.includes("erosion") || t.includes("erozyon")) return "edm";
  // Default to milling
  return "cnc_milling";
}

// ── CNC Material normalizer ─────────────────────────────────────────────
function normalizeMaterial(mat: string): string {
  const m = mat.toLowerCase().trim()
    .replace(/\s+/g, "_")
    .replace(/[^a-z0-9_]/g, "");

  const aliases: Record<string, string> = {
    "aluminum": "aluminum",
    "aluminyum": "aluminum",
    "al": "aluminum",
    "al6061": "aluminum",
    "aluminum_6061": "aluminum",
    "aluminium": "aluminum",
    "mild_steel": "mild_steel",
    "steel": "mild_steel",
    "carbon_steel": "mild_steel",
    "s235": "mild_steel",
    "stainless_steel": "stainless_304",
    "ss304": "stainless_304",
    "stainless": "stainless_304",
    "304": "stainless_304",
    "ss316": "stainless_316",
    "stainless_316": "stainless_316",
    "316": "stainless_316",
    "brass": "brass",
    "pirinc": "brass",
    "copper": "copper",
    "bakir": "copper",
    "titanium": "titanium",
    "ti": "titanium",
    "tool_steel": "tool_steel",
    "takim_celigi": "tool_steel",
  };
  return aliases[m] ?? m;
}

// ── CNC Material fiyatı DB'den çek ──────────────────────────────────────
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
    const matNorm = normalizeMaterial(material);

    // CNC materials in MaterialPrice use technology field like "cnc_milling", "cnc_turning"
    // Try exact key match
    const exactKey = `${techNorm}__${matNorm}`;
    let found = records.find((r: any) => r.material_key === exactKey);

    // Try technology match + suffix
    if (!found) {
      const techRecords = records.filter((r: any) =>
        r.technology === techNorm || r.technology === "cnc"
      );
      found = techRecords.find((r: any) =>
        r.material_key?.includes(matNorm)
      );
    }

    // Try by material name contains
    if (!found) {
      found = records.find((r: any) =>
        r.material_name?.toLowerCase().includes(matNorm.replace(/_/g, " "))
      );
    }

    if (!found) return { price: null, key_used: "no_match" };

    const price = (found.override_active && found.override_price_usd)
      ? found.override_price_usd
      : (found.current_price_usd || found.base_price_usd || null);

    return { price, key_used: found.material_key };
  } catch (e) {
    return { price: null, key_used: "error" };
  }
}

Deno.serve(async (req) => {
  // Health check
  if (req.method === "GET") {
    const res = await fetch(`${KERNEL_URL}/health`);
    const data = await res.json();
    return Response.json({
      ...data,
      cnc_endpoints: ["/analyze-cnc", "/features"],
      cnc_technologies: ["cnc_milling", "cnc_turning", "edm"],
    });
  }

  const base44 = createClientFromRequest(req);
  const body = await req.json();

  const {
    fileBase64,
    fileName,
    technology    = "cnc_milling",
    material      = "aluminum",
    quantity      = 1,
    tolerance     = "standard",
    finish        = "standard",
  } = body;

  if (!fileBase64 || !fileName) {
    return Response.json(
      { error: "fileBase64 ve fileName zorunlu" },
      { status: 400 }
    );
  }

  // DB'den canlı malzeme fiyatı çek
  const { price: dbPrice, key_used: keyUsed } = await getMaterialPriceFromDB(
    base44, technology, material
  );

  // Base64 → binary
  const binaryStr = atob(fileBase64);
  const bytes = new Uint8Array(binaryStr.length);
  for (let i = 0; i < binaryStr.length; i++) bytes[i] = binaryStr.charCodeAt(i);
  const blob = new Blob([bytes]);

  // FormData
  const form = new FormData();
  form.append("file", blob, fileName);

  // Build URL with query params
  const url = new URL(`${KERNEL_URL}/analyze-cnc`);
  url.searchParams.set("technology", normalizeTechnology(technology));
  url.searchParams.set("material", normalizeMaterial(material));
  url.searchParams.set("quantity", String(quantity));
  url.searchParams.set("tolerance", tolerance);
  url.searchParams.set("finish", finish);
  if (dbPrice !== null) {
    url.searchParams.set("material_price_usd_per_kg", String(dbPrice));
  }

  const res = await fetch(url.toString(), { method: "POST", body: form });
  const data = await res.json();

  if (!res.ok) {
    return Response.json(data, { status: res.status });
  }

  // TRY conversion
  const kurTRY = await getTcmbKur();
  const unitPriceUSD = data.pricing?.unit_price ?? 0;
  const totalPriceUSD = data.pricing?.total_price ?? 0;

  return Response.json({
    ...data,
    pricing: {
      ...data.pricing,
      unit_price_try: parseFloat((unitPriceUSD * kurTRY).toFixed(2)),
      total_price_try: parseFloat((totalPriceUSD * kurTRY).toFixed(2)),
      exchange_rate: parseFloat(kurTRY.toFixed(4)),
      price_source: dbPrice ? "db_live" : "static_fallback",
      material_price_usd_per_kg_used: dbPrice,
      material_key_matched: keyUsed,
    },
    // CNC-specific: feature summary for UI display
    features: data.features_summary || {},
    geometry: {
      volume_cm3: data.geometry?.volume_cm3,
      surface_area_cm2: data.geometry?.surface_area_cm2,
      dimensions_mm: data.geometry?.dimensions_mm,
      is_watertight: data.geometry?.is_watertight,
      triangle_count: data.geometry?.triangle_count,
      cnc_complexity_score: data.geometry?.cnc_complexity_score,
      estimated_machine_time_min: data.geometry?.estimated_machine_time_min,
      machine_time_breakdown: data.geometry?.machine_time_breakdown,
      warnings: data.geometry?.warnings,
    },
  });
});
