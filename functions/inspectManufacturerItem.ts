import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

Deno.serve(async (req) => {
  try {
    const base44 = createClientFromRequest(req);
    const body = await req.json().catch(() => ({}));
    const ids: string[] = body?.ids || [];
    const { accessToken } = await base44.asServiceRole.connectors.getConnection("wix");

    const out: any[] = [];
    for (const id of ids) {
      const resp = await fetch(`https://www.wixapis.com/wix-data/v2/items/${id}?dataCollectionId=manufacturers`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      const data = await resp.json();
      out.push(data);
    }
    return new Response(JSON.stringify(out), { status: 200, headers: { "Content-Type": "application/json" } });
  } catch (error: any) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  }
});
