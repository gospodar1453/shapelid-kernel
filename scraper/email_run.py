import json, re, time, warnings, requests
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
warnings.filterwarnings('ignore')

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
SOCIAL = ['instagram.com','linkedin.com','facebook.com','twitter.com','youtube.com']
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1)'}
EXCLUDE = [
    'noreply','no-reply','example.com','sentry.io','wix.com','wordpress.com',
    'hotmail.com','yahoo.com','yandex.','outlook.com','gmail.com',
    'natro.com','isimtescil.net','turhost.com','hostinger.com','godaddy.com',
    'cloudflare.com','protection.outlook','spamprotect',
]

def is_valid(e):
    el = e.lower()
    return not any(x in el for x in EXCLUDE) and 5 < len(e) < 80 and '.' in e.split('@')[-1]

def fetch(url, timeout=5):
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
            text = fetch(urljoin(base_domain, path), timeout=4)
            emails = [e for e in set(EMAIL_RE.findall(text)) if is_valid(e)]
            if emails: break
    return emails[:1]

data = json.load(open('/app/scraper/combined_all.json'))
to_scrape = [(i, r) for i, r in enumerate(data)
             if r.get('website','').startswith('http')
             and not any(s in r.get('website','') for s in SOCIAL)
             and not r.get('email','').strip()]

print(f'Kalan: {len(to_scrape)}', flush=True)
data_dict = {i: r for i, r in enumerate(data)}
total_found = 0

for b in range(0, len(to_scrape), 300):
    batch = to_scrape[b:b+300]
    batch_found = 0
    with ThreadPoolExecutor(max_workers=40) as ex:
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
    print(f'[{done}/{len(to_scrape)}] +{batch_found} (toplam: {total_found})', flush=True)
    updated = [data_dict[i] for i in range(len(data))]
    json.dump(updated, open('/app/scraper/combined_all.json','w'), ensure_ascii=False)

print(f'TAMAMLANDI: {total_found}', flush=True)
