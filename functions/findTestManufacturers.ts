import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

Deno.serve(async (req) => {
  try {
    const base44 = createClientFromRequest(req);
    const body = await req.json().catch(() => ({}));
    const startOffset = body?.offset ?? 0;
    const maxPages = body?.maxPages ?? 50;
    const pageLimit = body?.pageLimit ?? 100;

    const { accessToken } = await base44.asServiceRole.connectors.getConnection("wix");

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

    // Word-boundary match on "test" in title only. Exclude real words containing "test" like "testere" (saw).
    // Turkish word chars include ığüşöç, so define boundary as non Turkish-letter char.
    const testRegex = /(^|[^a-zçğıöşüi])test([^a-zçğıöşüi]|$)/i;

    const matches: any[] = [];
    for (const item of allItems) {
      const title = (item.data?.title || "").toString();
      const normalized = title.toLowerCase();
      if (testRegex.test(normalized)) {
        matches.push({ id: item.id, title, description: item.data?.description });
      }
    }

    return new Response(
      JSON.stringify({
        scannedThisCall: allItems.length,
        nextOffset: offset,
        hasMore,
        matchCount: matches.length,
        matches,
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  } catch (error: any) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  }
});
