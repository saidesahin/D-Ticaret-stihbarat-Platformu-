"""
ORTAK ALTYAPI - config.py
Tüm modüllerin ortak kullandığı ayarlar burada okunur.
Yeni bir modül eklerken bu dosyaya SADECE yeni bir API anahtarı gerekiyorsa
ekleme yaparsın, başka bir şeyi değiştirmezsin.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Genel ---
    APP_NAME: str = "Dis Ticaret Istihbarat Yazilimi"
    ENV: str = "development"

    # --- Veritabani ---
    # Gelistirme/test icin SQLite, production'da .env icinde
    # postgresql://kullanici:sifre@host:5432/dbadi seklinde degistirilir.
    DATABASE_URL: str = "sqlite:///./dev.db"

    # --- Auth ---
    SECRET_KEY: str = "gelistirme-icin-gecici-anahtar-DEGISTIR"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 saat

    # --- Modul 2+ icin ileride kullanilacak API anahtarlari (simdilik bos) ---
    SERPAPI_KEY: str = ""
    GOOGLE_PLACES_API_KEY: str = ""
    IPINFO_TOKEN: str = ""

    # --- Modul 2 - gorsel arama icin: yuklenen resimlerin PUBLIC URL'i bu adresle olusturulur ---
    # ONEMLI: localhost'ta bu URL disaridan (SerpAPI'nin sunuculari) erisilemez -
    # gorsel arama SADECE production'da gercek bir domain uzerinde anlamli sonuc verir.
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    # --- Modul 5 - toplu mail gonderimi icin SMTP ayarlari ---
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
