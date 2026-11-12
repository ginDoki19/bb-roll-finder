/* dates.js
 * Exam-date parsing, relative-day status and the countdown wording.
 */
/* ---------------------------------------------------------------- dates */
const TODAY = (() => { const d = new Date(); d.setHours(0,0,0,0); return d; })();
const toISO = s => {
  const m = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(String(s ?? "").trim());
  return m ? `${m[3]}-${m[2].padStart(2,"0")}-${m[1].padStart(2,"0")}` : null;
};
function dayDiff(iso){
  if (!iso) return null;
  const [y,m,d] = iso.split("-").map(Number);
  const t = new Date(y, m-1, d); t.setHours(0,0,0,0);
  return Math.round((t - TODAY) / 86400000);
}
function statusOf(n){
  const e = dayDiff(n.examDateISO), c = dayDiff(n.closingISO);
  if (e === 0)                       return { k:"today", cls:"s-today", lbl:t("examToday") };
  if (e !== null && e > 0 && e <= 7) return { k:"soon",  cls:"s-soon",  lbl:t("daysLeft")(NUM(e)) };
  if (e !== null && e > 7)           return { k:"up",    cls:"s-up",    lbl:t("upcoming") };
  if (c !== null && c < 0)           return { k:"past",  cls:"s-past",  lbl:t("completed") };
  if (e !== null && e < 0)           return { k:"past",  cls:"s-past",  lbl:t("completed") };
  return { k:"open", cls:"s-up", lbl:t("ongoing") };
}
function countdown(iso, timeLabel, reportBy){
  const d = dayDiff(iso);
  if (d === null) return "";
  let head, cls;
  if (d === 0)               { head = t("cdToday");          cls = "cd-today"; }
  else if (d === 1)          { head = t("cdTomorrow");       cls = "cd-soon";  }
  else if (d > 1 && d <= 21) { head = t("cdDays")(NUM(d));   cls = "cd-soon";  }
  else if (d < 0)            { head = t("cdPast")(NUM(-d));  cls = "cd-past";  }
  else return "";
  const bits = [];
  if (timeLabel) bits.push(timeLabel);
  if (reportBy)  bits.push(t("beThereBy")(reportBy));
  return `<div class="cd ${cls}"><b>${esc(head)}</b><span>${esc(bits.join(" · "))}</span></div>`;
}
const dnum = s => NUM(String(s ?? ""));
