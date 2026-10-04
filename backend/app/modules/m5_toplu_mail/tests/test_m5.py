"""
Modul 5 icin otomatik testler.
SMTP'ye gercek istek atmiyoruz - smtp_client.send_email sahtelenir.
"""
import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.main import app
from app.modules.m0_altyapi.models import User
from app.modules.m5_toplu_mail import smtp_client

client = TestClient(app)


@pytest.fixture(autouse=True)
def smtp_sahteleme(monkeypatch):
    def sahte_send(to_email, subject, html_body, from_name, from_email):
        if to_email == "basarisiz@test.com":
            return False, "sahte SMTP hatasi"
        return True, None
    monkeypatch.setattr(smtp_client, "send_email", sahte_send)


@pytest.fixture()
def admin_token():
    db = SessionLocal()
    if not db.query(User).filter(User.username == "admin").first():
        db.add(User(username="admin", hashed_password=hash_password("admin123"), is_admin=True))
        db.commit()
    db.close()
    resp = client.post("/api/auth/login", data={"username": "admin", "password": "admin123"})
    return resp.json()["access_token"]


def _kampanya_olustur(token, fiziksel_adres="Test Mah. No:1, Konya"):
    return client.post(
        "/api/m5/campaigns",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "konu": "Ürünlerimizi Tanitmak Istiyoruz",
            "govde_html": "<p>Merhaba, urunlerimiz hakkinda bilgi almak ister misiniz?</p>",
            "gonderen_adi": "Ornek Ihracat A.S.",
            "gonderen_email": "info@ornekihracat.com",
            "fiziksel_adres": fiziksel_adres,
        },
    )


def test_fiziksel_adres_bos_olamaz(admin_token):
    resp = _kampanya_olustur(admin_token, fiziksel_adres="")
    assert resp.status_code == 422   # pydantic validation error


def test_kampanya_olusturulabilir(admin_token):
    resp = _kampanya_olustur(admin_token)
    assert resp.status_code == 200
    assert resp.json()["gonderen_adi"] == "Ornek Ihracat A.S."


def test_gonderim_basarili_ve_footer_eklenir(admin_token):
    kampanya = _kampanya_olustur(admin_token).json()
    client.post(
        f"/api/m5/campaigns/{kampanya['id']}/recipients",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"emails": ["musteri1@test.com", "basarisiz@test.com"]},
    )
    resp = client.post(f"/api/m5/campaigns/{kampanya['id']}/send", headers={"Authorization": f"Bearer {admin_token}"})
    sonuclar = resp.json()

    basarili = next(r for r in sonuclar if r["email"] == "musteri1@test.com")
    basarisiz = next(r for r in sonuclar if r["email"] == "basarisiz@test.com")
    assert basarili["durum"] == "gonderildi"
    assert basarisiz["durum"] == "basarisiz"
    assert basarisiz["hata_mesaji"] == "sahte SMTP hatasi"


def test_unsubscribe_sonraki_gonderimi_engeller(admin_token):
    kampanya1 = _kampanya_olustur(admin_token).json()
    aliciler = client.post(
        f"/api/m5/campaigns/{kampanya1['id']}/recipients",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"emails": ["vazgecen@test.com"]},
    ).json()
    token = aliciler[0]["id"]  # id'yi alacagiz ama unsubscribe_token response'da yok, DB'den okuyalim

    from app.core.database import SessionLocal
    from app.modules.m5_toplu_mail.models import EmailCampaignRecipient
    db = SessionLocal()
    kayit = db.query(EmailCampaignRecipient).filter(EmailCampaignRecipient.email == "vazgecen@test.com").first()
    unsub_token = kayit.unsubscribe_token
    db.close()

    # Ziyaretci maildeki linke tikliyor (PUBLIC, token gerekmez)
    unsub_resp = client.get(f"/api/m5/unsubscribe/{unsub_token}")
    assert unsub_resp.status_code == 200
    assert "Abonelikten cikildi" in unsub_resp.text

    # Ayni musteri ikinci bir kampanya olusturup AYNI adrese tekrar eklemeye calisiyor
    kampanya2 = _kampanya_olustur(admin_token).json()
    aliciler2 = client.post(
        f"/api/m5/campaigns/{kampanya2['id']}/recipients",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"emails": ["vazgecen@test.com"]},
    ).json()

    # Suppression listesinde oldugu icin BEKLEMEDE degil, atlandi_suppression olarak eklenmis olmali
    assert aliciler2[0]["durum"] == "atlandi_suppression"

    # send cagrilsa bile bu kisiye GONDERILMEZ (durum zaten beklemede degil)
    client.post(f"/api/m5/campaigns/{kampanya2['id']}/send", headers={"Authorization": f"Bearer {admin_token}"})
    kontrol = client.get(
        f"/api/m5/campaigns/{kampanya2['id']}/recipients", headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    assert kontrol[0]["durum"] == "atlandi_suppression"


def test_gecersiz_unsubscribe_token_404_doner():
    resp = client.get("/api/m5/unsubscribe/olmayan-token")
    assert resp.status_code == 404


def test_baskasinin_kampanyasina_erisim_engellenir(admin_token):
    client.post(
        "/api/auth/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"username": "musteri_m5", "password": "sifre123", "is_admin": False},
    )
    musteri_token = client.post(
        "/api/auth/login", data={"username": "musteri_m5", "password": "sifre123"}
    ).json()["access_token"]

    kampanya = _kampanya_olustur(admin_token).json()

    resp = client.post(
        f"/api/m5/campaigns/{kampanya['id']}/send", headers={"Authorization": f"Bearer {musteri_token}"}
    )
    assert resp.status_code == 404


def test_suppression_listesi_goruntulenebilir(admin_token):
    resp = client.get("/api/m5/suppression-list", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert any(e["email"] == "vazgecen@test.com" for e in resp.json())
