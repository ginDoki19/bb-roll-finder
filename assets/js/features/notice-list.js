/* notice-list.js
 * The archive below the search: every notice as a card, with the kind filter.
 */
/* ------------------------------------------------------- notice archive */
let filter = "all";

function noticeCard(n){
  const k = KIND[n.kind] || KIND.circular;
  const st = statusOf(n);
  const post = postOf(n);
  let detail = "";

  if (n.centres){
    detail = `<details><summary>${esc(t("nCentres")(NUM(n.centres.length), NUM(n.rollFrom), NUM(n.rollTo)))}</summary>
      <div class="tscroll"><table><thead><tr><th>#</th><th>${esc(t("centre"))}</th><th>${esc(t("rolls"))}</th><th>${esc(t("seats"))}</th></tr></thead><tbody>
      ${n.centres.map(c => `<tr><td class="num">${esc(NUM(c.sl ?? ""))}</td>
        <td>${esc(c.name)}<div style="color:var(--text-muted);font-size:11.5px">${esc(c.address || "")}</div></td>
        <td class="num">${esc(NUM(c.from))}–${esc(NUM(c.to))}</td>
        <td class="num">${c.seats ? esc(NUM(c.seats.toLocaleString("en-US"))) : "—"}</td></tr>`).join("")}
      </tbody></table></div></details>`;
  } else if (n.sittings){
    detail = `<details><summary>${esc(t("nSittings")(NUM(n.sittings.length), NUM(n._count || 0)))}</summary>
      <div class="tscroll"><table><thead><tr><th>${esc(t("batch"))}</th><th>${esc(t("date"))}</th><th>${esc(t("time"))}</th><th>${esc(t("rolls"))}</th></tr></thead><tbody>
      ${n.sittings.map(b => `<tr><td class="num">${esc(NUM(b.sl))}</td><td>${esc(fmtDate(b.date) || "—")}</td>
        <td>${esc(clock(b.time) || "—")}</td><td class="num">${esc(NUM(b.count))}</td></tr>`).join("")}
      </tbody></table></div></details>`;
  } else if (n.kind === "scanned"){
    detail = `<div class="scanwarn">${t("scannedWarn")}<a ${pdfAttrs(n.pdf)} target="_blank" rel="noopener noreferrer">${esc(t("openPdfCheck"))}</a></div>`;
  } else if (n.groups && n.groups.length){
    const multi = n.groups.length > 1;
    detail = `<details><summary>${esc(multi
        ? t("nRollsIn")(NUM(n.rolls.length), NUM(n.groups.length))
        : t("nRolls")(NUM(n.rolls.length)))}</summary>
      ${n.groups.map(g => `${multi ? `<div class="grouphead">${esc(g.post || "—")}</div>` : ""}
        ${rollWrapHtml(g.rolls, null)}`).join("")}
      ${provenance(n)}</details>`;
  } else if (n.rolls && n.rolls.length){
    /* Previously truncated at an arbitrary 60 with a "…" — the full list is
       here now, wrapped and scrolled inside its own box. */
    detail = `<details><summary>${esc(t("nRolls")(NUM(n.rolls.length)))}</summary>
      ${rollWrapHtml(n.rolls, null)}${provenance(n)}</details>`;
  }

  return `<div class="ncard${st.k === "past" ? " past" : ""}">
    <div class="nhead">
      <span class="badge ${k.cls}">${esc(kindLabel(n.kind))}</span>
      <span class="badge ${st.cls}">${esc(st.lbl)}</span>
      <span class="badge sm"${jobAttr(n.jobId)}>${esc(t("job"))} ${esc(JOB_LABEL(n.jobId))}</span>
    </div>
    <p class="npost">${esc(post || t("multiPost"))}</p>
    <p class="ntitle">${esc(n.title)}</p>
    <div class="nmeta">
      ${/* 4 of 13 notices carry no published notice number — the portal lists only
           a Job ID for them. Printing "notice —" invented a field that does not
           exist, so the row is simply dropped instead. */""}
      ${n.noticeNo ? `<span>${esc(t("notice"))} ${esc(dnum(n.noticeNo))}</span>` : ""}
      ${n.published ? `<span>${esc(t("published"))} ${esc(fmtDate(n.published))}</span>` : ""}
      ${n.examDate ? `<span>${esc(t("exam"))} ${esc(fmtDate(n.examDate))}</span>` : ""}
      <a ${pdfAttrs(n.pdf)} target="_blank" rel="noopener noreferrer">${esc(t("officialPdf"))}${n.sizeKB ? ` · ${esc(NUM(n.sizeKB))} KB` : ""}</a>
      ${n.pages ? `<span>${esc(t("pages")(NUM(n.pages)))}</span>` : ""}
    </div>
    ${detail}
  </div>`;
}

function renderNotices(){
  const kinds = ["all", ...new Set(notices.map(n => n.kind))];
  $("#filters").innerHTML = kinds.map(k => {
    const lbl = k === "all"
      ? `${t("all")} ${NUM(notices.length)}`
      : `${kindLabel(k)} ${NUM(notices.filter(n => n.kind === k).length)}`;
    return `<button type="button" class="chip${k === filter ? " on" : ""}" data-f="${esc(k)}" aria-pressed="${k === filter}">${esc(lbl)}</button>`;
  }).join("");

  const shown = notices.filter(n => filter === "all" || n.kind === filter);
  const live = shown.filter(n => statusOf(n).k !== "past");
  const past = shown.filter(n => statusOf(n).k === "past");
  const order = { today:0, soon:1, up:2, open:3 };
  live.sort((a, b) => order[statusOf(a).k] - order[statusOf(b).k]);

  /* Archived notices stay fully searchable — they are only collapsed out of
     the way. People look backwards during appeals and document checks. */
  $("#notices").innerHTML = live.map(noticeCard).join("")
    + (past.length ? `<details class="arch"><summary>${esc(t("pastNotices")(NUM(past.length)))}</summary>${
        past.map(noticeCard).join("")}</details>` : "");
}
