/* ==========================================================================
   TRACKER.JS - Ziyaretci Tespiti (Modul 1)

   ONEMLI: Bu script bir "musteriye verilen embed kodu" DEGILDIR.
   Dogrudan KENDI web sitemize (index.html) gomulur ve bizim sitemizi
   ziyaret eden potansiyel alicilari/firmalari tespit etmek icin calisir.
   Toplanan veriler backend'de /api/m1/visits ile Ziyaretci Tespiti
   panelinde (visitor-detection.html) goruntulenir.

   SITE_KEY, backend'de "python -m app.scripts.create_own_site" scripti
   calistirilarak KENDI sitemiz icin bir kere uretilir (bkz. README).
   ========================================================================== */
(function () {
  var API_URL = (window.APP_API || "http://localhost:8000") + "/api/m1/track";
  var SITE_KEY = window.OWN_SITE_KEY || "SITE_KEY_BURAYA"; // create_own_site.py ciktisi ile degistirin
  var CEREZ_ADI = "ziyaretci_izin_karari";

  function cerezOku(ad) {
    var eslesme = document.cookie.match("(^|;)\\s*" + ad + "\\s*=\\s*([^;]+)");
    return eslesme ? eslesme.pop() : null;
  }

  function cerezYaz(ad, deger, gunSayisi) {
    var tarih = new Date();
    tarih.setTime(tarih.getTime() + gunSayisi * 24 * 60 * 60 * 1000);
    document.cookie = ad + "=" + deger + ";expires=" + tarih.toUTCString() + ";path=/";
  }

  function backendeGonder(consentGiven, lat, lng) {
    fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        site_key: SITE_KEY,
        page_url: window.location.href,
        consent_given: consentGiven,
        lat: lat || null,
        lng: lng || null,
      }),
    }).catch(function () {
      // Sessiz basarisizlik: takip hicbir zaman ziyaretcinin deneyimini bozmamali.
    });
  }

  function popupGizle() {
    var el = document.getElementById("ziyaretci-izin-popup");
    if (el) el.style.display = "none";
  }

  function evetTiklandi() {
    popupGizle();
    cerezYaz(CEREZ_ADI, "evet", 365);
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        function (pos) { backendeGonder(true, pos.coords.latitude, pos.coords.longitude); },
        function () { backendeGonder(false); },
        { timeout: 8000 }
      );
    } else {
      backendeGonder(false);
    }
  }

  function hayirTiklandi() {
    popupGizle();
    cerezYaz(CEREZ_ADI, "hayir", 365);
    backendeGonder(false);
  }

  function popupOlustur() {
    var wrap = document.createElement("div");
    wrap.id = "ziyaretci-izin-popup";
    wrap.innerHTML =
      '<p>Size daha iyi hizmet verebilmemiz i\u00e7in l\u00fctfen konum bilginizi bizimle payla\u015f\u0131n.</p>' +
      '<div class="ziyaretci-izin-btns">' +
      '<button id="ziyaretci-izin-evet">Evet, payla\u015f</button>' +
      '<button id="ziyaretci-izin-hayir">Hay\u0131r, te\u015fekk\u00fcrler</button>' +
      "</div>";
    document.body.appendChild(wrap);
    document.getElementById("ziyaretci-izin-evet").addEventListener("click", evetTiklandi);
    document.getElementById("ziyaretci-izin-hayir").addEventListener("click", hayirTiklandi);
  }

  document.addEventListener("DOMContentLoaded", function () {
    var oncekiKarar = cerezOku(CEREZ_ADI);
    if (oncekiKarar === "evet" || oncekiKarar === "hayir") {
      // Karar daha once verilmis: pop-up tekrar gosterilmez, sessizce IP tabanli kayit atilir.
      backendeGonder(false);
      return;
    }
    popupOlustur();
    setTimeout(function () {
      var el = document.getElementById("ziyaretci-izin-popup");
      if (el) el.classList.add("gorunur");
    }, 600);
  });
})();
