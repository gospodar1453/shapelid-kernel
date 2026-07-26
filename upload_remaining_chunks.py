
import json
import sys

# Chunk 1 micro-batches upload
for batch_idx in range(4):
    batch_file = f'/app/_micro_chunk1_batch_{batch_idx}.json'
    with open(batch_file) as f:
        batch_data = json.load(f)
    print(f"[MB {batch_idx}] Ready: {len(batch_data)} records")

# Chunks 2 ve 3'ü de micro-batch'le
for chunk_idx in [2, 3]:
    chunk_file = f'/app/_upload_chunk_batch_{chunk_idx}.json'
    with open(chunk_file) as f:
        chunk_data = json.load(f)
    
    micro_batch_size = 25
    batch_count = (len(chunk_data) + micro_batch_size - 1) // micro_batch_size
    print(f"[CHUNK {chunk_idx}] {len(chunk_data)} records → {batch_count} micro-batches")
