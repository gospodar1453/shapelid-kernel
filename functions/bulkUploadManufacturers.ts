import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

Deno.serve(async (req) => {
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "POST required" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const body = await req.json();
  const { records } = body;

  if (!Array.isArray(records) || records.length === 0) {
    return new Response(JSON.stringify({ error: "records array required" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const base44 = createClientFromRequest(req);

  try {
    // Bulk insert — 100'lü chunks'ta yükle
    const chunkSize = 100;
    let totalUploaded = 0;

    for (let i = 0; i < records.length; i += chunkSize) {
      const chunk = records.slice(i, i + chunkSize);

      const result = await base44.asServiceRole.entities.ManufacturerLead.bulkCreate({
        records: chunk,
      });

      totalUploaded += result.count || chunk.length;
    }

    return new Response(
      JSON.stringify({
        success: true,
        uploaded: totalUploaded,
        total: records.length,
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }
    );
  } catch (error) {
    return new Response(
      JSON.stringify({
        error: error.message || "Upload failed",
        details: error,
      }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      }
    );
  }
});
