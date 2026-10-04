"""
MODUL 4 - YETKILI MAIL BULMA
models.py

Dokumandaki istek: "Firmalarin web sitesindeki info@ yerine yetkilinin
(purchasing@, manager@, sahis ismi vb.) mail adresini bulma."

EmailLookup: taranacak tek bir web sitesi
EmailLookupResult: o sitede bulunan HER e-posta adresi + hangi sayfada
bulundugu + "genel" mi "yetkili" mi oldugu siniflandirmasi
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class EmailLookup(Base):
    __tablename__ = "email_lookups"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    website_url = Column(String, nullable=False)   # orn: https://ornekfirma.com

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    results = relationship("EmailLookupResult", back_populates="lookup")


class EmailLookupResult(Base):
    __tablename__ = "email_lookup_results"

    id = Column(Integer, primary_key=True, index=True)
    lookup_id = Column(Integer, ForeignKey("email_lookups.id"), nullable=False)

    email = Column(String, nullable=False)
    kaynak_sayfa = Column(String, nullable=False)   # bu mail hangi sayfada bulundu
    siniflandirma = Column(String, nullable=False, default="genel")  # "genel" veya "yetkili"

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lookup = relationship("EmailLookup", back_populates="results")
