#!/usr/bin/env python3
"""
Mega Upload Runner - 490 kayıtı toplu yükle
"""
import json
import time
from pathlib import Path

def load_batch_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def split_into_chunks(records, chunk_size=50):
    """Recordları chunk_size'lı parçalara böl"""
    return [records[i:i+chunk_size] for i in range(0, len(records), chunk_size)]

# Batch dosyalarını topla
batch_files = {
    'batch_1_remaining': '/app/batch_1_remaining.json',  # 140
    'batch_2': '/app/upload_batch_part_2.json',  # 150
    'batch_3': '/app/upload_batch_part_3.json',  # 150
    'batch_4': '/app/upload_batch_part_4.json',  # 50
}

total_records = 0
all_chunks = []

for name, filepath in batch_files.items():
    try:
        data = load_batch_file(filepath)
        chunks = split_into_chunks(data, 50)
        total_records += len(data)
        all_chunks.extend([(name, chunk) for chunk in chunks])
        print(f"✓ {name}: {len(data)} kayıt → {len(chunks)} chunk")
    except FileNotFoundError:
        print(f"✗ {name}: Dosya bulunamadı")

print(f"\n📦 Toplam: {total_records} kayıt")
print(f"🔀 Parçalar: {len(all_chunks)} chunk (her biri max 50 kayıt)")
print(f"\nYükleme planı:")
for i, (batch_name, chunk) in enumerate(all_chunks[:5], 1):
    print(f"  {i}. {batch_name} - {len(chunk)} kayıt")
if len(all_chunks) > 5:
    print(f"  ... {len(all_chunks)-5} chunk daha")

print(f"\n✅ Upload runner hazır - 490 kayıt yüklenmeye hazır")

