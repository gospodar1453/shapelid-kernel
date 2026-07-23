#!/usr/bin/env python3
"""Bulk upload remaining 139 manufacturer records"""

import json
import time
import subprocess
import sys

def load_chunk(chunk_num):
    """Load a tool chunk"""
    filename = f'tool_chunk_{chunk_num}.json'
    with open(filename, 'r') as f:
        return json.load(f)

def prepare_api_call(records):
    """Prepare records for API call"""
    return records

# Load all tool chunks
all_records = []
for i in range(1, 8):
    chunk = load_chunk(i)
    all_records.extend(chunk)

print(f"Loaded {len(all_records)} records total")

# Group into smaller batches for API upload (max ~20 per call)
batches = []
batch_size = 20
for i in range(0, len(all_records), batch_size):
    batch = all_records[i:i+batch_size]
    batches.append(batch)

print(f"Organized into {len(batches)} API batches:")
for idx, batch in enumerate(batches):
    print(f"  Batch {idx+1}: {len(batch)} records")

# Save batches for manual upload
for idx, batch in enumerate(batches):
    filename = f'api_batch_{idx+1}.json'
    with open(filename, 'w') as f:
        json.dump(batch, f, ensure_ascii=False)
    print(f"Saved {filename}")

print(f"\nTotal records ready: {len(all_records)}")
print("Previous uploads: 19 records")
print("New total when complete: 3907 + 158 = 4065 records")
