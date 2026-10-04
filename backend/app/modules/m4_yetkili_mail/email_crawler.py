"""
MODUL 4 - email_crawler.py

Akis:
1) Ana sayfayi cek
2) Ana sayfadaki linkler arasindan "iletisim/hakkimizda/ekip" gibi
   sayfalari bul (coklu dilde anahtar kelime listesi)
3) Ana sayfa + bulunan sayfalarda (en fazla MAX_SAYFA adet) regex ile
   e-posta adreslerini cikar
4) Her e-postayi "genel" (info@, contact@, sales@ gibi) veya "yetkili"
   (purchasing@, manager@, sahis ismi@ gibi) olarak siniflandir

SORUMLU TARAMA NOTU: robots.txt kontrol edilir (izin verilmeyen siteler
taranmaz), makul bir User-Agent kullanilir, sayfa sayisi ve zaman asimi
sinirlandirilir - siteye asiri yuk bindirmemek icin.
"""
import re
import urllib.robotparser
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

MAX_SAYFA = 5
ZAMAN_ASIMI = 8.0
USER_AGENT = "DisTicaretIstihbaratBot/1.0 (+iletisim-mail-bulma-araci)"

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# Form placeholder'larinda / ornek kodlarda sikca gecen SAHTE domain'ler.
# Gercek testte GitHub'in ana sayfasindan "you@domain.com" gibi bir placeholder
# yakalandigini gorduk - bu liste bu tur yanlis pozitifleri elemek icin.
SAHTE_DOMAIN_KALIPLARI = {
    "domain.com", "example.com", "email.com", "yourdomain.com",
    "yourcompany.com", "company.com", "test.com", "sentry.io",
    "wixpress.com", "godaddy.com", "placeholder.com",
}

# Coklu dilde "iletisim/hakkimizda/ekip" sayfa link anahtar kelimeleri
ILETISIM_ANAHTAR_KELIMELER = [
    "contact", "iletisim", "iletişim", "about", "hakkimizda", "hakkımızda",
    "team", "ekip", "kontakt", "kontakt-uns", "contacto", "impressum", "staff",
]

# "Genel" (kisiye ozel olmayan) e-posta on ekleri - dokumandaki "info@" ornegi
GENEL_ON_EKLER = {
    "info", "contact", "iletisim", "support", "sales", "admin", "office",
    "hello", "mail", "webmaster", "noreply", "no-reply", "destek", "satis",
}

# "Yetkili" olma ihtimali yuksek on ekler - dokumandaki "purchasing@, manager@" ornegi
YETKILI_ON_EK_IPUCLARI = {
    "purchasing", "procurement", "manager", "ceo", "gm", "director",
    "sales.manager", "export", "satinalma", "mudur", "genel.mudur",
}


def _robots_izin_veriyor_mu(url: str) -> bool:
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        return True  # robots.txt okunamazsa varsayilan olarak izin ver (cogu site boyle)


def _sayfa_getir(url: str) -> str | None:
    try:
        resp = httpx.get(url, headers={"User-Agent": USER_AGENT}, timeout=ZAMAN_ASIMI, follow_redirects=True)
        if resp.status_code == 200 and "text/html" in resp.headers.get("content-type", ""):
            return resp.text
    except httpx.HTTPError:
        pass
    return None


def _iletisim_linklerini_bul(ana_sayfa_html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(ana_sayfa_html, "html.parser")
    bulunanlar = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        metin = (a.get_text() or "").lower()
        hedef = href.lower()

        if any(kw in hedef or kw in metin for kw in ILETISIM_ANAHTAR_KELIMELER):
            tam_url = urljoin(base_url, href)
            if urlparse(tam_url).netloc == urlparse(base_url).netloc:  # sadece ayni site icinde kal
                bulunanlar.add(tam_url)

    return list(bulunanlar)[:MAX_SAYFA - 1]  # ana sayfa zaten 1 slot kullaniyor


def siniflandir(email: str) -> str:
    on_ek = email.split("@")[0].lower()
    if on_ek in GENEL_ON_EKLER:
        return "genel"
    if any(ipucu in on_ek for ipucu in YETKILI_ON_EK_IPUCLARI):
        return "yetkili"
    # Bilinen genel/yetkili kaliplarina uymuyorsa (orn: "jsmith", "ahmet.yilmaz")
    # muhtemelen sahis ismi - yetkili sayiyoruz (dokumandaki "sahis ismi varsa
    # o firma yetkilisi oluyor" notuna uygun)
    return "yetkili"


def taramayi_calistir(website_url: str) -> list[dict]:
    """Basarisiz olursa BOS LISTE doner - crash etmez (diger modullerle ayni desen)."""
    if not _robots_izin_veriyor_mu(website_url):
        return []

    sonuclar: list[dict] = []
    gorulen_mailler: set[str] = set()

    ana_html = _sayfa_getir(website_url)
    if not ana_html:
        return []

    taranacak_sayfalar = [website_url] + _iletisim_linklerini_bul(ana_html, website_url)

    for i, sayfa_url in enumerate(taranacak_sayfalar[:MAX_SAYFA]):
        html = ana_html if i == 0 else _sayfa_getir(sayfa_url)
        if not html:
            continue

        for email in EMAIL_REGEX.findall(html):
            email = email.lower()
            domain = email.split("@")[-1]
            # site ile alakasiz statik/analytics/placeholder maillerini elemek icin
            # basit dogruluk kontrolleri
            if len(email) > 60 or email in gorulen_mailler:
                continue
            if domain in SAHTE_DOMAIN_KALIPLARI:
                continue
            gorulen_mailler.add(email)
            sonuclar.append({
                "email": email,
                "kaynak_sayfa": sayfa_url,
                "siniflandirma": siniflandir(email),
            })

    return sonuclar
