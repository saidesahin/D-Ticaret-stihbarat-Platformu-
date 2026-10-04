"""
main.py
Bu dosya MANTIK icermez. Sadece hangi modullerin router'ini
API'ye "taktigini" gosterir. Yeni modul bitince buraya
2 satir eklersin, baska hicbir yeri degistirmezsin.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.database import Base, engine
from app.core.config import settings

# --- Modul 0 ---
from app.modules.m0_altyapi.router import router as m0_router
import app.modules.m0_altyapi.models  # noqa: F401  (tablolari Base'e kaydettirmek icin)

# --- Modul 1 --- (kodlama + test tamamlandi, aktif ediliyor)
from app.modules.m1_ziyaretci_tespiti.router import router as m1_router
import app.modules.m1_ziyaretci_tespiti.models  # noqa: F401

# --- Modul 2 --- (kodlama + test tamamlandi, aktif ediliyor)
from app.modules.m2_cok_dilli_arama.router import router as m2_router
import app.modules.m2_cok_dilli_arama.models  # noqa: F401

# --- Modul 3 --- (kodlama + test tamamlandi, aktif ediliyor)
from app.modules.m3_haritalar.router import router as m3_router
import app.modules.m3_haritalar.models  # noqa: F401

# --- Modul 4 --- (kodlama + test tamamlandi, aktif ediliyor)
from app.modules.m4_yetkili_mail.router import router as m4_router
import app.modules.m4_yetkili_mail.models  # noqa: F401

# --- Modul 5 --- (kodlama + test tamamlandi, aktif ediliyor)
from app.modules.m5_toplu_mail.router import router as m5_router
import app.modules.m5_toplu_mail.models  # noqa: F401

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # gelistirme icin - production'da musteri sitelerinin domainleri ile sinirla
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gelistirme kolayligi icin create_all kullaniyoruz.
# Production'a gecince bunun yerine Alembic migration kullanilacak (Modul 0 notlarinda yazdik).
Base.metadata.create_all(bind=engine)

app.include_router(m0_router)
app.include_router(m1_router)
app.include_router(m2_router)
app.include_router(m3_router)
app.include_router(m4_router)
app.include_router(m5_router)

# Modul 2 gorsel arama icin yuklenen resimler burada servis edilir
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}
