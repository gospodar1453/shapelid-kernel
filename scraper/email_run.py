#!/usr/bin/env python3
"""
E-posta scraper + Sheets güncelleme
Her 1000 firmada bir Sheets'e yazar.
"""
import json, re, time, warnings, requests, os
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
warnings.filterwarnings('ignore')

SHEET_ID = '1iU10AWTHZVkGlXoHawxJrnsCh7gUDmIjahlkl9T34_k'
TOKEN    = os.environ.get('GOOGLESHEETS_ACCESS_TOKEN','')

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
SOCIAL   = ['instagram.com','linkedin.com','facebook.com','twitter.com','youtube.com']
HEADERS  = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1)'}
EXCLUDE  = [
    'noreply','no-reply','example.com','sentry.io','wix.com','wordpress.com',
    'hotmail.com','yahoo.com','yandex.','outlook.com','gmail.com',
    'natro.com','isimtescil.net','turhost.com','hostinger.com','godaddy.com',
    'cloudflare.com','protection.outlook','spamprotect','@2x','@3x',
]

def is_valid(e):
    el = e.lower()
    return not any(x in el for x in EXCLUDE) and 5 < len(e) < 80 and '.' in e.split('@')[-1]

def fetch(url, timeout=4):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, verify=False, allow_redirects=True)
        return r.text if r.status_code == 200 else ''
    except: return ''

def scrape(website):
    if not website or any(s in website for s in SOCIAL): return []
    base = website.rstrip('/')
    parsed = urlparse(base)
    base_domain = f"{parsed.scheme}://{parsed.netloc}"
    emails = [e for e in set(EMAIL_RE.findall(fetch(base))) if is_valid(e)]
    if not emails:
        for path in ['/iletisim', '/contact', '/iletisim.html']:
            text = fetch(urljoin(base_domain, path), timeout=3)
            emails = [e for e in set(EMAIL_RE.findall(text)) if is_valid(e)]
            if emails: break
    return emails[:1]

def push_to_sheets(data):
    if not TOKEN: return
    rows = [['', r.get('company_name',''), "'" + r.get('phone',''), r.get('address',''),
             r.get('city',''), r.get('email',''), r.get('website',''),
             str(r.get('google_rating','') or ''), r.get('google_maps_url',''),
             ', '.join(r.get('capabilities',[])), r.get('source',''),
             r.get('verification_status','Taslak'), r.get('notes','')]
            for r in data]
    requests.post(
        f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/Firma%20Listesi!A2:M200000:clear',
        headers={'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}, json={})
    time.sleep(1)
    total = 0
    for i in range(0, len(rows), 1000):
        batch = rows[i:i+1000]
        r2 = i+2; r3 = r2+len(batch)-1
        resp = requests.put(
            f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/Firma%20Listesi!A{r2}:M{r3}?valueInputOption=USER_ENTERED',
            headers={'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'},
            json={'values': batch})
        if resp.status_code == 200: total += len(batch)
        time.sleep(0.4)
    print(f'  → Sheets guncellendi: {total} satir', flush=True)

# ─── Ana akış ───────────────────────────────────────────────────
data = json.load(open('/app/scraper/combined_all.json'))
to_scrape = [(i, r) for i, r in enumerate(data)
             if r.get('website','').startswith('http')
             and not any(s in r.get('website','') for s in SOCIAL)
             and not r.get('email','').strip()]

already = sum(1 for r in data if r.get('email','').strip())
print(f'Mevcut email: {already} | Kalan scrape: {len(to_scrape)}', flush=True)

data_dict = {i: r for i, r in enumerate(data)}
total_found = 0
BATCH      = 500
WORKERS    = 50
SHEET_EACH = 2000   # kaç firmada bir sheets'e yaz

for b in range(0, len(to_scrape), BATCH):
    batch = to_scrape[b:b+BATCH]
    batch_found = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(scrape, r.get('website','')): (idx, r) for idx, r in batch}
        for future in as_completed(futures):
            orig_idx, r = futures[future]
            try:
                emails = future.result()
                if emails:
                    data_dict[orig_idx]['email'] = emails[0]
                    batch_found += 1
            except: pass
    total_found += batch_found
    done = b + len(batch)
    pct  = done / len(to_scrape) * 100
    total_email = already + total_found
    print(f'[{done}/{len(to_scrape)} %{pct:.0f}] +{batch_found} | toplam email: {total_email}', flush=True)

    updated = [data_dict[i] for i in range(len(data))]
    json.dump(updated, open('/app/scraper/combined_all.json','w'), ensure_ascii=False)

    # Her SHEET_EACH firmada bir Sheets'e yaz
    if done % SHEET_EACH < BATCH:
        print(f'  Sheets yaziliyor...', flush=True)
        push_to_sheets(updated)

# Son Sheets güncellemesi
updated = [data_dict[i] for i in range(len(data))]
json.dump(updated, open('/app/scraper/combined_all.json','w'), ensure_ascii=False)
print('Son Sheets güncellemesi...', flush=True)
push_to_sheets(updated)

total_email = sum(1 for r in updated if r.get('email','').strip())
print(f'\n✅ TAMAMLANDI — Toplam email: {total_email}/{len(updated)} (%{total_email/len(updated)*100:.1f})', flush=True)
