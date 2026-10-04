"""
MODUL 4 - router.py

1) POST /api/m4/lookups            -> web sitesi URL'i ile tarama olustur
2) POST /api/m4/lookups/{id}/run   -> taramayi calistir
3) GET  /api/m4/lookups/{id}/results        -> JSON sonuclar (yetkili mailler once)
4) GET  /api/m4/lookups/{id}/results/excel  -> Excel export
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.excel_export import rows_to_excel_response
from app.modules.m0_altyapi.models import User
from app.modules.m4_yetkili_mail import service
from app.modules.m4_yetkili_mail.schemas import EmailLookupCreate, EmailLookupOut, EmailLookupResultOut

router = APIRouter(tags=["Modul 4 - Yetkili Mail Bulma"])


def _yetkili_once_sirala(sonuclar):
    # dokumandaki asil amac "yetkiliye ulasmak" oldugu icin yetkili mailler ustte gorunsun
    return sorted(sonuclar, key=lambda r: 0 if r.siniflandirma == "yetkili" else 1)


@router.post("/api/m4/lookups", response_model=EmailLookupOut)
def create_lookup(
    data: EmailLookupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.create_lookup(db, current_user.id, data)


@router.post("/api/m4/lookups/{lookup_id}/run", response_model=list[EmailLookupResultOut])
def run_lookup(
    lookup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lookup = service.get_owned_lookup(db, lookup_id, current_user.id)
    if not lookup:
        raise HTTPException(status_code=404, detail="Tarama bulunamadi")

    sonuclar = service.run_lookup(db, lookup)
    return _yetkili_once_sirala(sonuclar)


@router.get("/api/m4/lookups/{lookup_id}/results", response_model=list[EmailLookupResultOut])
def get_results(
    lookup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lookup = service.get_owned_lookup(db, lookup_id, current_user.id)
    if not lookup:
        raise HTTPException(status_code=404, detail="Tarama bulunamadi")
    return _yetkili_once_sirala(lookup.results)


@router.get("/api/m4/lookups/{lookup_id}/results/excel")
def export_results_excel(
    lookup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lookup = service.get_owned_lookup(db, lookup_id, current_user.id)
    if not lookup:
        raise HTTPException(status_code=404, detail="Tarama bulunamadi")

    sonuclar = _yetkili_once_sirala(lookup.results)
    rows = [
        {
            "E-posta": r.email,
            "Siniflandirma": "Yetkili (oncelikli)" if r.siniflandirma == "yetkili" else "Genel",
            "Bulundugu Sayfa": r.kaynak_sayfa,
        }
        for r in sonuclar
    ]
    return rows_to_excel_response(rows, sheet_name="Yetkili Mailler", filename=f"mail_tarama_{lookup_id}")
