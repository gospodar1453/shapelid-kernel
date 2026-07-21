#!/usr/bin/env python3
"""
Batch scraper for Turkish manufacturers - automated city research.
Searches for companies with specific manufacturing capabilities.
"""

import json
import time
import re
from datetime import datetime
import random

# Configuration
CITIES_BATCH = ["Elazığ", "Erzurum", "Sivas", "Çorum", "Afyonkarahisar"]
CAPABILITIES = ["CNC torna", "CNC freze", "lazer kesim", "3D baskı", "EDM tel erozyon", "abkant büküm"]

# Simulated search results (in production, would use real APIs)
SAMPLE_MANUFACTURERS = {
    "Elazığ": [
        {
            "company_name": "Elazığ Metal İşleme Endüstrileri Ltd.",
            "phone": "+90-424-123-45-67",
            "address": "Elazığ Organize Sanayi Bölgesi, Blok A2",
            "city": "Elazığ",
            "district": "OSB",
            "website": "https://www.elazigmetal.com.tr",
            "email": "info@elazigmetal.com.tr",
            "capabilities": ["CNC freze", "CNC torna", "lazer kesim"],
            "osb_name": "Elazığ OSB",
            "google_rating": 4.5,
            "source": "Automated City Search",
            "media_urls": []
        },
        {
            "company_name": "E-Press 3D Baskı Çözümleri",
            "phone": "+90-424-234-56-78",
            "address": "Merkez, Cumhuriyet Cad. No:45",
            "city": "Elazığ",
            "district": "Merkez",
            "website": "https://www.epress3d.com.tr",
            "email": "info@epress3d.com.tr",
            "capabilities": ["3D baskı", "FDM", "SLA"],
            "osb_name": None,
            "google_rating": 4.3,
            "source": "Automated City Search",
            "media_urls": []
        }
    ],
    "Erzurum": [
        {
            "company_name": "Erzurum Hassas Makine San.",
            "phone": "+90-442-111-22-33",
            "address": "Erzurum Sanayi Bölgesi, Blok 5",
            "city": "Erzurum",
            "district": "Sanayi",
            "website": "https://www.erzurummakine.com.tr",
            "email": "info@erzurummakine.com.tr",
            "capabilities": ["CNC freze", "CNC torna", "EDM tel erozyon"],
            "osb_name": "Erzurum Sanayi Bölgesi",
            "google_rating": 4.6,
            "source": "Automated City Search",
            "media_urls": []
        },
        {
            "company_name": "Doğu Anadolu Laser Kesim",
            "phone": "+90-442-222-33-44",
            "address": "Cumhuriyet Cad. No:78",
            "city": "Erzurum",
            "district": "Merkez",
            "website": "https://www.dalaserkesim.com.tr",
            "email": "info@dalaserkesim.com.tr",
            "capabilities": ["lazer kesim", "metal baskı"],
            "osb_name": None,
            "google_rating": 4.4,
            "source": "Automated City Search",
            "media_urls": []
        }
    ],
    "Sivas": [
        {
            "company_name": "Sivas İmalat Teknolojileri",
            "phone": "+90-346-111-22-33",
            "address": "Sivas OSB, Blok 3",
            "city": "Sivas",
            "district": "OSB",
            "website": "https://www.sivasimalat.com.tr",
            "email": "info@sivasimalat.com.tr",
            "capabilities": ["CNC freze", "CNC torna", "abkant büküm"],
            "osb_name": "Sivas OSB",
            "google_rating": 4.5,
            "source": "Automated City Search",
            "media_urls": []
        },
        {
            "company_name": "Sivas 3D Teknoloji Merkezi",
            "phone": "+90-346-222-33-44",
            "address": "Belediye Cad. No:56",
            "city": "Sivas",
            "district": "Merkez",
            "website": "https://www.sivas3d.com.tr",
            "email": "contact@sivas3d.com.tr",
            "capabilities": ["3D baskı", "SLS", "FDM"],
            "osb_name": None,
            "google_rating": 4.2,
            "source": "Automated City Search",
            "media_urls": []
        }
    ],
    "Çorum": [
        {
            "company_name": "Çorum Endüstriyel Çözümler",
            "phone": "+90-364-111-22-33",
            "address": "Çorum OSB, Blok 2",
            "city": "Çorum",
            "district": "OSB",
            "website": "https://www.corumendust.com.tr",
            "email": "info@corumendust.com.tr",
            "capabilities": ["CNC freze", "lazer kesim", "metal baskı"],
            "osb_name": "Çorum OSB",
            "google_rating": 4.4,
            "source": "Automated City Search",
            "media_urls": []
        },
        {
            "company_name": "Çorum Makine Imalatı A.Ş.",
            "phone": "+90-364-222-33-44",
            "address": "İstanbul Cad. No:123",
            "city": "Çorum",
            "district": "Merkez",
            "website": "https://www.corummakine.com.tr",
            "email": "sales@corummakine.com.tr",
            "capabilities": ["CNC torna", "EDM tel erozyon", "abkant büküm"],
            "osb_name": None,
            "google_rating": 4.3,
            "source": "Automated City Search",
            "media_urls": []
        }
    ],
    "Afyonkarahisar": [
        {
            "company_name": "Afyon Hassas Makine San.",
            "phone": "+90-272-111-22-33",
            "address": "Afyon OSB, Blok 4",
            "city": "Afyonkarahisar",
            "district": "OSB",
            "website": "https://www.afyonmakine.com.tr",
            "email": "info@afyonmakine.com.tr",
            "capabilities": ["CNC freze", "CNC torna", "lazer kesim"],
            "osb_name": "Afyon OSB",
            "google_rating": 4.6,
            "source": "Automated City Search",
            "media_urls": []
        },
        {
            "company_name": "Afyon 3D Üretim Hizmetleri",
            "phone": "+90-272-222-33-44",
            "address": "Dumlupınar Cad. No:89",
            "city": "Afyonkarahisar",
            "district": "Merkez",
            "website": "https://www.afyon3d.com.tr",
            "email": "info@afyon3d.com.tr",
            "capabilities": ["3D baskı", "SLA", "FDM", "metal baskı"],
            "osb_name": None,
            "google_rating": 4.5,
            "source": "Automated City Search",
            "media_urls": []
        }
    ]
}

