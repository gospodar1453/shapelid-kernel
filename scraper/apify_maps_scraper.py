#!/usr/bin/env python3
"""
Apify Google Maps Scraper — Shapelid Üretici Veri Toplama
Türkiye'deki 11 üretim teknolojisine sahip işletmeleri otomatik toplar.
"""

import os
import json
import time
import requests
from apify_client import ApifyClient

# ---- YAPILANDIRMA ----
APIFY_API_TOKEN = os.environ.get("APIFY_API_TOKEN", "")

# Hedef arama terimleri — her biri Türkiye'deki farklı üretim tipini kapsar
SEARCH_QUERIES = [
    # 3D Baskı
    "metal 3D baskı hizmet",
    "DMLS metal 3D baskı",
    "SLA 3D baskı hizmet",
    "SLS 3D baskı hizmet",
    "FDM 3D baskı hizmet",
    "HP MJF 3D baskı hizmet",
    "Polyjet 3D baskı hizmet",
    "3D baskı imalat merkezi",
    # CNC
    "CNC torna freze imalat",
    "CNC işleme merkezi hizmet",
    "talaşlı imalat CNC",
    # EDM
    "tel erozyon hizmet",
    "dalma erozyon EDM imalat",
    "wire EDM kalıp imalat",
    # Lazer & Büküm
    "lazer kesim abkant büküm metal",
    "fiber lazer kesim sac metal",
    "CNC abkant büküm hizmet",
]

# Türkiye'nin sanayi ağırlıklı illeri
CITIES = [
    "Istanbul, Turkey",
    "Ankara, Turkey",
    "Bursa, Turkey",
    "Kocaeli, Turkey",
    "Izmir, Turkey",
    "Gaziantep, Turkey",
    "Konya, Turkey",
    "Kayseri, Turkey",
    "Adana, Turkey",
    "Mersin, Turkey",
    "Eskisehir, Turkey",
    "Sakarya, Turkey",
    "Manisa, Turkey",
    "Denizli, Turkey",
    "Tekirdag, Turkey",
    "Ankara, Turkey",
    "Samsun, Turkey",
    "Antalya, Turkey",
]

def run_apify_scraper(api_token: str, query: str, location: str, max_results: int = 50) -> list:
    """Apify Google Maps Scraper'ı çalıştırır."""
    client = ApifyClient(api_token)
    
    run_input = {
        "searchStringsArray": [f"{query} {location}"],
        "maxCrawledPlacesPerSearch": max_results,
        "language": "tr",
        "countryCode": "tr",
        "includeHistogramData": False,
        "includeOpeningHours": False,
        "includePeopleAlsoSearch": False,
        "exportPlaceUrls": False,
    }
    
    print(f"  Çalışıyor: {query} @ {location}")
    run = client.actor("compass/crawler-google-places").call(run_input=run_input)
    
    results = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        results.append(item)
    
    print(f"  → {len(results)} sonuç bulundu")
    return results


def extract_fields(place: dict) -> dict:
    """Apify sonucundan gerekli alanları çıkarır."""
    # Adres parçalama
    address = place.get("address", "") or ""
    city = ""
    district = ""
    
    addr_comps = place.get("addressParsed", {}) or {}
    city = addr_comps.get("city", "") or addr_comps.get("state", "") or ""
    district = addr_comps.get("neighborhood", "") or addr_comps.get("district", "") or ""
    
    # Telefon
    phone = place.get("phone", "") or place.get("phoneUnformatted", "") or ""
    
    # Website
    website = place.get("website", "") or ""
    
    # Google Maps URL
    maps_url = place.get("url", "") or place.get("googleMapsUrl", "") or ""
    
    # Rating
    rating = place.get("totalScore", None) or place.get("stars", None)
    
    # Görseller
    media_urls = []
    for img in (place.get("imageUrls", []) or [])[:5]:
        if img:
            media_urls.append(img)
    
    return {
        "company_name": place.get("title", ""),
        "phone": phone,
        "address": address,
        "city": city,
        "district": district,
        "website": website,
        "google_maps_url": maps_url,
        "google_rating": float(rating) if rating else None,
        "media_urls": media_urls,
        "source": "Google Maps / Apify",
        "source_url": maps_url,
        "verification_status": "Taslak",
        "notes": f"Kategori: {place.get('categoryName', '')}. Reviews: {place.get('reviewsCount', 0)}",
    }


def save_results(results: list, filename: str = "scraper/raw_results.json"):
    """Sonuçları JSON olarak kaydeder."""
    os.makedirs("scraper", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✓ {len(results)} kayıt '{filename}' dosyasına kaydedildi.")


def main():
    if not APIFY_API_TOKEN:
        print("HATA: APIFY_API_TOKEN bulunamadı!")
        print("Lütfen Apify API token'ınızı ayarlayın.")
        return
    
    all_results = []
    seen_names = set()
    
    total_queries = len(SEARCH_QUERIES) * len(CITIES)
    print(f"Toplam {total_queries} sorgu çalıştırılacak...")
    print(f"Tahmini süre: ~{total_queries * 2} dakika\n")
    
    for city in CITIES:
        for query in SEARCH_QUERIES:
            try:
                places = run_apify_scraper(APIFY_API_TOKEN, query, city, max_results=20)
                
                for place in places:
                    name = place.get("title", "")
                    if name and name not in seen_names:
                        seen_names.add(name)
                        extracted = extract_fields(place)
                        all_results.append(extracted)
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                print(f"  HATA: {query} @ {city} — {e}")
                time.sleep(5)
    
    save_results(all_results)
    print(f"\n{'='*50}")
    print(f"TAMAMLANDI: {len(all_results)} benzersiz firma toplandı")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
