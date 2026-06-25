#!/usr/bin/env python3
"""
Google Maps Places API Scraper — Shapelid Üretici Veri Toplama
Türkiye'deki 11 üretim teknolojisine sahip işletmeleri otomatik toplar.

Gerekli: GOOGLE_MAPS_API_KEY (Places API etkin)
"""

import os
import json
import time
import requests
from datetime import datetime

# ---- YAPILANDIRMA ----
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
BASE44_API_KEY = os.environ.get("BASE44_API_KEY", "")

PLACES_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
PLACES_PHOTO_URL = "https://maps.googleapis.com/maps/api/place/photo"

# Arama sorguları — hedef 11 teknolojiyi kapsıyor
SEARCH_QUERIES = [
    # Metal / DMLS / SLM
    "metal 3D baskı imalat hizmet",
    "DMLS metal lazer sinterleme",
    "SLM metal 3D baskı",
    "metal eklemeli imalat hizmet",
    # SLA
    "SLA stereolithography 3D baskı hizmet",
    "reçine 3D baskı imalat",
    # SLS
    "SLS seçici lazer sinterleme 3D baskı",
    "polyamid toz 3D baskı hizmet",
    # FDM
    "FDM 3D baskı imalat hizmet",
    "endüstriyel 3D baskı hizmet",
    # MJF
    "HP Multi Jet Fusion 3D baskı",
    "MJF 3D baskı hizmet",
    # Polyjet
    "Polyjet 3D baskı hizmet",
    "Stratasys 3D baskı hizmet merkezi",
    # CNC
    "CNC torna freze imalat hizmet",
    "CNC işleme merkezi talaşlı imalat",
    "hassas CNC frezeleme hizmet",
    "CNC torna hizmet sanayi",
    # EDM
    "tel erozyon imalat hizmet",
    "dalma erozyon EDM hizmet",
    "wire EDM kalıp imalat",
    "erozyon işleme talaşlı imalat",
    # Lazer Kesim
    "lazer kesim sac metal hizmet",
    "fiber lazer kesim imalat",
    "CNC lazer kesim abkant büküm",
    # Büküm
    "abkant büküm sac metal hizmet",
    "CNC abkant pres büküm imalat",
]

# Türkiye sanayi illeri — OSB'leri kapsayacak şekilde
LOCATIONS = [
    # İstanbul bölgesi
    {"name": "İstanbul Anadolu", "lat": 40.9, "lng": 29.2},
    {"name": "İstanbul Avrupa", "lat": 41.07, "lng": 28.8},
    {"name": "İstanbul İkitelli OSB", "lat": 41.06, "lng": 28.77},
    {"name": "İstanbul Tuzla OSB", "lat": 40.83, "lng": 29.38},
    {"name": "İstanbul Dudullu OSB", "lat": 40.99, "lng": 29.18},
    # Ankara
    {"name": "Ankara OSTİM OSB", "lat": 39.92, "lng": 32.73},
    {"name": "Ankara İvedik OSB", "lat": 39.99, "lng": 32.74},
    {"name": "Ankara Sincan OSB", "lat": 39.97, "lng": 32.58},
    # Bursa
    {"name": "Bursa BOSAB", "lat": 40.19, "lng": 29.06},
    {"name": "Bursa NOSAB", "lat": 40.22, "lng": 28.98},
    {"name": "Bursa DOSAB", "lat": 40.15, "lng": 29.16},
    # Kocaeli / Gebze
    {"name": "Kocaeli Gebze OSB", "lat": 40.77, "lng": 29.47},
    {"name": "Kocaeli Dilovası OSB", "lat": 40.79, "lng": 29.55},
    {"name": "İzmit", "lat": 40.77, "lng": 29.92},
    # İzmir
    {"name": "İzmir AOSB", "lat": 38.45, "lng": 27.22},
    {"name": "İzmir Kemalpaşa OSB", "lat": 38.41, "lng": 27.43},
    {"name": "İzmir Atatürk OSB", "lat": 38.42, "lng": 27.14},
    # Gaziantep
    {"name": "Gaziantep Küsget OSB", "lat": 37.07, "lng": 37.35},
    {"name": "Gaziantep", "lat": 37.06, "lng": 37.38},
    # Konya
    {"name": "Konya OSB", "lat": 37.87, "lng": 32.48},
    {"name": "Konya", "lat": 37.87, "lng": 32.49},
    # Kayseri
    {"name": "Kayseri OSB", "lat": 38.73, "lng": 35.48},
    {"name": "Kayseri", "lat": 38.72, "lng": 35.49},
    # Adana / Mersin
    {"name": "Adana HASOSB", "lat": 37.00, "lng": 35.33},
    {"name": "Mersin", "lat": 36.80, "lng": 34.64},
    # Eskişehir
    {"name": "Eskişehir OSB", "lat": 39.77, "lng": 30.47},
    # Sakarya
    {"name": "Sakarya Arifiye OSB", "lat": 40.72, "lng": 30.39},
    # Manisa
    {"name": "Manisa OSB", "lat": 38.62, "lng": 27.48},
    # Denizli
    {"name": "Denizli OSB", "lat": 37.75, "lng": 29.08},
    # Tekirdağ
    {"name": "Tekirdağ Çerkezköy OSB", "lat": 41.29, "lng": 27.98},
    # Samsun
    {"name": "Samsun OSB", "lat": 41.30, "lng": 36.35},
    # Trabzon
    {"name": "Trabzon OSB", "lat": 40.99, "lng": 39.71},
    # Antalya
    {"name": "Antalya OSB", "lat": 36.91, "lng": 30.73},
]


