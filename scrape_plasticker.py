import requests
from bs4 import BeautifulSoup
import json

def scrape_plasticker(category="Regranulat"):
    url = f"https://plasticker.de/preise/pms_en.php?show=ok&make=ok&aog=A&kat={category}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        return {"error": f"Failed to fetch data: {str(e)}"}
        
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Plasticker has a table of prices. Let's find the table rows.
    # Typically, the rows have td cells representing:
    # Materialgroup | Number of offers | Total amount | Average amount | Number of prices | min price | max price | average price
    
    data = {}
    table = soup.find("table") # Let's find tables
    if not table:
        return {"error": "Table not found in the response"}
        
    rows = soup.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 8:
            # Check if the first cell is a valid material group (e.g. ABS, PLA, PA 6)
            material = cells[0].text.strip()
            # If the row has numeric-like values in fields
            try:
                num_offers = cells[1].text.strip()
                total_amount = cells[2].text.strip()
                avg_amount = cells[3].text.strip()
                num_prices = cells[4].text.strip()
                min_price = cells[5].text.strip()
                max_price = cells[6].text.strip()
                avg_price = cells[7].text.strip()
                
                # Check if we have an average price that is a float or has values
                if avg_price and (avg_price != "---" or num_prices != "0"):
                    data[material] = {
                        "category": category,
                        "offers": int(num_offers) if num_offers.isdigit() else num_offers,
                        "total_amount_tons": total_amount,
                        "avg_amount_tons": avg_amount,
                        "num_prices": int(num_prices) if num_prices.isdigit() else num_prices,
                        "min_price_eur_kg": float(min_price.replace(",", ".")) if min_price and min_price != "---" else None,
                        "max_price_eur_kg": float(max_price.replace(",", ".")) if max_price and max_price != "---" else None,
                        "avg_price_eur_kg": float(avg_price.replace(",", ".")) if avg_price and avg_price != "---" else None
                    }
            except Exception as ex:
                continue
                
    return data

if __name__ == "__main__":
    regranulat_data = scrape_plasticker("Regranulat")
    mahlgut_data = scrape_plasticker("Mahlgut")
    
    combined = {
        "Regranulat": regranulat_data,
        "Mahlgut": mahlgut_data
    }
    
    print(json.dumps(combined, indent=2, ensure_ascii=False))
