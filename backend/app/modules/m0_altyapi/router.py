"""
MODUL 0 - ALTYAPI
router.py: /api/auth/* ve /api/dashboard endpoint'leri.

main.py bu router'i tek satirla "takar":
    app.include_router(m0_router)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.modules.m0_altyapi import service
from app.modules.m0_altyapi.models import User
from app.modules.m0_altyapi.schemas import Token, UserCreate, UserOut

router = APIRouter(tags=["Modul 0 - Altyapi"])


@router.post("/api/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanici adi veya sifre hatali",
        )
    token = create_access_token(data={"sub": user.username})
    return Token(access_token=token)


@router.post("/api/auth/users", response_model=UserOut)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dokumandaki karar geregi kayit ekrani yok - sadece ADMIN yeni
    musteri kullanicisi olusturabilir.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Bu islem icin admin yetkisi gerekli")

    if service.get_user_by_username(db, data.username):
        raise HTTPException(status_code=400, detail="Bu kullanici adi zaten kayitli")

    return service.create_user(db, data)


@router.get("/api/dashboard")
def dashboard(current_user: User = Depends(get_current_user)):
    """
    Her modul burada bir kart olarak listelenecek.
    "sayfa" alani, frontend'in hangi HTML dosyasina yonlendirecegini soyler
    (durum "aktif" degilse frontend link olusturmaz, sadece rozet gosterir).
    """
    return {
        "hosgeldin": current_user.username,
        "firma": current_user.company_name,
        "aktif_moduller": [
            {"id": "m3", "ad": "Haritalarda Firma Arama", "durum": "aktif", "sayfa": "maps-search.html", "ikon": "harita"},
            {"id": "m4", "ad": "Yetkili Mail Bulma", "durum": "aktif", "sayfa": "email-lookup.html", "ikon": "mail"},
            {"id": "m5", "ad": "Toplu Mail Kampanyasi", "durum": "aktif", "sayfa": "email-campaign.html", "ikon": "gonder"},
            {"id": "m2", "ad": "Cok Dilli Urun Arama", "durum": "aktif", "sayfa": "search-form.html", "ikon": "arama"},
            {"id": "m1", "ad": "Ziyaretci Tespiti", "durum": "aktif", "sayfa": "visitor-detection.html", "ikon": "goz"},
            {"id": "raporlar", "ad": "Raporlar ve Istatistikler", "durum": "yakinda", "sayfa": None, "ikon": "grafik"},
            {"id": "diger", "ad": "Diger Moduller", "durum": "yakinda", "sayfa": None, "ikon": "grid"},
        ],
    }
