"""
Google Maps Mega Scraper
30 şehir x 30 sorgu = 900 kombinasyon
Hedef: 5000-8000 benzersiz firma
"""
import requests, os, json, time, sys

API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
if not API_KEY:
    print("❌ GOOGLE_MAPS_API_KEY bulunamadı!")
    sys.exit(1)

BASE_SEARCH = "https://maps.googleapis.com/maps/api/place/textsearch/json"
BASE_DETAIL = "https://maps.googleapis.com/maps/api/place/details/json"
OUT_FILE = "/app/scraper/mega_results.json"
LOG_FILE = "/app/scraper/mega_log.txt"

# ─── SORGULAR ────────────────────────────────────────────────────────────────
QUERIES = [
    # CNC Torna
    "CNC torna atölyesi",
    "CNC torna fason",
    "talaşlı imalat",
    "fason torna",
    "otomat torna",
    "CNC tornacı",
    # CNC Freze / İşleme Merkezi
    "CNC freze fason",
    "işleme merkezi",
    "5 eksen CNC",
    "dik işlem merkezi",
    "yatay işlem merkezi",
    "fason CNC işleme",
    # Lazer Kesim
    "fiber lazer kesim",
    "metal lazer kesim",
    "sac lazer kesim",
    "CNC lazer kesim",
    "lazer abkant",
    "lazer kesim büküm",
    # Sac / Abkant
    "abkant büküm sanayi",
    "sac büküm imalat",
    "sac işleme merkezi",
    "pres büküm",
    "sac metal fason",
    # EDM
    "tel erozyon fason",
    "dalma erozyon",
    "EDM fason",
    # 3D Baskı
    "3D baskı hizmet",
    "3D yazıcı imalat",
    "endüstriyel 3D baskı",
    # Genel Metal
    "metal fason imalat",
    "makina imalat sanayi",
    "metal imalat OSB",
]

# ─── ŞEHİRLER ────────────────────────────────────────────────────────────────
CITIES = [
    "İstanbul", "Ankara", "Bursa", "İzmir", "Kocaeli",
    "Sakarya", "Konya", "Kayseri", "Gaziantep", "Eskişehir",
    "Denizli", "Manisa", "Tekirdağ", "Samsun", "Antalya",
    "Adana", "Mersin", "Hatay", "Kahramanmaraş", "Şanlıurfa",
    "Balıkesir", "Çorum", "Aydın", "Trabzon", "Malatya",
    "Elazığ", "Düzce", "Yalova", "Gebze", "Çorlu",
]

# ─── KAPASİTE HARİTASI ───────────────────────────────────────────────────────
CAP_MAP = {
    "CNC Turning": ["torna","tornalama","talaşlı","otomat torna","cnc turn"],
    "CNC Milling": ["freze","frezeleme","işleme merkezi","5 eksen","4 eksen","dik işlem","yatay işlem"],
    "EDM Services": ["erozyon","edm","tel erezyon","dalma erozyon"],
    "Laser Cutting": ["lazer kesim","laser cut","fiber lazer","plazma kesim","lazer metal","lazer sac"],
    "Bending": ["büküm","abkant","sac büküm","pres bük","sac-pres"],
    "Fused Deposition Modeling": ["fdm","3d bask","3d yaz","filament","katmanlı","boyutlu bask"],
    "Stereolithography": ["sla","reçine","resin bask"],
    "Selective laser sintering": ["sls","toz 3d","nylon bask"],
    "HP Multi Jet Fusion": ["mjf","multi jet","hp bask"],
    "Direct Metal Laser Sintering": ["dmls","metal 3d","slm","direkt metal"],
}

def get_caps(name):
    text = name.lower()
    found = [cap for cap, kws in CAP_MAP.items() if any(kw in text for kw in kws)]
    return found if found else ["Laser Cutting"]

def get_detail(pid):
    params = {
        "place_id": pid,
        "fields": "name,international_phone_number,formatted_phone_number,website,formatted_address,address_components,url,rating,user_ratings_total",
        "key": API_KEY, "language": "tr"
    }
    try:
        r = requests.get(BASE_DETAIL, params=params, timeout=12)
        return r.json().get("result", {})
    except:
        return {}

def extract_city(comps):
    for c in comps:
        if "administrative_area_level_1" in c.get("types", []):
            return c.get("long_name", "")
    return ""

def log(msg):
    print(msg, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# ─── ANA DÖNGÜ ───────────────────────────────────────────────────────────────
all_records = []
seen_pids = set()
api_calls = 0
total_skipped = 0

log(f"🚀 Mega Scraper başladı: {len(QUERIES)} sorgu x {len(CITIES)} şehir")
log("="*70)

for city_idx, city in enumerate(CITIES):
    city_new = 0

    for query in QUERIES:
        full_query = f"{query} {city}"
        params = {
            "query": full_query,
            "key": API_KEY,
            "language": "tr",
            "region": "tr"
        }

        try:
            r = requests.get(BASE_SEARCH, params=params, timeout=12)
            d = r.json()
            api_calls += 1

            if d.get("status") == "REQUEST_DENIED":
                log(f"❌ API erişim reddedildi: {d.get('error_message','?')}")
                sys.exit(1)

            if d.get("status") not in ("OK", "ZERO_RESULTS"):
                log(f"  ⚠️ {city}/{query[:25]}: {d.get('status')}")
                time.sleep(0.5)
                continue

            results = d.get("results", [])

            for place in results[:20]:
                pid = place.get("place_id", "")
                if not pid or pid in seen_pids:
                    total_skipped += 1
                    continue
                seen_pids.add(pid)

                time.sleep(0.07)
                api_calls += 1
                det = get_detail(pid)

                phone = det.get("international_phone_number", "") or det.get("formatted_phone_number", "")
                address = det.get("formatted_address", "") or place.get("formatted_address", "")
                name = det.get("name", "") or place.get("name", "")

                if not name or not phone or not address:
                    continue

                city_name = extract_city(det.get("address_components", [])) or city

                all_records.append({
                    "company_name": name[:200],
                    "phone": phone,
                    "address": address,
                    "city": city_name,
                    "website": det.get("website", ""),
                    "google_maps_url": det.get("url", ""),
                    "google_rating": det.get("rating"),
                    "capabilities": get_caps(name),
                    "source": "Google Maps API",
                    "verification_status": "Taslak",
                    "notes": f"{det.get('user_ratings_total',0)} yorum | {query}",
                    "media_urls": [],
                })
                city_new += 1

            time.sleep(0.12)

        except KeyboardInterrupt:
            log("⚠️ Kullanıcı tarafından durduruldu")
            break
        except Exception as e:
            log(f"  Hata ({city}/{query[:20]}): {e}")
            time.sleep(1)

    # Şehir bitti - kaydet
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False)

    log(f"[{city_idx+1:2}/{len(CITIES)}] {city:15} +{city_new:4} yeni | TOPLAM: {len(all_records):6} | API: {api_calls:6}")

log(f"\n✅ TAMAMLANDI: {len(all_records)} benzersiz kayıt, {api_calls} API çağrısı")
with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(all_records, f, ensure_ascii=False, indent=2)
