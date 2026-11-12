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
  /* "//evil.example/x.pdf" carries no scheme, so the check below waves it
     through — but a browser reads it as protocol-relative and goes off-origin
     on the current protocol. Every legitimate link here is either a relative
     notices/ path or an explicit https:// URL, so this costs nothing. */
  if (s.indexOf("//") === 0) return "";
  const scheme = /^([a-z][a-z0-9+.\-]*):/i.exec(s);        // relative paths have none
  if (scheme && !/^https?$/i.test(scheme[1])) return "";   // javascript:, data:, vbscript:
  return esc(s);
};

/* print.css prints the official-PDF link as its URL so a printed card is
   still traceable back to the notice. CSS attr() can only read what is
   literally in the attribute, and that is a relative "notices/..." path —
   useless on paper. Resolving it here rather than in a beforeprint handler
   keeps it correct when the page is rendered to PDF programmatically, which
   never fires that event. */
const pdfAttrs = u => {
  const h = safeHref(u);
  if (!h) return "";
  let abs = h;
  try { abs = new URL(String(u), location.href).href; } catch(e){}
  return `href="${h}" data-abs="${esc(abs)}"`;
};
