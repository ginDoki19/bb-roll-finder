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
    if (!open && !ifr.src) ifr.src = ifr.dataset.src;
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

document.addEventListener("input", e => {
  if (e.target.classList.contains("rollfilter")) paintRolls(e.target.closest(".rollwrap"));
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
  dom:         { $, esc, safeHref },
  numbers:     { BN, AS, NUM, JOB, clock, clockRange },
  dates:       { TODAY, toISO, dayDiff, statusOf, countdown, dnum },
  language:    { get lang(){ return LANG; }, t, STR, kindLabel },
  constants:   { KIND, POST_RE },
  data:        { DATA, notices, searchable, scannedCount, findCentre, minus60 },
  maps:        { mapsUrl },
  results:     { postOf, identBlock, provenance, outcomeOf, nextBlock,
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

  const m = AS(decodeURIComponent(location.hash)).match(/roll=(\d+)/);
  if (m){ $("#roll").value = m[1]; renderResult(); }
})();
