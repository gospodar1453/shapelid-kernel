import json, os, time, urllib.request, urllib.parse

WIX_TOKEN = os.environ.get("WIX_ACCESS_TOKEN", "")
COLLECTION = "manufacturers"

removed = json.load(open('/app/scraper/removed_companies.json', encoding='utf-8'))
print(f"Silinecek: {len(removed)} firma")

def find_and_delete(title):
    # Query by title
    query_url = "https://www.wixapis.com/wix-data/v2/items/query"
    payload = json.dumps({
        "dataCollectionId": COLLECTION,
        "query": {
            "filter": {"title": {"$eq": title}},
            "paging": {"limit": 5}
        }
    }, ensure_ascii=False).encode("utf-8")
    
    req = urllib.request.Request(query_url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WIX_TOKEN}",
    }, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
    except Exception as e:
        return 0, str(e)
    
    items = result.get("dataItems", [])
    deleted = 0
    for item in items:
        item_id = item.get("id")
        if not item_id:
            continue
        del_url = f"https://www.wixapis.com/wix-data/v2/items/{item_id}?dataCollectionId={COLLECTION}"
        del_req = urllib.request.Request(del_url, headers={
            "Authorization": f"Bearer {WIX_TOKEN}",
        }, method="DELETE")
        try:
            with urllib.request.urlopen(del_req, timeout=15) as dr:
                deleted += 1
        except Exception as e:
            pass
    return deleted, None

total_deleted = 0
total_not_found = 0
errors = []

for i, title in enumerate(removed):
    deleted, err = find_and_delete(title)
    total_deleted += deleted
    if deleted == 0:
        total_not_found += 1
    if err:
        errors.append((title, err))
    if (i+1) % 20 == 0 or (i+1) == len(removed):
        print(f"[{i+1}/{len(removed)}] Silinen: {total_deleted} | Bulunamayan: {total_not_found}")
    time.sleep(0.1)  # rate limit

print(f"\n=== TAMAMLANDI ===")
print(f"Wix'ten silinen: {total_deleted}")
print(f"Wix'te bulunamayan: {total_not_found}")
print(f"Hata: {len(errors)}")
