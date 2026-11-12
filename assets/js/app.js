/* app.js
 * Wiring. Delegated event handlers, service-worker registration and boot().
 *
 * Loaded last: boot() runs immediately and calls into every feature, so every
 * other file must already have been concatenated above this one.
 */
/* --------------------------------------------------------- interactions */
document.addEventListener("click", e => {
  const map = e.target.closest("[data-map]");
  if (map){
    const box = map.closest(".card").querySelector(".mapbox");
    const ifr = box.querySelector("iframe");
    const open = box.style.display === "block";
    box.style.display = open ? "none" : "block";
    map.textContent = open ? t("showMap") : t("hideMap");
    map.setAttribute("aria-expanded", open ? "false" : "true");
    /* The embed is the one part of this page that needs the network. Offline
       it rendered as a blank grey rectangle that looked like a broken build,
       so say what is wrong and leave the Google Maps button as the way out. */
    if (!open && !navigator.onLine && !ifr.src){
      if (!box.querySelector(".mapoffline")){
        const msg = document.createElement("div");
        msg.className = "mapoffline";
        msg.textContent = t("mapOffline");
        box.appendChild(msg);
      }
      return;
    }
    const off = box.querySelector(".mapoffline");
    if (off) off.remove();
    if (!open && !ifr.src) ifr.src = ifr.dataset.src;
    return;
  }

  /* 7.8 — share. Web Share where it exists (Android/iOS), clipboard
     everywhere else; both paths confirm in the button itself. */
  const sh = e.target.closest("[data-share]");
  if (sh){
    const url = location.origin + location.pathname + "#roll=" + sh.dataset.share;
    const done = () => {
      const was = sh.textContent;
      sh.textContent = t("shared");
      setTimeout(() => { sh.textContent = was; }, 1600);
    };
    if (navigator.share) navigator.share({ title: document.title, url }).catch(() => {});
    else navigator.clipboard?.writeText(url).then(done).catch(() => {});
    return;
  }
  const th = e.target.closest("[data-theme-set]");
  if (th){ applyTheme(th.dataset.themeSet); return; }

  const lg = e.target.closest("[data-lang-set]");
  if (lg){ applyLang(lg.dataset.langSet); return; }

  const jp = e.target.closest("[data-job]");
  if (jp){
    prefJob = jp.dataset.job || "";
    try { prefJob ? localStorage.setItem("bb-job", prefJob) : localStorage.removeItem("bb-job"); } catch(err){}
    paintHits(AS($("#roll").value).replace(/\D/g, ""));
    return;
  }
  const cp = e.target.closest(".rollcopy");
  if (cp){
    const wrap = cp.closest(".rollwrap");
    const txt = (wrap.dataset.rolls || "").split(",").join(", ");
    navigator.clipboard?.writeText(txt).then(() => {
      cp.textContent = t("copied");
      setTimeout(() => { cp.textContent = t("copyAll"); }, 1400);
    }).catch(() => {});
    return;
  }
  const f = e.target.closest("[data-f]");
  if (f){ filter = f.dataset.f; renderNotices(); return; }
});

let filterTimer = 0;
document.addEventListener("input", e => {
  if (!e.target.classList.contains("rollfilter")) return;
  /* The longest list is 1,037 chips. Rebuilding that grid on every keystroke
     is visibly janky on a low-end phone; one frame of debounce is below the
     threshold where typing feels laggy and skips most of the work. */
  const wrap = e.target.closest(".rollwrap");
  clearTimeout(filterTimer);
  filterTimer = setTimeout(() => paintRolls(wrap), 60);
});
/* build the chips only when a list is actually opened */
document.addEventListener("toggle", e => {
  if (e.target.tagName !== "DETAILS" || !e.target.open) return;
  e.target.querySelectorAll(".rollwrap").forEach(w => {
    if (!w.dataset.painted){ w.dataset.painted = "1"; paintRolls(w); }
  });
}, true);

/* offline support — only meaningful over http(s); silently skipped on file:// */
if ("serviceWorker" in navigator && location.protocol.startsWith("http")){
  window.addEventListener("load", () => { navigator.serviceWorker.register("sw.js").catch(() => {}); });
}

/* -------------------------------------------------------------- surface
   The files in assets/js are concatenated into one classic <script>, so they
   already share a scope and call each other directly by name. BB does not
   provide that sharing and nothing above depends on it.

   What it is for: a single declared list of what each module contributes, so
   the split is visible from the console and testable from Playwright. If a
   file is ever dropped from JS_FILES in build_site.py, the matching BB entry
   throws at build time instead of failing silently in some rarely-hit branch.

   Deliberately not a module system: wrapping each file in an IIFE and routing
   every call through BB.* would mean rewriting several hundred call sites for
   no behavioural gain on a page that loads no other scripts. */
const BB = {
  dom:         { $, esc, safeHref, pdfAttrs },
  numbers:     { BN, AS, NUM, JOB, JOB_LIST, JOB_LABEL, jobAttr, clock, clockRange, ofTime },
  dates:       { TODAY, toISO, dayDiff, statusOf, countdown, dnum, fmtDay, fmtDate },
  language:    { get lang(){ return LANG; }, t, STR, kindLabel },
  constants:   { KIND, POST_RE },
  data:        { DATA, notices, searchable, scannedCount, findCentre, minus60 },
  maps:        { mapsUrl },
  results:     { timingsBlock, postOf, identBlock, provenance, outcomeOf, nextBlock,
                 lowConf, lowConfBlock, shareBtn,
                 seatCard, sittingCard, selectedCard },
  rolls:       { rollWrapHtml, paintRolls },
  search:      { collectHits, isPref, renderResult, paintHits, say },
  noticeList:  { noticeCard, renderNotices },
  preferences: { applyTheme, currentTheme, renderToggles, applyLang, paintStatic }
};
window.BB = BB;

/* ------------------------------------------------------------------ boot */
(function boot(){
  document.documentElement.setAttribute("data-lang", LANG);
  document.documentElement.lang = LANG;
  paintStatic();
  renderToggles();
  renderNotices();

  /* The search is a <form> so it is a landmark and so mobile keyboards show
     a submit key, but there is no server to submit to — results render as
     you type. Without this, Enter would navigate and throw the query away. */
  $("#searchform").addEventListener("submit", e => { e.preventDefault(); renderResult(); });

  $("#roll").addEventListener("input", renderResult);
  $("#roll").addEventListener("keydown", e => {
    if (e.key === "Escape"){ e.target.value = ""; renderResult(); }
  });

  /* "/" jumps to the search box unless the user is already typing somewhere.
     Deliberately not an autofocus: on a phone an autofocus opens the keyboard
     over the content before the visitor has seen the page, so the focus is
     only taken on a device that has a real pointer. */
  document.addEventListener("keydown", e => {
    if (e.key !== "/" || e.ctrlKey || e.metaKey || e.altKey) return;
    const el = document.activeElement, tag = el ? el.tagName : "";
    if (tag === "INPUT" || tag === "TEXTAREA" || (el && el.isContentEditable)) return;
    e.preventDefault();
    $("#roll").focus();
    $("#roll").select();
  });
  try {
    if (window.matchMedia && window.matchMedia("(hover: hover) and (pointer: fine)").matches) $("#roll").focus();
  } catch(e){}

  const m = AS(decodeURIComponent(location.hash)).match(/roll=(\d+)/);
  if (m){ $("#roll").value = m[1]; renderResult(); }
})();
