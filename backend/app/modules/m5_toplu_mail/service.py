"""
MODUL 5 - service.py

Gonderim akisi:
1) Alici eklenirken suppression listesinde mi diye kontrol edilir
2) send_campaign() SADECE durum="beklemede" olanlara gonderir
3) Her mailin govdesine OTOMATIK footer eklenir: fiziksel adres + zorunlu
   abonelikten cikma linki
4) Tek seferde en fazla MAX_GONDERIM_PER_RUN kadar gonderilir
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.m5_toplu_mail import smtp_client
from app.modules.m5_toplu_mail.models import EmailCampaign, EmailCampaignRecipient, SuppressionEntry
from app.modules.m5_toplu_mail.schemas import EmailCampaignCreate

MAX_GONDERIM_PER_RUN = 20


def create_campaign(db: Session, owner_id: int, data: EmailCampaignCreate) -> EmailCampaign:
    campaign = EmailCampaign(owner_id=owner_id, **data.model_dump())
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


def is_suppressed(db: Session, owner_id: int, email: str) -> bool:
    return (
        db.query(SuppressionEntry)
        .filter(SuppressionEntry.owner_id == owner_id, SuppressionEntry.email == email.lower())
        .first()
        is not None
    )


def add_recipients(db: Session, campaign: EmailCampaign, owner_id: int, emails: list[str]) -> list[EmailCampaignRecipient]:
    eklenenler: list[EmailCampaignRecipient] = []
    for email in emails:
        email = email.strip().lower()
        if not email:
            continue
        durum = "atlandi_suppression" if is_suppressed(db, owner_id, email) else "beklemede"
        alici = EmailCampaignRecipient(campaign_id=campaign.id, email=email, durum=durum)
        db.add(alici)
        eklenenler.append(alici)
    db.commit()
    return eklenenler


def _footer_ekle(html_govde: str, campaign: EmailCampaign, unsub_token: str) -> str:
    unsub_link = f"{settings.PUBLIC_BASE_URL}/api/m5/unsubscribe/{unsub_token}"
    footer = f"""
    <hr>
    <p style="font-size:12px;color:#888;">
      Bu e-posta {campaign.gonderen_adi} tarafindan gonderilmistir.<br>
      Adres: {campaign.fiziksel_adres}<br>
      Bu tur e-postalar almak istemiyorsaniz: <a href="{unsub_link}">abonelikten cik</a>
    </p>
    """
    return html_govde + footer


def send_campaign(db: Session, campaign: EmailCampaign) -> list[EmailCampaignRecipient]:
    bekleyenler = (
        db.query(EmailCampaignRecipient)
        .filter(EmailCampaignRecipient.campaign_id == campaign.id, EmailCampaignRecipient.durum == "beklemede")
        .limit(MAX_GONDERIM_PER_RUN)
        .all()
    )

    for alici in bekleyenler:
        govde = _footer_ekle(campaign.govde_html, campaign, alici.unsubscribe_token)
        basarili, hata = smtp_client.send_email(
            to_email=alici.email,
            subject=campaign.konu,
            html_body=govde,
            from_name=campaign.gonderen_adi,
            from_email=campaign.gonderen_email,
        )
        alici.durum = "gonderildi" if basarili else "basarisiz"
        alici.hata_mesaji = hata
        alici.gonderim_zamani = datetime.now(timezone.utc)

    db.commit()
    return bekleyenler


def unsubscribe(db: Session, token: str) -> bool:
    alici = db.query(EmailCampaignRecipient).filter(EmailCampaignRecipient.unsubscribe_token == token).first()
    if not alici:
        return False

    campaign = db.query(EmailCampaign).filter(EmailCampaign.id == alici.campaign_id).first()

    zaten_var = (
        db.query(SuppressionEntry)
        .filter(SuppressionEntry.owner_id == campaign.owner_id, SuppressionEntry.email == alici.email)
        .first()
    )
    if not zaten_var:
        db.add(SuppressionEntry(owner_id=campaign.owner_id, email=alici.email, eklenme_sebebi="kullanici_talebi"))

    diger_bekleyenler = (
        db.query(EmailCampaignRecipient)
        .join(EmailCampaign)
        .filter(
            EmailCampaign.owner_id == campaign.owner_id,
            EmailCampaignRecipient.email == alici.email,
            EmailCampaignRecipient.durum == "beklemede",
        )
        .all()
    )
    for d in diger_bekleyenler:
        d.durum = "atlandi_suppression"

    db.commit()
    return True


def get_owned_campaign(db: Session, campaign_id: int, owner_id: int) -> EmailCampaign | None:
    return (
        db.query(EmailCampaign)
        .filter(EmailCampaign.id == campaign_id, EmailCampaign.owner_id == owner_id)
        .first()
    )


def list_suppression(db: Session, owner_id: int) -> list[SuppressionEntry]:
    return db.query(SuppressionEntry).filter(SuppressionEntry.owner_id == owner_id).all()
