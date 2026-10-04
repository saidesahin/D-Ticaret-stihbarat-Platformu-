"""
MODUL 1 - ip_client.py

Ziyaretci "Hayir" derse elimizde SADECE IP adresi kalir.
ipinfo.io ücretsiz katmani (token'siz de calisir, ama rate-limit dusuk;
production'da .env'ye IPINFO_TOKEN eklenmeli) IP'den:
- country (ulke)
- city (sehir)
- org (o IP bloguna kayitli ISS/sirket adi - "AS12345 Firma Ltd" formatinda gelir)
dondurur.

Not: Kurumsal/ofis internetlerinde "org" alani cogu zaman gercekten
sirketin adini verir (ornek: "AS15169 Google LLC"). Ev/mobil internetlerde
ise sadece ISS adini verir (ornek: "Turk Telekom"), sirket adini VERMEZ -
bu durumda elimizde sadece ulke/sehir kalir. Bunu musteriye anlatmak
onemli, "her ziyaretcinin sirketini %100 buluruz" beklentisi yanlis olur.
"""
import httpx

from app.core.config import settings


def lookup_ip(ip_address: str) -> dict:
    """
    Basarisiz olursa (rate limit, agsiz ortam, gecersiz IP) bos degerlerle doner -
    servisin ayakta kalmasi, tek bir ziyaretin kaydini engellememesi onemli.
    """
    result = {"country": None, "city": None, "org_guess": None}

    # Localhost/dahili test IP'lerinde dis servise sormanin anlami yok
    if ip_address in ("127.0.0.1", "testclient", "localhost") or ip_address.startswith("192.168.") or ip_address.startswith("10."):
        return result

    url = f"https://ipinfo.io/{ip_address}/json"
    params = {}
    if settings.IPINFO_TOKEN:
        params["token"] = settings.IPINFO_TOKEN

    try:
        resp = httpx.get(url, params=params, timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            result["country"] = data.get("country")
            result["city"] = data.get("city")
            result["org_guess"] = data.get("org")
    except httpx.HTTPError:
        pass

    return result
