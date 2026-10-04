from datetime import datetime
from pydantic import BaseModel


class SiteCreate(BaseModel):
    domain: str


class SiteOut(BaseModel):
    id: int
    domain: str
    site_key: str

    class Config:
        from_attributes = True


class TrackPayload(BaseModel):
    """JS snippet'inin gonderdigi veri."""
    site_key: str
    page_url: str | None = None
    consent_given: bool = False
    lat: float | None = None    # sadece consent_given=True ise dolu gelir
    lng: float | None = None


class VisitOut(BaseModel):
    id: int
    ip_address: str
    page_url: str | None
    country: str | None
    city: str | None
    org_guess: str | None
    consent_given: int
    address_guess: str | None
    nearby_company_guess: str | None
    created_at: datetime

    class Config:
        from_attributes = True
