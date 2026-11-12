/* dom.js
 * The two primitives every render path uses: an element lookup and the HTML
 * escaper. esc() handles & < > " — it is applied to every interpolated value
 * that reaches innerHTML.
 */
const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

/* esc() makes a value safe as *text*, but not as a URL: it leaves
   "javascript:..." intact, and escaping does nothing to stop a browser
   running it when the value lands in href. Every PDF link on this page
   interpolates a path that came out of data/notices.json, so the scheme is
   checked before the value is allowed to become a link.

   All 13 current notices use relative "notices/..." paths, so nothing is
   exploitable today — this closes the hole before a future notice, an
   override file or a hand-edited JSON opens it.

   Returns "" for anything rejected, which is what esc() already produced for
   a missing pdf, so the rendered markup is unchanged for existing data. */
const safeHref = u => {
  const s = String(u ?? "").trim();
  if (!s) return "";
  if (/[\u0000-\u001f\u007f]/.test(s)) return "";          // smuggled control chars
  const scheme = /^([a-z][a-z0-9+.\-]*):/i.exec(s);        // relative paths have none
  if (scheme && !/^https?$/i.test(scheme[1])) return "";   // javascript:, data:, vbscript:
  return esc(s);
};
