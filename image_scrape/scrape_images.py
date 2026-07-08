#!/usr/bin/env python3
"""
Firma web sitelerinden logo + kapak görseli çekme - paralel threadli
"""
import json, requests, warnings, sys, time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings("ignore")

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

SKIP_DOMAINS = ['instagram.com', 'facebook.com', 'linkedin.com', 'twitter.com', 'x.com', 'wa.me', 'whatsapp.com']

def is_valid_img_url(u):
    if not u:
        return False
    bad = ['sprite', 'icon-', 'favicon', '.svg', 'placeholder', 'blank.', '1x1', 'pixel.']
    return not any(b in u.lower() for b in bad)

def scrape_one(record):
    url = record.get('website', '')
    if not url or any(d in url for d in SKIP_DOMAINS):
        return None
    full_url = url if url.startswith('http') else 'https://' + url
    result = {"id": record.get("_local_id"), "company_name": record.get("company_name"), "logo": None, "cover": None, "error": None}
    try:
        resp = requests.get(full_url, headers=HEADERS, timeout=10, verify=False, allow_redirects=True)
        soup = BeautifulSoup(resp.text, 'lxml')

        # 1) og:image -> cover adayı
        og = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'og:image'})
        if og and og.get('content') and is_valid_img_url(og['content']):
            result['cover'] = urljoin(full_url, og['content'])

        # 2) logo bul
        logo_img = soup.find('img', src=lambda s: s and 'logo' in s.lower())
        if not logo_img:
            logo_img = soup.find('img', attrs={'alt': lambda a: a and 'logo' in a.lower()})
        if not logo_img:
            logo_img = soup.find('img', class_=lambda c: c and 'logo' in (c if isinstance(c,str) else ' '.join(c)).lower())
        if logo_img and logo_img.get('src') and is_valid_img_url(logo_img['src']):
            result['logo'] = urljoin(full_url, logo_img['src'])

        # 3) cover yoksa, sayfadaki en büyük olası içerik görseli (basit heuristic: ilk büyük img)
        if not result['cover']:
            imgs = soup.find_all('img')
            for img in imgs:
                src = img.get('src') or img.get('data-src')
                if src and is_valid_img_url(src) and 'logo' not in src.lower():
                    w = img.get('width')
                    try:
                        if w and int(w) < 100:
                            continue
                    except:
                        pass
                    result['cover'] = urljoin(full_url, src)
                    break
    except Exception as e:
        result['error'] = str(e)[:150]
    return result

def main(input_file, output_file, max_workers=30, limit=None):
    data = json.load(open(input_file, encoding='utf-8'))
    for i, r in enumerate(data):
        r['_local_id'] = i
    todo = [r for r in data if r.get('website') and not any(d in r['website'] for d in SKIP_DOMAINS)]
    if limit:
        todo = todo[:limit]
    print(f"Taranacak site sayısı: {len(todo)}", flush=True)

    results = []
    done = 0
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(scrape_one, r): r for r in todo}
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                results.append(res)
            done += 1
            if done % 200 == 0:
                print(f"İlerleme: {done}/{len(todo)}", flush=True)

    ok_logo = sum(1 for r in results if r.get('logo'))
    ok_cover = sum(1 for r in results if r.get('cover'))
    print(f"\nTamamlandı. Logo bulunan: {ok_logo}, Cover bulunan: {ok_cover}, Toplam: {len(results)}")

    json.dump(results, open(output_file, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f"Kaydedildi: {output_file}")

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else '/app/scraper/combined_all.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else '/app/image_scrape/results.json'
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else None
    main(input_file, output_file, limit=limit)
