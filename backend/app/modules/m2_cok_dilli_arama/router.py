"""
MODUL 2 - router.py

Akis:
1) POST /api/m2/projects        -> formu doldur, proje olustur
2) POST /api/m2/projects/{id}/run -> ana dil + yan GTIP + rakip aramasini calistir
3) GET  /api/m2/projects/{id}/results       -> sonuclari JSON olarak gor
4) GET  /api/m2/projects/{id}/results/excel -> sonuclari Excel olarak indir
5) POST /api/m2/projects/{id}/images        -> urun resmi yukle
6) POST /api/m2/projects/{id}/run-image-search -> yuklenen resimlerle gorsel arama
7) POST/GET /api/m2/gtip-relations          -> admin'in yan GTIP tablosunu yonetmesi
"""
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.excel_export import rows_to_excel_response
from app.modules.m0_altyapi.models import User
from app.modules.m2_cok_dilli_arama import service, gtip_service
from app.modules.m2_cok_dilli_arama.schemas import (
    SearchProjectCreate, SearchProjectOut, SearchResultOut,
    GtipRelationCreate, GtipRelationOut, ProjectImageOut,
)

router = APIRouter(tags=["Modul 2 - Cok Dilli Arama"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "static", "uploads")
UPLOAD_DIR = os.path.abspath(UPLOAD_DIR)
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/api/m2/projects", response_model=SearchProjectOut)
def create_project(
    data: SearchProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.create_project(db, current_user.id, data)


@router.post("/api/m2/projects/{project_id}/run", response_model=list[SearchResultOut])
def run_search(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = service.get_owned_project(db, project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Proje bulunamadi")

    return service.run_search(db, project)


@router.get("/api/m2/projects/{project_id}/results", response_model=list[SearchResultOut])
def get_results(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = service.get_owned_project(db, project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Proje bulunamadi")
    return project.results


@router.get("/api/m2/projects/{project_id}/results/excel")
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
            "Kaynak": r.kaynak_tipi,
            "Dil": r.kullanilan_dil,
            "Arama Motoru": r.arama_motoru,
            "Sorgu": r.arama_sorgusu,
            "Baslik": r.title or "-",
            "URL": r.url,
            "Ozet": r.snippet or "-",
        }
        for r in project.results
    ]
    return rows_to_excel_response(rows, sheet_name="Arama Sonuclari", filename=f"proje_{project_id}_sonuclar")


@router.post("/api/m2/projects/{project_id}/images", response_model=ProjectImageOut)
def upload_project_image(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dokumandaki (e) maddesi: 'ürünün resmi' alani.
    Resim diske kaydedilir, PUBLIC_BASE_URL ile erisilebilir bir URL uretilir
    (bu URL'i SerpAPI'nin gorsel arama servisi kullanacak).
    """
    project = service.get_owned_project(db, project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Proje bulunamadi")

    uzanti = os.path.splitext(file.filename or "")[1] or ".jpg"
    dosya_adi = f"{uuid.uuid4().hex}{uzanti}"
    hedef_yol = os.path.join(UPLOAD_DIR, dosya_adi)

    with open(hedef_yol, "wb") as f:
        f.write(file.file.read())

    image_url = f"{settings.PUBLIC_BASE_URL}/static/uploads/{dosya_adi}"
    return service.add_project_image(db, project.id, image_url)


@router.post("/api/m2/projects/{project_id}/run-image-search", response_model=list[SearchResultOut])
def run_image_search(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = service.get_owned_project(db, project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Proje bulunamadi")

    return service.run_image_search(db, project)


@router.post("/api/m2/gtip-relations", response_model=GtipRelationOut)
def create_gtip_relation(
    data: GtipRelationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sadece admin doldurabilir - yan GTIP tablosu musteri bazli degil, genel/paylasilan bir bilgi kaynagidir."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Bu islem icin admin yetkisi gerekli")
    return gtip_service.add_relation(db, data.gtip_no, data.related_keyword_en, data.aciklama)


@router.get("/api/m2/gtip-relations", response_model=list[GtipRelationOut])
def list_gtip_relations(
    gtip_no: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return gtip_service.list_relations(db, gtip_no)
