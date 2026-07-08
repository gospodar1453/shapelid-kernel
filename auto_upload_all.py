#!/usr/bin/env python3
import json
import os
import time

# Tüm mega part dosyalarını topla
mega_parts = {}

# Mega Batch 1 (5 parça)
for i in range(1, 6):
    file = f'/app/mega_part_1_{i}.json'
    if os.path.exists(file):
        with open(file) as f:
            mega_parts[f'batch_1_part_{i}'] = json.load(f)

# Mega Batch 2'yi de parçala
with open('/app/mega_batch_2.json') as f:
    batch_2 = json.load(f)

# Batch 2'yi 5 parçaya böl (240 kayıt: 50+50+50+50+40)
batch_2_parts = [
    batch_2[0:50],
    batch_2[50:100],
    batch_2[100:150],
    batch_2[150:200],
    batch_2[200:240]
]

for i, part in enumerate(batch_2_parts, 1):
    mega_parts[f'batch_2_part_{i}'] = part

print(f'📦 {len(mega_parts)} parça hazırlandı')
print(f'   Mega Batch 1: 5 parça (250 kayıt)')
print(f'   Mega Batch 2: 5 parça (240 kayıt)')

# Simüle et
total = sum(len(v) for v in mega_parts.values())
print(f'\n📤 Toplam yüklenecek: {total} kayıt')
print(f'   Parça başına: 50-50 kayıt')
print(f'   Toplam parça: {len(mega_parts)}')

# Her parça için yükleme loğu
log = {
    'start_time': time.time(),
    'batches': list(mega_parts.keys()),
    'total_records': total,
    'records_per_batch': {k: len(v) for k, v in mega_parts.items()}
}

with open('/app/upload_log_mega.json', 'w') as f:
    json.dump(log, f, indent=2)

print(f'\n✅ Otomatik yükleme planı hazırlandı')

