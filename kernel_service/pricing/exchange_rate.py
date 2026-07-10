"""
TCMB Döviz Kuru Modülü
API: https://www.tcmb.gov.tr/kurlar/today.xml

- Günlük TCMB resmi ForexBuying kuru kullanılır
- Hafta sonu / tatil günlerinde TCMB kur yayınlamaz → son bilinen kur cache'den döner
- Cache TTL: 4 saat (aynı gün içinde tekrar çekilmez)
- Fallback: sabit 47.0 (TCMB erişilemezse)
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import threading

# ── In-memory cache ───────────────────────────────────────────────────
_cache = {
    "usd_try": None,
    "eur_try": None,
    "fetched_at": None,
}
_cache_lock = threading.Lock()
CACHE_TTL_HOURS = 4
FALLBACK_USD_TRY = 47.0
FALLBACK_EUR_TRY = 53.5

TCMB_URL = "https://www.tcmb.gov.tr/kurlar/today.xml"


def _fetch_tcmb() -> dict:
    """TCMB'den güncel kurları çek, XML parse et."""
    resp = requests.get(TCMB_URL, timeout=5)
    resp.raise_for_status()
    
    # encoding fix (TCMB bazen latin-1 gönderir)
    content = resp.content
    root = ET.fromstring(content)
    
    rates = {}
    for currency in root.findall("Currency"):
        code = currency.get("CurrencyCode")
        if code not in ("USD", "EUR"):
            continue
        unit = int(currency.findtext("Unit", "1"))
        buying = currency.findtext("ForexBuying", "").strip()
        if buying:
            rates[code] = float(buying) / unit

    return rates


def get_usd_try(force_refresh: bool = False) -> float:
    """
    Güncel USD/TRY kurunu döndür.
    Cache geçerliyse cache'den, değilse TCMB'den çeker.
    """
    with _cache_lock:
        now = datetime.utcnow()
        cache_expired = (
            _cache["fetched_at"] is None or
            (now - _cache["fetched_at"]) > timedelta(hours=CACHE_TTL_HOURS)
        )

        if force_refresh or cache_expired:
            try:
                rates = _fetch_tcmb()
                _cache["usd_try"] = rates.get("USD", FALLBACK_USD_TRY)
                _cache["eur_try"] = rates.get("EUR", FALLBACK_EUR_TRY)
                _cache["fetched_at"] = now
                _cache["source"] = "tcmb"
            except Exception as e:
                # TCMB erişilemez → fallback
                if _cache["usd_try"] is None:
                    _cache["usd_try"] = FALLBACK_USD_TRY
                    _cache["eur_try"] = FALLBACK_EUR_TRY
                _cache["source"] = f"fallback ({str(e)[:60]})"

        return _cache["usd_try"]


def get_eur_try() -> float:
    """Güncel EUR/TRY kurunu döndür."""
    get_usd_try()  # cache'i doldurur
    return _cache.get("eur_try", FALLBACK_EUR_TRY)


def get_rate_info() -> dict:
    """Kur bilgisini metadata ile döndür (API response için)."""
    usd = get_usd_try()
    return {
        "usd_try": usd,
        "eur_try": _cache.get("eur_try", FALLBACK_EUR_TRY),
        "source": _cache.get("source", "unknown"),
        "fetched_at": _cache["fetched_at"].isoformat() + "Z" if _cache["fetched_at"] else None,
        "next_refresh_in_min": _next_refresh_min(),
    }


def usd_to_try(amount_usd: float) -> float:
    """USD miktarını TRY'ye çevir."""
    return round(amount_usd * get_usd_try(), 2)


def _next_refresh_min() -> int:
    if _cache["fetched_at"] is None:
        return 0
    elapsed = (datetime.utcnow() - _cache["fetched_at"]).total_seconds() / 60
    return max(0, int(CACHE_TTL_HOURS * 60 - elapsed))
