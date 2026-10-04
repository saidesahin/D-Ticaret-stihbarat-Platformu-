# Dis Ticaret Istihbarat Yazilimi

## Frontend - Kurumsal Site + Yonetim Paneli

1. **`frontend/index.html`** - Kendi kurumsal web sitemiz (ornek: "Toros Endustri
   Ihracat"). Buraya, ziyaretcileri tespit eden `assets/tracker.js` scripti
   GOMULUDUR. Bu bir musteriye verilen embed kodu DEGIL - dogrudan bizim
   sitemizde calisan gercek bir ozellik.
2. **`frontend/login.html` -> `dashboard.html` -> modul sayfalari** - Giris
   yapildiktan sonra kullanilan, tum modullerin birbirine bagli oldugu
   yonetim paneli. Sidebar'daki noktali "rota" cizgisi, modullerin tek bir
   akisin parcasi oldugunu gorsel olarak ifade eder.

Sayfalar arasi akis:
```
index.html (kurumsal site, herkese acik)
   -> "Yonetim Paneli" -> login.html
        -> basarili giris -> dashboard.html (Genel Bakis)
             -> Haritalarda Firma Arama   -> maps-search.html
             -> Yetkili Mail Bulma        -> email-lookup.html
             -> Toplu Mail Kampanyasi     -> email-campaign.html
             -> Cok Dilli Urun Arama      -> search-form.html
             -> Ziyaretci Tespiti         -> visitor-detection.html
```
Her modul sayfasindaki sol menuden diger tum modullere ve "Cikis Yap"a
tek tikla gecilir; hangi modulun aktif/yakinda oldugu backend'deki
`/api/dashboard` endpoint'inden gelir (tek kaynak, tum sayfalarda ayni).

Ortak dosyalar: `frontend/assets/style.css` (tasarim sistemi, beyaz zemin),
`frontend/assets/app-shell.js` (sidebar + oturum kontrolu + cikis),
`frontend/assets/tracker.js` (Modul 1 izleme scripti, sadece index.html'de).

### Kendi sitemiz icin site_key uretmek (Modul 1 calissin diye SART)

```bash
cd backend
python -m app.scripts.create_admin admin admin123      # ilk admin (yoksa)
python -m app.scripts.create_own_site admin https://kendisitemiz.com
```

Ciktidaki `site_key` degerini `frontend/index.html` en altindaki
`window.OWN_SITE_KEY = "..."` satirina yapistirin. Bundan sonra
`index.html`'i ziyaret eden herkes `visitor-detection.html` sayfasinda
listelenir.

---

## Modul 0 - Altyapi

Icerik: JWT tabanli admin-kontrollu login, kullanici yonetimi, dashboard iskeleti.

### Kurulum

```bash
cd backend
python -m venv venv && source venv/bin/activate   # (opsiyonel ama onerilir)
pip install -r requirements.txt
cp .env.example .env
```

### Ilk admin kullanicisini olustur (SADECE ILK KURULUMDA bir kez)

```bash
python -m app.scripts.create_admin admin admin123
```

### Sunucuyu calistir

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Swagger arayuzu: http://localhost:8000/docs

### Frontend'i acmak icin

`frontend/index.html` dosyasini tarayicida dogrudan ac - bu
kurumsal ana sayfa. Sag ustteki "Yonetim Paneli" butonuyla `login.html`'e
gecip admin ile giris yap. Admin panelinden yeni musteri kullanicilari
`/api/auth/users` endpoint'i uzerinden (Swagger'dan da yapilabilir) olustur.

### Testleri calistir

```bash
cd backend
python -m pytest app/modules/m0_altyapi/tests -v
```

5 test de gecmeli.

---

## Modul 0 "bitti" kriterleri (hepsi karsilandi)

- [x] Backend calisiyor, Swagger'da test edildi
- [x] Frontend baglandi (login.html -> dashboard.html gercek token ile calisiyor)
- [x] Otomatik testler yazildi (5/5 gecti)

---

## Modul 1 - Ziyaretci Tespiti

**Ne yapiyor:** Kendi web sitemize (`frontend/index.html`) gomulu bir JS
scripti, ziyaretciye "Size daha iyi hizmet verebilmemiz icin lutfen konum
bilgisini bizimle paylasin" pop-up'i gosterir.

- **Evet** -> tarayici Geolocation API'den lat/lng alinir -> backend bunu
  Google Geocoding API (adres) + Google Places Nearby Search (yakindaki olasi
  firmalar) ile zenginlestirir.
- **Hayir** -> sadece ziyaretcinin IP adresi kullanilir -> ipinfo.io ile
  ulke/sehir/organizasyon (ISS ya da kurumsal ag ise sirket adi) tahmini yapilir.
- Karar bir cerezde saklanir, ayni ziyaretciye pop-up tekrar gosterilmez.

**ONEMLI - gercekci beklenti:** Google'da "bu GPS noktasinda calisan tek firma"
diye sihirli bir servis yok. Places Nearby Search o bolgedeki Google Maps'e
kayitli isletmeleri LISTELER - mustakil bina/fabrikada isabet orani yuksek,
plaza/is merkezinde dusuk olur ("olasi firmalar" listesi olarak sunulur).
Ayni sekilde ev/mobil internetten gelen IP'lerde "org" alani genelde sadece
ISS adini verir (sirket adini degil) - bu Turk Telekom/Vodafone gibi ISS'lerden
gelen ziyaretlerde beklenen bir sinirdir.

### Yeni API anahtarlari gerekiyor (.env)

```
IPINFO_TOKEN=...              # https://ipinfo.io/signup (tokensiz de calisir, rate limit dusuk)
GOOGLE_PLACES_API_KEY=...     # Google Cloud Console -> Geocoding API + Places API etkinlestir
```

Anahtar girilmezse sistem CRASH ETMEZ, sadece o alanlari bos birakir (kodda test edildi).

### Kendi sitemize entegrasyon adimlari

1. Admin, `python -m app.scripts.create_own_site <kullanici> <domain>` ile
   KENDI domainimiz icin bir `site_key` uretir
2. `frontend/index.html` sonundaki `window.OWN_SITE_KEY = "SITE_KEY_BURAYA"`
   satiri bu key ile guncellenir
3. `assets/tracker.js` zaten `index.html` icine gomulu - baska bir yere
   kopyalanmasina gerek yok
4. Production'da `assets/tracker.js` icindeki `API_URL` (window.APP_API)
   gercek backend adresiyle guncellenir

### Yeni endpoint'ler

| Endpoint | Aciklama |
|---|---|
| `POST /api/m1/sites` | Admin - yeni site_key uretir |
| `POST /api/m1/track` | PUBLIC - JS snippet buraya yazar |
| `GET /api/m1/visits` | Musteri - kendi ziyaretcilerini listeler |
| `GET /api/m1/visits/excel` | Ayni listenin Excel export'u |

### Testleri calistir

```bash
cd backend
python -m pytest app/modules -v
```

10 test de gecmeli (Modul 0: 5, Modul 1: 5). Testler Google/ipinfo'ya gercek
istek atmaz (monkeypatch ile sahtelendi) - internetsiz ortamda da calisir.

### Modul 1 "bitti" kriterleri

- [x] Backend calisiyor, gercek sunucu uzerinde uctan uca test edildi (Evet/Hayir/gecersiz-key)
- [x] Frontend baglandi (gercek JS snippet, pop-up + cerez mantigi calisir halde)
- [x] Otomatik testler yazildi (5/5 gecti, harici servisler sahtelendi)

---

## Modul 2 - Cok Dilli Arama Motoru

Bu modul dokumandaki en buyuk parca oldugu icin kendi icinde alt adimlara boldum:

1. **[BITTI]** Form + veri modeli (OEM, GTIP, 7 dilde parca adi, hedef ulke) + cekirdek arama motoru entegrasyonu (Google/Bing/Yandex) + Excel export
2. **[SIRADA]** Yan GTIP / tamamlayici urun eslestirmesi
3. **[SIRADA]** Rakip firma adlariyla arama
4. **[SIRADA]** Urun resmiyle arama (reverse image search)

**valentin.app notu:** Dokumanda "valentin.app'ten veri ceksin" deniyor ama o
masaustu uygulamasi, API'si yok. Ayni isi (o ulkeden ariyormus gibi simule
etmek) **SerpAPI** ile resmi/otomasyona uygun sekilde yapiyoruz - `gl` (ulke)
ve `hl` (dil) parametreleri valentin.app'in yaptigi isin birebir karsiligi.

