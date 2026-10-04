"""
Modul 1 icin otomatik testler.
Calistirmak icin (backend/ klasorunden): pytest app/modules/m1_ziyaretci_tespiti/tests -v

Not: Google/ipinfo gibi dis servislere gercek istek atmiyoruz (testler
internete bagimli olmamali, yavaslar ve kararsiz olur). Bunun yerine
service.py icindeki dis servis fonksiyonlarini monkeypatch ile sahteliyoruz.
DB kurulumu artik backend/conftest.py'de tek merkezden yapiliyor.
"""
import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.main import app
from app.modules.m0_altyapi.models import User
from app.modules.m1_ziyaretci_tespiti import ip_client, google_location_client

client = TestClient(app)


@pytest.fixture(autouse=True)
def disis_servisleri_sahteleme(monkeypatch):
    """Testler internete bagimli olmasin diye dis API cagrilarini sahteliyoruz."""
    monkeypatch.setattr(
        ip_client, "lookup_ip",
        lambda ip: {"country": "DE", "city": "Berlin", "org_guess": "AS1234 Ornek Musteri GmbH"},
    )
    monkeypatch.setattr(
        google_location_client, "reverse_geocode",
        lambda lat, lng: "Musterstrasse 1, 10115 Berlin",
    )
    monkeypatch.setattr(
        google_location_client, "find_nearby_companies",
        lambda lat, lng, radius_m=100: ["Ornek Ihracat GmbH", "Komsu Firma AG"],
    )


@pytest.fixture()
def admin_token():
    db = SessionLocal()
    if not db.query(User).filter(User.username == "admin").first():
        db.add(User(username="admin", hashed_password=hash_password("admin123"), is_admin=True))
        db.commit()
    db.close()
    resp = client.post("/api/auth/login", data={"username": "admin", "password": "admin123"})
    return resp.json()["access_token"]


def test_admin_site_olusturabilir(admin_token):
    resp = client.post(
        "/api/m1/sites",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"domain": "musterifirma.com"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["domain"] == "musterifirma.com"
    assert len(data["site_key"]) > 10


def test_gecersiz_site_key_ile_track_404_doner():
    resp = client.post("/api/m1/track", json={"site_key": "olmayan-key", "consent_given": False})
    assert resp.status_code == 404


def test_hayir_senaryosu_sadece_ip_ile_kaydedilir(admin_token):
    site_resp = client.post(
        "/api/m1/sites",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"domain": "hayirtest.com"},
    )
    site_key = site_resp.json()["site_key"]

    track_resp = client.post("/api/m1/track", json={
        "site_key": site_key,
        "page_url": "https://hayirtest.com/",
        "consent_given": False,
    })
    assert track_resp.status_code == 200

    visits = client.get("/api/m1/visits", headers={"Authorization": f"Bearer {admin_token}"}).json()
    kayit = next(v for v in visits if v["page_url"] == "https://hayirtest.com/")
    assert kayit["consent_given"] == 0
    assert kayit["country"] == "DE"
    assert kayit["org_guess"] == "AS1234 Ornek Musteri GmbH"
    assert kayit["address_guess"] is None          # Hayir dedigi icin konum verisi YOK
    assert kayit["nearby_company_guess"] is None


def test_evet_senaryosu_konum_ile_zenginlestirilir(admin_token):
    site_resp = client.post(
        "/api/m1/sites",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"domain": "evettest.com"},
    )
    site_key = site_resp.json()["site_key"]

    track_resp = client.post("/api/m1/track", json={
        "site_key": site_key,
        "page_url": "https://evettest.com/",
        "consent_given": True,
        "lat": 52.52,
        "lng": 13.405,
    })
    assert track_resp.status_code == 200

    visits = client.get("/api/m1/visits", headers={"Authorization": f"Bearer {admin_token}"}).json()
    kayit = next(v for v in visits if v["page_url"] == "https://evettest.com/")
    assert kayit["consent_given"] == 1
    assert kayit["address_guess"] == "Musterstrasse 1, 10115 Berlin"
    assert "Ornek Ihracat GmbH" in kayit["nearby_company_guess"]


def test_excel_export_calisir(admin_token):
    resp = client.get("/api/m1/visits/excel", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
