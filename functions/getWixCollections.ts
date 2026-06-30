import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

Deno.serve(async (req) => {
  const base44 = createClientFromRequest(req);
  const { accessToken } = await base44.asServiceRole.connectors.getConnection("wix");

  // Önce koleksiyonları listele (farklı endpoint)
  const resp = await fetch("https://www.wixapis.com/wix-data/v2/collections", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
  });

  const rawText = await resp.text();

  if (!resp.ok) {
    return new Response(JSON.stringify({ error: rawText, status: resp.status }), { status: 200 });
  }

  let data: any;
  try {
    data = JSON.parse(rawText);
  } catch {
    return new Response(JSON.stringify({ raw: rawText }), { headers: { "Content-Type": "application/json" } });
  }

  const collections = (data.collections || []).map((c: any) => ({
    id: c.id,
    displayName: c.displayName,
    fieldCount: (c.fields || []).length,
    fields: (c.fields || []).map((f: any) => ({
      key: f.key,
      displayName: f.displayName,
      type: f.type,
    })),
  }));

  return new Response(JSON.stringify({ collections, total: collections.length }, null, 2), {
    headers: { "Content-Type": "application/json" },
  });
});