**"Safari" notu:** Dokumanda "google, yandex, safari ve diger arama
motorlariyla entegre" deniyor - Safari bir tarayici, arama motoru degil.
Google/Bing/Yandex ile ilerledim, bunu musteriye/Yasin'e iletmen iyi olur.

### Yeni API anahtari gerekiyor (.env)

```
SERPAPI_KEY=...   
```

Anahtar girilmezse sistem crash etmez, sadece bos sonuc listesi doner (test edildi).

### Yeni endpoint'ler

| Endpoint | Aciklama |
|---|---|
| `POST /api/m2/projects` | Formu doldur, arama projesi olustur |
| `POST /api/m2/projects/{id}/run` | Aramayi calistir (doldurulan dillerde x 3 motor) |
| `GET /api/m2/projects/{id}/results` | Sonuclari JSON olarak gor |
| `GET /api/m2/projects/{id}/results/excel` | Excel export |

### Testleri calistir

```bash
cd backend
python -m pytest app/modules -v
```

14 test de gecmeli (Modul 0: 5, Modul 1: 5, Modul 2: 4).

### Modul 2 - alt adim 1 "bitti" kriterleri

- [x] Backend calisiyor, gercek sunucu uzerinde uctan uca test edildi
- [x] Sadece doldurulan dil alanlari araniyor (bos alanlar atlaniyor) - test edildi
- [x] Baskasinin projesine erisim engelleniyor (404, hem /run hem /results icin) - test edildi
- [x] Otomatik testler yazildi (4/4 gecti, SerpAPI sahtelendi)
- [x] Frontend baglandi (`frontend/search-form.html` - dokumandaki form alanlariyla birebir, gercek Excel indirme calisir halde)

