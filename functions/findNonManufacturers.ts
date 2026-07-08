import { createClientFromRequest } from "npm:@base44/sdk@0.8.31";

Deno.serve(async (req) => {
  try {
    const base44 = createClientFromRequest(req);
    const body = await req.json().catch(() => ({}));
    const startOffset = body?.offset ?? 0;
    const maxPages = body?.maxPages ?? 50;
    const pageLimit = body?.pageLimit ?? 100;

    const { accessToken } = await base44.asServiceRole.connectors.getConnection("wix");

    const allItems: any[] = [];
    let offset = startOffset;
    let pages = 0;
    let hasMore = true;

    while (hasMore && pages < maxPages) {
      const resp = await fetch("https://www.wixapis.com/wix-data/v2/items/query", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          dataCollectionId: "manufacturers",
          query: { paging: { limit: pageLimit, offset } },
        }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        return new Response(JSON.stringify({ error: data, step: "query", offset }), { status: 500 });
      }
      const items = data.dataItems || [];
      allItems.push(...items);
      hasMore = items.length === pageLimit;
      offset += pageLimit;
      pages++;
    }

    // Categories: only match on title, word-based patterns to avoid substring false positives.
    const keywordGroups: Record<string, string[]> = {
      reklam_tabela: ["reklam ajans", "reklam ajansı", "tabela", "grafik tasarım"],
      egitim_danismanlik: ["eğitim", "egitim", "danışmanlık", "danismanlik", "kurumsal teknik eğitim"],
      estetik_saglik: ["estetik", "saç ekimi", "sac ekimi", "klinik", "muayenehane", "diş teknoloji", "dişhekim", "dental"],
      kamu_edevlet: ["e-imza", "e-fatura", "e-dönüşüm", "e-donusum", "belediye", "kaymakamlık", "valilik", "müdürlüğü"],
      sadece_satis: ["filament üret", "filament uret", "3d yazıcı üret", "3d yazici uret", "3d yazıcı satış", "3d yazici satis", "profil satış", "profil satis", "teknoloji mağazası", "teknoloji magazasi", "toptan satış", "toptan satis", "perakende satış"],
      muayene_bakim: ["oto ekspertiz", "ekspertiz", "vize takip", "araç muayene", "arac muayene", "fren test", "trafo bakım", "trafo bakim", "bakım-servis", "bakim-servis"],
    };

    const allResults: Record<string, any[]> = {};
    for (const [cat, keywords] of Object.entries(keywordGroups)) {
      allResults[cat] = [];
      for (const item of allItems) {
        const title = (item.data?.title || "").toString().toLowerCase();
        const matched = keywords.some((k) => title.includes(k.toLowerCase()));
        if (matched) {
          allResults[cat].push({ id: item.id, title: item.data?.title });
        }
      }
    }

    const counts = Object.fromEntries(Object.entries(allResults).map(([k, v]) => [k, v.length]));

    return new Response(
      JSON.stringify({
        scannedThisCall: allItems.length,
        nextOffset: offset,
        hasMore,
        counts,
        results: allResults,
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  } catch (error: any) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  }
});
