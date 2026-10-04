"""
Modul 2 icin otomatik testler.
Calistirmak icin (backend/ klasorunden): pytest app/modules/m2_cok_dilli_arama/tests -v

SerpAPI'ye gercek istek atmiyoruz (Modul 1'deki ipinfo/google_places
sahteleme mantiginin ayni sekilde uygulanmasi).
"""
import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.main import app
from app.modules.m0_altyapi.models import User
from app.modules.m2_cok_dilli_arama import serp_client

client = TestClient(app)


@pytest.fixture(autouse=True)
def serpapi_sahteleme(monkeypatch):
    def sahte_search(query, engine, country_code, lang_code, num=10):
        return [
            {
                "title": f"{query} - {engine} sonucu",
                "url": f"https://ornek-{engine}-{lang_code}-{abs(hash(query))}.com",
                "snippet": f"{query} icin bulunan ornek sonuc ({engine}/{lang_code})",
            }
        ]

    def sahte_reverse_image(image_url, country_code):
        return [
            {"title": "Benzer urun bulundu", "url": "https://gorsel-eslesme-ornek.com", "snippet": "gorsel eslesme"},
        ]

    monkeypatch.setattr(serp_client, "search", sahte_search)
    monkeypatch.setattr(serp_client, "reverse_image_search", sahte_reverse_image)


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
        "/api/m2/projects",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "oem_no": "OEM-123",
            "gtip_no": "8708.30",
            "parca_adi_tr": "fren balatasi",
            "parca_adi_en": "brake pad",
            "hedef_ulke_kodu": "DE",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["oem_no"] == "OEM-123"


def test_sadece_doldurulan_diller_aranir(admin_token):
    # 7 dilden sadece TR ve EN dolu - digerleri (es/ru/ar/fr/de) BOS birakildi
    proje_resp = client.post(
        "/api/m2/projects",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "oem_no": "OEM-999",
            "parca_adi_tr": "vida",
            "parca_adi_en": "screw",
            "hedef_ulke_kodu": "US",
        },
    )
    project_id = proje_resp.json()["id"]

    run_resp = client.post(
        f"/api/m2/projects/{project_id}/run",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert run_resp.status_code == 200
    sonuclar = run_resp.json()

    # 2 dil (tr, en) x 3 arama motoru (google, bing, yandex) x 1 sahte sonuc = 6 satir
    assert len(sonuclar) == 6
    kullanilan_diller = {s["kullanilan_dil"] for s in sonuclar}
    assert kullanilan_diller == {"tr", "en"}  # es/ru/ar/fr/de aranmadi


def test_baskasinin_projesine_erisim_engellenir(admin_token):
    # ikinci bir musteri kullanicisi olustur
    client.post(
        "/api/auth/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"username": "musteri_m2", "password": "sifre123", "is_admin": False},
    )
    musteri_token = client.post(
        "/api/auth/login", data={"username": "musteri_m2", "password": "sifre123"}
    ).json()["access_token"]

    proje_resp = client.post(
        "/api/m2/projects",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"parca_adi_en": "gizli parca", "hedef_ulke_kodu": "FR"},
    )
    project_id = proje_resp.json()["id"]

    # musteri_m2, admin'in projesini calistirmaya calisiyor -> 404 (varligini bile gizliyoruz)
    resp = client.post(
        f"/api/m2/projects/{project_id}/run",
        headers={"Authorization": f"Bearer {musteri_token}"},
    )
    assert resp.status_code == 404

    # ayni sekilde sonuclari listeleme de 404 vermeli (tutarlilik)
    resp2 = client.get(
        f"/api/m2/projects/{project_id}/results",
        headers={"Authorization": f"Bearer {musteri_token}"},
    )
    assert resp2.status_code == 404


def test_excel_export_calisir(admin_token):
    proje_resp = client.post(
        "/api/m2/projects",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"parca_adi_de": "Schraube", "hedef_ulke_kodu": "DE"},
    )
    project_id = proje_resp.json()["id"]
    client.post(f"/api/m2/projects/{project_id}/run", headers={"Authorization": f"Bearer {admin_token}"})

    resp = client.get(
        f"/api/m2/projects/{project_id}/results/excel",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def test_yan_gtip_araması_calisir(admin_token):
    # Admin once bir GTIP iliskisi tanimliyor: "8708.30" (fren) -> "hardware store" (hirdavat)
    client.post(
        "/api/m2/gtip-relations",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"gtip_no": "8708.30", "related_keyword_en": "hardware store", "aciklama": "test iliskisi"},
    )

    proje_resp = client.post(
        "/api/m2/projects",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"gtip_no": "8708.30", "parca_adi_en": "brake pad", "hedef_ulke_kodu": "DE"},
    )
    project_id = proje_resp.json()["id"]

    run_resp = client.post(f"/api/m2/projects/{project_id}/run", headers={"Authorization": f"Bearer {admin_token}"})
    sonuclar = run_resp.json()

    yan_gtip_sonuclari = [s for s in sonuclar if s["kaynak_tipi"] == "yan_gtip"]
    assert len(yan_gtip_sonuclari) == 3  # 3 arama motoru
    assert "hardware store" in yan_gtip_sonuclari[0]["arama_sorgusu"]


def test_rakip_aramasi_calisir(admin_token):
    proje_resp = client.post(
        "/api/m2/projects",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "parca_adi_en": "brake pad",
            "hedef_ulke_kodu": "DE",
            "rakip_isimleri": "Bosch, Ferodo",
        },
    )
    project_id = proje_resp.json()["id"]

    run_resp = client.post(f"/api/m2/projects/{project_id}/run", headers={"Authorization": f"Bearer {admin_token}"})
    sonuclar = run_resp.json()

    rakip_sonuclari = [s for s in sonuclar if s["kaynak_tipi"] == "rakip"]
    # 2 rakip (Bosch, Ferodo) x 3 arama motoru = 6
    assert len(rakip_sonuclari) == 6
    aranan_sorgular = {s["arama_sorgusu"] for s in rakip_sonuclari}
    assert aranan_sorgular == {"Bosch", "Ferodo"}


def test_gorsel_yukleme_ve_arama_calisir(admin_token):
    proje_resp = client.post(
        "/api/m2/projects",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"parca_adi_en": "brake pad", "hedef_ulke_kodu": "DE"},
    )
    project_id = proje_resp.json()["id"]

    # sahte kucuk bir resim dosyasi yukle
    dosya = ("urun.jpg", b"sahte-resim-icerigi", "image/jpeg")
    upload_resp = client.post(
        f"/api/m2/projects/{project_id}/images",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": dosya},
    )
    assert upload_resp.status_code == 200
    assert upload_resp.json()["image_url"].startswith("http")

    arama_resp = client.post(
        f"/api/m2/projects/{project_id}/run-image-search",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert arama_resp.status_code == 200
    sonuclar = arama_resp.json()
    assert len(sonuclar) == 1
    assert sonuclar[0]["kaynak_tipi"] == "gorsel_arama"


def test_admin_olmayan_gtip_iliskisi_ekleyemez(admin_token):
    musteri_token = client.post(
        "/api/auth/login", data={"username": "musteri_m2", "password": "sifre123"}
    ).json()["access_token"]

    resp = client.post(
        "/api/m2/gtip-relations",
        headers={"Authorization": f"Bearer {musteri_token}"},
        json={"gtip_no": "1234", "related_keyword_en": "test"},
    )
    assert resp.status_code == 403
