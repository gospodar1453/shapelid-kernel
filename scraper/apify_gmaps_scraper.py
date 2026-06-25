#!/usr/bin/env python3
"""
Apify Google Maps Scraper - Shapelid Manufacturer Lead Collection
Hedef: Türkiye'deki 11 üretim teknolojisine sahip firmaları topla
"""

import os
import json
import time
import requests
from datetime import datetime

APIFY_TOKEN = os.environ.get("APIFY_API_TOKEN", "")
ACTOR_ID = "compass~crawler-google-places"
BASE_URL = "https://api.apify.com/v2"

# Hedef teknolojiler ve arama terimleri
SEARCH_QUERIES = [
    # 3D Baskı teknolojileri
    "DMLS metal 3D baskı Türkiye",
    "SLA 3D baskı hizmet Türkiye",
    "SLS 3D baskı hizmet Türkiye",
    "Polyjet 3D baskı hizmet Türkiye",
    "FDM 3D baskı hizmet Türkiye",
    "MJF HP Multi Jet Fusion 3D baskı Türkiye",
    # CNC İmalat
    "CNC torna fason imalat OSB",
    "CNC freze fason imalat OSB",
    "CNC talaşlı imalat sanayi",
    # EDM
    "tel erozyon EDM hizmet Türkiye",
    "dalma erozyon EDM imalat",
    # Lazer & Büküm
    "fiber lazer kesim sac büküm",
    "CNC lazer kesim abkant büküm",
    "lazer kesim büküm OSB sanayi",
]

# Öncelikli şehirler (sanayi yoğun)
CITIES = [
    "İstanbul", "Ankara", "Bursa", "İzmir", "Kocaeli",
    "Sakarya", "Konya", "Kayseri", "Gaziantep", "Eskişehir",
    "Adana", "Mersin", "Tekirdağ", "Denizli", "Manisa",
    "Samsun", "Trabzon", "Hatay", "Antalya", "Diyarbakır"
]

def run_actor(search_terms: list, max_crawled: int = 200) -> str:
    """Apify actor'ı başlat ve run ID döndür"""
    url = f"{BASE_URL}/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}"
    
    payload = {
        "searchStringsArray": search_terms,
        "maxCrawledPlacesPerSearch": max_crawled,
        "language": "tr",
        "countryCode": "tr",
        "includeWebResults": False,
        "exportPlaceUrls": False,
        "additionalInfo": False,
        "reviewsSort": "newest",
        "maxReviews": 0,
        "maxImages": 0,
        "scrapeDirectories": False,
        "deeperCityScrape": False,
    }
    
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    run_id = data["data"]["id"]
    print(f"✅ Actor başlatıldı. Run ID: {run_id}")
    return run_id

def wait_for_run(run_id: str, timeout_min: int = 30) -> bool:
    """Run tamamlanana kadar bekle"""
    url = f"{BASE_URL}/actor-runs/{run_id}?token={APIFY_TOKEN}"
    deadline = time.time() + timeout_min * 60
    
    while time.time() < deadline:
        resp = requests.get(url, timeout=15)
        status = resp.json()["data"]["status"]
        print(f"  Status: {status} [{datetime.now().strftime('%H:%M:%S')}]")
        
        if status == "SUCCEEDED":
            return True
        elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
            print(f"❌ Run failed: {status}")
            return False
        
        time.sleep(30)
    
    print("⏰ Timeout!")
    return False

def fetch_results(run_id: str) -> list:
    """Run sonuçlarını çek"""
    url = f"{BASE_URL}/actor-runs/{run_id}/dataset/items?token={APIFY_TOKEN}&format=json&clean=true"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.json()

def map_capabilities(title: str, categories: list) -> list:
    """Firma adı ve kategori'den capabilities belirle"""
    text = (title + " " + " ".join(categories or [])).lower()
    caps = []
    
    mapping = {
        "Direct Metal Laser Sintering": ["dmls", "metal 3d", "metal yaz", "slm", "direkt metal"],
        "Stereolithography": ["sla", "stereolitografi", "resin", "reçine 3d"],
        "Polyjet": ["polyjet", "poly jet", "stratasys"],
        "Selective laser sintering": ["sls", "selective laser", "toz 3d", "nylon 3d"],
        "Fused Deposition Modeling": ["fdm", "fff", "3d bask", "3d yaz", "filament", "3d print"],
        "HP Multi Jet Fusion": ["mjf", "multi jet fusion", "hp 3d"],
        "CNC Turning": ["torna", "cnc turn", "otomat", "kayar"],
        "CNC Milling": ["freze", "cnc mill", "frezeleme", "işleme merkezi", "talaşlı"],
        "EDM Services": ["erozyon", "edm", "tel kesim", "molibden", "dalma erozyon"],
        "Laser Cutting": ["lazer kesim", "laser cut", "fiber lazer", "plazma kesim", "cnc lazer"],
        "Bending": ["büküm", "abkant", "bending", "boru bük", "profil bük", "sac büküm"],
    }
    
    for cap, keywords in mapping.items():
        if any(kw in text for kw in keywords):
            caps.append(cap)
    
    return caps if caps else ["CNC Milling"]  # fallback

