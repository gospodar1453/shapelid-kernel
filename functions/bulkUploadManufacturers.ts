import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

Deno.serve(async (req) => {
  const base44 = createClientFromRequest(req);
  const body = await req.json();
  const { items } = body; // array of manufacturer objects

  if (!items || !Array.isArray(items) || items.length === 0) {
    return new Response(JSON.stringify({ error: "items array gerekli" }), { status: 400 });
  }

  const { accessToken } = await base44.asServiceRole.connectors.getConnection("wix");

  // Her kaydı Wix formatına dönüştür
  const dataItems = items.map((r: any) => {
    const hasPhone = !!(r.phone || "").trim();
    const hasEmail = !!(r.email || "").trim();
    const hasAddress = !!(r.address || "").trim();
    const contactDataFull = hasPhone && hasEmail && hasAddress;

    // Slug: company_name'den türet
    const slug = (r.company_name || "")
      .toLowerCase()
      .replace(/[çÇ]/g, "c")
      .replace(/[şŞ]/g, "s")
      .replace(/[ğĞ]/g, "g")
      .replace(/[üÜ]/g, "u")
      .replace(/[öÖ]/g, "o")
      .replace(/[ıİ]/g, "i")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .substring(0, 80);

    // Location: "Şehir/Turkey"
    const location = r.city ? [`${r.city}/Turkey`] : [];

    // Website: Instagram linkleri de dahil
    const website = (r.website || "").trim() || undefined;

    // Address objesi
    const addressObj = r.address ? {
      formatted: r.address,
      city: r.city || "",
      country: "TR",
    } : undefined;

    // Description: capabilities + şehir + notlar
    const caps = (r.capabilities || []).join(", ");
    const description = [
      caps ? `Üretim Teknolojileri: ${caps}` : "",
      r.city ? `Konum: ${r.city}` : "",
      r.notes ? r.notes : "",
    ].filter(Boolean).join(" | ");

    const data: any = {
      title: r.company_name || "",
      slug: slug,
      email: r.email || "",
      website: website,
      manufacturing: r.capabilities || [],
      capabilities: r.capabilities || [],
      location: location,
      address: addressObj,
      description: description,
      contactDataFull: contactDataFull,
      verified: false,
      certified: false,
    };

    // Media varsa img olarak ilk URL'yi ekle
    if (r.media_urls && r.media_urls.length > 0) {
      data.img = { url: r.media_urls[0] };
    }

    return { data };
  });

  // Wix bulk insert
  const resp = await fetch("https://www.wixapis.com/wix-data/v2/items/bulk", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      dataCollectionId: "manufacturers",
      dataItems: dataItems,
      returnEntity: false,
    }),
  });

  const result = await resp.json();

  if (!resp.ok) {
    return new Response(JSON.stringify({ error: result, status: resp.status }), { status: 200 });
  }

  const inserted = result.results?.filter((r: any) => r.dataItem)?.length || 0;
  const errors = result.bulkActionMetadata?.totalFailures || 0;

  return new Response(JSON.stringify({
    status: "ok",
    inserted,
    errors,
    totalSent: items.length,
  }), {
    headers: { "Content-Type": "application/json" },
  });
});
