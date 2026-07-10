Deno.serve(async (req) => {
  const KERNEL_URL = "https://shapelid-kernel-production.up.railway.app";

  // Health check
  if (req.method === "GET") {
    const res = await fetch(`${KERNEL_URL}/health`);
    const data = await res.json();
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" },
    });
  }

  const body = await req.json();
  const {
    fileBase64,
    fileName,
    technology = "fdm",
    material = "pla",
    quantity = 1,
    layer_height = 0.2,
    infill = 0.2,
    material_thickness = 2.0,
  } = body;

  if (!fileBase64 || !fileName) {
    return new Response(JSON.stringify({ error: "fileBase64 ve fileName zorunlu" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  // Base64'ü binary'e çevir
  const binaryStr = atob(fileBase64);
  const bytes = new Uint8Array(binaryStr.length);
  for (let i = 0; i < binaryStr.length; i++) {
    bytes[i] = binaryStr.charCodeAt(i);
  }
  const blob = new Blob([bytes]);

  // FormData oluştur
  const form = new FormData();
  form.append("file", blob, fileName);

  const url = new URL(`${KERNEL_URL}/analyze`);
  url.searchParams.set("technology", technology);
  url.searchParams.set("material", material);
  url.searchParams.set("quantity", String(quantity));
  url.searchParams.set("layer_height", String(layer_height));
  url.searchParams.set("infill", String(infill));
  url.searchParams.set("material_thickness", String(material_thickness));

  const res = await fetch(url.toString(), {
    method: "POST",
    body: form,
  });

  const data = await res.json();

  return new Response(JSON.stringify(data), {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
});
