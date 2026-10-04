"""
MODUL 3 - router.py

1) POST /api/m3/projects            -> ulke + anahtar kelime(ler) ile proje olustur
2) POST /api/m3/projects/{id}/run   -> Google Places'te aramayi calistir
3) GET  /api/m3/projects/{id}/results        -> JSON sonuclar
4) GET  /api/m3/projects/{id}/results/excel  -> Excel export
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.excel_export import rows_to_excel_response
from app.modules.m0_altyapi.models import User
from app.modules.m3_haritalar import service
from app.modules.m3_haritalar.schemas import MapSearchProjectCreate, MapSearchProjectOut, MapSearchResultOut

router = APIRouter(tags=["Modul 3 - Haritalar"])


@router.post("/api/m3/projects", response_model=MapSearchProjectOut)
def create_project(
    data: MapSearchProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.create_project(db, current_user.id, data)


@router.post("/api/m3/projects/{project_id}/run", response_model=list[MapSearchResultOut])
def run_search(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = service.get_owned_project(db, project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Proje bulunamadi")
    return service.run_search(db, project)


@router.get("/api/m3/projects/{project_id}/results", response_model=list[MapSearchResultOut])
def get_results(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = service.get_owned_project(db, project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Proje bulunamadi")
    return project.results


@router.get("/api/m3/projects/{project_id}/results/excel")
def export_results_excel(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = service.get_owned_project(db, project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Proje bulunamadi")

    rows = [
        {
            "Anahtar Kelime": r.anahtar_kelime,
            "Firma Adi": r.firma_adi,
            "Adres": r.adres or "-",
            "Telefon": r.telefon or "-",
            "Website": r.website or "-",
            "Enlem": r.lat or "-",
            "Boylam": r.lng or "-",
        }
        for r in project.results
    ]
    return rows_to_excel_response(rows, sheet_name="Harita Sonuclari", filename=f"harita_proje_{project_id}")
