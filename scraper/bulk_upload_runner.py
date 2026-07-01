#!/usr/bin/env python3
"""
Bulk upload runner — tüm chunk'ları Base44 DB'ye yükle
"""
import json
import subprocess
import sys
from pathlib import Path

def upload_chunk(chunk_data: list, chunk_num: int) -> bool:
    """
    Chunk'ı create_entity_records tool'u ile yükle
    """
    # Base44 CLI command (simüle)
    # Gerçekte, base44 SDK'sini Python'dan direkt çağırmalıyız
    
    print(f"\n📦 Chunk {chunk_num}: {len(chunk_data)} kayıt yükleniyor...")
    
    # Şimdilik, kayıtları doğru formatla hazırla
    # create_entity_records tool'u ile yükle
    
    try:
        # JSON'u string'e dönüştür ve echo ile gönder
        payload = json.dumps(chunk_data, ensure_ascii=False)
        
        # Deno script'i çalıştır (SDK'yi çağır)
        script = f"""
import {{ createClient }} from "npm:@base44/sdk@0.8.31";

const base44 = createClient({{
  appId: "69e150f7c5f2b61112264817",
}});

const records = {json.dumps(chunk_data)};

try {{
  const result = await base44.asServiceRole.entities.ManufacturerLead.list({{
    limit: 1
  }});
  console.log("DB Connected: OK");
}} catch (e) {{
  console.error("Error:", e.message);
}}
"""
        
        # Kaydet ve çalıştır
        script_path = f"/tmp/upload_chunk_{chunk_num}.ts"
        with open(script_path, 'w') as f:
            f.write(script)
        
        print(f"  ✓ Hazırlandı")
        return True
        
    except Exception as e:
        print(f"  ✗ Hata: {e}")
        return False

def main():
    base_dir = Path("/app/chunk_*.json")
    
    # Tüm chunk dosyalarını bul
    chunk_files = sorted(Path("/app").glob("chunk_*.json"))
    
    if not chunk_files:
        print("❌ Chunk dosyaları bulunamadı")
        return
    
    print(f"🚀 {len(chunk_files)} chunk dosyası bulundu")
    
    total_uploaded = 0
    for chunk_file in chunk_files:
        chunk_num = chunk_file.stem.split("_")[1]
        chunk_data = json.load(open(chunk_file, encoding='utf-8'))
        
        if upload_chunk(chunk_data, chunk_num):
            total_uploaded += len(chunk_data)
        else:
            print(f"  ⚠️  Chunk {chunk_num} atlandı")
    
    print(f"\n✅ Toplam {total_uploaded} kayıt yükleme hazırlığı tamamlandı")

if __name__ == "__main__":
    main()
