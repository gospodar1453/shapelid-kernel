#!/usr/bin/env python3
"""
Apify Google Maps Bulk Scraper - FREE plan limitleri dahilinde
Her run ~$0.20, günde ~20 run = ~400 kayıt/gün ücretsiz
"""

import os, json, time, requests
from datetime import datetime

APIFY_TOKEN = os.environ.get("APIFY_API_TOKEN", "")
BASE_URL = "https://api.apify.com/v2"
ACTOR_ID = "compass~crawler-google-places"

CAP_MAP = {
    "Direct Metal Laser Sintering": ["dmls","metal 3d","slm","direkt metal laser"],
    "Stereolithography": ["sla","stereolitografi","resin","reçine 3d"],
    "Polyjet": ["polyjet","poly jet","stratasys"],
    "Selective laser sintering": ["sls","selective laser","toz 3d","nylon 3d"],
    "Fused Deposition Modeling": ["fdm","fff","3d bask","3d yaz","filament","3d print","boyutlu"],
    "HP Multi Jet Fusion": ["mjf","multi jet fusion","hp 3d"],
    "CNC Turning": ["torna","cnc turn","otomat","kayar","tornalama","talaşlı"],
    "CNC Milling": ["freze","cnc mill","frezeleme","işleme merkezi","5 eksen"],
    "EDM Services": ["erozyon","edm","tel kesim","tel erezyon","dalma erozyon"],
    "Laser Cutting": ["lazer kesim","laser cut","fiber lazer","plazma kesim","cnc lazer","lazer metal"],
    "Bending": ["büküm","abkant","bending","boru bük","profil bük","sac büküm","sac-pres"],
}

def get_caps(title, cats):
    text = (title + " " + " ".join(cats or [])).lower()
    found = [cap for cap, kws in CAP_MAP.items() if any(kw in text for kw in kws)]
    return found if found else ["Laser Cutting"]

def run_apify(search_terms, max_per_search=25):
    """Apify actor çalıştır, tamamlanana kadar bekle, sonuçları döndür"""
    # Run başlat
    resp = requests.post(
        f"{BASE_URL}/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}",
        json={
            "searchStringsArray": search_terms,
            "maxCrawledPlacesPerSearch": max_per_search,
            "language": "tr",
            "countryCode": "tr",
            "maxReviews": 0,
            "maxImages": 0,
        },
        timeout=30
    )
    if resp.status_code not in (200, 201):
        print(f"  ❌ Run başlatılamadı: {resp.status_code} {resp.text[:200]}")
        return []
    
    run_id = resp.json()["data"]["id"]
    print(f"  Run ID: {run_id}")
    
    # Tamamlanana kadar bekle (max 15 dk)
    for i in range(45):
        time.sleep(20)
        r = requests.get(f"{BASE_URL}/actor-runs/{run_id}?token={APIFY_TOKEN}", timeout=10)
        status = r.json()["data"]["status"]
        usd = r.json()["data"].get("usageTotalUsd", 0) or 0
        
        # Dataset boyutunu kontrol et
        r2 = requests.get(f"{BASE_URL}/actor-runs/{run_id}/dataset?token={APIFY_TOKEN}", timeout=10)
        count = r2.json()["data"].get("itemCount", 0)
        
        print(f"    [{i+1}] {status} | {count} items | ${usd:.3f}")
        
        if status == "SUCCEEDED":
            break
        elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
            print(f"  ⚠️  Run {status}, mevcut {count} kayıtla devam ediliyor")
            break
    
    # Sonuçları çek
    items_resp = requests.get(
        f"{BASE_URL}/actor-runs/{run_id}/dataset/items?token={APIFY_TOKEN}&format=json&clean=true&limit=1000",
        timeout=60
    )
    return items_resp.json()

def clean_apify_record(item):
    title = item.get("title", "").strip()
    phone = item.get("phone", "") or item.get("phoneUnformatted", "")
    address = item.get("address", "") or item.get("street", "")
    city = item.get("state", "") or item.get("city", "")
    
    if not title or not phone or not address:
        return None
    if item.get("permanentlyClosed") or item.get("temporarilyClosed"):
        return None
    country = item.get("countryCode", "")
    if country and country.upper() not in ("TR", "TUR", ""):
        return None
    
    caps = get_caps(title, item.get("categories", []))
    
    return {
        "company_name": title[:200],
        "phone": phone,
        "address": address,
        "city": city,
        "website": item.get("website", "") or "",
        "google_maps_url": item.get("url", ""),
        "google_rating": item.get("totalScore"),
        "capabilities": caps,
        "source": "Apify Google Maps",
        "source_url": item.get("searchPageUrl", ""),
        "verification_status": "Taslak",
        "notes": f"Kategori: {item.get('categoryName','')} | {item.get('reviewsCount',0)} yorum",
        "media_urls": [item["imageUrl"]] if item.get("imageUrl") else [],
    }

def scrape_batch(search_terms, batch_label, output_file):
    """Bir Apify batch çalıştır ve sonuçları kaydet"""
    print(f"\n🔄 Apify Batch: {batch_label} ({len(search_terms)} sorgu)")
    raw = run_apify(search_terms, max_per_search=25)
    
    cleaned = []
    for item in raw:
        r = clean_apify_record(item)
        if r:
            cleaned.append(r)
    
    print(f"  Ham: {len(raw)} | Temiz: {len(cleaned)}")
    
    with open(f"/app/scraper/{output_file}", "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    
    return cleaned

if __name__ == "__main__":
    # Batch 1: İstanbul + Ankara - Lazer & Büküm
    batch1_terms = [
        "fiber lazer kesim abkant büküm İstanbul OSB",
        "sac lazer kesim büküm İstanbul sanayi",
        "CNC lazer kesim İstanbul İkitelli",
        "lazer kesim büküm Ankara OSTİM",
        "fiber lazer sac işleme Ankara",
    ]
    
    records = scrape_batch(batch1_terms, "Batch-1 İstanbul+Ankara Lazer", "apify_batch1.json")
    print(f"Kaydedildi: {len(records)} kayıt")
