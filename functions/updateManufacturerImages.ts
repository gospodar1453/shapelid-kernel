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

    const CHUNK = 90;
    let totalMatched = 0;
    let totalPatched = 0;
    let totalFailed = 0;
    const notFoundSlugs: string[] = [];
    const errors: any[] = [];

    for (let i = 0; i < items.length; i += CHUNK) {
      const chunk = items.slice(i, i + CHUNK);
      const slugs = chunk.map((c: any) => c.slug);

      // 1) Query items by slug
      const queryResp = await fetch("https://www.wixapis.com/wix-data/v2/items/query", {
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

      const queryData = await queryResp.json();
      if (!queryResp.ok) {
        errors.push({ step: "query", error: queryData });
        continue;
      }

      const dataItems = queryData.dataItems || [];
      const slugToId: Record<string, string> = {};
      for (const di of dataItems) {
        const s = di.data?.slug;
        if (s) slugToId[s] = di.id;
      }

      totalMatched += Object.keys(slugToId).length;
      for (const s of slugs) {
        if (!slugToId[s]) notFoundSlugs.push(s);
      }

      // 2) Build patch payload (correct format: patches[] with fieldModifications)
      const patches = chunk
        .filter((c: any) => slugToId[c.slug])
        .map((c: any) => {
          const fieldModifications: any[] = [];
          if (c.img) {
            fieldModifications.push({
              fieldPath: "img",
              action: "SET_FIELD",
              setFieldOptions: { value: c.img },
            });
          }
          if (c.cover) {
            fieldModifications.push({
              fieldPath: "cover",
              action: "SET_FIELD",
              setFieldOptions: { value: c.cover },
            });
          }
          return { dataItemId: slugToId[c.slug], fieldModifications };
        })
        .filter((p: any) => p.fieldModifications.length > 0);

      if (patches.length === 0) continue;

      const patchResp = await fetch("https://www.wixapis.com/wix-data/v2/bulk/items/patch", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          dataCollectionId: "manufacturers",
          patches: patches,
        }),
      });

      const patchData = await patchResp.json();
      if (!patchResp.ok) {
        errors.push({ step: "patch", error: patchData });
        totalFailed += patches.length;
        continue;
      }

      const results = patchData.results || [];
      const failures = results.filter((r: any) => r.itemMetadata?.error);
      totalFailed += failures.length;
      totalPatched += results.length - failures.length;
      if (failures.length > 0) {
        errors.push({ step: "patch_item_errors", sample: failures.slice(0, 3) });
      }
    }

    return new Response(
      JSON.stringify({
        totalInput: items.length,
        totalMatched,
        totalPatched,
        totalFailed,
        notFoundCount: notFoundSlugs.length,
        notFoundSample: notFoundSlugs.slice(0, 10),
        errorsSample: errors.slice(0, 5),
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  } catch (error: any) {
    return new Response(
      JSON.stringify({ error: error.message || "unknown error" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
});
