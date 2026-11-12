/* results.js
 * The result cards a candidate sees after a hit: identity (which job and post
 * this is), provenance (how the roll list was obtained), the outcome panel,
 * and the three card shapes — seat, sitting and selected.
 */
function postOf(n, group){
  if (group && group.post) return group.post;
  const g = n.groups || [];
  if (g.length === 1 && g[0].post) return g[0].post;
  if (g.length > 1) return null;                       // multi-post notice
  const title = n.title || "";
  if (/\d+\s+category\s+posts?/i.test(title)) return null;
  const m = POST_RE.exec(title);
  if (!m) return null;
  const p = m[1].replace(/[.\s]+$/, "").trim();
  if (!p || p.length > 60 || /circular|^spcbl/i.test(p)) return null;
  return p;
}
function identBlock(n, group, opts){
  opts = opts || {};
  const post = postOf(n, group);
  const bits = [];
  if (n.noticeNo)  bits.push(`${t("notice")} ${dnum(n.noticeNo)}`);
  if (n.published) bits.push(`${t("published")} ${dnum(n.published)}`);
  return `<div class="ident">
    <div class="jobtag"${jobAttr(n.jobId)}><span class="k">${esc(t("job"))}</span><span class="v">${esc(JOB_LABEL(n.jobId))}</span></div>
    <div class="identtext">
      <p class="post">${esc(post || t("multiPost"))}</p>
      ${bits.length ? `<div class="identmeta">${bits.map(b => `<span>${esc(b)}</span>`).join("")}</div>` : ""}
    </div>
    ${opts.preferred ? `<span class="yours">${esc(t("yoursBadge"))}</span>` : ""}
  </div>`;
}

/* ------------------------------------------------------------ provenance
   Never let an OCR-derived list look hand-checked, and never let either look
   like machine-extracted text. The wording differs on purpose. */
function provenance(n){
  if (n.rollSource === "ocr"){
    const tot = n.ocrChecks && n.ocrChecks.printedTotal ? dnum(n.ocrChecks.printedTotal) : "";
    return `<div class="prov">${t("ocrProv")(tot)}<a ${pdfAttrs(n.pdf)} target="_blank" rel="noopener noreferrer">${esc(t("confirmPdf"))}</a>${esc(t("stop"))}</div>`;
  }
  if (n.rollSource === "manual"){
    return `<div class="prov">${t("manualProv")}<a ${pdfAttrs(n.pdf)} target="_blank" rel="noopener noreferrer">${esc(t("confirmPdf"))}</a>${esc(t("stop"))}</div>`;
  }
  return "";
}

/* ------------------------------------------------- low-confidence rolls
   The OCR records the rolls it could not read the same way twice in
   ocrChecks.lowConfidence. Until now nothing read that field, so a candidate
   whose number was one of them got the ordinary green "you are on the list"
   card with no hint that the scan was unclear at exactly their number.

   The list is deliberately kept in rolls[] rather than dropped — a candidate
   searching a number the notice really does contain must not be told it is
   absent — so the disclosure has to happen at render time instead. */
function lowConf(n, roll){
  const lc = n.ocrChecks && n.ocrChecks.lowConfidence;
  if (!lc || !lc.length) return false;
  return lc.map(String).indexOf(String(roll)) !== -1;
}
function lowConfBlock(n, roll){
  if (!lowConf(n, roll)) return "";
  return `<div class="prov warn" role="note">
    <b>${esc(t("lowConfTitle"))}</b> ${esc(t("lowConfBody"))}
    <a ${pdfAttrs(n.pdf)} target="_blank" rel="noopener noreferrer">${esc(t("confirmPdf"))}</a>${esc(t("stop"))}</div>`;
}

