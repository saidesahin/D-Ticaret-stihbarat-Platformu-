"""
MODUL 1 - router.py

3 grup endpoint:
1) /api/m1/sites        -> ADMIN'in musteri icin site (site_key) olusturmasi
2) /api/m1/track        -> PUBLIC (login gerektirmez) - JS snippet buraya yazar
3) /api/m1/visits       -> Musterinin (login'li) kendi sitesindeki ziyaretleri gormesi
4) /api/m1/visits/excel -> Ayni listenin Excel export'u
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.excel_export import rows_to_excel_response
from app.modules.m0_altyapi.models import User
from app.modules.m1_ziyaretci_tespiti import service
from app.modules.m1_ziyaretci_tespiti.schemas import SiteCreate, SiteOut, TrackPayload, VisitOut

router = APIRouter(tags=["Modul 1 - Ziyaretci Tespiti"])


def _get_client_ip(request: Request) -> str:
    """
    Reverse proxy arkasindaysa (nginx, Cloudflare vb.) gercek IP
    X-Forwarded-For header'inda gelir. Yoksa dogrudan baglanti IP'si kullanilir.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"


@router.post("/api/m1/sites", response_model=SiteOut)
def create_site(
    data: SiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Admin, musteri adina bir site kaydi acar ve site_key uretilir.
    Bu site_key musteriye verilir, o da tracker.js icine yapistirir.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Bu islem icin admin yetkisi gerekli")
    return service.create_site(db, owner_id=current_user.id, domain=data.domain)


@router.post("/api/m1/track")
def track_visit(payload: TrackPayload, request: Request, db: Session = Depends(get_db)):
    """
    PUBLIC endpoint - ziyaretcinin tarayicisi buraya istek atar, login GEREKMEZ.
    Guvenlik site_key uzerinden saglanir (yanlis/bilinmeyen key -> 404).
    """
    site = service.get_site_by_key(db, payload.site_key)
    if not site:
        raise HTTPException(status_code=404, detail="Gecersiz site_key")

    client_ip = _get_client_ip(request)
    service.record_visit(db, site, payload, client_ip)
    return {"status": "kaydedildi"}


@router.get("/api/m1/visits", response_model=list[VisitOut])
def list_visits(
    site_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Musteri SADECE kendi sitelerinin ziyaretlerini gorur (owner_id filtresi)."""
    return service.list_visits_for_owner(db, current_user.id, site_id)


@router.get("/api/m1/visits/excel")
def export_visits_excel(
    site_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    visits = service.list_visits_for_owner(db, current_user.id, site_id)
    rows = [
        {
            "Tarih": v.created_at.strftime("%Y-%m-%d %H:%M"),
            "IP Adresi": v.ip_address,
            "Ulke": v.country or "-",
            "Sehir": v.city or "-",
            "Sirket/ISS Tahmini (IP)": v.org_guess or "-",
            "Izin Verildi mi": "Evet" if v.consent_given else "Hayir",
            "Adres (Konum)": v.address_guess or "-",
            "Yakindaki Olasi Firmalar": v.nearby_company_guess or "-",
            "Sayfa": v.page_url or "-",
        }
        for v in visits
    ]
    return rows_to_excel_response(rows, sheet_name="Ziyaretciler", filename="ziyaretci_raporu")
