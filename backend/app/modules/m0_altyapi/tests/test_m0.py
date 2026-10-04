"""
Modul 0 icin otomatik testler.
Calistirmak icin (backend/ klasorunden): pytest app/modules/m0_altyapi/tests -v

DB kurulumu artik backend/conftest.py'de tek merkezden yapiliyor.
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_admin_directly():
    from app.core.database import SessionLocal
    from app.core.security import hash_password
    from app.modules.m0_altyapi.models import User

    db = SessionLocal()
    admin = User(username="admin", hashed_password=hash_password("admin123"), is_admin=True)
    db.add(admin)
    db.commit()
    db.close()


def test_login_basarili():
    _create_admin_directly()
    resp = client.post("/api/auth/login", data={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_yanlis_sifre():
    resp = client.post("/api/auth/login", data={"username": "admin", "password": "yanlis"})
    assert resp.status_code == 401


def test_token_olmadan_dashboard_erisimi_engellenir():
    resp = client.get("/api/dashboard")
    assert resp.status_code == 401


def test_admin_yeni_kullanici_olusturabilir():
    login = client.post("/api/auth/login", data={"username": "admin", "password": "admin123"})
    token = login.json()["access_token"]

    resp = client.post(
        "/api/auth/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "musteri1", "password": "musteri123", "company_name": "Test A.S."},
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "musteri1"


def test_admin_olmayan_kullanici_olusturamaz():
    login = client.post("/api/auth/login", data={"username": "musteri1", "password": "musteri123"})
    token = login.json()["access_token"]

    resp = client.post(
        "/api/auth/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "musteri2", "password": "x"},
    )
    assert resp.status_code == 403