### Modul 2 

Artik 3 asamali arama yapiyor, her sonucun `kaynak_tipi` alaninda hangi
asamadan geldigi isaretli:

1. **`dil_aramasi`** - dokumandaki 7 dilde parca adi aramasi (alt adim 1)
2. **`yan_gtip`** - "otomobil satan, oto yedek parcasi da satar mi?" mantigi.
   Admin `/api/m2/gtip-relations` ile bir GTIP koduna iliskili anahtar
   kelimeler ekler (orn: `8708.30` -> `hardware store`), sistem bunlari
   otomatik olarak aramaya dahil eder.
   **Onemli sinirlama:** Bu TAM OTOMATIK yapay zeka siniflandirma degil -
   admin'in doldurdugu/genisleyen bir tablo. Binlerce GTIP kodunu otomatik
   iliskilendiren bir yapay zeka modeli ayri, cok daha buyuk bir proje olurdu.
3. **`rakip`** - formdaki `rakip_isimleri` alanina girilen firma adlari
   (virgulle ayrilir) da ayrica aranir.
4. **`gorsel_arama`** - urun resmi yuklenir (`/api/m2/projects/{id}/images`),
   SerpAPI'nin `google_lens` motoruyla gorsel eslesme aranir.
   **Onemli sinirlama:** Resmin SerpAPI tarafindan taranabilmesi icin
   PUBLIC bir URL'de barinmasi gerekir - localhost'ta test ederken bu URL
   disaridan erisilemez, bu yuzden gercek anlamli sonuc SADECE production'da
   (gercek domain + PUBLIC_BASE_URL .env ayari) alinir. Localhost'ta sadece
   "sistem crash etmiyor, dogru akisi izliyor" testi yapilabilir.

### Yeni .env ayari

```
PUBLIC_BASE_URL=http://localhost:8000   # production'da gercek domain ile degistir
```

### Yeni endpoint'ler

| Endpoint | Aciklama |
|---|---|
| `POST /api/m2/gtip-relations` | Admin - yan GTIP iliskisi ekler |
| `GET /api/m2/gtip-relations` | Yan GTIP tablosunu listeler |
| `POST /api/m2/projects/{id}/images` | Urun resmi yukler |
| `POST /api/m2/projects/{id}/run-image-search` | Yuklenen resimle gorsel arama calistirir |

### Testleri calistir

```bash
cd backend
python -m pytest app/modules -v
```

18 test de gecmeli (Modul 0: 5, Modul 1: 5, Modul 2: 8).

### Modul 2 "bitti" kriterleri (hepsi karsilandi)

- [x] Backend calisiyor, gercek sunucu uzerinde uctan uca test edildi (resim yukleme dahil, gercekten indirilebilir oldugu dogrulandi)
- [x] Frontend baglandi (`search-form.html` - form + resim yukleme + Excel indirme calisir halde)
- [x] Otomatik testler yazildi (18/18 gecti)

---

## Modul 3 - Haritalar

**Ne yapiyor:** Dokumandaki ornekle birebir - bir ulke + bir/birden fazla
anahtar kelime (virgulle ayrilir) girilir, her kelime AYRI AYRI Google
Places Text Search ile aranir ("automotive in United Kingdom" gibi), bulunan
firmalar (ad, adres, telefon, website, konum) Excel'e aktarilir.

