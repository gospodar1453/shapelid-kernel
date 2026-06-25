#!/usr/bin/env python3
"""
Google Maps sonuçlarını ManufacturerLead veritabanına yükler.
Minimum standart: şirket adı + telefon + adres
"""

import json
import os
import sys
import requests
from datetime import datetime

BASE44_API_URL = os.environ.get("BASE44_API_URL", "https://api.base44.com")
APP_ID = "69e150f7c5f2b61112264817"

# Teknoloji anahtar kelimeleri → capability eşleştirme
CAPABILITY_KEYWORDS = {
    "Direct Metal Laser Sintering": [
        "dmls", "metal 3d baskı", "metal lazer sinterleme", "slm", "metal eklemeli",
        "metal additive", "direct metal", "selective laser melting", "3d metal"
    ],
    "Stereolithography": [
        "sla", "stereolithography", "reçine baskı", "resin print", "stereolito",
        "dlp baskı", "reçineli baskı"
    ],
    "Polyjet": [
        "polyjet", "poly jet", "stratasys j850", "stratasys j750", "material jetting",
        "çok malzemeli baskı", "multijet"
    ],
    "Selective laser sintering": [
        "sls", "selective laser sintering", "seçici lazer sinterleme", "nylon toz",
        "pa12 3d", "toz sinterleme"
    ],
    "Fused Deposition Modeling": [
        "fdm", "fused deposition", "fff", "filament baskı", "3d baskı",
        "ekstrüzyon baskı", "fdm baskı"
    ],
    "HP Multi Jet Fusion": [
        "mjf", "multi jet fusion", "hp mjf", "hp 3d", "hp multi jet",
        "fusion 3d"
    ],
    "CNC Turning": [
        "cnc torna", "cnc turning", "talaşlı imalat", "torna hizmet",
        "tornalama", "cnc talaşlı"
    ],
    "CNC Milling": [
        "cnc freze", "cnc frezeleme", "cnc milling", "işleme merkezi",
        "cnc işleme", "5 eksen", "5eksen", "freze hizmet"
    ],
    "EDM Services": [
        "tel erozyon", "dalma erozyon", "edm", "wire edm", "elektro erozyon",
        "erozyon işleme", "erezyon"
    ],
    "Laser Cutting": [
        "lazer kesim", "laser cutting", "fiber lazer", "cnc lazer",
        "lazer cut", "lazer metal"
    ],
    "Bending": [
        "abkant", "büküm", "bending", "press brake", "sac büküm",
        "cnc büküm", "abkant büküm"
    ],
}


def detect_capabilities(text: str) -> list:
    """Metin içinden üretim kapabilitelerini tespit eder."""
    text_lower = text.lower()
    found = []
    
    for capability, keywords in CAPABILITY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                if capability not in found:
                    found.append(capability)
                break
    
    return found


def meets_minimum_standard(record: dict) -> bool:
    """Minimum veri standardını kontrol eder: isim + telefon + adres."""
    has_name = bool(record.get("company_name", "").strip())
    has_phone = bool(record.get("phone", "").strip()) and record.get("phone") != "+90 000 000 00 00"
    has_address = bool(record.get("address", "").strip())
    return has_name and has_phone and has_address


def load_raw_results(filepath: str = "scraper/raw_results.json") -> list:
    """Ham sonuçları yükler."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def prepare_record(raw: dict) -> dict:
    """Ham sonucu ManufacturerLead formatına hazırlar."""
    # Capability tespiti için tüm metin alanlarını birleştir
    search_text = " ".join([
        raw.get("company_name", ""),
        raw.get("notes", ""),
        raw.get("address", ""),
        raw.get("website", ""),
    ])
    
    capabilities = detect_capabilities(search_text)
    
    # Eğer capability bulunamazsa, varsayılan olarak genel imalat ekle
    if not capabilities:
        # Kategori tipine göre tahmin et
        notes_lower = raw.get("notes", "").lower()
        if "3d" in notes_lower:
            capabilities = ["Fused Deposition Modeling"]
        elif "cnc" in notes_lower or "metal" in notes_lower:
            capabilities = ["CNC Milling"]
        elif "lazer" in notes_lower or "laser" in notes_lower:
            capabilities = ["Laser Cutting"]
    
    record = {
        "company_name": raw.get("company_name", "").strip(),
        "phone": raw.get("phone", "").strip(),
        "address": raw.get("address", "").strip(),
        "city": raw.get("city", "").strip(),
        "district": raw.get("district", "").strip(),
        "website": raw.get("website", "").strip(),
        "google_maps_url": raw.get("google_maps_url", "").strip(),
        "google_rating": raw.get("google_rating"),
        "media_urls": raw.get("media_urls", []),
        "capabilities": capabilities,
        "source": raw.get("source", "Google Maps API"),
        "source_url": raw.get("source_url", "").strip(),
        "verification_status": "Taslak",
        "notes": raw.get("notes", ""),
    }
    
    # OSB tespiti
    address_lower = record["address"].lower()
    if "osb" in address_lower or "organize sanayi" in address_lower:
        for part in record["address"].split(","):
            if "osb" in part.lower() or "organize sanayi" in part.lower():
                record["osb_name"] = part.strip()
                break
    
    return record


def upload_batch(records: list, api_key: str, batch_size: int = 50) -> int:
    """Kayıtları toplu olarak yükler."""
    uploaded = 0
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        
        url = f"{BASE44_API_URL}/api/apps/{APP_ID}/entities/ManufacturerLead/bulk"
        resp = requests.post(url, json={"records": batch}, headers=headers, timeout=30)
        
        if resp.status_code in (200, 201):
            uploaded += len(batch)
            print(f"  ✓ Batch {i//batch_size + 1}: {len(batch)} kayıt yüklendi")
        else:
            print(f"  ✗ Batch {i//batch_size + 1} HATA: {resp.status_code} — {resp.text[:200]}")
    
    return uploaded


def main():
    api_key = os.environ.get("BASE44_API_KEY", "")
    
    filepath = sys.argv[1] if len(sys.argv) > 1 else "scraper/raw_results.json"
    
    if not os.path.exists(filepath):
        print(f"HATA: '{filepath}' bulunamadı!")
        return
    
    print(f"Yükleniyor: {filepath}")
    raw_results = load_raw_results(filepath)
    print(f"Ham kayıt sayısı: {len(raw_results)}")
    
    # Hazırlık ve filtreleme
    valid_records = []
    skipped = 0
    
    for raw in raw_results:
        record = prepare_record(raw)
        if meets_minimum_standard(record):
            valid_records.append(record)
        else:
            skipped += 1
    
    print(f"Geçerli kayıt: {len(valid_records)} | Atlanan: {skipped}")
    
    if not valid_records:
        print("Yüklenecek kayıt yok.")
        return
    
    if not api_key:
        # API key yoksa sadece hazır kayıtları göster
        print("\nAPI key bulunamadı — kayıtlar 'scraper/ready_to_upload.json' olarak kaydedildi.")
        with open("scraper/ready_to_upload.json", "w", encoding="utf-8") as f:
            json.dump(valid_records, f, ensure_ascii=False, indent=2)
        return
    
    print(f"\n{len(valid_records)} kayıt veritabanına yükleniyor...")
    uploaded = upload_batch(valid_records, api_key)
    
    print(f"\n{'='*50}")
    print(f"✅ {uploaded} kayıt başarıyla yüklendi!")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
