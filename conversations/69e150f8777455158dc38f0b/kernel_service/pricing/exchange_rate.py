"""
TCMB Döviz Kuru Modülü
API: https://www.tcmb.gov.tr/kurlar/today.xml

Kur riski önlemleri:
  A) KUR TAMPONU: TCMB kuru üstüne %4 buffer uygulanır
     → Küçük dalgalanmalar (±%3) absorbe edilir, platform zarar etmez
  B) GEÇERLİLİK SÜRESİ: Her teklif oluşturulduğunda snapshot alınır
     → Müşteriye "Bu fiyat X saat geçerlidir" bilgisi verilir
  D) USD İÇ / TRY DIŞ: İç hesap her zaman USD, gösterim TRY
     → Malzeme/makine fiyatları kur bağımsız kalır

Cache TTL: 4 saat (aynı gün içinde TCMB tekrar çarılmaz)
Fallback: TCMB erişilemezse 47.0 TL (sabit)
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import threading

# ── Kur tamponu (A önlemi) ──────────────────────────────────────────────
# TCMB kuru * (1 + BUFFER) → fiyatlamada kullanılan kur
# %4 tampon: kur %3.8'e kadar yükselirse platform zarar etmez
KUR_TAMPONU = 0.04   # %4

# ── Teklif geçerlilik süreleri (B önlemi) ─────────────────────────────
VALIDITY_HOURS = {
    "fdm":     24,   # FDM: 24 saat (hızlı üretim, düşük kur riski)
    "sla":     24,
    "sls":     48,   # SLS/MJF: 48 saat (daha pahalı, daha uzun planlama)
    "mjf":     48,
    "laser":   24,   # Lazer: 24 saat
    "bending": 24,
    "cnc":     48,
    "dmls":    72,   # DMLS metal: 72 saat (çok pahalı, detaylı teklif)
    "default": 24,
}

# ── In-memory cache ────────────────────────────────────────────────────
_cache = {
    "usd_try": None,
    "eur_try": None,
    "fetched_at": None,
    "source": None,
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
    root = ET.fromstring(resp.content)
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


def _refresh_if_needed(force: bool = False):
    """Cache süresi dolmuşsa TCMB'den yenile."""
    now = datetime.utcnow()
    expired = (
        _cache["fetched_at"] is None or
        (now - _cache["fetched_at"]) > timedelta(hours=CACHE_TTL_HOURS)
    )
    if force or expired:
        try:
            rates = _fetch_tcmb()
            _cache["usd_try"] = rates.get("USD", FALLBACK_USD_TRY)
            _cache["eur_try"] = rates.get("EUR", FALLBACK_EUR_TRY)
            _cache["fetched_at"] = now
            _cache["source"] = "tcmb"
        except Exception as e:
            if _cache["usd_try"] is None:
                _cache["usd_try"] = FALLBACK_USD_TRY
                _cache["eur_try"] = FALLBACK_EUR_TRY
            _cache["source"] = f"fallback ({str(e)[:60]})"


def get_usd_try(force_refresh: bool = False, with_buffer: bool = False) -> float:
    """
    Güncel USD/TRY kurunu döndür.
    with_buffer=True → fiyatlama için %4 tamponlu kur
    with_buffer=False → ham TCMB kuru (gösterim / bilgi için)
    """
    with _cache_lock:
        _refresh_if_needed(force_refresh)
        rate = _cache["usd_try"]
    return round(rate * (1 + KUR_TAMPONU), 4) if with_buffer else rate


def get_eur_try() -> float:
    with _cache_lock:
        _refresh_if_needed()
        return _cache["eur_try"]


def get_pricing_rate(technology: str = "default") -> dict:
    """
    Fiyatlama için tamponu uygulanmış kur + geçerlilik bilgisi.
    engine.py bu fonksiyonu kullanır.
    """
    with _cache_lock:
        _refresh_if_needed()
        tcmb_rate = _cache["usd_try"]
        source = _cache["source"]
        fetched_at = _cache["fetched_at"]

    buffered_rate = round(tcmb_rate * (1 + KUR_TAMPONU), 4)
    validity_hours = VALIDITY_HOURS.get(technology, VALIDITY_HOURS["default"])
    valid_until = datetime.utcnow() + timedelta(hours=validity_hours)

    return {
        "tcmb_rate": tcmb_rate,                          # ham TCMB kuru
        "pricing_rate": buffered_rate,                    # fiyatlamada kullanılan kur (%4 tamponlu)
        "buffer_pct": KUR_TAMPONU * 100,                  # 4.0
        "source": source,
        "fetched_at": fetched_at.isoformat() + "Z" if fetched_at else None,
        "valid_until": valid_until.isoformat() + "Z",    # teklifin geçerlilik sonu
        "valid_hours": validity_hours,
    }


def get_rate_info() -> dict:
    """Kur bilgisini metadata ile döndür (/exchange-rate endpoint için)."""
    with _cache_lock:
        _refresh_if_needed()
        tcmb = _cache["usd_try"]
        eur = _cache["eur_try"]
        source = _cache["source"]
        fetched_at = _cache["fetched_at"]

    buffered = round(tcmb * (1 + KUR_TAMPONU), 4)
    next_min = _next_refresh_min(fetched_at)

    return {
        "usd_try": tcmb,
        "usd_try_buffered": buffered,
        "eur_try": eur,
        "buffer_pct": KUR_TAMPONU * 100,
        "source": source,
        "fetched_at": fetched_at.isoformat() + "Z" if fetched_at else None,
        "next_refresh_in_min": next_min,
        "validity_hours_by_technology": VALIDITY_HOURS,
    }


def usd_to_try(amount_usd: float, with_buffer: bool = True) -> float:
    """
    USD miktarını TRY'ye çevir.
    with_buffer=True (default) → fiyatlama için tamponu uygulanmış kur
    with_buffer=False → ham TCMB kuru
    """
    rate = get_usd_try(with_buffer=with_buffer)
    return round(amount_usd * rate, 2)


def _next_refresh_min(fetched_at) -> int:
    if fetched_at is None:
        return 0
    elapsed = (datetime.utcnow() - fetched_at).total_seconds() / 60
    return max(0, int(CACHE_TTL_HOURS * 60 - elapsed))
