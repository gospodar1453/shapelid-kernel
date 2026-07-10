/**
 * getMaterialPrices — Kernel servisi için malzeme fiyatlarını döndürür.
 * Railway'deki kernel servisi bu endpoint'i çağırarak canlı fiyatları alır.
 */

import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

Deno.serve(async (req) => {
  const base44 = createClientFromRequest(req);

  try {
    const resp = await base44.asServiceRole.entities.MaterialPrice.list();
    const materials = Array.isArray(resp) ? resp : (resp?.items ?? resp?.data ?? []);

    const prices = materials.map((mat: any) => {
      const d = mat.data ?? mat;
      return {
        material_key:       d.material_key,
        material_name:      d.material_name,
        category:           d.category,
        technology:         d.technology,
        base_price_usd:     d.base_price_usd,
        current_price_usd:  d.current_price_usd,
        override_active:    d.override_active ?? false,
        override_price_usd: d.override_price_usd ?? null,
        price_unit:         d.price_unit,        // usd_per_kg veya usd_per_cm3
        lme_delta_pct:      d.lme_delta_pct ?? 0,
        last_auto_update:   d.last_auto_update ?? null,
      };
    });

    return Response.json({ success: true, count: prices.length, prices });
  } catch (e: any) {
    return Response.json(
      { success: false, error: String(e.message) },
      { status: 500 }
    );
  }
});
