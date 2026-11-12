/* notices.js
 * The notice dataset and the lookup structures derived from it.
 *
 * DATA is substituted at build time by parser/build_site.py — the JSON is
 * inlined rather than fetched so the page works from file://, offline, and
 * inside sandboxed previews.
 *
 * This file does real work at load time (it decodes the delta-encoded sittings
 * into Maps), so it must be concatenated before anything that reads `notices`
 * outside a function body.
 */
/* data is inlined at build time by parser/build_site.py so the page works
   from file://, from a phone with no signal, and inside sandboxed previews */
const DATA = /*__DATA__*/;

/* ---------------------------------------------------------------- index */
const notices = DATA.notices.slice();
const scannedCount = notices.filter(n => n.kind === "scanned").length;
notices.forEach(n => {
  if (n.rolls) n._set = new Set(n.rolls.map(String));
  if (n.centres) n.centres.sort((a, b) => a.from - b.from);
  /* Sittings arrive delta-encoded: r = [first, gap, gap, ...]. Undo the deltas
     and build one Map for O(1) roll lookup. Done once at load; for the whole
     dataset this is well under a millisecond, and it keeps the shipped JSON
     5.6x smaller than storing a record per roll. */
  if (n.sittings){
    n._rolls = new Map();
    n._count = 0;
    for (const s of n.sittings){
      let acc = 0;
      for (const d of s.r){ acc += d; n._rolls.set(acc, s); n._count++; }
    }
  }
});
const searchable = notices.filter(n => n.centres || n.sittings || n.rolls);

function findCentre(n, roll){
  const v = n.centres;
  let lo = 0, hi = v.length - 1;
  while (lo <= hi){
    const mid = (lo + hi) >> 1, c = v[mid];
    if (roll < c.from) hi = mid - 1;
    else if (roll > c.to) lo = mid + 1;
    else return c;
  }
  return null;
}
/* "3:00 PM" minus 60 minutes -> "2:00 PM" */
function minus60(label){
  const m = /^(\d{1,2}):(\d{2})\s*(AM|PM)$/i.exec(label || "");
  if (!m) return null;
  let h = parseInt(m[1], 10) % 12 + (m[3].toUpperCase() === "PM" ? 12 : 0);
  let x = (h * 60 + parseInt(m[2], 10) - 60 + 1440) % 1440;
  const hh = Math.floor(x / 60), mm = String(x % 60).padStart(2, "0");
  return `${(hh % 12) || 12}:${mm} ${hh < 12 ? "AM" : "PM"}`;
}