def search_places(query: str, location: dict, radius: int = 10000) -> list:
    """Google Places Text Search API ile arama yapar."""
    params = {
        "query": query,
        "location": f"{location['lat']},{location['lng']}",
        "radius": radius,
        "language": "tr",
        "region": "tr",
        "key": GOOGLE_MAPS_API_KEY,
    }
    
    results = []
    next_page_token = None
    
    while True:
        if next_page_token:
            params["pagetoken"] = next_page_token
            time.sleep(2)  # next_page_token için bekleme
        
        resp = requests.get(PLACES_SEARCH_URL, params=params, timeout=15)
        data = resp.json()
        
        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            print(f"    API Hatası: {data.get('status')} — {data.get('error_message','')}")
            break
        
        results.extend(data.get("results", []))
        next_page_token = data.get("next_page_token")
        
        if not next_page_token or len(results) >= 60:
            break
    
    return results


def get_place_details(place_id: str) -> dict:
    """Belirli bir yerin detaylarını çeker."""
    params = {
        "place_id": place_id,
        "fields": "name,formatted_phone_number,website,formatted_address,geometry,rating,photos,url",
        "language": "tr",
        "key": GOOGLE_MAPS_API_KEY,
    }
    
    resp = requests.get(PLACES_DETAILS_URL, params=params, timeout=15)
    data = resp.json()
    
    if data.get("status") == "OK":
        return data.get("result", {})
    return {}


def get_photo_url(photo_reference: str, max_width: int = 800) -> str:
    """Fotoğraf URL'si oluşturur."""
    return (
        f"{PLACES_PHOTO_URL}?maxwidth={max_width}"
        f"&photo_reference={photo_reference}"
        f"&key={GOOGLE_MAPS_API_KEY}"
    )


def extract_city_from_address(address: str) -> str:
    """Adresten il ismini çıkarır."""
    turkey_cities = [
        "İstanbul", "Istanbul", "Ankara", "İzmir", "Izmir", "Bursa", "Kocaeli",
        "Gaziantep", "Konya", "Kayseri", "Adana", "Mersin", "Eskişehir", "Eskisehir",
        "Sakarya", "Manisa", "Denizli", "Tekirdağ", "Tekirdag", "Samsun", "Antalya",
        "Trabzon", "Yalova", "Zonguldak", "Balıkesir", "Balikesir", "Gebze", "Izmit",
    ]
    for city in turkey_cities:
        if city.lower() in address.lower():
            return city
    return ""


def process_place(place: dict, location_name: str) -> dict:
    """Ham place verisini ManufacturerLead formatına dönüştürür."""
    place_id = place.get("place_id", "")
    
    # Detayları çek
    details = get_place_details(place_id) if place_id else {}
    
    name = details.get("name") or place.get("name", "")
    phone = details.get("formatted_phone_number", "") or ""
    website = details.get("website", "") or ""
    address = details.get("formatted_address") or place.get("formatted_address", "") or ""
    maps_url = details.get("url", "") or f"https://maps.google.com/?cid={place_id}"
    rating = details.get("rating") or place.get("rating")
    
    # Fotoğraf URL'leri
    media_urls = []
    photos = details.get("photos", []) or place.get("photos", [])
    for photo in photos[:5]:
        ref = photo.get("photo_reference", "")
        if ref:
            media_urls.append(get_photo_url(ref))
    
    city = extract_city_from_address(address)
    
    return {
        "company_name": name,
        "phone": phone,
        "address": address,
        "city": city,
        "website": website,
        "google_maps_url": maps_url,
        "google_rating": float(rating) if rating else None,
        "media_urls": media_urls,
        "source": "Google Maps API",
        "source_url": maps_url,
        "verification_status": "Taslak",
        "notes": f"Arama: {location_name}. Types: {', '.join(place.get('types', [])[:3])}",
        "_place_id": place_id,  # deduplicate için
    }


def main():
    if not GOOGLE_MAPS_API_KEY:
        print("HATA: GOOGLE_MAPS_API_KEY bulunamadı!")
        print("Lütfen Google Maps API anahtarınızı ayarlayın.")
        return
    
    all_results = []
    seen_place_ids = set()
    total = len(SEARCH_QUERIES) * len(LOCATIONS)
    count = 0
    
    print(f"Toplam {total} sorgu × {len(LOCATIONS)} lokasyon")
    print(f"Başlangıç: {datetime.now().strftime('%H:%M:%S')}\n")
    
    for location in LOCATIONS:
        print(f"\n📍 {location['name']}")
        
        for query in SEARCH_QUERIES:
            count += 1
            print(f"  [{count}/{total}] {query[:40]}...")
            
            try:
                places = search_places(query, location)
                new_count = 0
                
                for place in places:
                    pid = place.get("place_id", "")
                    if pid and pid not in seen_place_ids:
                        seen_place_ids.add(pid)
                        time.sleep(0.3)  # Details API için küçük bekleme
                        processed = process_place(place, location["name"])
                        
                        # Boş isim veya adres olmayanları atla
                        if processed["company_name"] and processed["address"]:
                            all_results.append(processed)
                            new_count += 1
                
                print(f"    +{new_count} yeni (toplam: {len(all_results)})")
                time.sleep(0.5)
                
            except Exception as e:
                print(f"    HATA: {e}")
                time.sleep(3)
        
        # Her şehir sonrası ara kaydet
        save_progress(all_results)
    
    # Son kayıt
    save_progress(all_results)
    print(f"\n{'='*60}")
    print(f"✅ TAMAMLANDI: {len(all_results)} benzersiz firma toplandı")
    print(f"Bitiş: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")


def save_progress(results: list):
    """Ara kayıt yapar."""
    os.makedirs("scraper", exist_ok=True)
    with open("scraper/raw_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"  💾 Kaydedildi: {len(results)} kayıt")


if __name__ == "__main__":
    main()
