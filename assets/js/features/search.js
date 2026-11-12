/* search.js
 * Roll lookup: collecting hits across every notice, ranking the preferred job
 * first, and rendering the result area.
 *
 * A roll number is only unique within a job, so a search can legitimately
 * match more than one notice; that ambiguity is surfaced, never guessed at.
 */
/* --------------------------------------------------------------- search */
let prefJob = (() => { try { return localStorage.getItem("bb-job") || ""; } catch(e){ return ""; } })();
let lastHits = [];

function collectHits(roll, raw){
  const hits = [];
  for (const n of notices){
    if (n.centres){
      const c = findCentre(n, roll);
      if (c) hits.push({ n, job:String(n.jobId || ""), html:() => seatCard(n, c, raw, isPref(n)) });
    }
    if (n._rolls && n._rolls.has(roll)){
      const s = n._rolls.get(roll);
      hits.push({ n, job:String(n.jobId || ""), html:() => sittingCard(n, { d:s.date, t:s.time, b:s.sl }, raw, isPref(n)) });
    }
    if (n._set && n._set.has(String(roll))){
      hits.push({ n, job:String(n.jobId || ""), html:() => selectedCard(n, roll, isPref(n)) });
    }
  }
  return hits;
}
const isPref = n => !!prefJob && String(n.jobId || "") === prefJob;

/* Announce an outcome once. #result deliberately is not a live region: it can
   hold several full cards, and with aria-live on it a screen reader re-read
   every card on every keystroke. Writing only when the sentence actually
   changes also stops repeat announcements when a keystroke does not change
   the outcome. */
let lastSaid = "";
function say(msg){
  const el = $("#srstatus");
  if (!el || msg === lastSaid) return;
  lastSaid = msg;
  el.textContent = msg;
}

function renderResult(){
  const raw = AS($("#roll").value).replace(/\D/g, "");
  const box = $("#result"), dis = $("#disambig");
  if (!raw){ box.innerHTML = ""; dis.innerHTML = ""; lastHits = []; say(""); return; }

  if (raw.length < 3){
    dis.innerHTML = "";
    box.innerHTML = `<div class="card bad"><div class="meta" style="margin:0">${esc(t("tooShort")(NUM(raw)))}</div></div>`;
    say(t("tooShort")(NUM(raw)));
    return;
  }
  const roll = parseInt(raw, 10);
  lastHits = collectHits(roll, raw);

  if (!lastHits.length){
    dis.innerHTML = "";
    const cover = searchable.map(n => {
      const p = postOf(n);
      const kind = (KIND[n.kind] || {}).en || n.kind;
      return `<li>${esc(t("job"))} ${esc(JOB_LABEL(n.jobId))} — ${esc(p ? `${p} · ${kind}` : kind)}</li>`;
    }).join("");
    box.innerHTML = `<div class="card bad">
      <p class="post" style="margin-bottom:8px">${esc(t("notFoundTitle")(NUM(raw)))}</p>
      <div class="meta">${esc(t("notFoundBody")(NUM(searchable.length)))}</div>
      <div class="meta" style="margin-bottom:6px"><b>${esc(t("notFoundList"))}</b></div>
      <ul style="color:var(--text-secondary);font-size:13px;margin:0 0 0 18px;padding:0">${cover}</ul>
      <div class="actions"><a class="btn" href="${safeHref(DATA.source)}" target="_blank" rel="noopener noreferrer">${esc(t("checkPortal"))}</a></div>
    </div>`;
    say(t("notFoundTitle")(NUM(raw)));
    return;
  }
  paintHits(raw);
}

function paintHits(raw){
  const dis = $("#disambig"), box = $("#result");
  const jobs = [...new Set(lastHits.map(h => h.job))].filter(Boolean);

  /* The core fix: one roll can legitimately belong to two unrelated jobs,
     so when that happens we say so and let the candidate choose. */
  if (jobs.length > 1){
    const opts = jobs.map(j => {
      const n = lastHits.find(h => h.job === j).n;
      const p = postOf(n);
      return `<button type="button" data-job="${esc(j)}" aria-pressed="${prefJob === j}"${jobAttr(j)}>
        <b>${esc(t("job"))} ${esc(JOB_LABEL(j))}</b><span>${esc(p || (KIND[n.kind]||{}).en || n.kind)}</span></button>`;
    }).join("");
    dis.innerHTML = `<div class="disambig">
      <p>${esc(t("disambigQ")(NUM(raw), NUM(jobs.length)))}</p>
      <p class="why">${esc(t("disambigWhy"))}</p>
      <div class="jobpick">${opts}
        <button type="button" data-job="" aria-pressed="${!prefJob}">${esc(t("showAll"))}</button></div>
    </div>`;
  } else dis.innerHTML = "";

  /* A remembered job floats to the top but nothing is ever hidden. */
  const ordered = lastHits.slice().sort((a, b) =>
    (isPref(b.n) ? 1 : 0) - (isPref(a.n) ? 1 : 0));
  box.innerHTML = ordered.map(h => h.html()).join("");

  say(jobs.length > 1
    ? t("srAmbig")(NUM(ordered.length), NUM(raw), NUM(jobs.length))
    : t("srFound")(NUM(ordered.length), NUM(raw)));
}
