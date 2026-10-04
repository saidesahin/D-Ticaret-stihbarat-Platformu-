"""
MODUL 1 - google_location_client.py

Ziyaretci "Evet" derse tarayicidan lat/lng aliriz (dogru konum, IP'den cok
daha kesin). Dokumandaki notta gecen "konum bilgisinden firma ismini bulan
Google servisi" icin gercekte 2 farkli Google servisi birlikte kullanilir:

1) Geocoding API  -> lat/lng'den acik ADRES cikarir (sokak, bina no)
2) Places API (Nearby Search) -> o koordinata yakin (~100m) KAYITLI
   isletmelerin listesini verir

ONEMLI - musteriye dogru beklenti vermek icin:
Google'da "bu GPS koordinatinda calisan tek bir firma" diye sihirli bir
servis YOK. Places Nearby Search o bolgedeki Google Maps'e kayitli
isletmeleri LISTELER (bir bina icinde 5 farkli firma varsa 5'i de gelebilir).
Bu yuzden "kesin sonuc" degil "olasi firmalar listesi" olarak sunuyoruz -
tek katli mustakil bir fabrika/depo binasinda isabet orani yuksek,
plaza/is merkezi gibi cok kiracili binalarda dusuk olur.

API anahtari icin: Google Cloud Console -> Geocoding API + Places API
etkinlestirilmeli, .env'ye GOOGLE_PLACES_API_KEY olarak yazilmali.
"""
import httpx

from app.core.config import settings

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"


def reverse_geocode(lat: float, lng: float) -> str | None:
    if not settings.GOOGLE_PLACES_API_KEY:
        return None
    try:
        resp = httpx.get(
            GEOCODE_URL,
            params={"latlng": f"{lat},{lng}", "key": settings.GOOGLE_PLACES_API_KEY, "language": "tr"},
            timeout=5.0,
        )
        data = resp.json()
        results = data.get("results") or []
        if results:
            return results[0].get("formatted_address")
    except httpx.HTTPError:
        pass
    return None


def find_nearby_companies(lat: float, lng: float, radius_m: int = 100) -> list[str]:
    """Ham koordinata en yakin, Google Maps'e isletme olarak kayitli yerleri dondurur."""
    if not settings.GOOGLE_PLACES_API_KEY:
        return []
    try:
        resp = httpx.get(
            NEARBY_URL,
            params={
                "location": f"{lat},{lng}",
                "radius": radius_m,
                "key": settings.GOOGLE_PLACES_API_KEY,
            },
            timeout=5.0,
        )
        data = resp.json()
        results = data.get("results") or []
        # en yakin 5 isletme adi yeterli - liste cok uzarsa anlamini kaybeder
        return [r.get("name") for r in results[:5] if r.get("name")]
    except httpx.HTTPError:
        return []
