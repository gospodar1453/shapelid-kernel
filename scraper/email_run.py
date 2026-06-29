#!/usr/bin/env python3
"""
Derin web scraper — mailto + çoklu path + Sheets güncelleme
Her 2000 firmada bir Sheets Firma Listesi sekmesine yazar.
"""
import json, re, requests, warnings, os, time
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
warnings.filterwarnings('ignore')

SHEET_ID = '1iU10AWTHZVkGlXoHawxJrnsCh7gUDmIjahlkl9T34_k'
TOKEN    = os.environ.get('GOOGLESHEETS_ACCESS_TOKEN', '')

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
EXCLUDE  = ['noreply','no-reply','example.com','sentry.io','wix.com','wordpress.com',
            'hotmail.com','yahoo.com','yandex.','outlook.com','gmail.com',
            'natro.com','isimtescil.net','turhost.com','hostinger.com','godaddy.com',
            'cloudflare.com','protection.outlook','spamprotect','@2x','@3x',
            'w3.org','schema.org','jquery','bootstrap','svg','png','jpg']
SOCIAL   = ['instagram.com','linkedin.com','facebook.com','twitter.com','youtube.com']
HEADERS  = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0'}
PATHS    = ['/', '/iletisim', '/contact', '/bize-ulasin', '/bize-ulaşın',
            '/hakkimizda', '/about', '/iletisim.html', '/contact.html']

def is_valid(e):
    el = e.lower()
    return not any(x in el for x in EXCLUDE) and 5 < len(e) < 80 and '.' in e.split('@')[-1]

def fetch(url, timeout=5):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, verify=False, allow_redirects=True)
        return r.text if r.status_code == 200 else ''
    except: return ''

def scrape_deep(website):
    if not website or any(s in website for s in SOCIAL): return None
    base  = website.rstrip('/')
    parsed = urlparse(base)
    base_domain = f"{parsed.scheme}://{parsed.netloc}"
    for path in PATHS:
        url  = urljoin(base_domain, path)
        text = fetch(url)
        if not text: continue
        # Önce mailto: linkleri — en güvenilir
        mailto = re.findall(r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', text)
        valid = [e for e in mailto if is_valid(e)]
        if valid: return valid[0]
        # Sonra düz metin
        emails = [e for e in set(EMAIL_RE.findall(text)) if is_valid(e)]
        if emails: return emails[0]
    return None

def push_to_sheets(data, token):
    if not token: return
    import requests as req
    rows = []
    for r in data:
        rows.append([
            '',
            r.get('company_name', ''),
            "'" + r.get('phone', ''),
            r.get('address', ''),
            r.get('city', ''),
            r.get('email', ''),
            r.get('website', ''),
            str(r.get('google_rating', '') or ''),
            r.get('google_maps_url', ''),
            ', '.join(r.get('capabilities', [])) if isinstance(r.get('capabilities'), list) else r.get('capabilities', ''),
            r.get('source', ''),
            r.get('verification_status', 'Taslak'),
            r.get('notes', '')
        ])
    req.post(
        f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/Firma%20Listesi!A2:M200000:clear',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, json={})
    time.sleep(1)
    written = 0
    for i in range(0, len(rows), 1000):
        chunk = rows[i:i+1000]
        r2 = i + 2; r3 = r2 + len(chunk) - 1
        resp = req.put(
            f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/Firma%20Listesi!A{r2}:M{r3}?valueInputOption=USER_ENTERED',
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json={'values': chunk})
        if resp.status_code == 200:
            written += len(chunk)
        time.sleep(0.3)
    print(f'  → Sheets güncellendi: {written} satır', flush=True)

# ── Ana akış ──────────────────────────────────────────────────────
data = json.load(open('/app/scraper/combined_all.json'))
to_scrape = [(i, r) for i, r in enumerate(data)
             if r.get('website', '').startswith('http')
             and not any(s in r.get('website', '') for s in SOCIAL)
             and not r.get('email', '').strip()]

already = sum(1 for r in data if r.get('email', '').strip())
print(f'Mevcut e-posta: {already} | Taranacak: {len(to_scrape)}', flush=True)

data_dict  = {i: r for i, r in enumerate(data)}
total_new  = 0
BATCH      = 200
WORKERS    = 25
SHEET_EACH = 2000

for b in range(0, len(to_scrape), BATCH):
    batch = to_scrape[b:b+BATCH]
    batch_found = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(scrape_deep, r.get('website', '')): (idx, r) for idx, r in batch}
        for future in as_completed(futures):
            orig_idx, r = futures[future]
            try:
                email = future.result()
                if email:
                    data_dict[orig_idx]['email'] = email
                    batch_found += 1
            except: pass
    total_new += batch_found
    done = b + len(batch)
    pct  = done / len(to_scrape) * 100
    total_email = already + total_new
    print(f'[{done}/{len(to_scrape)} %{pct:.0f}] +{batch_found} | toplam e-posta: {total_email}', flush=True)

    updated = [data_dict[i] for i in range(len(data))]
    json.dump(updated, open('/app/scraper/combined_all.json', 'w'), ensure_ascii=False)

    if done % SHEET_EACH < BATCH:
        print('  Sheets yazılıyor...', flush=True)
        push_to_sheets(updated, TOKEN)

# Final
updated = [data_dict[i] for i in range(len(data))]
json.dump(updated, open('/app/scraper/combined_all.json', 'w'), ensure_ascii=False)
print('Final Sheets güncellemesi...', flush=True)
push_to_sheets(updated, TOKEN)
total_email = sum(1 for r in updated if r.get('email', '').strip())
print(f'\n✅ TAMAMLANDI — Toplam e-posta: {total_email}/{len(updated)} (%{total_email/len(updated)*100:.1f})', flush=True)
