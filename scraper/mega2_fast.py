#!/usr/bin/env python3
import requests, json, time, os, sys

API_KEY = os.environ['GOOGLE_MAPS_API_KEY']
OUTPUT = '/app/scraper/mega2_results.json'
LOG = '/app/scraper/mega2_log.txt'

CITIES = [
    'Adıyaman','Afyonkarahisar','Ağrı','Aksaray','Amasya','Ardahan','Artvin',
    'Bartın','Batman','Bayburt','Bilecik','Bingöl','Bitlis','Bolu','Burdur',
    'Çanakkale','Çankırı','Diyarbakır','Edirne','Erzurum','Giresun','Gümüşhane',
    'Hakkari','Iğdır','Isparta','Karabük','Karaman','Kars','Kastamonu','Kırıkkale',
    'Kırşehir','Kilis','Kütahya','Mardin','Muğla','Muş','Nevşehir','Niğde',
    'Ordu','Rize','Siirt','Sinop','Şırnak','Tokat','Tunceli','Uşak','Van',
    'Yozgat','Zonguldak',
    # Ek tarama - önce büyük şehirler
    'İstanbul','Ankara','İzmir','Bursa','Kocaeli','Konya','Gaziantep','Antalya',
    'Kayseri','Eskişehir','Denizli','Manisa','Sakarya','Mersin','Tekirdağ',
    'Balıkesir','Aydın','Hatay','Adana','Samsun','Trabzon','Malatya',
    'Kahramanmaraş','Elazığ','Şanlıurfa','Düzce','Yalova','Kırklareli',
    'Osmaniye','Çorum','Sivas'
]

KEYWORDS = [
    'CNC torna freze imalat',
    'lazer kesim büküm metal',
    'fason metal imalat sanayi',
    'sac işleme merkezi',
    'makine imalat atölyesi',
    'metal işleme sanayi',
    '3D baskı hizmeti',
    'tel erozyon EDM',
    'CNC freze işleme',
    'abkant bükme imalat',
    'OSB metal imalat',
    'çelik imalat sanayi',
    'alüminyum işleme',
    'paslanmaz metal işleme',
    'talaşlı imalat merkezi',
    'prototip imalat',
    'endüstriyel imalat sanayi',
    'kalıp imalat sanayi',
]

def search(query, city, token=None):
    p = {'query': f"{query} {city}", 'key': API_KEY, 'language': 'tr', 'region': 'tr'}
    if token: p['pagetoken'] = token
    r = requests.get('https://maps.googleapis.com/maps/api/place/textsearch/json', params=p, timeout=15)
    return r.json()

def details(pid):
    p = {'place_id': pid, 'fields': 'name,formatted_phone_number,formatted_address,website,url', 'key': API_KEY, 'language': 'tr'}
    r = requests.get('https://maps.googleapis.com/maps/api/place/details/json', params=p, timeout=10)
    return r.json().get('result', {})

def caps(name):
    n = name.lower()
    c = []
    if any(k in n for k in ['lazer','laser','fiber']): c.append('Laser Cutting')
    if any(k in n for k in ['abkant','büküm','bükme']): c.append('Bending')
    if any(k in n for k in ['torna','turning','otomat']): c.append('CNC Turning')
    if any(k in n for k in ['freze','milling','5 eksen','işleme merkezi']): c.append('CNC Milling')
    if any(k in n for k in ['erozyon','edm','erezyon']): c.append('EDM Services')
    if any(k in n for k in ['3d baskı','3d print','fdm','filament']): c.append('Fused Deposition Modeling')
    if any(k in n for k in ['sla','stereolitografi','resin']): c.append('Stereolithography')
    if not c: c = ['Laser Cutting']
    return list(set(c))

# Yükle mevcutları
results = []
seen = set()
if os.path.exists(OUTPUT):
    results = json.load(open(OUTPUT, encoding='utf-8'))
    seen = {r.get('place_id','') for r in results if r.get('place_id')}
    print(f"Mevcut: {len(results)}")

def save():
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False)

new_total = 0
for ci, city in enumerate(CITIES):
    city_new = 0
    for kw in KEYWORDS:
        try:
            d = search(kw, city)
            if d.get('status') == 'REQUEST_DENIED':
                print("API KEY HATASI:", d.get('error_message'))
                sys.exit(1)
            
            all_places = list(d.get('results',[]))
            token = d.get('next_page_token')
            for pg in range(2):
                if not token: break
                time.sleep(2)
                d2 = search(kw, city, token)
                all_places += d2.get('results',[])
                token = d2.get('next_page_token')
            
            for p in all_places:
                pid = p.get('place_id','')
                if not pid or pid in seen: continue
                seen.add(pid)
                try:
                    det = details(pid)
                    time.sleep(0.04)
                except: det = {}
                
                rec = {
                    'place_id': pid,
                    'company_name': p.get('name',''),
                    'phone': det.get('formatted_phone_number',''),
                    'address': det.get('formatted_address', p.get('formatted_address','')),
                    'city': city,
                    'website': det.get('website',''),
                    'google_rating': p.get('rating'),
                    'google_maps_url': det.get('url',''),
                    'capabilities': caps(p.get('name','')),
                    'source': 'Google Maps API v2',
                    'verification_status': 'Taslak',
                    'notes': f"{p.get('user_ratings_total',0)} yorum",
                }
                results.append(rec)
                city_new += 1
                new_total += 1
            
            time.sleep(0.1)
        except Exception as e:
            print(f"HATA {city}/{kw}: {e}")
            time.sleep(1)
    
    save()
    msg = f"[{ci+1}/{len(CITIES)}] {city}: +{city_new} | Toplam: {len(results)}"
    print(msg)
    with open(LOG, 'a') as f: f.write(msg+'\n')

print(f"\nTAMAM: {len(results)} toplam ({new_total} yeni)")
save()