def clean_record(place: dict) -> dict | None:
    """Ham Apify verisini ManufacturerLead formatına dönüştür"""
    title = place.get("title", "")
    phone = place.get("phone", "") or place.get("phoneUnformatted", "")
    address = place.get("address", "") or place.get("street", "")
    city = place.get("city", "") or place.get("state", "")
    
    # Minimum veri kontrolü
    if not title or not phone or not address:
        return None
    
    # Türkiye filtresi
    country = place.get("countryCode", "")
    if country and country.upper() not in ("TR", "TUR", ""):
        return None
    
    capabilities = map_capabilities(title, place.get("categories", []))
    
    return {
        "company_name": title,
        "phone": phone,
        "address": address,
        "city": city,
        "website": place.get("website", ""),
        "email": place.get("email", ""),
        "google_maps_url": place.get("url", "") or place.get("googleMapsUrl", ""),
        "google_rating": place.get("totalScore") or place.get("rating"),
        "capabilities": capabilities,
        "source": "Apify Google Maps",
        "source_url": place.get("url", ""),
        "verification_status": "Taslak",
        "notes": f"Kategoriler: {', '.join(place.get('categories', [])[:3])}",
    }

def batch_upload(records: list, batch_size: int = 50) -> int:
    """Base44 entity'ye toplu yükle"""
    import sys
    sys.path.insert(0, "/app")
    
    # Base44 SDK ile yükle
    token = os.environ.get("BASE44_SERVICE_TOKEN", "")
    app_id = "69e150f7c5f2b61112264817"
    url = f"https://api.base44.com/api/apps/{app_id}/entities/ManufacturerLead"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    total_uploaded = 0
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        for record in batch:
            try:
                resp = requests.post(url, json=record, headers=headers, timeout=10)
                if resp.status_code in (200, 201):
                    total_uploaded += 1
                else:
                    print(f"  ⚠️ Upload error: {resp.status_code} - {record['company_name'][:30]}")
            except Exception as e:
                print(f"  ❌ Exception: {e}")
        print(f"  📤 {total_uploaded}/{len(records)} yüklendi...")
        time.sleep(0.5)
    
    return total_uploaded

def main():
    print("🚀 Apify Google Maps Scraper başlatılıyor...")
    print(f"Token: {APIFY_TOKEN[:15]}...")
    
    # İlk batch: tüm şehirler x temel sorgular
    search_terms = []
    for city in CITIES[:10]:  # İlk 10 şehir
        for tech in ["CNC torna fason imalat", "lazer kesim büküm", "3D baskı hizmet", "tel erozyon EDM"]:
            search_terms.append(f"{tech} {city}")
    
    print(f"\n📋 {len(search_terms)} arama terimi hazırlandı")
    print("Örnek:", search_terms[:3])
    
    # Actor çalıştır
    run_id = run_actor(search_terms, max_crawled=50)
    
    # Bekle
    print("\n⏳ Sonuçlar bekleniyor...")
    success = wait_for_run(run_id, timeout_min=20)
    
    if not success:
        print("❌ Run başarısız!")
        return
    
    # Sonuçları çek
    print("\n📥 Sonuçlar indiriliyor...")
    raw_results = fetch_results(run_id)
    print(f"Ham kayıt sayısı: {len(raw_results)}")
    
    # Ham veriyi kaydet
    with open("/app/scraper/apify_raw_latest.json", "w", encoding="utf-8") as f:
        json.dump(raw_results, f, ensure_ascii=False, indent=2)
    
    # Temizle
    cleaned = []
    for place in raw_results:
        record = clean_record(place)
        if record:
            cleaned.append(record)
    
    print(f"Geçerli kayıt sayısı: {len(cleaned)}")
    
    # Temiz veriyi kaydet
    with open("/app/scraper/apify_clean_latest.json", "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    
    # Veritabanına yükle
    print("\n📤 Veritabanına yükleniyor...")
    uploaded = batch_upload(cleaned)
    print(f"\n✅ Tamamlandı! {uploaded} firma veritabanına eklendi.")

if __name__ == "__main__":
    main()
