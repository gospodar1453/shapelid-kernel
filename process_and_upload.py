import json

# Read the batch file
with open('/app/manufacturer_batch_20260717_060127.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Deduplicate records by company_name + address
seen = {}
unique_records = []
for record in data['records']:
    key = (record['company_name'], record['address'])
    if key not in seen:
        seen[key] = True
        unique_records.append(record)

print(f"Original records: {len(data['records'])}")
print(f"After deduplication: {len(unique_records)}")

# Save deduplicated batch
with open('/app/batch_to_upload.json', 'w', encoding='utf-8') as f:
    json.dump(unique_records, f, ensure_ascii=False, indent=2)

print(f"Ready for upload: /app/batch_to_upload.json")

