import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_tcmb_usd_try():
    """
    Fetches the current daily USD/TRY rate from TCMB today.xml.
    """
    url = "https://www.tcmb.gov.tr/kurlar/today.xml"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            for curr in root.findall('Currency'):
                if curr.attrib.get('Kod') == 'USD':
                    buying = float(curr.find('ForexBuying').text)
                    selling = float(curr.find('ForexSelling').text)
                    date = root.attrib.get('Tarih', 'Unknown Date')
                    return {"date": date, "usd_buying": buying, "usd_selling": selling}
        return None
    except Exception as e:
        print(f"Error fetching TCMB rates: {e}")
        return None

def get_b2bpolymers_prices():
    """
    Parses current monthly average polymer granule prices in Turkey from b2bpolymers.com.
    """
    url = "https://b2bpolymers.com"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            text_content = soup.get_text()
            
            # Use regex to find the price section
            # The structure in b2bpolymers is raw text on the main page like:
            # LDPE ▼ 1,325 \n LLDPE ▼ 1,225 etc.
            import re
            pattern = r"(LDPE|LLDPE|HDPE|PPH|PPC|PPR|GPPS|HIPS|ABS)\s+[▲▼]?\s*([\d,]+)"
            matches = re.findall(pattern, text_content)
            
            prices = {}
            for mat, val in matches:
                # convert e.g. "1,850" to float 1850.0
                prices[mat] = float(val.replace(',', ''))
            
            # Find date if possible
            date_match = re.search(r"(\d{2}\.\d{2}\.\d{4})", text_content)
            date = date_match.group(1) if date_match else "Unknown"
            
            return {"date": date, "unit": "USD/MT (USD/ton)", "prices": prices}
        return None
    except Exception as e:
        print(f"Error parsing b2bpolymers: {e}")
        return None

if __name__ == "__main__":
    print("--- FETCHING TCMB EXCHANGE RATES ---")
    tcmb = get_tcmb_usd_try()
    if tcmb:
        print(f"TCMB Date: {tcmb['date']}")
        print(f"USD/TRY Forex Buying: {tcmb['usd_buying']}")
        print(f"USD/TRY Forex Selling: {tcmb['usd_selling']}")
    else:
        print("TCMB Fetch Failed")
        
    print("\n--- FETCHING B2BPOLYMERS GRANULE PRICES ---")
    polymers = get_b2bpolymers_prices()
    if polymers:
        print(f"b2bPolymers Reference Date: {polymers['date']}")
        print(f"Unit: {polymers['unit']}")
        for mat, price in polymers['prices'].items():
            # Convert USD/ton to TL/kg using TCMB rate if available
            tl_kg = ""
            if tcmb:
                # price in USD/ton / 1000 = USD/kg. USD/kg * usd_selling = TRY/kg
                usd_kg = price / 1000.0
                try_kg = usd_kg * tcmb['usd_selling']
                tl_kg = f" | Approx: {try_kg:.2f} TL/kg + KDV"
            print(f"  {mat}: {price:.0f} USD/ton{tl_kg}")
    else:
        print("b2bPolymers Fetch Failed")
