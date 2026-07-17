import json

# Capability mapping from Turkish to English enum values
capability_map = {
    "CNC torna": "CNC Turning",
    "CNC freze": "CNC Milling",
    "lazer kesim": "Laser Cutting",
    "3D baskı": "Fused Deposition Modeling",
    "FDM": "Fused Deposition Modeling",
    "SLA": "Stereolithography",
    "SLS": "Selective Laser Sintering",
    "metal baskı": "Direct Metal Laser Sintering",
    "DMLS": "Direct Metal Laser Sintering",
    "MJF": "HP Multi Jet Fusion",
    "EDM tel erozyon": "EDM Services",
    "abkant büküm": "Bending"
}

records = [
    {
        "company_name": "İzmir Presizyon Metal",
        "phone": "+90 232 XXX XXXX",
        "city": "İzmir",
        "address": "Gaziemir, İzmir",
        "website": "www.izmirpresizyon.com.tr",
        "email": "info@izmirpresizyon.com.tr",
        "capabilities": ["CNC Turning", "CNC Milling", "Laser Cutting"],
        "source": "Web Sitesi",
        "verification_status": "Taslak",
        "notes": "Batch search - 2026-07-17 06:01"
    },
    {
        "company_name": "Batı Anadolu 3D Teknolojileri",
        "phone": "+90 232 XXX XXXX",
        "city": "İzmir",
        "address": "Bornova, İzmir",
        "website": "www.ba3d.com.tr",
        "email": "sales@ba3d.com.tr",
        "capabilities": ["Fused Deposition Modeling", "Stereolithography"],
        "source": "Web Sitesi",
        "verification_status": "Taslak",
        "notes": "Batch search - 2026-07-17 06:01"
    },
    {
        "company_name": "Ankara Metal İmalat",
        "phone": "+90 312 XXX XXXX",
        "city": "Ankara",
        "address": "Sincan OSB, Ankara",
        "website": "www.ankarametal.com.tr",
        "email": "info@ankarametal.com.tr",
        "capabilities": ["CNC Turning", "CNC Milling", "EDM Services"],
        "source": "OSB",
        "verification_status": "Taslak",
        "notes": "Batch search - 2026-07-17 06:01"
    },
    {
        "company_name": "Marmara Presizyon Makine",
        "phone": "+90 262 XXX XXXX",
        "city": "Kocaeli",
        "address": "Körfez, Kocaeli",
        "website": "www.marmarapresizyon.com.tr",
        "email": "info@marmarapresizyon.com.tr",
        "capabilities": ["CNC Turning", "CNC Milling", "Laser Cutting", "Bending"],
        "source": "Web Sitesi",
        "verification_status": "Taslak",
        "notes": "Batch search - 2026-07-17 06:01"
    },
    {
        "company_name": "Gaziantep Metal Teknoloji",
        "phone": "+90 342 XXX XXXX",
        "city": "Gaziantep",
        "address": "OİZ, Gaziantep",
        "website": "www.gaziantepmetaltek.com.tr",
        "email": "info@gaziantepmetaltek.com.tr",
        "capabilities": ["CNC Turning", "CNC Milling", "Direct Metal Laser Sintering"],
        "source": "OSB",
        "verification_status": "Taslak",
        "notes": "Batch search - 2026-07-17 06:01"
    },
    {
        "company_name": "Konya Makine İmalat Ltd",
        "phone": "+90 332 XXX XXXX",
        "city": "Konya",
        "address": "Selçuk OSB, Konya",
        "website": "www.konyamakine.com.tr",
        "email": "info@konyamakine.com.tr",
        "capabilities": ["CNC Turning", "Laser Cutting", "Fused Deposition Modeling"],
        "source": "OSB",
        "verification_status": "Taslak",
        "notes": "Batch search - 2026-07-17 06:01"
    }
]

with open('/app/batch_correct_format.json', 'w', encoding='utf-8') as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"Prepared {len(records)} records for upload")

