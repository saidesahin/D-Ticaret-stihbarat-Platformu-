"""
conftest.py - pytest, test dosyalarini import etmeden ONCE bu dosyayi okur.
Bu yuzden DATABASE_URL'i burada, herhangi bir modul import edilmeden
once ayarliyoruz - boylece app.core.config.Settings() tek ve dogru
degerle olusuyor (Modul 0 testlerinde yasadigimiz "iki farkli DB'ye
yaziliyor sanip aslinda ayni engine'i paylasma" sorununu onler).
"""
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_all.db"

import pytest

from app.core.database import Base, engine


@pytest.fixture(scope="session", autouse=True)
def tum_tablolari_bir_kere_kur():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("test_all.db"):
        os.remove("test_all.db")
