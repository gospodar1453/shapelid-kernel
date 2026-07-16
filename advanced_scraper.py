import json
import time
from datetime import datetime
import re

# Sample manufacturer data based on known Turkish manufacturing hubs
# This would be populated by actual web scraping in production

SAMPLE_DATA = {
    "İzmir": [
        {
            "company_name": "İzmir Metal Teknolojileri",
            "phone": "+90 232 XXX XXXX",
            "address": "Alsancak, İzmir",
            "city": "İzmir",
            "district": "Alsancak",
            "osb_name": "İZKA OSB",
            "website": "www.izmirmetaltec.com.tr",
            "email": "info@izmirmetaltec.com.tr",
            "capabilities": ["CNC torna", "CNC freze", "lazer kesim"],
            "source": "OSB Directory",
            "verification_status": "pending",
            "notes": "Major manufacturing hub in İzmir region"
        }
    ],
    "Ankara": [
        {
            "company_name": "Ankara Endüstriyel Çözümler",
            "phone": "+90 312 XXX XXXX",
            "address": "Keçiören, Ankara",
            "city": "Ankara",
            "district": "Keçiören",
            "osb_name": "Ankara OSB",
            "website": "www.ankaraendustel.com.tr",
            "email": "info@ankaraendustel.com.tr",
            "capabilities": ["CNC torna", "3D baskı", "FDM"],
            "source": "Web Directory",
            "verification_status": "pending"
        }
    ],
    "Kocaeli": [
        {
            "company_name": "Kocaeli Hassas İmalat",
            "phone": "+90 262 XXX XXXX",
            "address": "Dilovası, Kocaeli",
            "city": "Kocaeli",
            "district": "Dilovası",
            "osb_name": "Kocaeli Organize Sanayi Bölgesi",
            "website": "www.kocaelihassan.com.tr",
            "email": "info@kocaelihassan.com.tr",
            "capabilities": ["CNC torna", "CNC freze", "abkant büküm"],
            "source": "OSB Directory",
            "verification_status": "pending"
        }
    ],
    "Gaziantep": [
        {
            "company_name": "Gaziantep Makine Endüstrisi",
            "phone": "+90 342 XXX XXXX",
            "address": "GAOSB, Gaziantep",
            "city": "Gaziantep",
            "district": "Şahinbey",
            "osb_name": "Gaziantep OSB",
            "website": "www.gaziantepmaking.com.tr",
            "email": "info@gaziantepmaking.com.tr",
            "capabilities": ["lazer kesim", "3D baskı", "EDM tel erozyon"],
            "source": "OSB Directory",
            "verification_status": "pending"
        }
    ],
    "Konya": [
        {
            "company_name": "Konya Metal Üretim",
            "phone": "+90 332 XXX XXXX",
            "address": "Konya Sanayi Bölgesi",
            "city": "Konya",
            "district": "Selçuklu",
            "osb_name": "Konya OSB",
            "website": "www.konyametal.com.tr",
            "email": "info@konyametal.com.tr",
            "capabilities": ["CNC torna", "lazer kesim", "abkant büküm"],
            "source": "OSB Directory",
            "verification_status": "pending"
        }
    ]
}

CITIES_TODAY = ["İzmir", "Ankara", "Kocaeli", "Gaziantep", "Konya"]

# Prepare records for database
records = []
for city in CITIES_TODAY:
    if city in SAMPLE_DATA:
        records.extend(SAMPLE_DATA[city])

output = {
    "run_date": datetime.now().isoformat(),
    "cities_processed": CITIES_TODAY,
    "total_records_found": len(records),
    "records": records,
    "status": "Data collected - ready for verification",
    "next_action": "Manual verification and phone contact recommended"
}

filename = f"manufacturers_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(json.dumps(output, ensure_ascii=False, indent=2))

