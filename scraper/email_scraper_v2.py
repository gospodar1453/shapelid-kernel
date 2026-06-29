import json, re, time, warnings, requests, sys
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
warnings.filterwarnings('ignore')

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
SOCIAL = ['instagram.com','linkedin.com','facebook.com','twitter.com','youtube.com']
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1)'}

# Geçersiz e-posta domain'leri (hosting, CMS, genel)
EXCLUDE = [
    'noreply','no-reply','example.com','sentry.io','wix.com','wordpress.com',
    'hotmail.com','yahoo.com','yandex.','outlook.com','gmail.com',
    'natro.com','isimtescil.net','turhost.com','biges.com','name.com',
    'hostinger.com','godaddy.com','ihs.com.tr','cloudflare.com',
    'protection.outlook','spamprotect','info@info','test@','admin@admin',
]

def is_valid(e):
    el = e.lower()
    return not any(x in el for x in EXCLUDE) and 5 < len(e) < 80 and '.' in e.split('@')[-1]

def fetch(url, timeout=7):
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
        for path in ['/iletisim', '/contact', '/iletisim.html', '/contact.html', '/tr/iletisim']:
            text = fetch(urljoin(base_domain, path), timeout=5)
            emails = [e for e in set(EMAIL_RE.findall(text)) if is_valid(e)]
            if emails: break
            time.sleep(0.2)
    return emails[:1]

data = json.load(open('/app/scraper/combined_all.json'))
to_scrape = [(i, r) for i, r in enumerate(data)
             if r.get('website','').startswith('http')
             and not any(s in r.get('website','') for s in SOCIAL)
             and not r.get('email','').strip()]

print(f'Scrape edilecek: {len(to_scrape)} firma', flush=True)

data_dict = {i: r for i, r in enumerate(data)}
total_found = 0
BATCH = 500
WORKERS = 25

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
    print(f'[{done}/{len(to_scrape)}] Batch tamamlandi: +{batch_found} (toplam: {total_found})', flush=True)
    updated = [data_dict[i] for i in range(len(data))]
    json.dump(updated, open('/app/scraper/combined_all.json','w'), ensure_ascii=False)
    time.sleep(0.5)

updated = [data_dict[i] for i in range(len(data))]
json.dump(updated, open('/app/scraper/combined_all.json','w'), ensure_ascii=False)
has_email = sum(1 for r in updated if r.get('email',''))
print(f'\nTAMAMLANDI: {has_email} firmada e-posta var ({has_email/len(updated)*100:.1f}%)', flush=True)
