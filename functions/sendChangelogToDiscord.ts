/**
 * sendChangelogToDiscord
 * Sends a versioned changelog embed to the Shapelid #changelog Discord channel.
 *
 * Body:
 *   version   : string   — e.g. "v2.1.0"
 *   summary   : string   — one-line description shown under the title
 *   changes   : {
 *     new?      : string[]   — ✨ New features / pages
 *     ui?       : string[]   — 🎨 UI improvements
 *     improved? : string[]   — 🔧 Backend / logic improvements
 *     removed?  : string[]   — 🗑️ Removed features / pages
 *     fix?      : string[]   — 🐛 Bug fixes
 *   }
 *   app?      : string   — "Client Portal" | "Supplier Portal" | "Kernel" | "Platform" (optional)
 */

const WEBHOOK = Deno.env.get("DISCORD_WEBHOOK_CHANGELOG") || "";
const BRAND_COLOR = 0x1a3a8f; // Shapelid navy blue

const ICONS: Record<string, string> = {
  new:      "✨",
  ui:       "🎨",
  improved: "🔧",
  removed:  "🗑️",
  fix:      "🐛",
};

const LABELS: Record<string, string> = {
  new:      "New",
  ui:       "UI",
  improved: "Improved",
  removed:  "Removed",
  fix:      "Fixed",
};

Deno.serve(async (req) => {
  if (!WEBHOOK) {
    return Response.json({ success: false, error: "DISCORD_WEBHOOK_CHANGELOG not set" }, { status: 500 });
  }

  const body = await req.json().catch(() => ({}));
  const { version, summary, changes = {}, app } = body;

  if (!version || !summary) {
    return Response.json({ success: false, error: "version and summary are required" }, { status: 400 });
  }

  // Build fields from change categories
  const fields: { name: string; value: string; inline: boolean }[] = [];
  for (const [key, icon] of Object.entries(ICONS)) {
    const items: string[] = changes[key] ?? [];
    if (items.length === 0) continue;
    fields.push({
      name: `${icon} ${LABELS[key]}`,
      value: items.map((i: string) => `• ${i}`).join("\n"),
      inline: false,
    });
  }

  const appLabel = app ? ` · ${app}` : "";
  const now = new Date().toISOString();

  const embed = {
    title: `${version}${appLabel}`,
    description: summary,
    color: BRAND_COLOR,
    fields,
    footer: { text: "Shapelid Platform" },
    timestamp: now,
  };

  const payload = {
    username: "Shapelid Releases",
    avatar_url: "https://cdn.discordapp.com/embed/avatars/0.png",
    embeds: [embed],
  };

  const res = await fetch(WEBHOOK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (res.status === 204) {
    return Response.json({ success: true, version, app: app ?? "Platform", timestamp: now });
  } else {
    const text = await res.text();
    return Response.json({ success: false, status: res.status, body: text }, { status: 500 });
  }
});
