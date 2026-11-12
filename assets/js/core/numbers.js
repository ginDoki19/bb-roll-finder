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
   দুপুর ১:৩০, বিকাল ৩:৩০ — and use Bengali digits. English is left alone. */
const clock = s => {
  if (!s || LANG !== "bn") return s;
  return String(s).replace(/(\d{1,2}):(\d{2})\s*(AM|PM)/gi, (_, h, m, ap) => {
    let hh = +h % 12; if (/pm/i.test(ap)) hh += 12;
    const part = hh >= 5 && hh < 12 ? "সকাল" : hh >= 12 && hh < 16 ? "দুপুর"
               : hh >= 16 && hh < 18 ? "বিকাল" : hh >= 18 && hh < 20 ? "সন্ধ্যা" : "রাত";
    return `${part} ${BN(+h)}:${BN(m)}`;
  });
};

/* "সকাল ১০:০০ – সকাল ১১:০০" -> "সকাল ১০:০০ – ১১:০০": say the part of the day once. */
const clockRange = (a, b) => {
  if (LANG !== "bn") return `${a} – ${b}`;
  const x = clock(a), y = clock(b), px = x.split(" ")[0];
  return `${x} – ${y.startsWith(px + " ") ? y.slice(px.length + 1) : y}`;
};
