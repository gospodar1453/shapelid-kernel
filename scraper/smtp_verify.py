#!/usr/bin/env python3
"""
SMTP e-posta doğrulama:
1. Web sitesi domain'inden info@, iletisim@, contact@ gibi adaylar üret
2. SMTP RCPT TO ile sunucuya sor (e-posta göndermeden)
3. Doğrulanan adresleri combined_all.json'a kaydet
4. Her 500 firmada bir Sheets'e yaz
"""
import json, re, os, time, socket, smtplib
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

SHEET_ID = '1iU10AWTHZVkGlXoHawxJrnsCh7gUDmIjahlkl9T34_k'
TOKEN    = os.environ.get('GOOGLESHEETS_ACCESS_TOKEN', '')

# Türk firmaları için en yaygın prefix'ler (öncelik sırasıyla)
PREFIXES = ['info', 'iletisim', 'contact', 'mail', 'ofis', 'bilgi', 'satis', 'destek']

SOCIAL = ['instagram.com','linkedin.com','facebook.com','twitter.com','youtube.com']

def extract_domain(website):
    try:
        p = urlparse(website)
        host = p.netloc.lower().replace('www.','')
        return host if '.' in host else None
    except: return None

def get_mx(domain):
    """Domain'in MX kaydını çek"""
    try:
        import dns.resolver
        mx = dns.resolver.resolve(domain, 'MX', lifetime=5)
        return sorted(mx, key=lambda r: r.preference)[0].exchange.to_text().rstrip('.')
    except:
        # dnspython yoksa domain'i direkt dene
        return domain

def smtp_verify(email, mx_host, timeout=8):
    """SMTP RCPT TO ile e-posta var mı diye sor (göndermeden)"""
    try:
        with smtplib.SMTP(timeout=timeout) as smtp:
            smtp.connect(mx_host, 25)
            smtp.helo('shapelid.com')
            smtp.mail('verify@shapelid.com')
            code, msg = smtp.rcpt(email)
            return code == 250
    except Exception as e:
        err = str(e).lower()
        # 550/551/553 = kesin yok; timeout/connection = belirsiz
        if any(x in err for x in ['550','551','553','does not exist','unknown user']):
            return False
        # Bağlanamadıysak domain'i geç ama email'i kaydetme
        return False

def find_email_for_domain(domain):
    """Domain için en olası e-posta adresini bul"""
    mx = get_mx(domain)
    if not mx:
        return None
    for prefix in PREFIXES:
        candidate = f"{prefix}@{domain}"
        try:
            if smtp_verify(candidate, mx):
                return candidate
        except:
            pass
        time.sleep(0.1)
    return None

def push_to_sheets(data, token):
    """Sheets Firma Listesi sekmesini güncelle"""
    import requests as req
    if not token: return
    rows = []
    for r in data:
        rows.append([
            '',
            r.get('company_name',''),
            "'" + r.get('phone',''),
            r.get('address',''),
            r.get('city',''),
            r.get('email',''),
            r.get('website',''),
            str(r.get('google_rating','') or ''),
            r.get('google_maps_url',''),
            ', '.join(r.get('capabilities',[])) if isinstance(r.get('capabilities'), list) else r.get('capabilities',''),
            r.get('source',''),
            r.get('verification_status','Taslak'),
            r.get('notes','')
        ])
    # Temizle
    req.post(
        f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/Firma%20Listesi!A2:M200000:clear',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, json={})
    time.sleep(1)
    total_written = 0
    for i in range(0, len(rows), 1000):
        chunk = rows[i:i+1000]
        r2 = i + 2; r3 = r2 + len(chunk) - 1
        resp = req.put(
            f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/Firma%20Listesi!A{r2}:M{r3}?valueInputOption=USER_ENTERED',
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json={'values': chunk})
        if resp.status_code == 200:
            total_written += len(chunk)
        time.sleep(0.3)
    print(f'  → Sheets güncellendi: {total_written} satır', flush=True)

# ── Ana akış ──────────────────────────────────────────────────────
data = json.load(open('/app/scraper/combined_all.json'))

to_process = [(i, r) for i, r in enumerate(data)
              if r.get('website','').startswith('http')
              and not any(s in r.get('website','') for s in SOCIAL)
              and not r.get('email','').strip()]

already = sum(1 for r in data if r.get('email','').strip())
print(f'Mevcut e-posta: {already} | SMTP denenecek: {len(to_process)}', flush=True)

data_dict = {i: r for i, r in enumerate(data)}
total_found = 0
BATCH       = 100
WORKERS     = 30
SHEET_EVERY = 500

for b in range(0, len(to_process), BATCH):
    batch = to_process[b:b+BATCH]
    batch_found = 0

    def try_find(args):
        idx, r = args
        domain = extract_domain(r.get('website',''))
        if not domain: return idx, None
        email = find_email_for_domain(domain)
        return idx, email

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(try_find, item): item for item in batch}
        for future in as_completed(futures):
            try:
                idx, email = future.result()
                if email:
                    data_dict[idx]['email'] = email
                    batch_found += 1
            except: pass

    total_found += batch_found
    done = b + len(batch)
    pct  = done / len(to_process) * 100
    total_email = already + total_found
    print(f'[{done}/{len(to_process)} %{pct:.0f}] +{batch_found} | toplam e-posta: {total_email}', flush=True)

    updated = [data_dict[i] for i in range(len(data))]
    json.dump(updated, open('/app/scraper/combined_all.json','w'), ensure_ascii=False)

    if done % SHEET_EVERY < BATCH:
        print('  Sheets yazılıyor...', flush=True)
        push_to_sheets(updated, TOKEN)

# Son kayıt
updated = [data_dict[i] for i in range(len(data))]
json.dump(updated, open('/app/scraper/combined_all.json','w'), ensure_ascii=False)
print('Son Sheets güncellemesi...', flush=True)
push_to_sheets(updated, TOKEN)

total_email = sum(1 for r in updated if r.get('email','').strip())
print(f'\n✅ TAMAMLANDI — Toplam e-posta: {total_email}/{len(updated)} (%{total_email/len(updated)*100:.1f})', flush=True)
