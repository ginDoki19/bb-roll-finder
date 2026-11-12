/* dates.js
 * Exam-date parsing, relative-day status and the countdown wording.
 */
/* ---------------------------------------------------------------- dates */
const TODAY = (() => { const d = new Date(); d.setHours(0,0,0,0); return d; })();
const toISO = s => {
  const m = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(String(s ?? "").trim());
  return m ? `${m[3]}-${m[2].padStart(2,"0")}-${m[1].padStart(2,"0")}` : null;
};
/* Both sides of the subtraction are UTC midnights. Doing it with local Date
   objects meant the gap between two calendar days was 23 or 25 hours across a
   DST change, and Math.round could then land a day out — "exam tomorrow" on
   the morning of the exam. Bangladesh keeps no DST, so this only ever bit a
   candidate checking from abroad, but the UTC form is correct everywhere and
   costs nothing. The epoch-day helper keeps TODAY a Date for anything that
   still wants one. */
const EPOCH_DAY = dt => Math.floor(Date.UTC(dt.getFullYear(), dt.getMonth(), dt.getDate()) / 86400000);
const TODAY_DAY = EPOCH_DAY(TODAY);
function dayDiff(iso){
  if (!iso) return null;
  const [y,m,d] = String(iso).split("-").map(Number);
  if (!y || !m || !d) return null;
  return Math.floor(Date.UTC(y, m-1, d) / 86400000) - TODAY_DAY;
}
/* The footer used to print DATA.generated raw, which in Bengali rendered as
   ২০২৬-১১-১২T০৩:২৪:৫৪Z — a machine stamp with a stray T and Z in the middle
   of a sentence. Only the day matters to a reader. */
const MONTHS = {
  en:["January","February","March","April","May","June","July","August","September","October","November","December"],
  bn:["জানুয়ারি","ফেব্রুয়ারি","মার্চ","এপ্রিল","মে","জুন","জুলাই","আগস্ট","সেপ্টেম্বর","অক্টোবর","নভেম্বর","ডিসেম্বর"]
};
const fmtDay = iso => {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso ?? ""));
  if (!m) return dnum(iso);
  const names = MONTHS[LANG] || MONTHS.en;
  return `${NUM(+m[3])} ${names[+m[2] - 1]} ${NUM(m[1])}`;
};
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
/* ১৬/১১/২০২৬ in the middle of a Bengali card is the loudest possible signal
   that no one wrote it: the papers always spell the month — "১৬ নভেম্বর
   ২০২৬". English keeps the numeric form, which is the ordinary convention
   there. Anything that is not a date (357/2026, a batch number) falls
   through to dnum untouched, which is why this is separate from it. */
const fmtDate = s => {
  if (LANG !== "bn") return dnum(s);
  const iso = toISO(s);
  return iso ? fmtDay(iso) : dnum(s);
};
