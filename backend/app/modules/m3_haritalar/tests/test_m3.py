"""
Modul 3 icin otomatik testler.
Calistirmak icin (backend/ klasorunden): pytest app/modules/m3_haritalar/tests -v

Google Places'e gercek istek atmiyoruz (Modul 1/2'deki sahteleme deseninin ayni).
"""
import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.main import app
from app.modules.m0_altyapi.models import User
from app.modules.m3_haritalar import places_text_client

client = TestClient(app)


@pytest.fixture(autouse=True)
def places_sahteleme(monkeypatch):
    def sahte_text_search(query, max_sayfa=3):
        # "automotive in United Kingdom" -> 2 sahte firma
        return [
            {"firma_adi": f"Ornek Firma A ({query})", "adres": "1 Test Street, London", "lat": 51.5, "lng": -0.1, "google_place_id": "place_1"},
            {"firma_adi": f"Ornek Firma B ({query})", "adres": "2 Test Road, Manchester", "lat": 53.4, "lng": -2.2, "google_place_id": "place_2"},
        ]

    def sahte_place_details(place_id):
        if place_id == "place_1":
            return {"telefon": "+44 20 1234 5678", "website": "https://ornekfirmaa.co.uk"}
        # place_2 icin dokumandaki notu simule ediyoruz: web sitesi YOK ama telefon var
        return {"telefon": "+44 161 987 6543", "website": None}

    monkeypatch.setattr(places_text_client, "text_search", sahte_text_search)
    monkeypatch.setattr(places_text_client, "place_details", sahte_place_details)


@pytest.fixture()
def admin_token():
    db = SessionLocal()
    if not db.query(User).filter(User.username == "admin").first():
        db.add(User(username="admin", hashed_password=hash_password("admin123"), is_admin=True))
        db.commit()
    db.close()
    resp = client.post("/api/auth/login", data={"username": "admin", "password": "admin123"})
    return resp.json()["access_token"]


def test_proje_olusturulabilir(admin_token):
    resp = client.post(
        "/api/m3/projects",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"hedef_ulke": "United Kingdom", "anahtar_kelimeler": "automotive, spare parts"},
    )
    assert resp.status_code == 200
    assert resp.json()["hedef_ulke"] == "United Kingdom"


def test_iki_kelime_ile_arama_calisir_ve_detaylari_getirir(admin_token):
    proje_resp = client.post(
        "/api/m3/projects",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"hedef_ulke": "United Kingdom", "anahtar_kelimeler": "automotive, spare parts"},
    )
    project_id = proje_resp.json()["id"]

    run_resp = client.post(f"/api/m3/projects/{project_id}/run", headers={"Authorization": f"Bearer {admin_token}"})
    assert run_resp.status_code == 200
    sonuclar = run_resp.json()

    # 2 kelime x 2 sahte firma = 4 sonuc
    assert len(sonuclar) == 4
    kelimeler = {s["anahtar_kelime"] for s in sonuclar}
    assert kelimeler == {"automotive", "spare parts"}

    # place_1 -> website dolu, place_2 -> website BOS (dokumandaki "web sitesi olmayabilir" notu)
    website_bos_olanlar = [s for s in sonuclar if s["website"] is None]
    assert len(website_bos_olanlar) > 0
    assert all(s["telefon"] is not None for s in sonuclar)  # hepsinde telefon var


def test_detay_getir_false_ise_telefon_website_bos_kalir(admin_token):
    proje_resp = client.post(
        "/api/m3/projects",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"hedef_ulke": "Germany", "anahtar_kelimeler": "engine parts", "detay_getir": False},
    )
    project_id = proje_resp.json()["id"]

    run_resp = client.post(f"/api/m3/projects/{project_id}/run", headers={"Authorization": f"Bearer {admin_token}"})
    sonuclar = run_resp.json()

    assert len(sonuclar) == 2
    assert all(s["telefon"] is None and s["website"] is None for s in sonuclar)


def test_baskasinin_projesine_erisim_engellenir(admin_token):
    client.post(
        "/api/auth/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"username": "musteri_m3", "password": "sifre123", "is_admin": False},
    )
    musteri_token = client.post(
        "/api/auth/login", data={"username": "musteri_m3", "password": "sifre123"}
    ).json()["access_token"]

    proje_resp = client.post(
        "/api/m3/projects",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"hedef_ulke": "France", "anahtar_kelimeler": "gizli"},
    )
    project_id = proje_resp.json()["id"]

    resp = client.post(f"/api/m3/projects/{project_id}/run", headers={"Authorization": f"Bearer {musteri_token}"})
    assert resp.status_code == 404

    resp2 = client.get(f"/api/m3/projects/{project_id}/results", headers={"Authorization": f"Bearer {musteri_token}"})
    assert resp2.status_code == 404


def test_excel_export_calisir(admin_token):
    proje_resp = client.post(
        "/api/m3/projects",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"hedef_ulke": "United Kingdom", "anahtar_kelimeler": "automotive"},
    )
    project_id = proje_resp.json()["id"]
    client.post(f"/api/m3/projects/{project_id}/run", headers={"Authorization": f"Bearer {admin_token}"})

    resp = client.get(f"/api/m3/projects/{project_id}/results/excel", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
