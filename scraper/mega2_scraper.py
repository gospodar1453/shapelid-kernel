#!/usr/bin/env python3
"""
MEGA TARAMA v2 - 49 yeni il + genişletilmiş anahtar kelimeler
Hedef: 15.000+ yeni kayıt
"""
import requests, json, time, os, re

API_KEY = os.environ['GOOGLE_MAPS_API_KEY']
OUTPUT_FILE = '/app/scraper/mega2_results.json'
LOG_FILE = '/app/scraper/mega2_log.txt'

# 49 taranmamış il
CITIES = [
    'Adıyaman','Afyonkarahisar','Ağrı','Aksaray','Amasya','Ardahan','Artvin',
    'Bartın','Batman','Bayburt','Bilecik','Bingöl','Bitlis','Bolu','Burdur',
    'Çanakkale','Çankırı','Diyarbakır','Edirne','Erzurum','Giresun','Gümüşhane',
    'Hakkari','Iğdır','Isparta','Karabük','Karaman','Kars','Kastamonu','Kırıkkale',
    'Kırşehir','Kilis','Kütahya','Mardin','Muğla','Muş','Nevşehir','Niğde',
    'Ordu','Rize','Siirt','Sinop','Şırnak','Tokat','Tunceli','Uşak','Van',
    'Yozgat','Zonguldak'
]

# Daha önce taranmış ama az veri olan şehirlere ek tarama
EXTRA_CITIES = [
    'İstanbul','Ankara','İzmir','Bursa','Kocaeli','Konya','Gaziantep','Antalya',
    'Kayseri','Eskişehir','Denizli','Manisa','Sakarya','Mersin','Tekirdağ',
    'Balıkesir','Aydın','Hatay','Adana','Samsun','Trabzon','Malatya'
]

# Genişletilmiş anahtar kelimeler - 11 teknoloji + alt kategoriler
KEYWORDS = [
    # CNC
    'CNC torna freze',
    'CNC işleme merkezi',
    'fason talaşlı imalat',
    'CNC freze imalat',
    'talaşlı imalat atölyesi',
    'hassas işleme merkezi',
    'CNC otomat torna',
    '5 eksen CNC',
    # Lazer / Büküm
    'lazer kesim büküm',
    'fiber lazer kesim',
    'abkant bükme sac işleme',
    'sac metal işleme',
    'metal kesim büküm imalat',
    'plazma lazer kesim',
    'profil boru lazer kesim',
    # 3D Baskı
    '3D baskı hizmeti',
    '3D baskı prototip',
    'FDM baskı hizmeti',
    'endüstriyel 3D baskı',
    'SLA baskı hizmeti',
    # EDM
    'tel erozyon kesim',
    'EDM tel erozyon',
    'dalma erozyon',
    # Metal imalat genel
    'metal imalat sanayi',
    'makine imalat atölyesi',
    'fason metal imalat',
    'çelik konstrüksiyon imalat',
    'paslanmaz metal işleme',
    'alüminyum işleme imalat',
    # OSB bazlı
    'organize sanayi bölgesi metal',
    'OSB makine imalat',
    'OSB lazer kesim',
    'OSB CNC imalat',
]

def search_places(query, city, page_token=None):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        'query': f"{query} {city} Türkiye",
        'key': API_KEY,
        'language': 'tr',
        'region': 'tr',
    }
    if page_token:
        params['pagetoken'] = page_token
    r = requests.get(url, params=params, timeout=15)
    return r.json()

def get_place_details(place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        'place_id': place_id,
        'fields': 'name,formatted_phone_number,formatted_address,website,rating,user_ratings_total,types,url',
        'key': API_KEY,
        'language': 'tr',
    }
    r = requests.get(url, params=params, timeout=10)
    return r.json().get('result', {})

def infer_capabilities(name, types):
    caps = []
    name_lower = name.lower()
    types_str = ' '.join(types).lower() if types else ''
    combined = name_lower + ' ' + types_str
    
    if any(k in combined for k in ['lazer', 'laser', 'fiber laser']):
        caps.append('Laser Cutting')
    if any(k in combined for k in ['abkant', 'büküm', 'bükme', 'bending']):
        caps.append('Bending')
    if any(k in combined for k in ['torna', 'turning', 'otomat']):
        caps.append('CNC Turning')
    if any(k in combined for k in ['freze', 'milling', 'işleme merkezi', '5 eksen']):
        caps.append('CNC Milling')
    if any(k in combined for k in ['tel erozyon', 'edm', 'erezyon', 'elektro erozyon']):
        caps.append('EDM Services')
    if any(k in combined for k in ['3d baskı', '3d print', 'fdm', 'fff', 'filament']):
        caps.append('Fused Deposition Modeling')
    if any(k in combined for k in ['sla', 'stereolitografi', 'resin', 'photopolymer']):
        caps.append('Stereolithography')
    if any(k in combined for k in ['sls', 'selective laser sinter', 'nylon powder']):
        caps.append('Selective laser sintering')
    if any(k in combined for k in ['dmls', 'metal sintering', 'metal powder']):
        caps.append('Direct Metal Laser Sintering')
    if any(k in combined for k in ['polyjet', 'stratasys', 'connex']):
        caps.append('Polyjet')
    if any(k in combined for k in ['mjf', 'multi jet', 'hp baskı']):
        caps.append('HP Multi Jet Fusion')
    
    if not caps:
        # Genel metal imalat
        if any(k in combined for k in ['metal', 'sac', 'çelik', 'alüminyum', 'paslanmaz']):
            caps.append('Laser Cutting')
        if any(k in combined for k in ['makine', 'makina', 'imalat', 'talaşlı']):
            caps.append('CNC Turning')
    
    return list(set(caps))

