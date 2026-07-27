#!/usr/bin/env python3
"""
Google Sheets - Wix ile örtüşmeyen satırları sil
Kalan 7391 request'i 100'lük batch'lerle gönder
"""
import json, urllib.request, os, time

token = os.environ.get('GOOGLESHEETS_ACCESS_TOKEN','')
if not token:
    # .env'den oku
    try:
        with open('/app/.agents/.env') as f:
            for line in f:
                if line.startswith('GOOGLESHEETS_ACCESS_TOKEN='):
                    token = line.strip().split('=',1)[1].strip('"').strip("'")
    except: pass

sheets_id = "1iU10AWTHZVkGlXoHawxJrnsCh7gUDmIjahlkl9T34_k"

with open('/app/sheets_remaining_requests.json') as f:
    all_requests = json.load(f)

print(f"Kalan request: {len(all_requests)}", flush=True)

BATCH_SIZE = 100
total_batches = (len(all_requests) + BATCH_SIZE - 1) // BATCH_SIZE
total_done = 0
total_rows_deleted = 0

for b in range(total_batches):
    batch = all_requests[b * BATCH_SIZE : (b+1) * BATCH_SIZE]
    body = json.dumps({"requests": batch}).encode()
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheets_id}:batchUpdate"
    req = urllib.request.Request(url, data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method='POST')
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            result = json.loads(r.read())
        total_done += len(batch)
        rows_in_batch = sum(
            r['deleteDimension']['range']['endIndex'] - r['deleteDimension']['range']['startIndex']
            for r in batch
        )
        total_rows_deleted += rows_in_batch
        if (b+1) % 10 == 0 or b == total_batches-1:
            print(f"Batch {b+1}/{total_batches} | {total_done}/{len(all_requests)} req | ~{total_rows_deleted} satır silindi", flush=True)
    except urllib.error.HTTPError as e:
        err = e.read().decode()[:200]
        print(f"Batch {b+1} HTTP {e.code}: {err}", flush=True)
        # 1 saniye bekle ve devam et
        time.sleep(1)
        continue
    except Exception as e:
        print(f"Batch {b+1} HATA: {e}", flush=True)
        time.sleep(2)
        continue
    
    # Rate limit koruması
    time.sleep(0.2)

print(f"\nTAMAM: {total_done}/{len(all_requests)} request | ~{total_rows_deleted} satır silindi", flush=True)
