"""
MODUL 3 - places_text_client.py

Dokumandaki "Ulke: X, kelime: Y -> haritada isaretli firmalar" istegini
Google Places API'nin TEXT SEARCH ucuyla karsiliyoruz. Nearby Search'ten
farkli olarak Text Search bir lat/lng/yaricap gerektirmez, "automotive in
United Kingdom" gibi serbest metin sorgusu kabul eder - bu da dokumandaki
"ulke ulke arama" mantigina Nearby Search'ten cok daha uygun.

Ayni GOOGLE_PLACES_API_KEY, Modul 1'de kullandigimizla ayni anahtar.

Iki asamali calisir:
1) text_search()    -> firma adi, adres, konum, place_id (ucretsiz/ucuz)
2) place_details()  -> telefon + website (EK sorgu, place_id basina 1 istek -
   bu yuzden `detay_getir=False` ile kapatilabilir, maliyeti dusurmek icin)
"""
import time

import httpx

from app.core.config import settings

TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


def text_search(query: str, max_sayfa: int = 3) -> list[dict]:
    """
    Google en fazla 20 sonuc/sayfa doner, `next_page_token` ile 3 sayfaya
    kadar (60 sonuca kadar) gidilebilir. Token'in aktif olmasi icin Google'in
    onerdigi kisa bir bekleme (~2sn) gerekir.
    """
    if not settings.GOOGLE_PLACES_API_KEY:
        return []

    sonuclar: list[dict] = []
    params = {"query": query, "key": settings.GOOGLE_PLACES_API_KEY}

    try:
        for sayfa in range(max_sayfa):
            resp = httpx.get(TEXT_SEARCH_URL, params=params, timeout=10.0)
            if resp.status_code != 200:
                break
            data = resp.json()

            for r in data.get("results", []):
                konum = r.get("geometry", {}).get("location", {})
                sonuclar.append({
                    "firma_adi": r.get("name"),
                    "adres": r.get("formatted_address"),
                    "lat": konum.get("lat"),
                    "lng": konum.get("lng"),
                    "google_place_id": r.get("place_id"),
                })

            next_token = data.get("next_page_token")
            if not next_token:
                break
            time.sleep(2)  # Google'in gereksinimi - token hemen aktif olmuyor
            params = {"pagetoken": next_token, "key": settings.GOOGLE_PLACES_API_KEY}
    except httpx.HTTPError:
        pass

    return sonuclar


def place_details(place_id: str) -> dict:
    """Sadece telefon + website icin ek sorgu. Basarisiz olursa bos deger doner (crash etmez)."""
    if not settings.GOOGLE_PLACES_API_KEY or not place_id:
        return {"telefon": None, "website": None}

    params = {
        "place_id": place_id,
        "fields": "formatted_phone_number,website",
        "key": settings.GOOGLE_PLACES_API_KEY,
    }
    try:
        resp = httpx.get(DETAILS_URL, params=params, timeout=10.0)
        if resp.status_code != 200:
            return {"telefon": None, "website": None}
        result = resp.json().get("result", {})
        return {
            "telefon": result.get("formatted_phone_number"),
            "website": result.get("website"),   # dokumandaki nota gore bu ALAN BOS gelebilir - normal
        }
    except httpx.HTTPError:
        return {"telefon": None, "website": None}
