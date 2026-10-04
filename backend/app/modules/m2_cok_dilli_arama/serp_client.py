"""
MODUL 2 - serp_client.py

valentin.app'in yaptigi isi ("o ulkeden ariyormus gibi simule etmek")
resmi/otomasyona uygun sekilde SerpAPI ile yapiyoruz:
- engine=google/bing/yandex -> hangi arama motoru
- gl=<ulke kodu>  -> "bu ulkeden arıyormuş gibi" (valentin.app'in tam yaptigi is)
- hl=<dil kodu>   -> arama arayuz dili

API anahtari yoksa (SERPAPI_KEY bos) fonksiyon bos liste doner - sistem
CRASH ETMEZ (Modul 1'deki ipinfo/google_places ile ayni pattern).
"""
import httpx

from app.core.config import settings

SERPAPI_URL = "https://serpapi.com/search"

# Dil kodu -> arama motoru hl parametresi eslesmesi
DIL_KODU_MAP = {
    "tr": "tr", "en": "en", "es": "es", "ru": "ru",
    "ar": "ar", "fr": "fr", "de": "de",
}


def search(query: str, engine: str, country_code: str, lang_code: str, num: int = 10) -> list[dict]:
    """
    Basarisiz olursa (key yok, rate limit, timeout) BOS LISTE doner -
    bir dil/motor kombinasyonunun basarisiz olmasi tum aramayi durdurmamali.
    """
    if not settings.SERPAPI_KEY:
        return []

    params = {
        "engine": engine,
        "q": query,
        "gl": country_code.lower(),
        "hl": lang_code,
        "num": num,
        "api_key": settings.SERPAPI_KEY,
    }

    try:
        resp = httpx.get(SERPAPI_URL, params=params, timeout=15.0)
        if resp.status_code != 200:
            return []
        data = resp.json()
        organic = data.get("organic_results", [])
        return [
            {
                "title": r.get("title"),
                "url": r.get("link"),
                "snippet": r.get("snippet"),
            }
            for r in organic if r.get("link")
        ]
    except httpx.HTTPError:
        return []


def reverse_image_search(image_url: str, country_code: str) -> list[dict]:
    """
    Dokumandaki (e) maddesi: "Arama yerine urunun resmi... urunun resmiyle
    eslesen web sitelerini tarayacak."

    SerpAPI'nin google_lens motoru bir GORSEL URL'i alir (dosya degil!) ve o
    gorsele gorsel olarak benzer / o urunu satan sayfalari dondurur.

    ONEMLI SINIRLAMA: image_url INTERNETTEN ERISILEBILIR olmali - yani
    localhost'ta calisirken (backend internetten erisilemedigi icin) bu
    fonksiyon anlamli sonuc VEREMEZ. Production'da backend gercek bir
    domainde yayinda oldugunda calisir. Bu sinirlama testlerde monkeypatch
    ile, gercek ortamda ise musteriye acikca belirtilmeli.
    """
    if not settings.SERPAPI_KEY:
        return []

    params = {
        "engine": "google_lens",
        "url": image_url,
        "country": country_code.lower(),
        "api_key": settings.SERPAPI_KEY,
    }

    try:
        resp = httpx.get(SERPAPI_URL, params=params, timeout=20.0)
        if resp.status_code != 200:
            return []
        data = resp.json()
        matches = data.get("visual_matches", [])
        return [
            {
                "title": m.get("title"),
                "url": m.get("link"),
                "snippet": m.get("source"),
            }
            for m in matches if m.get("link")
        ]
    except httpx.HTTPError:
        return []
