#!/usr/bin/env python3
import json
import sys
import os

# This script will be called by the automation to upload records in chunks

def load_json_file(filepath):
    """Load JSON file safely"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return []

def main():
    # Load all batches
    batches = [
        ('batch_chunk1_part_1.json', load_json_file('batch_chunk1_part_1.json')),
        ('batch_chunk1_part_2.json', load_json_file('batch_chunk1_part_2.json')),
        ('chunk_2_upload.json', load_json_file('chunk_2_upload.json'))
    ]
    
    total_records = sum(len(batch[1]) for batch in batches)
    print(f"Total records to upload: {total_records}")
    print("Batch files:")
    for name, data in batches:
        print(f"  - {name}: {len(data)} records")
    
    # Return file list for tool use
    return [b[0] for b in batches if b[1]]

if __name__ == '__main__':
    batch_files = main()
    print("\nBatch files ready:")
    for f in batch_files:
        print(f"  {f}")

