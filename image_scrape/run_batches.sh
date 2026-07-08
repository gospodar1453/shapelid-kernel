#!/bin/bash
cd /app/image_scrape
LOG=/app/image_scrape/upload_log.txt
> "$LOG"
for f in batch_*.json; do
  echo "=== $f ===" | tee -a "$LOG"
  resp=$(curl -s -X POST "https://base44.app/api/apps/69e150f7c5f2b61112264817/functions/updateManufacturerImages" \
    -H "Authorization: Bearer $BASE44_SERVICE_TOKEN" \
    -H "Content-Type: application/json" \
    --data-binary @"$f")
  echo "$resp" | tee -a "$LOG"
  sleep 2
done
echo "TÜMÜ TAMAMLANDI" | tee -a "$LOG"
