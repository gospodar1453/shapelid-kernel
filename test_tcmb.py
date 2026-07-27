import urllib.request
import xml.etree.ElementTree as ET
import json

def fetch_tcmb_rates():
    url = "https://www.tcmb.gov.tr/kurlar/today.xml"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
    except Exception as e:
        return {"error": f"Failed to fetch TCMB XML: {e}"}
        
    try:
        root = ET.fromstring(xml_data)
        date = root.attrib.get("Tarih", "")
        rates = {}
        for currency in root.findall("Currency"):
            code = currency.attrib.get("CurrencyCode", "")
            # We are interested in USD, EUR, etc.
            if code in ["USD", "EUR"]:
                forex_buying = currency.find("ForexBuying").text
                forex_selling = currency.find("ForexSelling").text
                rates[code] = {
                    "Buying": float(forex_buying.strip()) if forex_buying else None,
                    "Selling": float(forex_selling.strip()) if forex_selling else None
                }
        return {
            "date": date,
            "rates": rates
        }
    except Exception as e:
        return {"error": f"Failed to parse XML: {e}"}

if __name__ == "__main__":
    result = fetch_tcmb_rates()
    print(json.dumps(result, indent=2))
