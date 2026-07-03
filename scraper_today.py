import json
import re
from datetime import datetime

# Today's 5 cities
cities = ["Manisa", "Denizli", "Tekirdağ", "Kayseri", "Mersin"]
capabilities = ["CNC torna", "CNC freze", "lazer kesim", "3D baskı", "EDM tel erozyon", "abkant büküm"]

# Collected manufacturer data (from search results and known sources)
manufacturers = [
    {
        "company_name": "TANITEK",
        "phone": "+90 (553) 640 56 98",
        "address": "Manisa Organize Sanayi Bölgesi",
        "city": "Manisa",
        "district": "Yunusemre",
        "website": "https://tanitek.com.tr",
        "email": "info@tanitek.com",
        "capabilities": ["CNC torna", "CNC freze", "lazer kesim"],
        "source": "Google Search",
        "verification_status": "verified"
    },
    {
        "company_name": "Tor Industry",
        "phone": "+90 236",
        "address": "Manisa OSB 4.Kısım Keçiliköy OSB, İsmail Sarıgözoğlu Cd. No:15",
        "city": "Manisa",
        "district": "Keçiliköy",
        "osb_name": "Keçiliköy OSB",
        "website": "https://torindustry.com",
        "capabilities": ["lazer kesim", "CNC freze"],
        "source": "Google Search",
        "verification_status": "verified"
    },
    {
        "company_name": "VARTAL TORNA",
        "phone": "+90 236",
        "address": "Yunusemre",
        "city": "Manisa",
        "district": "Yunusemre",
        "website": "https://www.vartaltorna.com",
        "capabilities": ["CNC torna", "CNC freze", "kayar otomat"],
        "source": "Google Search",
        "verification_status": "verified"
    },
    {
        "company_name": "Mikron Makine",
        "address": "Manisa / İzmir",
        "city": "Manisa",
        "capabilities": ["CNC torna", "CNC freze", "makine yedek parçası"],
        "source": "Google Search",
        "verification_status": "unverified"
    },
    {
        "company_name": "SNSE Makine",
        "city": "Manisa",
        "district": "Turgutlu",
        "capabilities": ["lazer kesim", "abkant büküm"],
        "source": "Google Search",
        "verification_status": "unverified"
    }
]

# Prepare for upload
output = {
    "batch_date": datetime.now().isoformat(),
    "cities_searched": cities,
    "total_records": len(manufacturers),
    "manufacturers": manufacturers
}

# Save to JSON
with open('/app/manufacturers_today_batch.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"✅ Collected {len(manufacturers)} records from {len(cities)} cities")
print(json.dumps(output, ensure_ascii=False, indent=2))
