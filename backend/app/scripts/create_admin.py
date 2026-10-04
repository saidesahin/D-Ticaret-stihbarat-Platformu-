"""
scripts/create_admin.py

Neden bu script var: /api/auth/users endpoint'i "sadece admin yeni
kullanici olusturabilir" diyor - ama ilk admin nasil olusacak?
Bu script, API'yi hic kullanmadan dogrudan veritabanina ilk admin'i yazar.
Sadece BIR KERE, kurulumda calistirilir.

Kullanim (backend/ klasorunden):
    python -m app.scripts.create_admin admin sifre123
"""
import sys

from app.core.database import Base, engine, SessionLocal
from app.modules.m0_altyapi.models import User
from app.core.security import hash_password


def main():
    if len(sys.argv) != 3:
        print("Kullanim: python -m app.scripts.create_admin <kullanici_adi> <sifre>")
        sys.exit(1)

    username, password = sys.argv[1], sys.argv[2]

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"'{username}' zaten mevcut, cikiliyor.")
            return

        admin = User(
            username=username,
            hashed_password=hash_password(password),
            is_admin=True,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"Admin kullanici olusturuldu: {username}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
