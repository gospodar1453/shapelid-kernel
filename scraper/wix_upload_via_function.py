import json, os, time, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

# Backend function URL (agent'in kendi app'i)
FUNCTION_URL = os.environ.get("BACKEND_FUNCTION_URL", "")
API_KEY = os.environ.get("BASE44_API_KEY_VAL", "")

data = json.load(open('/app/scraper/combined_all.json', encoding='utf-8'))
print(f"Toplam kayıt: {len(data)}")

BATCH_SIZE = 100
batches = [data[i:i+BATCH_SIZE] for i in range(0, len(data), BATCH_SIZE)]
print(f"Batch sayısı: {len(batches)}")
print(f"Function URL: {FUNCTION_URL[:50]}...")

def upload_batch(batch_items):
    payload = json.dumps({"action": "insert", "items": batch_items}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(FUNCTION_URL, data=payload, headers={
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
    }, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            return result.get("inserted", 0), result.get("errors", 0), None
    except Exception as e:
        return 0, len(batch_items), str(e)

total_inserted = 0
total_errors = 0
start = time.time()

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(upload_batch, b): i for i, b in enumerate(batches)}
    done = 0
    for fut in as_completed(futures):
        ins, err, exc = fut.result()
        done += 1
        total_inserted += ins
        total_errors += err
        if done % 25 == 0 or done == len(batches):
            elapsed = time.time() - start
            rate = total_inserted / elapsed if elapsed > 0 else 0
            print(f"[{done}/{len(batches)}] Yüklenen: {total_inserted} | Hata: {total_errors} | {rate:.0f}/sn", flush=True)

print(f"\n=== TAMAMLANDI ===")
print(f"Toplam yüklenen: {total_inserted}")
print(f"Toplam hata: {total_errors}")
