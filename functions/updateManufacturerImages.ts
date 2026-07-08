import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

Deno.serve(async (req) => {
  try {
    const base44 = createClientFromRequest(req);
    const body = await req.json();
    const { items } = body || {}; // [{slug, img?, cover?}]

    if (!items || !Array.isArray(items) || items.length === 0) {
      return new Response(JSON.stringify({ error: "items array gerekli" }), { status: 400 });
    }

    const { accessToken } = await base44.asServiceRole.connectors.getConnection("wix");

    async function queryBySlugs(slugs: string[]) {
      const resp = await fetch("https://www.wixapis.com/wix-data/v2/items/query", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          dataCollectionId: "manufacturers",
          query: {
            filter: { slug: { $in: slugs } },
            paging: { limit: 100 },
          },
        }),
      });
      const data = await resp.json();
      if (!resp.ok) return { ok: false, error: data, map: {} as Record<string, string> };
      const map: Record<string, string> = {};
      for (const di of data.dataItems || []) {
        const s = di.data?.slug;
        if (s) map[s] = di.id;
      }
      return { ok: true, map };
    }

    async function patchBatch(chunk: any[], slugToId: Record<string, string>) {
      // Build patches, deduplicated by dataItemId (Wix rejects duplicate item ids in one bulk call)
      const byItemId = new Map<string, any>();
      for (const c of chunk) {
        const id = slugToId[c.slug];
        if (!id) continue;
        const fieldModifications: any[] = [];
        if (c.img) fieldModifications.push({ fieldPath: "img", action: "SET_FIELD", setFieldOptions: { value: c.img } });
        if (c.cover) fieldModifications.push({ fieldPath: "cover", action: "SET_FIELD", setFieldOptions: { value: c.cover } });
        if (fieldModifications.length > 0) {
          byItemId.set(id, { dataItemId: id, fieldModifications });
        }
      }
      const patches = Array.from(byItemId.values());

      if (patches.length === 0) return { patched: 0, failed: 0, errors: [] as any[] };

      const resp = await fetch("https://www.wixapis.com/wix-data/v2/bulk/items/patch", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ dataCollectionId: "manufacturers", patches }),
      });
      const data = await resp.json();
      if (!resp.ok) return { patched: 0, failed: patches.length, errors: [{ step: "patch", error: data }] };
      const results = data.results || [];
      const failures = results.filter((r: any) => r.itemMetadata?.error);
      return { patched: results.length - failures.length, failed: failures.length, errors: failures.length ? [{ step: "patch_item_errors", sample: failures.slice(0, 3) }] : [] };
    }

    const CHUNK = 40;
    let totalMatched = 0;
    let totalPatched = 0;
    let totalFailed = 0;
    let stillNotFound: string[] = [];
    const errors: any[] = [];

    for (let i = 0; i < items.length; i += CHUNK) {
      const chunk = items.slice(i, i + CHUNK);
      const slugs = chunk.map((c: any) => c.slug);

      const q = await queryBySlugs(slugs);
      if (!q.ok) {
        errors.push({ step: "query", error: q.error });
        continue;
      }

      const notFoundHere = slugs.filter((s) => !q.map[s]);

      // Retry not-found slugs individually (handles $in-size quirks)
      const retryMap: Record<string, string> = {};
      for (const s of notFoundHere) {
        const rq = await queryBySlugs([s]);
        if (rq.ok && rq.map[s]) retryMap[s] = rq.map[s];
      }

      const combinedMap = { ...q.map, ...retryMap };
      totalMatched += Object.keys(combinedMap).length;
      stillNotFound = stillNotFound.concat(slugs.filter((s) => !combinedMap[s]));

      const r = await patchBatch(chunk, combinedMap);
      totalPatched += r.patched;
      totalFailed += r.failed;
      if (r.errors.length) errors.push(...r.errors);
    }

    return new Response(
      JSON.stringify({
        totalInput: items.length,
        totalMatched,
        totalPatched,
        totalFailed,
        notFoundCount: stillNotFound.length,
        notFoundSample: stillNotFound.slice(0, 10),
        errorsSample: errors.slice(0, 5),
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  } catch (error: any) {
    return new Response(JSON.stringify({ error: error.message || "unknown error" }), { status: 500, headers: { "Content-Type": "application/json" } });
  }
});
