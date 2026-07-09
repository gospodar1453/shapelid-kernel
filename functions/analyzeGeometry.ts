import { createClientFromRequest } from 'npm:@base44/sdk@0.8.31';

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "Sadece POST destekleniyor" }), {
      status: 405,
      headers: { "Content-Type": "application/json" },
    });
  }

  const base44 = createClientFromRequest(req);

  let body: any;
  try {
    body = await req.json();
  } catch {
    return new Response(JSON.stringify({ error: "Geçersiz JSON body" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const {
    file_url,
    file_name,
    technology = "fdm",
    material = "pla",
    quantity = 1,
    layer_height = 0.2,
    infill = 0.2,
    material_thickness = 2.0,
    user_id,
    enterprise_quota_check = false,
  } = body;

  if (!file_url || !file_name) {
    return new Response(
      JSON.stringify({ error: "file_url ve file_name zorunlu" }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }

  const ext = file_name.split(".").pop()?.toLowerCase();
  const NATIVE_FORMATS = ["sldprt", "catpart", "ipt", "prt", "dwg"];
  const SUPPORTED_FORMATS = ["stl", "dxf", "step", "stp", "iges", "igs"];

  // ── Native format → Enterprise kontrolü ──
  if (NATIVE_FORMATS.includes(ext || "")) {
    if (!enterprise_quota_check) {
      return new Response(
        JSON.stringify({
          error: "ENTERPRISE_ONLY",
          message: `${ext?.toUpperCase()} formatı yalnızca Enterprise kullanıcıları için desteklenmektedir.`,
          upgrade_url: "https://shapelid.com/enterprise",
        }),
        { status: 403, headers: { "Content-Type": "application/json" } }
      );
    }
    return new Response(
      JSON.stringify({
        status: "APS_REQUIRED",
        message: "Bu format APS entegrasyonu gerektirir (Faz-2).",
        file_name,
        technology,
      }),
      { status: 202, headers: { "Content-Type": "application/json" } }
    );
  }

  if (!SUPPORTED_FORMATS.includes(ext || "")) {
    return new Response(
      JSON.stringify({
        error: "UNSUPPORTED_FORMAT",
        message: `Desteklenmeyen format: .${ext}. STEP, IGES, STL veya DXF yükleyin.`,
        supported: SUPPORTED_FORMATS,
      }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }

  // ── Faz-1: yalnızca STL / DXF ──
  if (["step", "stp", "iges", "igs"].includes(ext || "")) {
    return new Response(
      JSON.stringify({
        status: "COMING_SOON",
        message: "STEP/IGES desteği Faz-2'de aktif olacak. Şimdilik STL veya DXF yükleyin.",
        file_name,
      }),
      { status: 202, headers: { "Content-Type": "application/json" } }
    );
  }

  // ── Dosyayı indir ──
  let fileBuffer: ArrayBuffer;
  try {
    const fileResp = await fetch(file_url);
    if (!fileResp.ok) throw new Error(`HTTP ${fileResp.status}`);
    fileBuffer = await fileResp.arrayBuffer();
  } catch (err: any) {
    return new Response(
      JSON.stringify({ error: "Dosya indirme hatası", detail: err.message }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }

  // ── Kernel mikroservisine gönder ──
  const KERNEL_URL = Deno.env.get("KERNEL_SERVICE_URL") ?? "";
  const KERNEL_KEY = Deno.env.get("KERNEL_API_KEY") ?? "";

  if (!KERNEL_URL) {
    return new Response(
      JSON.stringify({ error: "KERNEL_SERVICE_URL ortam değişkeni tanımlı değil" }),
      { status: 503, headers: { "Content-Type": "application/json" } }
    );
  }

  const formData = new FormData();
  formData.append("file", new Blob([fileBuffer]), file_name);
  formData.append("technology", technology);
  formData.append("material", material);
  formData.append("quantity", String(quantity));
  formData.append("layer_height", String(layer_height));
  formData.append("infill", String(infill));
  formData.append("material_thickness", String(material_thickness));

  let kernelResult: any;
  try {
    const headers: Record<string, string> = {};
    if (KERNEL_KEY) headers["X-Kernel-Key"] = KERNEL_KEY;

    const kernelResp = await fetch(`${KERNEL_URL}/analyze`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (!kernelResp.ok) {
      const errText = await kernelResp.text();
      throw new Error(`Kernel ${kernelResp.status}: ${errText}`);
    }
    kernelResult = await kernelResp.json();
  } catch (err: any) {
    return new Response(
      JSON.stringify({ error: "Kernel servisi yanıt vermedi", detail: err.message }),
      { status: 502, headers: { "Content-Type": "application/json" } }
    );
  }

  // ── Güven skoruna göre quote_mode ──
  const confidence = kernelResult.pricing?.confidence;
  let quote_mode: string = "auto";
  if (confidence?.recommend_manual_quote) {
    quote_mode = confidence.score < 30 ? "manual" : "both";
  }

  return new Response(
    JSON.stringify({
      success: true,
      file_name,
      technology,
      material,
      quantity,
      geometry: kernelResult.geometry,
      pricing: kernelResult.pricing,
      quote_mode,
      routing: kernelResult.pricing?.routing,
      meta: {
        kernel_version: "faz-1",
        processed_at: new Date().toISOString(),
        user_id: user_id ?? null,
      },
    }),
    { status: 200, headers: { "Content-Type": "application/json" } }
  );
});
