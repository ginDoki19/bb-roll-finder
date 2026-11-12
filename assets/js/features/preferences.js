/* preferences.js
 * Theme and language preferences, the segmented toggles that set them, and the
 * static text repaint that a language change triggers.
 */
/* -------------------------------------------------------------- toggles */
function applyTheme(mode){
  const r = document.documentElement;
  if (mode === "system") r.removeAttribute("data-theme");
  else r.setAttribute("data-theme", mode);
  try { mode === "system" ? localStorage.removeItem("bb-theme") : localStorage.setItem("bb-theme", mode); } catch(e){}
  renderToggles();
}
function currentTheme(){
  try { return localStorage.getItem("bb-theme") || "system"; } catch(e){ return "system"; }
}
function renderToggles(){
  const th = currentTheme();
  $("#themeseg").innerHTML = ["system","light","dark"].map(m =>
    `<button type="button" data-theme-set="${m}" aria-pressed="${th === m}">${esc(t(m))}</button>`).join("");
  $("#langseg").innerHTML = [["bn","বাংলা"],["en","English"]].map(([c, l]) =>
    `<button type="button" data-lang-set="${c}" aria-pressed="${LANG === c}">${esc(l)}</button>`).join("");
}
function applyLang(code){
  LANG = code;
  try { localStorage.setItem("bb-lang", code); } catch(e){}
  document.documentElement.setAttribute("data-lang", code);
  document.documentElement.lang = code;
  paintStatic();
  renderToggles();
  // The box the user typed into is the one thing paintStatic cannot reach:
  // it holds a value, not a label. Round-trip it through ASCII so Bengali
  // digits become 200983 in English and 2009৮3 can never survive a switch.
  const box = $("#roll");
  if (box && box.value.trim()) box.value = NUM(AS(box.value));
  /* P4-3: say() suppresses a repeat of the same sentence, so after a language
     switch the status line kept the old-language text until the next
     keystroke. Clearing the memo lets renderResult() re-announce it. */
  lastSaid = "";
  renderNotices();
  renderResult();
}
function paintStatic(){
  $("#t-tagline").textContent    = t("tagline");
  $("#roll").placeholder         = t("placeholder");
  $("#t-rolllabel").textContent  = t("rollLabel");
  $("#t-allnotices").textContent = t("allNotices");
  $("#t-fdata").textContent      = t("fData");
  $("#t-fconfirm").textContent   = t("fConfirm");
  $("#t-fstatic").textContent    = t("fStatic");

  const centres = notices.reduce((a, n) => a + (n.centres ? n.centres.length : 0), 0);
  const rolls   = notices.reduce((a, n) => a + (n._count || 0) + (n.rolls ? n.rolls.length : 0), 0);
  $("#stats").innerHTML =
    `<span class="stat"><b>${NUM(notices.length)}${esc(t("cls"))}</b> ${esc(t("statNotices"))}</span>
     <span class="stat"><b>${NUM(centres)}${esc(t("cls"))}</b> ${esc(t("statCentres"))}</span>
     <span class="stat"><b>${NUM(rolls.toLocaleString("en-IN"))}${esc(t("cls"))}</b> ${esc(t("statRolls"))}</span>`;
  $("#hint").textContent = t("hintBase")(NUM(searchable.length))
    + (scannedCount ? t("hintScanned")(NUM(scannedCount)) : "");

  const age = dayDiff(DATA.generated.slice(0, 10));
  const fresh = age === 0 ? t("updToday") : age === -1 ? t("updYesterday")
              : age < 0 ? t("updDays")(NUM(-age)) : t("upd");
  $("#gen").textContent = `${fresh} ${t("builtFrom")(fmtDay(DATA.generated), NUM(notices.length))} ${t("fDataRest")}`;
}
