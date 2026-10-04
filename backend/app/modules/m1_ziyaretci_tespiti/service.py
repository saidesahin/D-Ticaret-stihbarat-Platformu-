"""
MODUL 1 - service.py

Dokumandaki 2 senaryoyu burada birlestiriyoruz:
(a) Ziyaretci "Evet" -> lat/lng var -> Google servisleriyle adres + olasi firma
(b) Ziyaretci "Hayir" -> sadece IP var -> ipinfo.io ile ulke/org tahmini

Her iki durumda da IP tabanli sorgu HER ZAMAN yapilir (ulke bilgisi icin
temel/yedek katman), "Evet" durumunda bunun UZERINE konum verisi eklenir.
"""
import json

from sqlalchemy.orm import Session

from app.modules.m1_ziyaretci_tespiti import ip_client, google_location_client
from app.modules.m1_ziyaretci_tespiti.models import Site, Visit
from app.modules.m1_ziyaretci_tespiti.schemas import TrackPayload


def get_site_by_key(db: Session, site_key: str) -> Site | None:
    return db.query(Site).filter(Site.site_key == site_key).first()


def create_site(db: Session, owner_id: int, domain: str) -> Site:
    site = Site(owner_id=owner_id, domain=domain)
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


def record_visit(db: Session, site: Site, payload: TrackPayload, client_ip: str) -> Visit:
    # Her zaman calisan temel katman: IP -> ulke/org tahmini
    ip_info = ip_client.lookup_ip(client_ip)

    address_guess = None
    nearby_companies: list[str] = []

    # Sadece ziyaretci "Evet" dediyse (consent_given=True) ve koordinat geldiyse calisir
    if payload.consent_given and payload.lat is not None and payload.lng is not None:
        address_guess = google_location_client.reverse_geocode(payload.lat, payload.lng)
        nearby_companies = google_location_client.find_nearby_companies(payload.lat, payload.lng)

    visit = Visit(
        site_id=site.id,
        ip_address=client_ip,
        page_url=payload.page_url,
        country=ip_info["country"],
        city=ip_info["city"] if not address_guess else ip_info["city"],
        org_guess=ip_info["org_guess"],
        consent_given=1 if payload.consent_given else 0,
        lat=payload.lat,
        lng=payload.lng,
        address_guess=address_guess,
        nearby_company_guess=json.dumps(nearby_companies, ensure_ascii=False) if nearby_companies else None,
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)
    return visit


def list_visits_for_owner(db: Session, owner_id: int, site_id: int | None = None) -> list[Visit]:
    q = db.query(Visit).join(Site).filter(Site.owner_id == owner_id)
    if site_id:
        q = q.filter(Visit.site_id == site_id)
    return q.order_by(Visit.created_at.desc()).all()