/* --------------------------------------------------------- outcome panel */
function outcomeOf(n){
  const txt = `${n.title || ""} ${n.category || ""}`;
  const hl = LANG === "bn" ? (n.headlineBn || n.headline) : (n.headline || n.headlineBn);
  if (hl) return { tone:"ok", title:hl, steps:null };
  if (/offer\s+letter/i.test(txt))        return { tone:"ok", title:t("congratsOffer"),   steps:t("nextOffer") };
  if (/primarily\s+selected|selected\s+candidate/i.test(txt))
                                          return { tone:"ok", title:t("congratsPrimary"), steps:t("nextPrimary") };
  return { tone:"neutral", title:t("congratsGeneric"), steps:t("nextPrimary") };
}
function detailRows(details){
  return `<div class="dets">` + details.map(d =>
    `<div class="det${d.warn ? " warn" : ""}">` +
      `<div class="k">${esc(d.k)}</div><div class="v">${esc(d.v)}</div></div>`).join("") + `</div>`;
}
/* A curated notice can describe the next step two ways. `details` is a list
   of labelled facts and wins, because a candidate scanning for a time or a
   gate-closing deadline should not have to read a paragraph to find it.
   `note` is the older free-prose form and stays as the fallback. */
function nextBlock(steps, note, details){
  if (details && details.length)
    return `<div class="next"><h4>${esc(t("whatNext"))}</h4>${detailRows(details)}</div>`;
  if (note) return `<div class="next"><h4>${esc(t("whatNext"))}</h4><p>${esc(note)}</p></div>`;
  if (!steps || !steps.length) return "";
  return `<div class="next"><h4>${esc(t("whatNext"))}</h4><ol>${
    steps.map(s => `<li>${esc(s)}</li>`).join("")}</ol></div>`;
}

/* 7.8 — share. The page already restores #roll=NNN on load, so the link is
   just this page plus the roll; no new routing. navigator.share exists on
   nearly every Android browser, and app.js falls back to the clipboard. */
function shareBtn(roll){
  return `<button type="button" class="btn" data-share="${esc(roll)}">${esc(t("share"))}</button>`;
}

/* ---------------------------------------------------------------- cards */
function seatCard(n, c, roll, pref){
  const from = n.examWindow?.[0], to = n.examWindow?.[1];
  const rep = from ? clock(minus60(from)) : null;
  const q = c.mapQuery || `${c.name}, ${c.address}`;
  const st = statusOf(n);
  return `<div class="card${pref ? " preferred" : ""}">
    <div class="kicker">
      <span class="badge ${KIND.seat.cls}">${esc(kindLabel("seat"))}</span>
      <span class="badge ${st.cls}">${esc(st.lbl)}</span>
    </div>
    ${identBlock(n, null, { preferred: pref })}
    ${countdown(n.examDateISO, from ? clockRange(from, to) : null, rep)}
    <div class="panel info">
      <div class="eyebrow">${esc(t("yourCentre"))}</div>
      <div class="big">${esc(c.name)}</div>
      <div class="refline">${esc(c.address || "")}${c.address ? " · " : ""}${esc(t("seatRange"))} ${esc(NUM(c.from))}–${esc(NUM(c.to))}</div>
    </div>
    <div class="grid">
      <div class="cell"><div class="k">${esc(t("examDate"))}</div><div class="v">${esc(dnum(n.examDate) || "—")}</div></div>
      <div class="cell"><div class="k">${esc(t("time"))}</div><div class="v acc">${esc(from ? clockRange(from, to) : "—")}</div></div>
      ${rep ? `<div class="cell"><div class="k">${esc(t("beThere"))}</div><div class="v warn">${esc(rep)}</div></div>` : ""}
      <div class="cell"><div class="k">${esc(t("yourRoll"))}</div><div class="v">${esc(NUM(roll))}</div></div>
    </div>
    ${nextBlock(t("nextSeat"), null)}
    <div class="actions">
      <a class="btn primary" target="_blank" rel="noopener noreferrer" href="${mapsUrl(q)}">${esc(t("openMaps"))}</a>
      <button type="button" class="btn" data-map="1" aria-expanded="false" aria-controls="map-${esc(n.id)}">${esc(t("showMap"))}</button>
      <a class="btn" ${pdfAttrs(n.pdf)} target="_blank" rel="noopener noreferrer">${esc(t("officialPdf"))}</a>
      ${shareBtn(roll)}
    </div>
    <div class="mapbox" id="map-${esc(n.id)}" role="region" aria-label="${esc(t("yourCentre"))}"><iframe loading="lazy" title="${esc(t("yourCentre"))}"
      data-src="https://maps.google.com/maps?q=${encodeURIComponent(q)}&z=15&output=embed"></iframe></div>
  </div>`;
}

