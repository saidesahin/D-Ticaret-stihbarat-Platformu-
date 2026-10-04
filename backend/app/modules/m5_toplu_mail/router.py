"""
MODUL 5 - router.py

1) POST /api/m5/campaigns                    -> kampanya olustur (gonderen+adres ZORUNLU)
2) POST /api/m5/campaigns/{id}/recipients     -> alici listesi ekle (suppression kontrolu otomatik)
3) POST /api/m5/campaigns/{id}/send           -> gonderimi baslat (max 20/calistirma)
4) GET  /api/m5/campaigns/{id}/recipients     -> gonderim durumlarini gor
5) GET  /api/m5/unsubscribe/{token}           -> PUBLIC - abonelikten cikma linki
6) GET  /api/m5/suppression-list              -> vazgecme listesini gor
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.m0_altyapi.models import User
from app.modules.m5_toplu_mail import service
from app.modules.m5_toplu_mail.schemas import (
    EmailCampaignCreate, EmailCampaignOut, AddRecipientsRequest, RecipientOut, SuppressionEntryOut,
)

router = APIRouter(tags=["Modul 5 - Toplu Mail (dikkatli kullanin)"])


@router.post("/api/m5/campaigns", response_model=EmailCampaignOut)
def create_campaign(
    data: EmailCampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.create_campaign(db, current_user.id, data)


@router.post("/api/m5/campaigns/{campaign_id}/recipients", response_model=list[RecipientOut])
def add_recipients(
    campaign_id: int,
    data: AddRecipientsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = service.get_owned_campaign(db, campaign_id, current_user.id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Kampanya bulunamadi")
    return service.add_recipients(db, campaign, current_user.id, data.emails)


@router.post("/api/m5/campaigns/{campaign_id}/send", response_model=list[RecipientOut])
def send_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = service.get_owned_campaign(db, campaign_id, current_user.id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Kampanya bulunamadi")
    return service.send_campaign(db, campaign)


@router.get("/api/m5/campaigns/{campaign_id}/recipients", response_model=list[RecipientOut])
def list_recipients(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = service.get_owned_campaign(db, campaign_id, current_user.id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Kampanya bulunamadi")
    return campaign.alicilar


@router.get("/api/m5/unsubscribe/{token}", response_class=HTMLResponse)
def unsubscribe(token: str, db: Session = Depends(get_db)):
    basarili = service.unsubscribe(db, token)
    if basarili:
        return "<html><body style='font-family:sans-serif;text-align:center;padding:4rem;'>" \
               "<h2>Abonelikten cikildi.</h2><p>Bu adrese bir daha e-posta gonderilmeyecek.</p></body></html>"
    return HTMLResponse(
        "<html><body style='font-family:sans-serif;text-align:center;padding:4rem;'>"
        "<h2>Gecersiz veya suresi dolmus link.</h2></body></html>",
        status_code=404,
    )


@router.get("/api/m5/suppression-list", response_model=list[SuppressionEntryOut])
def get_suppression_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_suppression(db, current_user.id)
