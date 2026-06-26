#!/usr/bin/env python3
"""
Google Maps Places API Scraper - Shapelid
Türkiye'deki 11 üretim teknolojisine sahip firmaları toplar.
Text Search + Place Details ile her firmaya tam bilgi çeker.
"""

import os, json, time, requests
from datetime import datetime

API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
BASE_SEARCH = "https://maps.googleapis.com/maps/api/place/textsearch/json"
BASE_DETAIL = "https://maps.googleapis.com/maps/api/place/details/json"

# 20 öncelikli şehir
CITIES = [
    "İstanbul", "Ankara", "Bursa", "İzmir", "Kocaeli",
    "Sakarya", "Konya", "Kayseri", "Gaziantep", "Eskişehir",
    "Adana", "Mersin", "Tekirdağ", "Denizli", "Manisa",
    "Samsun", "Trabzon", "Hatay", "Antalya", "Diyarbakır",
    "Kırıkkale", "Karabük", "Zonguldak", "Gebze", "Çorlu"
]

# Arama sorguları — teknoloji x şehir kombinasyonu
TECH_QUERIES = [
    "CNC torna fason imalat",
    "CNC freze talaşlı imalat",
    "fiber lazer kesim sac",
    "lazer kesim büküm abkant",
    "tel erozyon EDM fason",
    "3D baskı FDM hizmet",
    "metal lazer kesim OSB",
    "CNC işleme merkezi fason",
    "sac büküm pres metal",
    "dalma erozyon EDM",
]

CAP_MAP = {
    "Direct Metal Laser Sintering": ["dmls","metal 3d","slm","direkt metal laser","metal yazıcı"],
    "Stereolithography": ["sla","stereolitografi","resin","reçine 3d"],
    "Polyjet": ["polyjet","poly jet","stratasys"],
    "Selective laser sintering": ["sls","selective laser","toz 3d","nylon 3d"],
    "Fused Deposition Modeling": ["fdm","fff","3d bask","3d yaz","filament","3d print","boyutlu bask","üç boyutlu"],
    "HP Multi Jet Fusion": ["mjf","multi jet fusion","hp 3d"],
    "CNC Turning": ["torna","cnc turn","otomat","kayar","tornalama","talaşlı"],
    "CNC Milling": ["freze","cnc mill","frezeleme","işleme merkezi","5 eksen","4 eksen"],
    "EDM Services": ["erozyon","edm","tel kesim","tel erezyon","dalma erozyon","spark erosion"],
    "Laser Cutting": ["lazer kesim","laser cut","fiber lazer","plazma kesim","cnc lazer","lazer metal","lazer sac"],
    "Bending": ["büküm","abkant","bending","boru bük","profil bük","sac büküm","sac işleme","pres bük"],
}

def get_caps(name, types_list, vicinity=""):
    text = (name + " " + " ".join(types_list or []) + " " + vicinity).lower()
    found = [cap for cap, kws in CAP_MAP.items() if any(kw in text for kw in kws)]
    return found if found else ["Laser Cutting"]

def search_places(query, city, page_token=None):
    params = {
        "query": f"{query} {city}",
        "key": API_KEY,
        "language": "tr",
        "region": "tr",
    }
    if page_token:
        params["pagetoken"] = page_token
    r = requests.get(BASE_SEARCH, params=params, timeout=15)
    return r.json()

def get_details(place_id):
    """Telefon, website, adres detayı için Places Details çağrısı"""
    params = {
        "place_id": place_id,
        "fields": "name,formatted_phone_number,international_phone_number,website,formatted_address,address_components,url,rating,user_ratings_total,photos,types",
        "key": API_KEY,
        "language": "tr",
    }
    r = requests.get(BASE_DETAIL, params=params, timeout=15)
    d = r.json().get("result", {})
    return d

def extract_city_from_components(components):
    """address_components'dan il adını çıkar"""
    for comp in components:
        types = comp.get("types", [])
        if "administrative_area_level_1" in types:
            return comp.get("long_name", "")
    for comp in components:
        types = comp.get("types", [])
        if "locality" in types:
            return comp.get("long_name", "")
    return ""

