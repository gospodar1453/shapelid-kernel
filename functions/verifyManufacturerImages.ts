import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

Deno.serve(async (req) => {
  try {
    const base44 = createClientFromRequest(req);
    const body = await req.json().catch(() => ({}));
    const slugs = body?.slugs || ["cnc-torna", "unlu-torna-cnc-otomat", "mert-cnc-maki-ne"];

    const { accessToken } = await base44.asServiceRole.connectors.getConnection("wix");

    const resp = await fetch("https://www.wixapis.com/wix-data/v2/items/query", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        dataCollectionId: "manufacturers",
        query: { filter: { slug: { $in: slugs } }, paging: { limit: 10 } },
      }),
    });
    const data = await resp.json();
    const out = (data.dataItems || []).map((di: any) => ({
      slug: di.data?.slug,
      img: di.data?.img,
      cover: di.data?.cover,
    }));
    return new Response(JSON.stringify({ count: out.length, out }), { status: 200, headers: { "Content-Type": "application/json" } });
  } catch (error: any) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  }
});