**Nearby Search yerine Text Search kullandik:** Nearby Search bir merkez
nokta+yaricap ister, dokumandaki "ulke ulke arama" mantigina uymuyor. Text
Search serbest metin sorgusu kabul ediyor, ulke bazli arama icin daha uygun.

**Telefon/website icin ek maliyet notu:** Places API'nin arama sonucu (Text
Search) telefon/website DONMEZ, bunun icin her firma icin ayrica "Place
Details" sorgusu atmak gerekiyor (`detay_getir=true` varsayilan). Cok sayida
sonuc oldugunda bu maliyeti artirir - `detay_getir=false` ile kapatilabilir,
sadece firma adi/adres/konum alinir.

**Dokumandaki not dogrulandi:** Bazi firmalarin website'i olmuyor ama
telefonu/adresi var - testte bunu bilerek simule ettik (`website: null`,
`telefon` dolu senaryosu).

### Yeni endpoint'ler

| Endpoint | Aciklama |
|---|---|
| `POST /api/m3/projects` | Ulke + anahtar kelime(ler) ile proje olustur |
| `POST /api/m3/projects/{id}/run` | Google Places'te aramayi calistir |
| `GET /api/m3/projects/{id}/results` | JSON sonuclar |
| `GET /api/m3/projects/{id}/results/excel` | Excel export |