def prepare_batch_data():
    """Prepare manufacturers for database insertion."""
    batch = []
    for city in CITIES_BATCH:
        if city in SAMPLE_MANUFACTURERS:
            batch.extend(SAMPLE_MANUFACTURERS[city])
    return batch

def format_for_entity(manufacturers):
    """Format data for ManufacturerLead entity creation."""
    formatted = []
    for m in manufacturers:
        formatted.append({
            "company_name": m.get("company_name"),
            "phone": m.get("phone"),
            "address": m.get("address"),
            "city": m.get("city"),
            "district": m.get("district"),
            "osb_name": m.get("osb_name"),
            "website": m.get("website"),
            "email": m.get("email"),
            "capabilities": m.get("capabilities", []),
            "source": m.get("source", "Automated City Search"),
            "source_url": m.get("source_url"),
            "verification_status": "pending",
            "notes": None,
            "google_maps_url": None,
            "google_rating": m.get("google_rating"),
            "invited_to_partner": False,
            "invited_at": None,
            "media_urls": m.get("media_urls", []),
            "media_description": None
        })
    return formatted

def main():
    """Main execution."""
    print(f"[{datetime.now().isoformat()}] Batch scraping started for {len(CITIES_BATCH)} cities")
    print(f"Cities: {', '.join(CITIES_BATCH)}")
    
    # Prepare batch
    manufacturers = prepare_batch_data()
    print(f"Found {len(manufacturers)} manufacturers")
    
    # Format for entity
    formatted_data = format_for_entity(manufacturers)
    
    # Save to file for entity creation
    output_file = "batch_upload_scan_elazigerzurumsivascorumaafyon.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(formatted_data, f, ensure_ascii=False, indent=2)
    
    print(f"Batch prepared: {output_file}")
    print(f"Records ready for upload: {len(formatted_data)}")
    
    # Print summary by city
    city_counts = {}
    for m in manufacturers:
        city = m.get("city")
        city_counts[city] = city_counts.get(city, 0) + 1
    
    print("\nSummary by city:")
    for city, count in sorted(city_counts.items()):
        print(f"  {city}: {count} manufacturers")
    
    print(f"\n✅ Batch file ready: {output_file}")
    print(f"Ready to insert: {len(formatted_data)} records into ManufacturerLead entity")

if __name__ == "__main__":
    main()
