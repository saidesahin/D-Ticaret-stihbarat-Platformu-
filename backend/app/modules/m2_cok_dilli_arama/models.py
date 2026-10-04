"""
MODUL 2 - COK DILLI ARAMA MOTORU
models.py

SearchProject: dokumandaki formun BIREBIR karsiligi - kullanici bir kere
doldurur (OEM no, GTIP, 7 dilde parca adi, hedef ulke), bu bir "proje" olur.

SearchResult: o proje icin taranan HER arama motoru + HER dil kombinasyonundan
gelen web sitesi sonuclari. Bir projede onlarca sonuc satiri olabilir.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SearchProject(Base):
    __tablename__ = "search_projects"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    oem_no = Column(String, nullable=True)
    gtip_no = Column(String, nullable=True)

    # Dokumandaki tabloyla BIREBIR ayni 7 dil
    parca_adi_tr = Column(String, nullable=True)
    parca_adi_en = Column(String, nullable=True)
    parca_adi_es = Column(String, nullable=True)
    parca_adi_ru = Column(String, nullable=True)
    parca_adi_ar = Column(String, nullable=True)
    parca_adi_fr = Column(String, nullable=True)
    parca_adi_de = Column(String, nullable=True)

    # "Aranacak olan ulke uzantisi" - orn: com, ru, de (nokta olmadan saklanir)
    hedef_ulke_kodu = Column(String, nullable=False)   # ISO ulke kodu, orn: "RU", "DE" (gl parametresi icin)
    hedef_uzanti = Column(String, nullable=True)        # orn: "ru", "com.tr" (bilgi amacli, filtreleme icin kullanilabilir)

    rakip_isimleri = Column(String, nullable=True)      # virgulle ayrilmis, Modul 2b'de kullanilacak

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    results = relationship("SearchResult", back_populates="project")


class SearchResult(Base):
    __tablename__ = "search_results"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("search_projects.id"), nullable=False)

    kullanilan_dil = Column(String, nullable=False)     # hangi dildeki parca adiyla bulundu (tr/en/es/ru/ar/fr/de)
    arama_sorgusu = Column(String, nullable=False)       # gercekte gonderilen sorgu metni
    arama_motoru = Column(String, nullable=False)        # google / bing / yandex / google_lens

    # kaynak_tipi: bu sonuc HANGI arama turunden geldi - dokumandaki 3 farkli
    # arama bicimini (ana dil aramasi / yan GTIP / rakip / gorsel) ayirt etmek icin
    kaynak_tipi = Column(String, nullable=False, default="dil_aramasi")

    title = Column(String, nullable=True)
    url = Column(String, nullable=False)
    snippet = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("SearchProject", back_populates="results")


class GtipRelation(Base):
    """
    Yan/tamamlayici GTIP eslestirme tablosu.
    Dokumandaki ornek: "otomobil satan, oto yedek parcasi da satar mi?"
    Bu tabloyu ADMIN doldurur (tam otomatik/yapay zeka ile GTIP siniflandirma
    ayri, cok daha buyuk bir is - ilk surumde manuel/kural tabanli baslıyoruz,
    ileride genisletilebilir).
    """
    __tablename__ = "gtip_relations"

    id = Column(Integer, primary_key=True, index=True)
    gtip_no = Column(String, nullable=False, index=True)
    related_keyword_en = Column(String, nullable=False)   # aramaya eklenecek Ingilizce anahtar kelime
    aciklama = Column(String, nullable=True)               # orn: "Otomotiv yedek parcasi -> hirdavat pazari"


class ProjectImage(Base):
    """Kullanicinin yukledigi urun resimleri - gorselle arama icin kullanilir."""
    __tablename__ = "project_images"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("search_projects.id"), nullable=False)
    image_url = Column(String, nullable=False)   # public erisilebilir URL (reverse image search icin sart)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
