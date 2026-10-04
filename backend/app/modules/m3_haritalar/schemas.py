from datetime import datetime
from pydantic import BaseModel


class MapSearchProjectCreate(BaseModel):
    hedef_ulke: str                       # orn: "United Kingdom"
    anahtar_kelimeler: str                # orn: "automotive, spare parts"
    detay_getir: bool = True              # telefon/website icin ek sorgu atilsin mi


class MapSearchResultOut(BaseModel):
    id: int
    anahtar_kelime: str
    firma_adi: str
    adres: str | None
    telefon: str | None
    website: str | None
    lat: float | None
    lng: float | None

    class Config:
        from_attributes = True


class MapSearchProjectOut(BaseModel):
    id: int
    hedef_ulke: str
    anahtar_kelimeler: str
    created_at: datetime

    class Config:
        from_attributes = True
