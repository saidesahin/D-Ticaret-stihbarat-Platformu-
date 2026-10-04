"""
MODUL 0 - ALTYAPI
models.py: kullanici tablosu.

Dokumandaki karar: "Program tek serverdan kontrol edilmeli, son kullaniciya
biz kullanici adi/sifre veririz" -> yani kayit (signup) ekrani YOK,
kullanicilari admin panelinden BIZ olusturuyoruz.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    company_name = Column(String, nullable=True)   # musteri firma adi
    is_admin = Column(Boolean, default=False)       # biz mi, musteri mi
    is_active = Column(Boolean, default=True)        # admin kullaniciyi pasife alabilsin
    created_at = Column(DateTime(timezone=True), server_default=func.now())
