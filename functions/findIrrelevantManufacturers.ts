import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

Deno.serve(async (req) => {
  try {
    const base44 = createClientFromRequest(req);
    const body = await req.json().catch(() => ({}));
    const startOffset = body?.offset ?? 0;
    const maxPages = body?.maxPages ?? 50; // pages per call
    const pageLimit = body?.pageLimit ?? 100;

    const { accessToken } = await base44.asServiceRole.connectors.getConnection("wix");

    const keywordGroups: Record<string, string[]> = {
      tarim_gubre: ["tarım", "tarim", "gübre", "gubre", "ziraat", "zirai"],
      kozmetik: ["kozmetik", "cosmetic"],
      lastikci: ["lastikçi", "lastikci", "oto lastik", "lastik satış", "lastik satis", "lastik servis", "lastik bakım", "lastik bakim", "lastikçisi"],
      tekstil: ["tekstil", "textile", "konfeksiyon", "dokuma", "iplik"],
      sirkeci: ["sirke", "vinegar"],
    };

    const allItems: any[] = [];
    let offset = startOffset;
    let pages = 0;
    let hasMore = true;

    while (hasMore && pages < maxPages) {
      const resp = await fetch("https://www.wixapis.com/wix-data/v2/items/query", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          dataCollectionId: "manufacturers",
          query: { paging: { limit: pageLimit, offset } },
        }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        return new Response(JSON.stringify({ error: data, step: "query", offset }), { status: 500 });
      }
      const items = data.dataItems || [];
      allItems.push(...items);
      hasMore = items.length === pageLimit;
      offset += pageLimit;
      pages++;
    }

    const allResults: Record<string, any[]> = {};
    function isFalsePositive(cat: string, combined: string): boolean {
      if (cat === "lastikci" && combined.includes("plastik") && !combined.match(/(^|[^a-zçğıöşü])lastik/i)) return true;
      return false;
    }

    for (const [cat, keywords] of Object.entries(keywordGroups)) {
      allResults[cat] = [];
      for (const item of allItems) {
        const name = (item.data?.title || "").toString().toLowerCase();
        const desc = (item.data?.description || "").toString().toLowerCase();
        const combined = name + " " + desc;
        const matched = keywords.some((k) => combined.includes(k.toLowerCase()));
        if (matched && !isFalsePositive(cat, combined)) {
          allResults[cat].push({ id: item.id, slug: item.data?.slug, name: item.data?.title });
        }
      }
    }

    const counts = Object.fromEntries(Object.entries(allResults).map(([k, v]) => [k, v.length]));

    return new Response(
      JSON.stringify({
        scannedThisCall: allItems.length,
        nextOffset: offset,
        hasMore,
        counts,
        results: allResults,
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  } catch (error: any) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  }
});
