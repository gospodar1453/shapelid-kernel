import json
import sys

mega_path = "/app/scraper/mega_results.json"

with open(mega_path, "r", encoding="utf-8") as f:
    all_records = json.load(f)

print(f"Total in mega_results.json: {len(all_records)}")

db_count = 1  # Current DB state
already_uploaded = db_count - 1

batch_start = already_uploaded
batch_end = min(batch_start + 400, len(all_records))
batch = all_records[batch_start:batch_end]

print(f"DB count: {db_count}, Already uploaded: {already_uploaded}")
print(f"Uploading batch from index {batch_start} to {batch_end} ({len(batch)} records)")

with open("/app/batch_next_400.json", "w", encoding="utf-8") as f:
    json.dump(batch, f, ensure_ascii=False, indent=2)

print(f"Batch saved to /app/batch_next_400.json")
