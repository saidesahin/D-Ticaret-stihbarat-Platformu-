"""
MODUL 3 - service.py

Her anahtar kelime icin ayri bir text_search yapar (dokumandaki ornekte
"automotive" ve "spare part" AYRI AYRI arattiriliyor, tek sorguda degil -
boylece hangi firmanin hangi kelimeyle bulundugu ayirt edilebiliyor).
"""
from sqlalchemy.orm import Session

from app.modules.m3_haritalar import places_text_client
from app.modules.m3_haritalar.models import MapSearchProject, MapSearchResult
from app.modules.m3_haritalar.schemas import MapSearchProjectCreate


def create_project(db: Session, owner_id: int, data: MapSearchProjectCreate) -> MapSearchProject:
    project = MapSearchProject(
        owner_id=owner_id,
        hedef_ulke=data.hedef_ulke,
        anahtar_kelimeler=data.anahtar_kelimeler,
        detay_getir=1 if data.detay_getir else 0,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def run_search(db: Session, project: MapSearchProject) -> list[MapSearchResult]:
    yeni_sonuclar: list[MapSearchResult] = []
    kelimeler = [k.strip() for k in project.anahtar_kelimeler.split(",") if k.strip()]

    for kelime in kelimeler:
        sorgu = f"{kelime} in {project.hedef_ulke}"
        bulunanlar = places_text_client.text_search(sorgu)

        for firma in bulunanlar:
            telefon, website = None, None
            if project.detay_getir and firma.get("google_place_id"):
                detay = places_text_client.place_details(firma["google_place_id"])
                telefon, website = detay["telefon"], detay["website"]

            sonuc = MapSearchResult(
                project_id=project.id,
                anahtar_kelime=kelime,
                firma_adi=firma["firma_adi"],
                adres=firma.get("adres"),
                telefon=telefon,
                website=website,
                lat=firma.get("lat"),
                lng=firma.get("lng"),
                google_place_id=firma.get("google_place_id"),
            )
            db.add(sonuc)
            yeni_sonuclar.append(sonuc)

    db.commit()
    return yeni_sonuclar


def get_owned_project(db: Session, project_id: int, owner_id: int) -> MapSearchProject | None:
    return (
        db.query(MapSearchProject)
        .filter(MapSearchProject.id == project_id, MapSearchProject.owner_id == owner_id)
        .first()
    )
