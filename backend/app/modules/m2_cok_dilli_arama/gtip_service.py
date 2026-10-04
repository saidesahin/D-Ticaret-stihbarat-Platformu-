"""
MODUL 2 - gtip_service.py

Dokumandaki ornek: "otomobil satan, oto yedek parcasi da satar mi?
vinc satan, demir de satar mi?" - direkt ithalatcilari degil, IKINCIL
ithalatcilari/potansiyel yeni musterileri yakalamak icin.

Ilk surum: TAM OTOMATIK yapay zeka ile GTIP siniflandirma cok buyuk,
ayri bir proje sayilir (binlerce GTIP kodu + iliskilerini ogrenen bir
model gerekir). Bunun yerine ADMIN'in doldurdugu, genisleyen bir
"iliskili anahtar kelime" tablosu kullaniyoruz - staj suresinde
gercekci ve calisan bir cozum budur.
"""
from sqlalchemy.orm import Session

from app.modules.m2_cok_dilli_arama.models import GtipRelation


def get_related_keywords(db: Session, gtip_no: str | None) -> list[str]:
    if not gtip_no:
        return []
    rows = db.query(GtipRelation).filter(GtipRelation.gtip_no == gtip_no).all()
    return [r.related_keyword_en for r in rows]


def add_relation(db: Session, gtip_no: str, related_keyword_en: str, aciklama: str | None) -> GtipRelation:
    row = GtipRelation(gtip_no=gtip_no, related_keyword_en=related_keyword_en, aciklama=aciklama)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_relations(db: Session, gtip_no: str | None = None) -> list[GtipRelation]:
    q = db.query(GtipRelation)
    if gtip_no:
        q = q.filter(GtipRelation.gtip_no == gtip_no)
    return q.all()
