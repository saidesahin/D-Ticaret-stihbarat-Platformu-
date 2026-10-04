"""
scripts/create_own_site.py

Neden bu script var: Ziyaretci Tespiti (Modul 1) artik bir musteriye
verilen embed kodu degil - dogrudan KENDI web sitemize (frontend/index.html)
gomulu calisiyor. Bu scripti BIR KERE calistirip cikan site_key'i
frontend/index.html icindeki `window.OWN_SITE_KEY` degerine yapistirmaniz
yeterli; ondan sonra kendi sitenizi ziyaret eden herkes otomatik
kaydedilir ve panelde "Ziyaretci Tespiti" sayfasinda listelenir.

Kullanim (backend/ klasorunden, once bir admin/kullanici olusturulmus olmali):
    python -m app.scripts.create_own_site admin https://kendisitemiz.com
"""
import sys

from app.core.database import Base, engine, SessionLocal
from app.modules.m0_altyapi.models import User
from app.modules.m1_ziyaretci_tespiti.service import create_site


def main():
    if len(sys.argv) != 3:
        print("Kullanim: python -m app.scripts.create_own_site <kullanici_adi> <domain>")
        sys.exit(1)

    username, domain = sys.argv[1], sys.argv[2]

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        owner = db.query(User).filter(User.username == username).first()
        if not owner:
            print(f"'{username}' adinda bir kullanici bulunamadi. Once create_admin.py ile olusturun.")
            sys.exit(1)

        site = create_site(db, owner_id=owner.id, domain=domain)
        print("Site kaydi olusturuldu.")
        print(f"  domain   : {site.domain}")
        print(f"  site_key : {site.site_key}")
        print()
        print("Simdi frontend/index.html icindeki su satiri guncelleyin:")
        print(f'  window.OWN_SITE_KEY = "{site.site_key}";')
    finally:
        db.close()


if __name__ == "__main__":
    main()
