#!/bin/bash

# Upload 8 batches sequentially
UPLOADED=0

for i in {1..8}; do
    batch_file=$(printf "batch_upload_%02d.json" $i)
    
    if [ ! -f "$batch_file" ]; then
        echo "❌ Batch $i file not found: $batch_file"
        continue
    fi
    
    # Count records in this batch
    count=$(python3 -c "import json; print(len(json.load(open('$batch_file'))))")
    
    echo "📤 Batch $i: $count records -> $batch_file"
    UPLOADED=$((UPLOADED + count))
    
done

echo ""
echo "==============="
echo "Total records ready: $UPLOADED"
echo "Ready for upload to ManufacturerLead"

