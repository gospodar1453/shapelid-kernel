import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

Deno.serve(async (req) => {
  try {
    const base44 = createClientFromRequest(req);
    const { accessToken } = await base44.asServiceRole.connectors.getConnection("wix");

    const resp = await fetch("https://www.wixapis.com/wix-data/v2/items/query", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        dataCollectionId: "manufacturers",
        query: { paging: { limit: 1 } },
      }),
    });
    const data = await resp.json();
    return new Response(JSON.stringify(data.pagingMetadata || {}), { status: 200, headers: { "Content-Type": "application/json" } });
  } catch (error: any) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  }
});
