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
    <div class="jobtag"><span class="k">${esc(t("job"))}</span><span class="v">${esc(JOB(n.jobId))}</span></div>
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
    return `<div class="prov">${t("ocrProv")(tot)}<a href="${safeHref(n.pdf)}" target="_blank" rel="noopener noreferrer">${esc(t("confirmPdf"))}</a>.</div>`;
  }
  if (n.rollSource === "manual"){
    return `<div class="prov">${t("manualProv")}<a href="${safeHref(n.pdf)}" target="_blank" rel="noopener noreferrer">${esc(t("confirmPdf"))}</a>.</div>`;
  }
  return "";
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
function nextBlock(steps, note){
  if (note) return `<div class="next"><h4>${esc(t("whatNext"))}</h4><p>${esc(note)}</p></div>`;
  if (!steps || !steps.length) return "";
  return `<div class="next"><h4>${esc(t("whatNext"))}</h4><ol>${
    steps.map(s => `<li>${esc(s)}</li>`).join("")}</ol></div>`;
}

/* ---------------------------------------------------------------- cards */
function seatCard(n, c, roll, pref){
  const from = n.examWindow?.[0], to = n.examWindow?.[1];
  const rep = from ? minus60(from) : null;
  const q = c.mapQuery || `${c.name}, ${c.address}`;
  const st = statusOf(n);
  return `<div class="card${pref ? " preferred" : ""}">
    <div class="kicker">
      <span class="badge ${KIND.seat.cls}">${esc(kindLabel("seat"))}</span>
      <span class="badge ${st.cls}">${esc(st.lbl)}</span>
    </div>
    ${identBlock(n, null, { preferred: pref })}
    ${countdown(n.examDateISO, from ? `${from} – ${to}` : null, rep)}
    <div class="panel info">
      <div class="eyebrow">${esc(t("yourCentre"))}</div>
      <div class="big">${esc(c.name)}</div>
      <div class="refline">${esc(c.address || "")}${c.address ? " · " : ""}${esc(t("seatRange"))} ${esc(NUM(c.from))}–${esc(NUM(c.to))}</div>
    </div>
    <div class="grid">
      <div class="cell"><div class="k">${esc(t("examDate"))}</div><div class="v">${esc(dnum(n.examDate) || "—")}</div></div>
      <div class="cell"><div class="k">${esc(t("time"))}</div><div class="v acc">${esc(from ? `${from} – ${to}` : "—")}</div></div>
      ${rep ? `<div class="cell"><div class="k">${esc(t("beThere"))}</div><div class="v warn">${esc(rep)}</div></div>` : ""}
      <div class="cell"><div class="k">${esc(t("yourRoll"))}</div><div class="v">${esc(NUM(roll))}</div></div>
    </div>
    ${nextBlock(t("nextSeat"), null)}
    <div class="actions">
      <a class="btn primary" target="_blank" rel="noopener noreferrer" href="${mapsUrl(q)}">${esc(t("openMaps"))}</a>
      <button type="button" class="btn" data-map="1">${esc(t("showMap"))}</button>
      <a class="btn" href="${safeHref(n.pdf)}" target="_blank" rel="noopener noreferrer">${esc(t("officialPdf"))}</a>
    </div>
    <div class="mapbox"><iframe loading="lazy" title="map"
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
    ${countdown(toISO(info.d), info.t, null)}
    <div class="panel info">
      <div class="eyebrow">${esc(t("reportingTime"))}</div>
      <div class="big">${esc(dnum(info.d) || "—")}${info.t ? ` · ${esc(info.t)}` : ""}</div>
      ${n.venue ? `<div class="refline">${esc(n.venue)}</div>` : ""}
    </div>
    <div class="grid">
      <div class="cell"><div class="k">${esc(t("date"))}</div><div class="v">${esc(dnum(info.d) || "—")}</div></div>
      <div class="cell"><div class="k">${esc(t("reportingTime"))}</div><div class="v acc">${esc(info.t || "—")}</div></div>
      <div class="cell"><div class="k">${esc(t("yourRoll"))}</div><div class="v">${esc(NUM(roll))}</div></div>
    </div>
    ${nextBlock(t("nextViva"), null)}
    <div class="actions">
      ${q ? `<a class="btn primary" target="_blank" rel="noopener noreferrer" href="${mapsUrl(q)}">${esc(t("openMaps"))}</a>` : ""}
      <a class="btn" href="${safeHref(n.pdf)}" target="_blank" rel="noopener noreferrer">${esc(t("officialPdf"))}</a>
    </div>
  </div>`;
}

function selectedCard(n, roll, pref){
  const group = (n.groups || []).find(g => g.rolls.includes(roll)) || null;
  const o = outcomeOf(n);
  const note = LANG === "bn" ? (n.noteBn || n.note) : (n.note || n.noteBn);
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
    ${nextBlock(o.steps, note)}
    ${provenance(n)}
    <div class="actions"><a class="btn primary" href="${safeHref(n.pdf)}" target="_blank" rel="noopener noreferrer">${esc(t("openPdf"))}</a></div>
  </div>`;
}
