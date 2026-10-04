"""
MODUL 5 - TOPLU MAIL GONDERIMI
models.py

Bu modul dokumanda da belirtildigi gibi hukuki risk tasiyor (spam
yasalari, KVKK/GDPR). Bu yuzden 3 seyi ZORUNLU kildik, atlanamaz:

1) Her kampanyada GONDEREN KIMLIGI ve FIZIKSEL ADRES zorunlu alan
   (CAN-SPAM ve benzeri duzenlemelerin asgari sarti)
2) Her gonderilen mailin sonuna OTOMATIK "abonelikten cik" linki eklenir
3) SuppressionEntry (vazgecme listesi) - bir e-posta buraya bir kere
   girdiginde, hangi kampanyada olursa olsun BIR DAHA ASLA mail atilmaz
"""
import uuid

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class EmailCampaign(Base):
    __tablename__ = "email_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    konu = Column(String, nullable=False)
    govde_html = Column(Text, nullable=False)

    gonderen_adi = Column(String, nullable=False)
    gonderen_email = Column(String, nullable=False)
    fiziksel_adres = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    alicilar = relationship("EmailCampaignRecipient", back_populates="campaign")


def generate_unsub_token() -> str:
    return uuid.uuid4().hex


class EmailCampaignRecipient(Base):
    __tablename__ = "email_campaign_recipients"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("email_campaigns.id"), nullable=False)

    email = Column(String, nullable=False)
    unsubscribe_token = Column(String, unique=True, default=generate_unsub_token)

    durum = Column(String, nullable=False, default="beklemede")
    hata_mesaji = Column(String, nullable=True)
    gonderim_zamani = Column(DateTime(timezone=True), nullable=True)

    campaign = relationship("EmailCampaign", back_populates="alicilar")


class SuppressionEntry(Base):
    __tablename__ = "suppression_entries"
    __table_args__ = (UniqueConstraint("owner_id", "email", name="uq_owner_email"),)

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email = Column(String, nullable=False)
    eklenme_sebebi = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
