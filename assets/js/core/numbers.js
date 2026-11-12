/* numbers.js
 * Digit systems. The UI and the source PDFs both use Bengali numerals, so
 * every number crossing into or out of the interface passes through here.
 */
const BN = s => String(s).replace(/[0-9]/g, d => "০১২৩৪৫৬৭৮৯"[d]);

/* Bengali (and Arabic-Indic) numerals -> ASCII. The UI prints numbers in
   Bengali and the source PDFs do too, so a candidate copying their roll off
   this page or off the notice types ০-৯. Without this the \D strip below
   wipes the whole string and the search silently returns nothing. */
const AS = s => String(s)
  .replace(/[\u09E6-\u09EF]/g, d => d.charCodeAt(0) - 0x09E6)   // ০-৯
  .replace(/[\u0660-\u0669]/g, d => d.charCodeAt(0) - 0x0660)   // ٠-٩
  .replace(/[\uFF10-\uFF19]/g, d => d.charCodeAt(0) - 0xFF10);  // full-width

/* Clock times arrive as "10:00 AM" / "1:30 PM". In Bengali that reads like a
   machine export; people say the part of the day first — সকাল ১০:০০,
   দুপুর ১:৩০, বিকাল ৩:৩০ — and use Bengali digits. English is left alone.

   A time that does not match the expected shape — "10.00 AM", "১০টা",
   "10:00 - 11:00" — used to fall through completely and print ASCII digits in
   the middle of a Bengali card. BN() over the result fixes that: it only
   touches 0-9, so digits the replacer already localised are left alone. */
const clock = s => {
  if (!s || LANG !== "bn") return s;
  const out = String(s).replace(/(\d{1,2}):(\d{2})\s*(AM|PM)/gi, (_, h, m, ap) => {
    let hh = +h % 12; if (/pm/i.test(ap)) hh += 12;
    /* বিকেল, not বিকাল — both papers use the চলিত spelling. ভোর is a real
       part of the day here; candidates queue from before dawn. The 3 PM
       boundary is set by the notices themselves: BB writes "দুপুর ২.৩০টা"
       but "বিকাল ৩.০০টা", so বিকেল starts at 15:00, not 16:00. */
    const part = hh >= 4 && hh < 6 ? "ভোর" : hh >= 6 && hh < 12 ? "সকাল"
               : hh >= 12 && hh < 15 ? "দুপুর" : hh >= 15 && hh < 18 ? "বিকেল"
               : hh >= 18 && hh < 20 ? "সন্ধ্যা" : "রাত";
    /* A clock face is spoken, not punctuated: সকাল ১০টা, never সকাল ১০:০০.
       Half past has its own words for one and two o'clock — দেড়টা and
       আড়াইটা. "সাড়ে ১টা" is not something anyone says or prints. */
    const h12 = +h, mm = +m;
    const face = mm === 0  ? `${BN(h12)}টা`
               : mm === 30 ? (h12 === 1 ? "দেড়টা" : h12 === 2 ? "আড়াইটা" : `সাড়ে ${BN(h12)}টা`)
               :             `${BN(h12)}টা ${BN(mm)} মিনিট`;
    return `${part} ${face}`;
  });
  return BN(out);
};

/* Bengali genitive on a clock face. "দুপুর ২টা" -> "দুপুর ২টার"; a
   consonant-final one like "৯টা ২০ মিনিট" -> "...মিনিটের". Hyphenating the
   case ending on ("২টা-এর") is a transliteration habit — it reads as though
   the sentence were assembled rather than written. */
const ofTime = s => {
  if (!s || LANG !== "bn") return s;
  return /[\u09BE\u09BF\u09C0-\u09C4\u09C7\u09C8\u09CB\u09CC\u0985-\u0994]$/.test(s) ? s + "র" : s + "ের";
};

/* "সকাল ১০:০০ – সকাল ১১:০০" -> "সকাল ১০:০০ – ১১:০০": say the part of the day once. */
const clockRange = (a, b) => {
  if (LANG !== "bn") return `${a} – ${b}`;
  const x = clock(a), y = clock(b), px = x.split(" ")[0];
  return `${x} – ${y.startsWith(px + " ") ? y.slice(px.length + 1) : y}`;
};
