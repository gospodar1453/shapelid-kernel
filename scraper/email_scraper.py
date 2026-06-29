#!/usr/bin/env python3
"""
Web sitelerinden e-posta adresi çeken toplu scraper.
Her site için iletisim, hakkimizda, contact sayfalarına bakar.
"""
import json, re, time, requests, os
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
SOCIAL = ['instagram.com','linkedin.com','facebook.com','twitter.com','youtube.com']

CONTACT_PATHS = ['/iletisim', '/contact', '/hakkimizda', '/about', 
                 '/iletisim.html', '/contact.html', '/iletisim.php',
                 '/tr/iletisim', '/tr/contact']

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Accept': 'text/html,application/xhtml+xml',
}

EXCLUDE_EMAILS = ['noreply','no-reply','donotreply','example.com','sentry.io',
                   'wix.com','wordpress.com','gmail.com','hotmail.com','yahoo.com',
                   'yandex.com','outlook.com']

def is_valid_email(email):
    e = email.lower()
    if any(ex in e for ex in EXCLUDE_EMAILS):
        return False
    if len(email) > 80:
        return False
    return True

def extract_emails(text):
    found = EMAIL_RE.findall(text)
    return [e for e in set(found) if is_valid_email(e)]

def fetch_page(url, timeout=8):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, 
                        allow_redirects=True, verify=False)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return ''

def scrape_emails(website):
    if not website or any(s in website for s in SOCIAL):
        return []
    
    base = website.rstrip('/')
    parsed = urlparse(base)
    base_domain = f"{parsed.scheme}://{parsed.netloc}"
    
    all_emails = []
    
    # Ana sayfa
    text = fetch_page(base)
    all_emails += extract_emails(text)
    
    # Eğer ana sayfada bulunamadıysa iletişim sayfalarını dene
    if not all_emails:
        for path in CONTACT_PATHS:
            contact_url = urljoin(base_domain, path)
            text = fetch_page(contact_url, timeout=6)
            emails = extract_emails(text)
            if emails:
                all_emails += emails
                break
            time.sleep(0.3)
    
    return list(set(all_emails))[:3]  # max 3 email

def process_batch(firms, start_idx, total, results_file):
    found_count = 0
    results = []
    
    for i, r in enumerate(firms):
        website = r.get('website','')
        emails = scrape_emails(website)
        
        if emails:
            r['email'] = emails[0]  # en iyi adayı al
            found_count += 1
        
        results.append(r)
        
        if (i+1) % 100 == 0:
            progress = start_idx + i + 1
            print(f'  İlerleme: {progress}/{total} | Bu batch bulunan: {found_count}', flush=True)
            # Ara kaydet
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False)
    
    return results, found_count

if __name__ == '__main__':
    import warnings
    warnings.filterwarnings('ignore')
    
    data = json.load(open('/app/scraper/combined_all.json', encoding='utf-8'))
    
    # Scrape edilecekler: web sitesi var, e-posta yok
    to_scrape = [(i, r) for i, r in enumerate(data) 
                 if r.get('website','').startswith('http')
                 and not any(s in r.get('website','') for s in SOCIAL)
                 and not r.get('email','').strip()]
    
    already_done = [(i, r) for i, r in enumerate(data) 
                    if not (r.get('website','').startswith('http')
                    and not any(s in r.get('website','') for s in SOCIAL)
                    and not r.get('email','').strip())]
    
    print(f'Scrape edilecek: {len(to_scrape)} firma')
    print(f'Atlanan (sosyal/yok/zaten var): {len(already_done)} firma')
    
    BATCH_SIZE = 500
    total_found = 0
    
    # Tüm data'yı indeksli dict'e al
    data_by_idx = {i: r for i, r in enumerate(data)}
    
    for batch_start in range(0, len(to_scrape), BATCH_SIZE):
        batch = to_scrape[batch_start:batch_start+BATCH_SIZE]
        print(f'\nBatch {batch_start//BATCH_SIZE + 1}: {batch_start+1}-{batch_start+len(batch)}/{len(to_scrape)}')
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(scrape_emails, r.get('website','')): (idx, r) 
                      for idx, r in batch}
            
            batch_found = 0
            for future in as_completed(futures):
                orig_idx, r = futures[future]
                try:
                    emails = future.result()
                    if emails:
                        data_by_idx[orig_idx]['email'] = emails[0]
                        batch_found += 1
                except:
                    pass
        
        total_found += batch_found
        print(f'  Batch tamamlandı: {batch_found} e-posta bulundu (toplam: {total_found})')
        
        # Her batch sonrası kaydet
        updated_data = [data_by_idx[i] for i in range(len(data))]
        with open('/app/scraper/combined_all.json', 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False)
        
        time.sleep(1)
    
    # Final kaydet
    updated_data = [data_by_idx[i] for i in range(len(data))]
    with open('/app/scraper/combined_all.json', 'w', encoding='utf-8') as f:
        json.dump(updated_data, f, ensure_ascii=False)
    
    has_email = sum(1 for r in updated_data if r.get('email',''))
    print(f'\n✅ Tamamlandı!')
    print(f'   Toplam firma: {len(updated_data)}')
    print(f'   E-posta bulunan: {has_email}')
    print(f'   Başarı oranı: {has_email/len(to_scrape)*100:.1f}%')
