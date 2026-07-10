import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

const METALS_DEV_KEY = Deno.env.get("METALS_DEV_API_KEY") || "";
const METALS_DEV_URL = "https://api.metals.dev/v1/metal/spot";

const LME_SYMBOL_MAP: Record<string, string> = {
  "LME-ALU": "aluminum",
  "LME-XCU": "copper",
  "LME-NI":  "nickel",
  "STEEL-SC": "steel",
  "STEEL-RE": "steel",
};

async function fetchMetalPrice(metalName: string): Promise<number | null> {
  if (!METALS_DEV_KEY) return null;
  try {
    const url = `${METALS_DEV_URL}?api_key=${METALS_DEV_KEY}&metal=${metalName}&currency=USD&unit=kg`;
    const res = await fetch(url);
    if (!res.ok) return null;
    const data = await res.json();
    return data?.price ?? null;
  } catch {
    return null;
  }
}

Deno.serve(async (req) => {
  const base44 = createClientFromRequest(req);
  const now = new Date().toISOString();
  const results: any[] = [];
  const alerts: string[] = [];

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

    const metalName = LME_SYMBOL_MAP[d.lme_symbol];
    if (!metalName) {
      results.push({ key: d.material_key, status: "unknown_symbol" });
      continue;
    }

    // LME fiyatını çek
    const lmeCurrent = await fetchMetalPrice(metalName);
    if (lmeCurrent === null) {
      results.push({ key: d.material_key, status: "fetch_failed_no_api_key" });
      continue;
    }

    const lmeRef = d.lme_reference_price || lmeCurrent;
    const deltaPct = ((lmeCurrent - lmeRef) / lmeRef) * 100;

    // Yeni fiyat = base_price * (1 + delta%) * buffer
    const bufferFactor = 1 + (d.material_buffer_pct || 6) / 100;
    const newPrice = parseFloat(
      (d.base_price_usd * (1 + deltaPct / 100) * bufferFactor).toFixed(4)
    );

    // Alert threshold kontrolü
    const threshold = d.alert_threshold_pct || 5;
    if (Math.abs(deltaPct) >= threshold) {
      alerts.push(
        `⚠️ ${d.material_name}: LME ${deltaPct > 0 ? "▲" : "▼"}${Math.abs(deltaPct).toFixed(1)}% değişti → ${d.current_price_usd?.toFixed(4)} → ${newPrice.toFixed(4)} USD/kg`
      );
    }

    // Güncelle
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
      lme_prev: lmeRef,
      lme_current: lmeCurrent,
      delta_pct: parseFloat(deltaPct.toFixed(2)),
      new_price: newPrice,
    });
  }

  return Response.json({
    success: true,
    timestamp: now,
    updated: results.filter(r => r.status === "updated").length,
    skipped_override: results.filter(r => r.status === "skipped_override").length,
    no_lme: results.filter(r => r.status === "no_lme_symbol").length,
    alerts,
    details: results,
  });
});
