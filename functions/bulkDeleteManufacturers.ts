import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

Deno.serve(async (req) => {
  try {
    const base44 = createClientFromRequest(req);
    const body = await req.json();
    const ids: string[] = body?.ids || [];

    if (!ids.length) {
      return new Response(JSON.stringify({ error: "ids array gerekli" }), { status: 400 });
    }

    const { accessToken } = await base44.asServiceRole.connectors.getConnection("wix");

    const resp = await fetch("https://www.wixapis.com/wix-data/v2/bulk/items/remove", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        dataCollectionId: "manufacturers",
        dataItemIds: ids,
      }),
    });
    const data = await resp.json();
    if (!resp.ok) {
      return new Response(JSON.stringify({ error: data }), { status: 500 });
    }
    const results = data.results || [];
    const failures = results.filter((r: any) => r.itemMetadata?.error);
    return new Response(
      JSON.stringify({
        totalInput: ids.length,
        totalDeleted: results.length - failures.length,
        totalFailed: failures.length,
        failuresSample: failures.slice(0, 5),
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  } catch (error: any) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  }
});
