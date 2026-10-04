from datetime import datetime
from pydantic import BaseModel


class EmailLookupCreate(BaseModel):
    website_url: str   # orn: https://ornekfirma.com


class EmailLookupResultOut(BaseModel):
    id: int
    email: str
    kaynak_sayfa: str
    siniflandirma: str

    class Config:
        from_attributes = True


class EmailLookupOut(BaseModel):
    id: int
    website_url: str
    created_at: datetime

    class Config:
        from_attributes = True