def scrape_all(cities=None, queries=None, max_per_query=60, output_file="gmaps_results.json"):
    cities = cities or CITIES
    queries = queries or TECH_QUERIES
    
    all_records = []
    seen_place_ids = set()
    total_api_calls = 0
    
    print(f"🚀 Google Maps API Scraper başladı")
    print(f"   Şehir: {len(cities)} | Sorgu: {len(queries)} | Max/sorgu: {max_per_query}")
    print(f"   Toplam kombinasyon: {len(cities) * len(queries)}\n")
    
    for city in cities:
        for query in queries:
            print(f"  🔍 {query} — {city}")
            page_token = None
            city_query_count = 0
            
            for page in range(3):  # max 3 sayfa = 60 sonuç/sorgu
                if page > 0:
                    time.sleep(2)  # pagetoken için bekle
                
                data = search_places(query, city, page_token)
                total_api_calls += 1
                status = data.get("status", "")
                
                if status not in ("OK", "ZERO_RESULTS"):
                    print(f"    ⚠️  API status: {status}")
                    break
                
                results = data.get("results", [])
                
                for place in results:
                    pid = place.get("place_id", "")
                    if pid in seen_place_ids:
                        continue
                    seen_place_ids.add(pid)
                    
                    # Details çek (telefon için zorunlu)
                    time.sleep(0.15)
                    total_api_calls += 1
                    details = get_details(pid)
                    
                    phone = details.get("international_phone_number", "") or details.get("formatted_phone_number", "")
                    address = details.get("formatted_address", "") or place.get("formatted_address", "")
                    name = details.get("name", "") or place.get("name", "")
                    
                    if not name or not phone or not address:
                        continue
                    
                    components = details.get("address_components", [])
                    city_name = extract_city_from_components(components) or city
                    
                    # Türkiye filtresi
                    if "Turkey" not in address and "Türkiye" not in address and "TR" not in address:
                        country_ok = any(
                            "country" in c.get("types", []) and c.get("short_name") == "TR"
                            for c in components
                        )
                        if not country_ok:
                            continue
                    
                    # Capability tespiti
                    types_list = details.get("types", place.get("types", []))
                    caps = get_caps(name, types_list, address)
                    
                    # Google Photos
                    photos = details.get("photos", [])
                    photo_ref = photos[0].get("photo_reference", "") if photos else ""
                    photo_url = ""
                    if photo_ref:
                        photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photo_reference={photo_ref}&key={API_KEY}"
                    
                    record = {
                        "company_name": name[:200],
                        "phone": phone,
                        "address": address,
                        "city": city_name,
                        "website": details.get("website", ""),
                        "google_maps_url": details.get("url", "") or f"https://www.google.com/maps/place/?q=place_id:{pid}",
                        "google_rating": details.get("rating"),
                        "capabilities": caps,
                        "source": "Google Maps API",
                        "source_url": f"https://www.google.com/maps/place/?q=place_id:{pid}",
                        "verification_status": "Taslak",
                        "notes": f"Yorum: {details.get('user_ratings_total',0)} | Query: {query} {city}",
                        "media_urls": [photo_url] if photo_url else [],
                    }
                    
                    all_records.append(record)
                    city_query_count += 1
                
                # Sonraki sayfa
                page_token = data.get("next_page_token")
                if not page_token or city_query_count >= max_per_query:
                    break
            
            print(f"    ✅ {city_query_count} kayıt | Toplam: {len(all_records)} | API calls: {total_api_calls}")
            time.sleep(0.5)
        
        # Şehir tamamlandığında ara kaydet
        with open(f"/app/scraper/{output_file}", "w", encoding="utf-8") as f:
            json.dump(all_records, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Kaydedildi: {len(all_records)} kayıt ({output_file})\n")
    
    print(f"\n✅ TAMAMLANDI: {len(all_records)} toplam kayıt, {total_api_calls} API çağrısı")
    return all_records

if __name__ == "__main__":
    scrape_all(
        cities=CITIES[:10],      # İlk 10 şehir
        queries=TECH_QUERIES,    # 10 sorgu
        max_per_query=40,
        output_file="gmaps_api_results.json"
    )
