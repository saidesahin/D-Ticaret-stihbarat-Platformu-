from datetime import datetime
from pydantic import BaseModel


class SearchProjectCreate(BaseModel):
    """Dokumandaki formun BIREBIR karsiligi."""
    oem_no: str | None = None
    gtip_no: str | None = None

    parca_adi_tr: str | None = None
    parca_adi_en: str | None = None
    parca_adi_es: str | None = None
    parca_adi_ru: str | None = None
    parca_adi_ar: str | None = None
    parca_adi_fr: str | None = None
    parca_adi_de: str | None = None

    hedef_ulke_kodu: str        # zorunlu - orn "DE", "RU", "US" (SerpAPI 'gl' parametresi)
    hedef_uzanti: str | None = None
    rakip_isimleri: str | None = None


class SearchProjectOut(BaseModel):
    id: int
    oem_no: str | None
    gtip_no: str | None
    hedef_ulke_kodu: str
    created_at: datetime

    class Config:
        from_attributes = True


class SearchResultOut(BaseModel):
    id: int
    kullanilan_dil: str
    arama_sorgusu: str
    arama_motoru: str
    kaynak_tipi: str
    title: str | None
    url: str
    snippet: str | None

    class Config:
        from_attributes = True


class SearchProjectDetailOut(SearchProjectOut):
    results: list[SearchResultOut] = []


class GtipRelationCreate(BaseModel):
    gtip_no: str
    related_keyword_en: str
    aciklama: str | None = None


class GtipRelationOut(BaseModel):
    id: int
    gtip_no: str
    related_keyword_en: str
    aciklama: str | None

    class Config:
        from_attributes = True


class ProjectImageOut(BaseModel):
    id: int
    image_url: str

    class Config:
        from_attributes = True
