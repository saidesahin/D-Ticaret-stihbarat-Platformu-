"""
MODUL 3 - HARITALAR
models.py

Dokumandaki ornek BIREBIR:
"Ulke: Ingiltere, Aramak istedigim kelime: automotive, spare part ->
Excel listesi"

MapSearchProject: bir ulke + bir/birden fazla anahtar kelime (virgulle ayrilir)
MapSearchResult: her anahtar kelime icin haritada bulunan HER firma
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class MapSearchProject(Base):
    __tablename__ = "map_search_projects"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    hedef_ulke = Column(String, nullable=False)          # serbest metin, orn: "United Kingdom", "Germany"
    anahtar_kelimeler = Column(String, nullable=False)    # virgulle ayrilmis, orn: "automotive, spare parts"
    detay_getir = Column(Integer, default=1)              # 1: telefon/website icin ek sorgu da atilsin (daha yavas/pahali)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    results = relationship("MapSearchResult", back_populates="project")


class MapSearchResult(Base):
    __tablename__ = "map_search_results"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("map_search_projects.id"), nullable=False)

    anahtar_kelime = Column(String, nullable=False)   # bu firma hangi kelimeyle bulundu
    firma_adi = Column(String, nullable=False)
    adres = Column(String, nullable=True)
    telefon = Column(String, nullable=True)            # sadece detay_getir=1 ise dolu
    website = Column(String, nullable=True)             # sadece detay_getir=1 ise dolu (bos olabilir - dokumandaki "web sitesi olmayabilir" notu)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    google_place_id = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("MapSearchProject", back_populates="results")
