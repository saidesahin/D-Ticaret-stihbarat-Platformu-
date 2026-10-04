"""
MODUL 2 - service.py

Dokumandaki (a) ve (b) maddelerinin karsiligi:
"Kullanici hangi bilgileri biliyorsa onlari dolduracak" -> sadece DOLU
olan dil alanlari aranir, bos birakilanlar atlanir.

"Form arama motorlariyla entegreli calisacak" -> google/bing/yandex
uc motorda da aranir (dokumanda "google, yandex, safari" deniyor;
Safari bir tarayici, arama motoru degil - bu yuzden google/bing/yandex
ile devam ediyoruz, Yasin'e/musteriye bu notu iletmekte fayda var).
"""
from sqlalchemy.orm import Session

from app.modules.m2_cok_dilli_arama import serp_client, gtip_service
from app.modules.m2_cok_dilli_arama.models import SearchProject, SearchResult, ProjectImage
from app.modules.m2_cok_dilli_arama.schemas import SearchProjectCreate

ARANACAK_MOTORLAR = ["google", "bing", "yandex"]

# SearchProject alan adi -> (dil kodu) eslemesi
DIL_ALANLARI = {
    "parca_adi_tr": "tr",
    "parca_adi_en": "en",
    "parca_adi_es": "es",
    "parca_adi_ru": "ru",
    "parca_adi_ar": "ar",
    "parca_adi_fr": "fr",
    "parca_adi_de": "de",
}


def create_project(db: Session, owner_id: int, data: SearchProjectCreate) -> SearchProject:
    project = SearchProject(owner_id=owner_id, **data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def _kaydet(db: Session, project_id: int, dil: str, sorgu: str, motor: str, kaynak: str, bulunanlar: list[dict]) -> list[SearchResult]:
    yeni: list[SearchResult] = []
    for r in bulunanlar:
        sonuc = SearchResult(
            project_id=project_id,
            kullanilan_dil=dil,
            arama_sorgusu=sorgu,
            arama_motoru=motor,
            kaynak_tipi=kaynak,
            title=r["title"],
            url=r["url"],
            snippet=r["snippet"],
        )
        db.add(sonuc)
        yeni.append(sonuc)
    return yeni


def run_search(db: Session, project: SearchProject) -> list[SearchResult]:
    """
    3 asamali arama yapar (dokumandaki 3 farkli talebin karsiligi):
    1) Ana dil aramasi   - doldurulmus her dilde parca adi + OEM no
    2) Yan GTIP aramasi  - iliskili/tamamlayici urun anahtar kelimeleriyle (Ingilizce)
    3) Rakip arama       - kullanicinin girdigi rakip firma isimleriyle
    Her sonucun `kaynak_tipi` alani hangi asamadan geldigini gosterir.
    """
    yeni_sonuclar: list[SearchResult] = []

    # --- 1) Ana dil aramasi ---
    for alan_adi, dil_kodu in DIL_ALANLARI.items():
        parca_adi = getattr(project, alan_adi)
        if not parca_adi:
            continue

        sorgu = f"{parca_adi} {project.oem_no}" if project.oem_no else parca_adi
        for motor in ARANACAK_MOTORLAR:
            bulunanlar = serp_client.search(sorgu, motor, project.hedef_ulke_kodu, dil_kodu)
            yeni_sonuclar += _kaydet(db, project.id, dil_kodu, sorgu, motor, "dil_aramasi", bulunanlar)

    # --- 2) Yan GTIP aramasi ---
    ilgili_kelimeler = gtip_service.get_related_keywords(db, project.gtip_no)
    ana_urun_adi = project.parca_adi_en or project.parca_adi_tr
    if ilgili_kelimeler and ana_urun_adi:
        for kelime in ilgili_kelimeler:
            sorgu = f"{ana_urun_adi} {kelime}"
            for motor in ARANACAK_MOTORLAR:
                bulunanlar = serp_client.search(sorgu, motor, project.hedef_ulke_kodu, "en")
                yeni_sonuclar += _kaydet(db, project.id, "en", sorgu, motor, "yan_gtip", bulunanlar)

    # --- 3) Rakip arama ---
    if project.rakip_isimleri:
        rakipler = [r.strip() for r in project.rakip_isimleri.split(",") if r.strip()]
        for rakip in rakipler:
            for motor in ARANACAK_MOTORLAR:
                bulunanlar = serp_client.search(rakip, motor, project.hedef_ulke_kodu, "en")
                yeni_sonuclar += _kaydet(db, project.id, "en", rakip, motor, "rakip", bulunanlar)

    db.commit()
    return yeni_sonuclar


def add_project_image(db: Session, project_id: int, image_url: str) -> ProjectImage:
    img = ProjectImage(project_id=project_id, image_url=image_url)
    db.add(img)
    db.commit()
    db.refresh(img)
    return img


def run_image_search(db: Session, project: SearchProject) -> list[SearchResult]:
    """Dokumandaki (e) maddesi: urunun resmiyle eslesen siteleri arar."""
    yeni_sonuclar: list[SearchResult] = []
    images = db.query(ProjectImage).filter(ProjectImage.project_id == project.id).all()

    for img in images:
        bulunanlar = serp_client.reverse_image_search(img.image_url, project.hedef_ulke_kodu)
        yeni_sonuclar += _kaydet(db, project.id, "gorsel", img.image_url, "google_lens", "gorsel_arama", bulunanlar)

    db.commit()
    return yeni_sonuclar


def list_results(db: Session, project_id: int, owner_id: int) -> list[SearchResult]:
    project = (
        db.query(SearchProject)
        .filter(SearchProject.id == project_id, SearchProject.owner_id == owner_id)
        .first()
    )
    if not project:
        return []
    return project.results


def get_owned_project(db: Session, project_id: int, owner_id: int) -> SearchProject | None:
    return (
        db.query(SearchProject)
        .filter(SearchProject.id == project_id, SearchProject.owner_id == owner_id)
        .first()
    )
