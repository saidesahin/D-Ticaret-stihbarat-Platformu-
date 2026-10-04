/* ==========================================================================
   APP-SHELL.JS
   Giris yapilmis her sayfada ortak sidebar'i olusturur, oturum kontrolu
   yapar ve cikis islemini saglar. Sidebar, backend'deki /api/dashboard
   endpoint'inden gelen modul listesine gore kendini kurar - yani hangi
   modulun aktif/yakinda oldugu TEK bir yerden (backend) yonetilir ve
   tum sayfalarda ayni sekilde yansir. Boylece moduller gercekten
   "birbirine bagli" tek bir uygulama gibi davranir.
   ========================================================================== */
window.APP_API = "http://localhost:8000";

(function () {
  const API = window.APP_API;
  const token = localStorage.getItem("access_token");
  const path = window.location.pathname.split("/").pop() || "index.html";
  const PUBLIC_PAGES = ["login.html", "index.html", ""];

  window.cikisYap = function () {
    localStorage.removeItem("access_token");
    window.location.href = "login.html";
  };

  if (!PUBLIC_PAGES.includes(path) && !token) {
    window.location.href = "login.html";
    return;
  }

  const sidebarEl = document.getElementById("sidebar");
  if (!sidebarEl) return; // login.html / index.html'de sidebar yok

  const ICONS = {
    genel: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/></svg>`,
    harita: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 12-9 12s-9-5-9-12a9 9 0 0 1 18 0Z"/><circle cx="12" cy="10" r="3"/></svg>`,
    mail: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 6-10 7L2 6"/></svg>`,
    gonder: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>`,
    arama: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>`,
    grafik: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
    goz: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8Z"/><circle cx="12" cy="12" r="3"/></svg>`,
    grid: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>`,
  };

  const BRAND_MARK = `<svg viewBox="0 0 34 34" width="34" height="34"><circle cx="17" cy="17" r="16" fill="#0B4F6C"/><circle cx="17" cy="17" r="16" fill="none" stroke="#B3801F" stroke-width="1"/><path d="M17 6v22M6 17h22" stroke="#EAF2F5" stroke-width="1"/><circle cx="17" cy="17" r="4.2" fill="none" stroke="#B3801F" stroke-width="1.4"/><path d="M17 12.8 18 16l3.2 1-3.2 1-1 3.2-1-3.2-3.2-1 3.2-1Z" fill="#B3801F"/></svg>`;

  function render(data) {
    const items = [
      { id: "genel-bakis", ad: "Genel Bakis", durum: "aktif", sayfa: "dashboard.html", ikon: "genel" },
    ].concat(data.aktif_moduller || []);

    let html = `<div class="brand"><span class="brand-mark">${BRAND_MARK}</span>
      <div class="brand-text"><strong>Dis Ticaret</strong><small>Istihbarat Platformu</small></div></div>`;

    html += `<nav class="nav">`;
    items.forEach((m) => {
      const isActive = path === m.sayfa;
      const clickable = m.durum === "aktif" && !!m.sayfa;
      const svg = ICONS[m.ikon] || ICONS.grid;
      const tag = clickable ? "a" : "div";
      const hrefAttr = clickable ? `href="${m.sayfa}"` : "";
      const cls = "nav-item" + (isActive ? " is-active" : "") + (clickable ? "" : " is-disabled");
      html += `<${tag} class="${cls}" ${hrefAttr}>
          <span class="nav-dot"></span>
          <span class="nav-icon">${svg}</span>
          <span class="nav-label">${m.ad}</span>
          ${m.durum !== "aktif" ? '<span class="nav-soon">yakinda</span>' : ""}
        </${tag}>`;
    });
    html += `</nav>`;

    html += `<div class="sidebar-foot">
        <div class="user-line">Hosgeldin, <strong>${data.hosgeldin || ""}</strong></div>
        <button class="btn-ghost-logout" onclick="cikisYap()">Cikis Yap</button>
      </div>`;

    sidebarEl.innerHTML = html;
  }

  fetch(`${API}/api/dashboard`, { headers: { Authorization: `Bearer ${token}` } })
    .then((resp) => {
      if (resp.status === 401) {
        localStorage.removeItem("access_token");
        window.location.href = "login.html";
        throw new Error("401");
      }
      return resp.json();
    })
    .then(render)
    .catch(() => {});
})();
