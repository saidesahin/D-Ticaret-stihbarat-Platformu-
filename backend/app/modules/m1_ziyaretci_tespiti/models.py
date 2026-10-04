"""
MODUL 1 - ZIYARETCI TESPITI
models.py

Site: musterinin izlenecek web sitesi (her musterinin 1+ sitesi olabilir)
Visit: o siteye gelen her ziyaretin kaydi
"""
import uuid

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


def generate_site_key() -> str:
    return uuid.uuid4().hex


class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    domain = Column(String, nullable=False)                 # ornek: musterifirma.com
    site_key = Column(String, unique=True, index=True, default=generate_site_key)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    visits = relationship("Visit", back_populates="site")


class Visit(Base):
    __tablename__ = "visits"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)

    ip_address = Column(String, nullable=False)
    page_url = Column(String, nullable=True)

    # IP intelligence sonuclari
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)
    org_guess = Column(String, nullable=True)   # ISP/sirket tahmini (ipinfo "org" alani)

    # Kullanici konum iznini KABUL ederse bu alanlar da dolar (daha kesin sonuc)
    consent_given = Column(Integer, default=0)  # 0/1 - kullanici izin verdi mi
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    address_guess = Column(String, nullable=True)       # reverse geocode sonucu acik adres
    nearby_company_guess = Column(String, nullable=True)  # o konumdaki olasi firmalar (JSON string, virgulle ayrilmis liste)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    site = relationship("Site", back_populates="visits")
