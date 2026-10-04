from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator


class EmailCampaignCreate(BaseModel):
    konu: str
    govde_html: str
    gonderen_adi: str
    gonderen_email: EmailStr
    fiziksel_adres: str

    @field_validator("fiziksel_adres")
    @classmethod
    def adres_bos_olamaz(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Fiziksel adres zorunludur (yasal gereklilik)")
        return v


class EmailCampaignOut(BaseModel):
    id: int
    konu: str
    gonderen_adi: str
    gonderen_email: str
    created_at: datetime

    class Config:
        from_attributes = True


class AddRecipientsRequest(BaseModel):
    emails: list[str]


class RecipientOut(BaseModel):
    id: int
    email: str
    durum: str
    hata_mesaji: str | None
    gonderim_zamani: datetime | None

    class Config:
        from_attributes = True


class SuppressionEntryOut(BaseModel):
    id: int
    email: str
    eklenme_sebebi: str | None
    created_at: datetime

    class Config:
        from_attributes = True
