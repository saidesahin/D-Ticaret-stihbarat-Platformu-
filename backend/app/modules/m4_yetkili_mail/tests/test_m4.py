"""
Modul 4 icin otomatik testler.
Calistirmak icin (backend/ klasorunden): pytest app/modules/m4_yetkili_mail/tests -v

Gercek internete istek atmiyoruz - email_crawler.taramayi_calistir'i
dogrudan monkeypatch ile sahteliyoruz (Modul 1/2/3'teki ayni desen).
"""
import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.main import app
from app.modules.m0_altyapi.models import User
from app.modules.m4_yetkili_mail import email_crawler, service

client = TestClient(app)


def test_siniflandirma_genel_mailleri_dogru_ayirir():
    assert email_crawler.siniflandir("info@ornekfirma.com") == "genel"
    assert email_crawler.siniflandir("support@ornekfirma.com") == "genel"
    assert email_crawler.siniflandir("iletisim@ornekfirma.com") == "genel"


def test_siniflandirma_yetkili_ipucu_iceren_mailleri_dogru_ayirir():
    assert email_crawler.siniflandir("purchasing@ornekfirma.com") == "yetkili"
    assert email_crawler.siniflandir("export.manager@ornekfirma.com") == "yetkili"


def test_siniflandirma_sahis_ismini_yetkili_sayar():
    # dokumandaki not: "sahis ismi varsa genelde o firma yetkilisi oluyor"
    assert email_crawler.siniflandir("ahmet.yilmaz@ornekfirma.com") == "yetkili"
    assert email_crawler.siniflandir("jsmith@examplecorp.com") == "yetkili"


@pytest.fixture(autouse=True)
def crawler_sahteleme(monkeypatch):
    def sahte_tarama(website_url):
        return [
            {"email": "info@ornekfirma.com", "kaynak_sayfa": website_url, "siniflandirma": "genel"},
            {"email": "purchasing@ornekfirma.com", "kaynak_sayfa": f"{website_url}/iletisim", "siniflandirma": "yetkili"},
            {"email": "ahmet.yilmaz@ornekfirma.com", "kaynak_sayfa": f"{website_url}/hakkimizda", "siniflandirma": "yetkili"},
        ]
    monkeypatch.setattr(email_crawler, "taramayi_calistir", sahte_tarama)


@pytest.fixture()
def admin_token():
    db = SessionLocal()
    if not db.query(User).filter(User.username == "admin").first():
        db.add(User(username="admin", hashed_password=hash_password("admin123"), is_admin=True))
        db.commit()
    db.close()
    resp = client.post("/api/auth/login", data={"username": "admin", "password": "admin123"})
    return resp.json()["access_token"]


def test_tarama_olusturulabilir(admin_token):
    resp = client.post(
        "/api/m4/lookups",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"website_url": "https://ornekfirma.com"},
    )
    assert resp.status_code == 200
    assert resp.json()["website_url"] == "https://ornekfirma.com"


def test_tarama_calisir_ve_yetkili_mailler_once_gelir(admin_token):
    lookup_resp = client.post(
        "/api/m4/lookups",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"website_url": "https://ornekfirma.com"},
    )
    lookup_id = lookup_resp.json()["id"]

    run_resp = client.post(f"/api/m4/lookups/{lookup_id}/run", headers={"Authorization": f"Bearer {admin_token}"})
    assert run_resp.status_code == 200
    sonuclar = run_resp.json()

    assert len(sonuclar) == 3
    # ilk sonuclar yetkili olmali (genel en sona atilir)
    assert sonuclar[0]["siniflandirma"] == "yetkili"
    assert sonuclar[1]["siniflandirma"] == "yetkili"
    assert sonuclar[2]["siniflandirma"] == "genel"


def test_baskasinin_taramasina_erisim_engellenir(admin_token):
    client.post(
        "/api/auth/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"username": "musteri_m4", "password": "sifre123", "is_admin": False},
    )
    musteri_token = client.post(
        "/api/auth/login", data={"username": "musteri_m4", "password": "sifre123"}
    ).json()["access_token"]

    lookup_resp = client.post(
        "/api/m4/lookups",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"website_url": "https://gizlifirma.com"},
    )
    lookup_id = lookup_resp.json()["id"]

    resp = client.post(f"/api/m4/lookups/{lookup_id}/run", headers={"Authorization": f"Bearer {musteri_token}"})
    assert resp.status_code == 404

    resp2 = client.get(f"/api/m4/lookups/{lookup_id}/results", headers={"Authorization": f"Bearer {musteri_token}"})
    assert resp2.status_code == 404


def test_excel_export_calisir(admin_token):
    lookup_resp = client.post(
        "/api/m4/lookups",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"website_url": "https://ornekfirma.com"},
    )
    lookup_id = lookup_resp.json()["id"]
    client.post(f"/api/m4/lookups/{lookup_id}/run", headers={"Authorization": f"Bearer {admin_token}"})

    resp = client.get(f"/api/m4/lookups/{lookup_id}/results/excel", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