function sittingCard(n, info, roll, pref){
  const st = statusOf(n);
  const q = n.venueMapQuery || n.venue;
  return `<div class="card${pref ? " preferred" : ""}">
    <div class="kicker">
      <span class="badge ${(KIND[n.kind]||KIND.viva).cls}">${esc(kindLabel(n.kind))}</span>
      <span class="badge ${st.cls}">${esc(st.lbl)}</span>
      ${info.b ? `<span class="badge sm">${esc(t("batch"))} ${esc(dnum(info.b))}</span>` : ""}
    </div>
    ${identBlock(n, null, { preferred: pref })}
    ${countdown(toISO(info.d), clock(info.t), null)}
    <div class="panel info">
      <div class="eyebrow">${esc(t("yourSitting"))}</div>
      <div class="big">${esc(dnum(info.d) || "—")}${info.t ? ` · ${esc(clock(info.t))}` : ""}</div>
      ${n.venue ? `<div class="refline">${esc(n.venue)}</div>` : ""}
    </div>
    <div class="grid">
      <div class="cell"><div class="k">${esc(t("date"))}</div><div class="v">${esc(dnum(info.d) || "—")}</div></div>
      <div class="cell"><div class="k">${esc(t("reportingTime"))}</div><div class="v acc">${esc(clock(info.t) || "—")}</div></div>
      <div class="cell"><div class="k">${esc(t("yourRoll"))}</div><div class="v">${esc(NUM(roll))}</div></div>
    </div>
    ${nextBlock(t("nextViva"), null)}
    <div class="actions">
      ${q ? `<a class="btn primary" target="_blank" rel="noopener noreferrer" href="${mapsUrl(q)}">${esc(t("openMaps"))}</a>` : ""}
      <a class="btn" ${pdfAttrs(n.pdf)} target="_blank" rel="noopener noreferrer">${esc(t("officialPdf"))}</a>
      ${shareBtn(roll)}
    </div>
  </div>`;
}

function selectedCard(n, roll, pref){
  const group = (n.groups || []).find(g => g.rolls.includes(roll)) || null;
  const o = outcomeOf(n);
  const note = LANG === "bn" ? (n.noteBn || n.note) : (n.note || n.noteBn);
  const details = LANG === "bn" ? (n.detailsBn || n.details) : (n.details || n.detailsBn);
  const st = statusOf(n);
  return `<div class="card${pref ? " preferred" : ""}">
    <div class="kicker">
      <span class="badge ${KIND.selected.cls}">${esc(kindLabel("selected"))}</span>
      <span class="badge ${st.cls}">${esc(st.lbl)}</span>
    </div>
    ${identBlock(n, group, { preferred: pref })}
    <div class="panel ${o.tone}">
      <div class="eyebrow">${esc(kindLabel("selected"))}</div>
      <div class="big">${esc(o.title)}</div>
      <div class="refline">${esc(t("selectedRef"))}<b>${esc(NUM(roll))}</b></div>
    </div>
    ${nextBlock(o.steps, note, details)}
    ${lowConfBlock(n, roll)}
    ${provenance(n)}
    <div class="actions">
      <a class="btn primary" ${pdfAttrs(n.pdf)} target="_blank" rel="noopener noreferrer">${esc(t("openPdf"))}</a>
      ${shareBtn(roll)}
    </div>
  </div>`;
}
