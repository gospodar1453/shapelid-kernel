/**
 * batchCreateMaterialPrices — Superagent'tan gelen malzeme fiyatlarını 
 * Client Portal MaterialPrice entity'sine toplu yazma.
 * 
 * POST /functions/batchCreateMaterialPrices
 * Body: { "materials": [...], "clear_existing": true }
 */

import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

Deno.serve(async (req) => {
  if (req.method !== "POST") {
    return Response.json({ error: "POST only" }, { status: 405 });
  }

  const base44 = createClientFromRequest(req);

  try {
    const body = await req.json();
    const { materials, clear_existing = true } = body;

    if (!Array.isArray(materials) || materials.length === 0) {
      return Response.json({ error: "materials array required" }, { status: 400 });
    }

    let deletedCount = 0;
    
    // Optionally clear existing records
    if (clear_existing) {
      try {
        const existing = await base44.asServiceRole.entities.MaterialPrice.list({ limit: 500 });
        const items = Array.isArray(existing) ? existing : (existing?.items ?? existing?.data ?? []);
        for (const item of items) {
          const id = item.id || item._id || (item.data && (item.data.id || item.data._id));
          if (id) {
            await base44.asServiceRole.entities.MaterialPrice.delete(id);
            deletedCount++;
          }
        }
      } catch (e) {
        // Continue even if delete fails
      }
    }

    // Create new records in batches
    const created = [];
    const errors = [];
    const batchSize = 25;
    
    for (let i = 0; i < materials.length; i += batchSize) {
      const batch = materials.slice(i, i + batchSize);
      try {
        for (const mat of batch) {
          const record = await base44.asServiceRole.entities.MaterialPrice.create({
            material_key: mat.material_key,
            material_name: mat.material_name,
            technology: mat.technology,
            current_price_usd: mat.current_price_usd,
            price_unit: mat.price_unit || 'per_kg',
            display_mode: mat.display_mode || 'advanced',
            density_g_per_cm3: mat.density_g_per_cm3 || null,
            source: 'live_sync',
            last_updated: new Date().toISOString()
          });
          created.push(record);
        }
      } catch (e) {
        errors.push({ batch_index: i, error: String(e?.message || e) });
      }
    }

    return Response.json({
      success: true,
      deleted: deletedCount,
      created: created.length,
      total_input: materials.length,
      errors: errors
    });
  } catch (e) {
    return Response.json({ 
      success: false, 
      error: String(e?.message || e),
      stack: e?.stack 
    }, { status: 500 });
  }
});
