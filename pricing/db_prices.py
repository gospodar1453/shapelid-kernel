"""
DB Fiyat Katmanı — MaterialPrice entity'sinden canlı fiyat çeker.

Base44 backend function üzerinden MaterialPrice kayıtlarını okur.
Başarısız olursa material_rates.py'deki sabit değerlere fallback yapar.

Cache: 4 saatlik in-memory cache (Railway container yeniden başlayana kadar geçerli)
"""

import os
import time
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ── Konfigürasyon ──────────────────────────────────────────────────────
BASE44_API_URL = os.getenv("BASE44_API_URL", "")          # Backend function URL
BASE44_API_KEY = os.getenv("BASE44_API_KEY", "")          # Service API key (opsiyonel)
CACHE_TTL_SEC  = int(os.getenv("PRICE_CACHE_TTL", "14400"))  # 4 saat default

# ── In-memory cache ────────────────────────────────────────────────────
_cache: dict = {}          # material_key → {price_per_cm3, price_per_kg, ...}
_cache_ts: float = 0.0     # son yükleme zamanı


def _is_cache_valid() -> bool:
    return bool(_cache) and (time.time() - _cache_ts) < CACHE_TTL_SEC


def _load_from_db() -> bool:
    """Base44 getMaterialPrices backend function'ını çağırır."""
    if not BASE44_API_URL:
        logger.warning("BASE44_API_URL tanımlı değil — DB fiyatları atlanıyor")
        return False
    try:
        url = BASE44_API_URL.rstrip("/") + "/getMaterialPrices"
        headers = {"Content-Type": "application/json"}
        if BASE44_API_KEY:
            headers["Authorization"] = f"Bearer {BASE44_API_KEY}"
        resp = requests.post(url, json={}, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            logger.warning("getMaterialPrices başarısız: %s", data)
            return False
        _populate_cache(data.get("prices", []))
        return True
    except Exception as e:
        logger.warning("DB fiyat çekme hatası: %s", e)
        return False


def _populate_cache(prices: list) -> None:
    global _cache, _cache_ts
    new_cache = {}
    for p in prices:
        key = p.get("material_key")
        if not key:
            continue
        # override_active ise override_price, yoksa current_price kullan
        active_price = (
            p["override_price_usd"] if p.get("override_active") and p.get("override_price_usd")
            else p.get("current_price_usd") or p.get("base_price_usd")
        )
        new_cache[key] = {
            "active_price_usd_per_kg": active_price,
            "source": "db",
            "override_active": p.get("override_active", False),
            "last_update": p.get("last_auto_update", ""),
        }
    _cache = new_cache
    _cache_ts = time.time()
    logger.info("DB fiyat cache güncellendi: %d kayıt", len(_cache))


def get_db_price(material_key: str) -> Optional[float]:
    """
    Verilen material_key için USD/kg fiyatı döndürür.
    DB'den yüklenemezse None döner (fallback devreye girer).
    """
    if not _is_cache_valid():
        _load_from_db()
    entry = _cache.get(material_key)
    if entry:
        return entry["active_price_usd_per_kg"]
    return None


def invalidate_cache():
    """Zorla cache temizle (test veya manual override sonrası)."""
    global _cache, _cache_ts
    _cache = {}
    _cache_ts = 0.0
