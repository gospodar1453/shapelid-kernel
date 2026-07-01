import json, os, time, glob, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request, urllib.error

WIX_TOKEN = os.environ.get("WIX_ACCESS_TOKEN", "")
URL = "https://www.wixapis.com/wix-data/v2/bulk/items/insert"

def transform_item(r):
    has_phone = bool((r.get("phone") or "").strip())
    has_email = bool((r.get("email") or "").strip())
    has_address = bool((r.get("address") or "").strip())
    contact_data_full = has_phone and has_email and has_address

    slug = (r.get("company_name") or "").lower()
    for a, b in [("ç","c"),("ş","s"),("ğ","g"),("ü","u"),("ö","o"),("ı","i"),("İ","i"),("Ç","c"),("Ş","s"),("Ğ","g"),("Ü","u"),("Ö","o")]:
        slug = slug.replace(a, b)
    import re
    slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')[:80]

    location = [f"{r['city']}/Turkey"] if r.get("city") else []
    caps = (r.get("capabilities") or [])
    desc_parts = []
    if caps: desc_parts.append(f"Uretim Teknolojileri: {', '.join(caps)}")
    if r.get("city"): desc_parts.append(f"Konum: {r['city']}")
    if r.get("notes"): desc_parts.append(r["notes"])
    description = " | ".join(desc_parts)

    data = {
        "title": r.get("company_name") or "",
        "slug": slug,
        "email": r.get("email") or "",
        "manufacturing": caps,
        "capabilities": caps,
        "location": location,
        "description": description,
        "contactDataFull": contact_data_full,
        "verified": False,
        "certified": False,
    }
    if (r.get("website") or "").strip():
        data["website"] = r["website"].strip()
    if r.get("media_urls") and len(r["media_urls"]) > 0:
        data["img"] = {"url": r["media_urls"][0]}

    return {"data": data}

def upload_batch(batch_items):
    data_items = [transform_item(r) for r in batch_items]
    payload = json.dumps({
        "dataCollectionId": "manufacturers",
        "dataItems": data_items,
        "returnEntity": False
    }, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(URL, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WIX_TOKEN}",
    }, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            s = result.get("bulkActionMetadata", {}).get("totalSuccesses", 0)
            f = result.get("bulkActionMetadata", {}).get("totalFailures", 0)
            return s, f, None
    except Exception as e:
        return 0, len(batch_items), str(e)

# Tüm veriyi yükle
data = json.load(open("/app/scraper/combined_all.json", encoding="utf-8"))
print(f"Toplam kayıt: {len(data)}")

BATCH_SIZE = 100
batches = [data[i:i+BATCH_SIZE] for i in range(0, len(data), BATCH_SIZE)]
print(f"Batch sayısı: {len(batches)} (batch başına {BATCH_SIZE})")

total_inserted = 0
total_errors = 0
failed_batches = []

start = time.time()
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(upload_batch, b): i for i, b in enumerate(batches)}
    done = 0
    for fut in as_completed(futures):
        idx = futures[fut]
        ins, err, exc = fut.result()
        done += 1
        total_inserted += ins
        total_errors += err
        if exc or err > 0:
            failed_batches.append((idx, exc or f"{err} hatali"))
        if done % 25 == 0 or done == len(batches):
            elapsed = time.time() - start
            rate = total_inserted / elapsed if elapsed > 0 else 0
            print(f"[{done}/{len(batches)}] Yüklenen: {total_inserted} | Hata: {total_errors} | Hız: {rate:.0f}/sn", flush=True)

print(f"\n=== TAMAMLANDI ===")
print(f"Toplam yüklenen: {total_inserted}")
print(f"Toplam hata: {total_errors}")
if failed_batches:
    print(f"Başarısız batch'ler: {len(failed_batches)}")
    for idx, e in failed_batches[:5]:
        print(f"  Batch {idx}: {e}")