# Yükle mevcut sonuçları (devam için)
results = []
seen_ids = set()
if os.path.exists(OUTPUT_FILE):
    results = json.load(open(OUTPUT_FILE, encoding='utf-8'))
    seen_ids = {r.get('place_id','') for r in results}
    print(f"Mevcut: {len(results)} kayıt yüklendi")

# İstatistik
total_queries = 0
total_new = 0

def log(msg):
    print(msg)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

log(f"\n=== MEGA2 TARAMA BAŞLADI ===")
log(f"Yeni il: {len(CITIES)}, Ek şehir: {len(EXTRA_CITIES)}, Anahtar kelime: {len(KEYWORDS)}")
log(f"Toplam sorgu: ~{(len(CITIES)+len(EXTRA_CITIES)) * len(KEYWORDS)}")

# Önce yeni iller
all_cities = CITIES + EXTRA_CITIES

for city in all_cities:
    city_new = 0
    for keyword in KEYWORDS:
        query = f"{keyword}"
        data = search_places(query, city)
        total_queries += 1
        
        places = data.get('results', [])
        for place in places:
            pid = place.get('place_id','')
            if pid in seen_ids:
                continue
            seen_ids.add(pid)
            
            # Detay çek
            try:
                detail = get_place_details(pid)
                time.sleep(0.05)
            except:
                detail = {}
            
            name = place.get('name','')
            caps = infer_capabilities(name, place.get('types',[]))
            
            record = {
                'company_name': name,
                'phone': detail.get('formatted_phone_number',''),
                'address': detail.get('formatted_address', place.get('formatted_address','')),
                'city': city,
                'website': detail.get('website',''),
                'google_rating': place.get('rating'),
                'google_maps_url': detail.get('url', f"https://maps.google.com/?cid={pid}"),
                'capabilities': caps,
                'source': 'Google Maps API v2',
                'verification_status': 'Taslak',
                'notes': f"{place.get('user_ratings_total',0)} yorum | {keyword}",
                'place_id': pid,
            }
            results.append(record)
            city_new += 1
            total_new += 1
        
        # Sayfalama (max 3 sayfa = 60 sonuç/sorgu)
        token = data.get('next_page_token')
        for _ in range(2):
            if not token:
                break
            time.sleep(2)
            data2 = search_places(query, city, token)
            for place in data2.get('results', []):
                pid = place.get('place_id','')
                if pid in seen_ids:
                    continue
                seen_ids.add(pid)
                try:
                    detail = get_place_details(pid)
                    time.sleep(0.05)
                except:
                    detail = {}
                name = place.get('name','')
                caps = infer_capabilities(name, place.get('types',[]))
                record = {
                    'company_name': name,
                    'phone': detail.get('formatted_phone_number',''),
                    'address': detail.get('formatted_address', place.get('formatted_address','')),
                    'city': city,
                    'website': detail.get('website',''),
                    'google_rating': place.get('rating'),
                    'google_maps_url': detail.get('url', f"https://maps.google.com/?cid={pid}"),
                    'capabilities': caps,
                    'source': 'Google Maps API v2',
                    'verification_status': 'Taslak',
                    'notes': f"{place.get('user_ratings_total',0)} yorum | {keyword}",
                    'place_id': pid,
                }
                results.append(record)
                city_new += 1
                total_new += 1
            token = data2.get('next_page_token')
        
        time.sleep(0.1)
        
        # Her 500 yeni kayıtta kaydet
        if total_new > 0 and total_new % 500 == 0:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            log(f"  💾 Kaydedildi: {len(results)} toplam")
    
    log(f"✅ {city}: {city_new} yeni kayıt (toplam: {len(results)})")
    
    # Her şehirden sonra kaydet
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

log(f"\n=== TAMAMLANDI ===")
log(f"Toplam yeni kayıt: {total_new}")
log(f"Grand total: {len(results)}")

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"BITTI: {len(results)} kayıt")
