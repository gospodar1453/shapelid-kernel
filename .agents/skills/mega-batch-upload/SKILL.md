# Mega Batch Upload

Uploads ManufacturerLead records from pre-prepared chunks in `/app/upload_chunk_manifest_*.json` files.

**Usage:**
```bash
run_skill mega-batch-upload
```

**What it does:**
- Uploads 8 chunks of 50 records each (400 total) to ManufacturerLead entity
- Handles chunked uploads to avoid payload limits
- Reports success/failure for each chunk
- Tracks total upload count

**Input files:**
- `/app/upload_chunk_manifest_0.json` through `_7.json`

**Output:**
- Console log with upload progress
- Summary of uploaded vs failed records
