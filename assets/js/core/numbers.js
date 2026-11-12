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
