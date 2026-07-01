import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

Deno.serve(async (req) => {
  const base44 = createClientFromRequest(req);
  const body = await req.json();

  // Payload: { email, full_name, phone, source } 
  // source: "client" | "supplier"
  const { email, full_name, phone, source } = body;

  if (!email && !full_name) {
    return new Response(JSON.stringify({ error: "email veya full_name gerekli" }), { status: 400 });
  }

  const { accessToken } = await base44.asServiceRole.connectors.getConnection("wix");

  // Ad soyad ayır
  const nameParts = (full_name || "").trim().split(" ");
  const firstName = nameParts[0] || "";
  const lastName = nameParts.slice(1).join(" ") || "";

  // Etiket: client → "custom.client", supplier → "custom.supplier"
  const labelKey = source === "supplier" ? "custom.supplier" : "custom.client";

  const contactPayload: any = {
    info: {
      name: {
        first: firstName,
        last: lastName,
      },
      labelKeys: {
        items: [labelKey],
      },
    },
    allowDuplicates: false,
  };

  if (email) {
    contactPayload.info.emails = {
      items: [{ email, tag: "MAIN", primary: true }],
    };
  }

  if (phone) {
    const cleanPhone = phone.replace(/\s+/g, "").replace(/^0/, "+90");
    contactPayload.info.phones = {
      items: [{ phone: cleanPhone, tag: "MOBILE", primary: true, countryCode: "TR" }],
    };
  }

  const resp = await fetch("https://www.wixapis.com/contacts/v4/contacts", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(contactPayload),
  });

  const result = await resp.json();

  if (!resp.ok) {
    // Duplicate durumunda başarı say
    if (result.message?.includes("already exists") || resp.status === 409) {
      return new Response(JSON.stringify({ status: "already_exists", source }), { status: 200 });
    }
    return new Response(JSON.stringify({ error: result, status: resp.status }), { status: 200 });
  }

  return new Response(JSON.stringify({
    status: "created",
    wixContactId: result.contact?.id,
    label: labelKey,
    source,
  }), {
    headers: { "Content-Type": "application/json" },
  });
});