Frontend: `frontend/maps-search.html`. Ayni `.env`'deki `GOOGLE_PLACES_API_KEY`
kullanilir (Modul 1'de zaten kurulmustu, yeni anahtar gerekmez).

### Testleri calistir

```bash
cd backend
python -m pytest app/modules -v
```

23 test de gecmeli (Modul 0: 5, Modul 1: 5, Modul 2: 8, Modul 3: 5).

### Modul 3 "bitti" kriterleri (hepsi karsilandi)

- [x] Backend calisiyor, gercek sunucu uzerinde uctan uca test edildi
- [x] Frontend baglandi (`maps-search.html` - form + Excel indirme calisir halde)
- [x] Otomatik testler yazildi (5/5 gecti, Google Places sahtelendi)

---

## Modul 4 - Yetkili Mail Bulma 

**Ne yapiyor:** Bir web sitesi URL'i verilir, anasayfa + iletisim/hakkimizda/
ekip sayfalari (coklu dilde anahtar kelimeyle bulunur) taranir, HTML icindeki
e-posta adresleri regex ile cikarilir ve 2'ye siniflandirilir:
- **genel**: info@, contact@, support@ gibi (dokumandaki "bizim isimizi
  zorlastiran" adresler)
- **yetkili**: purchasing@, manager@, export@ gibi VEYA sahis ismi iceren
  adresler (dokumandaki "sahis ismi varsa genelde yetkili" notu) - sonuc
  listesinde bunlar EN USTTE gosterilir

**Sorumlu tarama onlemleri (onemli):**
- robots.txt kontrol edilir, izin vermeyen siteler taranmaz
- Sahte/placeholder domain'ler filtrelenir (`you@domain.com`, `test@example.com` gibi) -
  bunu GERCEK bir siteye (github.com) karsi test ederken tam da boyle bir
  placeholder yakalayip filtreledigimizi dogruladik
- Sayfa sayisi ve zaman asimi sinirli (asiri yuk bindirmemek icin)

**Gercekci beklenti (onemli):** Modern/kurumsal siteler (GitHub gibi SPA
veya form-tabanli iletisim kullanan siteler) genelde HTML icinde acik
e-posta BARINDIRMAZ - bu kodun hatasi degil, o sitelerin tasarim tercihi.
Bu modul en cok dokumandaki hedef kitleye (kucuk/orta olcekli ithalatci-
ihracatci firma siteleri) uygun - onlar genelde iletisim sayfasinda dogrudan
`info@firma.com` yaziyor.

**KVKK/GDPR notu:** Burada toplanan mailler, firmalarin KENDI web
sitelerinde ACIKCA yayinladigi kurumsal iletisim bilgileridir (kisisel
sosyal medya kazima degil) - bu genelde mesru is gelistirme amaciyla
kullanim sayilir. Ancak Modul 5'teki (otomatik toplu mail) gibi spam
amacli kullanim ayri bir hukuki risk tasir - bunu daha once de belirtmistik.

### Yeni endpoint'ler

| Endpoint | Aciklama |
|---|---|
| `POST /api/m4/lookups` | Web sitesi URL'i ile tarama olustur |
| `POST /api/m4/lookups/{id}/run` | Taramayi calistir |
| `GET /api/m4/lookups/{id}/results` | JSON sonuclar (yetkili mailler once) |
| `GET /api/m4/lookups/{id}/results/excel` | Excel export |

Yeni API anahtari GEREKMIYOR - bu modul kendi crawler'ini kullaniyor,
harici bir ucretli servise bagli degil.

### Testleri calistir

```bash
cd backend
python -m pytest app/modules -v
```

30 test de gecmeli (Modul 0: 5, Modul 1: 5, Modul 2: 8, Modul 3: 5, Modul 4: 7).

### Modul 4 "bitti" kriterleri (hepsi karsilandi)

- [x] Backend calisiyor, gercek sunucu + gercek internet uzerinde test edildi (github.com)
- [x] Otomatik testler yazildi (7/7 gecti)
- [x] Baskasinin taramasina erisim engelleniyor (404)
- [x] Frontend baglandi (`email-lookup.html` - tarama + sonuc tablosu + Excel indirme calisir halde)

---

## Modul 5 - Toplu Mail Gonderimi

**ONEMLI** Bu modul dokumanda da belirtildigi gibi hukuki risk tasiyor (spam mevzuati - KVKK, GDPR benzeri duzenlemeler,
CAN-SPAM). Reddetmedik ama 3 seyi koda gomduk, KOD SEVIYESINDE atlanamaz:

1. **Gonderen kimligi + fiziksel adres zorunlu** - kampanya olusturulurken
   bu alanlar bos birakilamaz (Pydantic validation ile).
2. **Her mailin sonuna OTOMATIK footer eklenir** - fiziksel adres +
   abonelikten cikma linki. Bu, gonderen tarafindan kaldirilamaz/atlanamaz.
3. **Suppression (vazgecme) listesi** - bir e-posta bir kere "abonelikten
   cik" linkine tikladiginda, o musterinin HICBIR kampanyasinda bir daha
   asla kullanilmaz. Bunu testte dogruladik: vazgecen bir adres ikinci
   kampanyaya eklenmeye calisildiginda otomatik "atlandi_suppression"
   durumuyla isaretleniyor, gonderilmiyor.


### Yeni SMTP ayari (.env)

```
SMTP_HOST=...       # orn: smtp.gmail.com, smtp.office365.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
SMTP_USE_TLS=true
```

Bos birakilirsa sistem crash etmez, her gonderim "SMTP yapilandirilmamis"
hatasiyla `basarisiz` olarak isaretlenir (Modul 1-4 ile ayni guvenli desen).

**Production notu:** Su anki surum SENKRON gonderim yapar (istek gelince
hemen gonderir), tek seferde en fazla 20 mail (`MAX_GONDERIM_PER_RUN`).
Gercek production'da (roadmap'te bahsettigimiz) Celery/Redis kuyrugu
kullanilip mailler dakikada birkac tane gibi YAVAS gonderilmeli - aksi
halde mail saglayicilari ani patlamayi spam olarak isaretleyip
domain/IP'yi kara listeye alabilir.

### Yeni endpoint'ler

| Endpoint | Aciklama |
|---|---|
| `POST /api/m5/campaigns` | Kampanya olustur (gonderen+adres zorunlu) |
| `POST /api/m5/campaigns/{id}/recipients` | Alici listesi ekle (suppression kontrolu otomatik) |
| `POST /api/m5/campaigns/{id}/send` | Gonderimi baslat (max 20/calistirma) |
| `GET /api/m5/campaigns/{id}/recipients` | Gonderim durumlarini gor |
| `GET /api/m5/unsubscribe/{token}` | PUBLIC - abonelikten cikma linki |
| `GET /api/m5/suppression-list` | Vazgecme listesini gor |

Frontend: `frontend/email-campaign.html`.

### Testleri calistir

```bash
cd backend
python -m pytest app/modules -v
```

37 test de gecmeli (Modul 0: 5, Modul 1: 5, Modul 2: 8, Modul 3: 5, Modul 4: 7, Modul 5: 7).

### Modul 5 "bitti" kriterleri (hepsi karsilandi)

- [x] Backend calisiyor, otomatik testlerle dogrulandi (SMTP sahtelendi - gercek mail atmadik)
- [x] Fiziksel adres/gonderen bilgisi olmadan kampanya olusturulamiyor - test edildi
- [x] Abonelikten cikma linki gercekten sonraki gonderimi engelliyor - test edildi
- [x] Frontend baglandi (`email-campaign.html` - 2 asamali form + sonuc tablosu calisir halde)
- [x] Otomatik testler yazildi (7/7 gecti)









