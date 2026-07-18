
import json
import sys
import os

# Load all batches
all_records = []

for file in ['batch_chunk1_part_1.json', 'batch_chunk1_part_2.json', 'chunk_2_upload.json']:
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            all_records.extend(json.load(f))

print(f"Total records loaded: {len(all_records)}")

# Upload in chunks of 100 using the Base44 API
# This will be called by automation
sys.exit(0)
