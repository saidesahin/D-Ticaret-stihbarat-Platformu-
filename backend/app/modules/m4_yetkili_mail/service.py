from sqlalchemy.orm import Session

from app.modules.m4_yetkili_mail import email_crawler
from app.modules.m4_yetkili_mail.models import EmailLookup, EmailLookupResult
from app.modules.m4_yetkili_mail.schemas import EmailLookupCreate


def create_lookup(db: Session, owner_id: int, data: EmailLookupCreate) -> EmailLookup:
    lookup = EmailLookup(owner_id=owner_id, website_url=data.website_url)
    db.add(lookup)
    db.commit()
    db.refresh(lookup)
    return lookup


def run_lookup(db: Session, lookup: EmailLookup) -> list[EmailLookupResult]:
    bulunanlar = email_crawler.taramayi_calistir(lookup.website_url)

    yeni_sonuclar: list[EmailLookupResult] = []
    for b in bulunanlar:
        sonuc = EmailLookupResult(
            lookup_id=lookup.id,
            email=b["email"],
            kaynak_sayfa=b["kaynak_sayfa"],
            siniflandirma=b["siniflandirma"],
        )
        db.add(sonuc)
        yeni_sonuclar.append(sonuc)

    db.commit()
    return yeni_sonuclar


def get_owned_lookup(db: Session, lookup_id: int, owner_id: int) -> EmailLookup | None:
    return (
        db.query(EmailLookup)
        .filter(EmailLookup.id == lookup_id, EmailLookup.owner_id == owner_id)
        .first()
    )
