import json, os, time, glob, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request, urllib.error

FUNCTION_URL = "https://run.base44.com/api/functions/bulkUploadManufacturers/run"

# API key'i env'den al
API_KEY = os.environ.get("BASE44_API_KEY", "")

def upload_batch(fpath):
    with open(fpath, 'rb') as f:
        data = f.read()
    req = urllib.request.Request(
        FUNCTION_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return fpath, result.get("inserted", 0), result.get("errors", 0), None
    except Exception as e:
        return fpath, 0, 0, str(e)

batches = sorted(glob.glob("/app/scraper/wix_batch_*.json"))
print(f"Toplam batch: {len(batches)}")

total_inserted = 0
total_errors = 0
failed = []

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(upload_batch, b): b for b in batches}
    done = 0
    for fut in as_completed(futures):
        fpath, ins, err, exc = fut.result()
        done += 1
        total_inserted += ins
        total_errors += err
        if exc or err > 0:
            failed.append((fpath, exc or f"{err} errors"))
        if done % 50 == 0 or done == len(batches):
            print(f"[{done}/{len(batches)}] Yüklenen: {total_inserted} | Hata: {total_errors}")

print(f"\n=== TAMAMLANDI ===")
print(f"Toplam yüklenen: {total_inserted}")
print(f"Toplam hata: {total_errors}")
if failed:
    print(f"Başarısız batch'ler ({len(failed)}):")
    for f, e in failed[:10]:
        print(f"  {os.path.basename(f)}: {e}")
