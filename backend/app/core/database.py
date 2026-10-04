"""
ORTAK ALTYAPI - database.py
Tum moduller ayni veritabani baglantisini buradan alir.
Her modul kendi models.py dosyasinda Base'i import eder,
kendi tablosunu tanimlar. Baska modulun tablosuna dokunmaz.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Her API cagrisinda FastAPI'nin Depends() ile kullanacagi DB oturumu."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
