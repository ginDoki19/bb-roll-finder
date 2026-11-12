#!/usr/bin/env python3
"""
uitest.py — browser regression tests for the generated index.html.

selftest.py checks the data and greps the template; this drives a real browser
against the built page, because the things most likely to break in a refactor
(language defaults, persisted preferences, escaping, offline) cannot be proven
by reading source.

    python3 tools/uitest.py

Serves the repo on an ephemeral port, runs the checks headless, shuts the
server down. Requires playwright (already required by tools/test_fetch.py).
Exit code 0 = all pass, 1 = at least one failure.
"""

from __future__ import annotations

import datetime
import functools
import http.server
import os
import socketserver
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("playwright is not installed — pip install playwright && python3 -m playwright install chromium")


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):            # keep the test output readable
        pass


class Results:
    def __init__(self):
        self.failed = []
        self.count = 0

    def check(self, name, ok, detail=""):
        self.count += 1
        print(("  PASS  " if ok else "  FAIL  ") + name + ("" if ok else f"   <<< {detail}"))
        if not ok:
            self.failed.append(name)

    def section(self, title):
        print(f"\n— {title} —")


def main() -> int:
    index = os.path.join(ROOT, "index.html")
    if not os.path.exists(index):
        sys.exit("index.html not found — run parser/build_site.py first")

    handler = functools.partial(_Quiet, directory=ROOT)
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    URL = f"http://127.0.0.1:{port}/index.html"
    FILE_URL = "file://" + index

    r = Results()
    today = datetime.date.today()

    with sync_playwright() as p:
        browser = p.chromium.launch()

        def fresh(**kw):
            """A clean profile — no saved theme or language preference."""
            ctx = browser.new_context(**kw)
            pg = ctx.new_page()
            pg.goto(URL, wait_until="networkidle")
            return ctx, pg

        # ---------------------------------------------------------- language
        r.section("1-5  language defaults and the fixed English identifier")

        ctx, pg = fresh()
        r.check("first visit defaults to English",
                pg.evaluate("document.documentElement.lang") == "en",
                pg.evaluate("document.documentElement.lang"))
        # inner_text reflects CSS text-transform, so compare case-insensitively
        r.check("first visit shows English copy",
                "all notices" in pg.inner_text("body").lower())
        r.check("no language preference written just by visiting",
                pg.evaluate("localStorage.getItem('bb-lang')") is None)
        ctx.close()

        # a saved Bengali preference must survive
        ctx = browser.new_context()
        ctx.add_init_script("localStorage.setItem('bb-lang','bn')")
        pg = ctx.new_page(); pg.goto(URL, wait_until="networkidle")
        r.check("saved Bengali preference is respected",
                pg.evaluate("document.documentElement.lang") == "bn",
                pg.evaluate("document.documentElement.lang"))
        r.check("saved Bengali preference renders Bengali copy",
                "সব নোটিশ" in pg.inner_text("body"))
        ctx.close()

        # a corrupt preference must not break the page
        ctx = browser.new_context()
        ctx.add_init_script("localStorage.setItem('bb-lang','xx')")
        pg = ctx.new_page(); pg.goto(URL, wait_until="networkidle")
        r.check("invalid saved language falls back to English",
                pg.evaluate("document.documentElement.lang") == "en",
                pg.evaluate("document.documentElement.lang"))
        ctx.close()

        ctx, pg = fresh()
        pg.click("[data-lang-set='bn']"); pg.wait_for_timeout(300)
        r.check("switching sets <html lang> to bn",
                pg.evaluate("document.documentElement.lang") == "bn")
        r.check("switching updates visible text",
                "সব নোটিশ" in pg.inner_text("body"))
        r.check("switch is persisted",
                pg.evaluate("localStorage.getItem('bb-lang')") == "bn")
        pg.reload(wait_until="networkidle")
        r.check("Bengali survives a reload",
                pg.evaluate("document.documentElement.lang") == "bn")
        pg.click("[data-lang-set='en']"); pg.wait_for_timeout(300)
        pg.reload(wait_until="networkidle")
        r.check("switching back to English survives a reload",
                pg.evaluate("document.documentElement.lang") == "en")

        # Job ID: fixed English label, ASCII digits, in BOTH languages
        for lang in ("en", "bn"):
            pg.click(f"[data-lang-set='{lang}']"); pg.wait_for_timeout(300)
            pg.fill("#roll", "100001"); pg.wait_for_timeout(400)
            labels = pg.evaluate("[...document.querySelectorAll('.jobtag .k')].map(e=>e.textContent.trim())")
            values = pg.evaluate("[...document.querySelectorAll('.jobtag .v')].map(e=>e.textContent.trim())")
            r.check(f"[{lang}] Job ID label is exactly 'Job ID'",
                    labels and all(x == "Job ID" for x in labels), labels)
            # the DOM can say "Job ID" while CSS renders "JOB ID" — check both
            shown = pg.evaluate("[...document.querySelectorAll('.jobtag .k')].map(e=>e.innerText)")
            r.check(f"[{lang}] Job ID label is not case-transformed on screen",
                    shown and all(x == "Job ID" for x in shown), shown)
            r.check(f"[{lang}] Job ID number stays ASCII",
                    values and all(x.isascii() for x in values), values)
            r.check(f"[{lang}] no Bengali translation of the label leaked",
                    "জব আইডি" not in pg.inner_text("body"))

        # fallback: a key missing from Bengali must render the English string
        pg.click("[data-lang-set='bn']"); pg.wait_for_timeout(250)
        fb = pg.evaluate("""() => { delete STR.bn.whatNext; return t('whatNext'); }""")
        r.check("missing Bengali key falls back to English",
                fb == "What happens next", fb)
        pg.reload(wait_until="networkidle")
        ctx.close()

        # The header used to fit on one row in Bengali and wrap in English,
        # so switching language made the whole page jump 54px. The control
        # labels and .seg padding are sized so the widest language still
        # fits beside the brand; this catches it if either grows again.
        ctx, pg = fresh()
        pg.set_viewport_size({"width": 1280, "height": 900})
        _rows = {}
        for _l in ("bn", "en"):
            pg.click(f"[data-lang-set='{_l}']"); pg.wait_for_timeout(250)
            _rows[_l] = pg.evaluate("""() => {const R=e=>e.getBoundingClientRect();
              const t=document.querySelector('.topbar'),b=document.querySelector('.brand'),
                    c=document.querySelector('.controls');
              return Math.round(R(t).height) <= Math.max(R(b).height, R(c).height) + 4}""")
        r.check("header stays on one row in Bengali", _rows["bn"])
        r.check("header stays on one row in English", _rows["en"])
        r.check("switching language does not reflow the header",
                _rows["bn"] == _rows["en"] is True)

        # Switching language must convert the value the user typed, not just
        # the labels around it: an English page showing ২০০৯৮৩ is a bug.
        pg.click("[data-lang-set='bn']"); pg.wait_for_timeout(200)
        pg.fill("#roll", "২০০৯৮৩"); pg.wait_for_timeout(400)
        pg.click("[data-lang-set='en']"); pg.wait_for_timeout(400)
        _v = pg.input_value("#roll")
        r.check("the typed roll follows the language into English", _v == "200983", _v)
        pg.click("[data-lang-set='bn']"); pg.wait_for_timeout(400)
        _v = pg.input_value("#roll")
        r.check("the typed roll follows the language into Bengali", _v == "২০০৯৮৩", _v)
        ctx.close()

        # ------------------------------------------------------------ search
        r.section("6-8  roll lookup, digits and disambiguation")

        ctx, pg = fresh()
        for lang in ("en", "bn"):
            pg.click(f"[data-lang-set='{lang}']"); pg.wait_for_timeout(250)
            for q, label in [("105432", "ASCII"), ("১০৫৪৩২", "Bengali"),
                             ("١٠٥٤٣٢", "Arabic-Indic")]:
                pg.fill("#roll", q); pg.wait_for_timeout(350)
                r.check(f"[{lang}] {label} digits find the centre",
                        "মোল্লা" in pg.inner_text("#result"),
                        pg.inner_text("#result")[:70].replace("\n", " "))

        pg.click("[data-lang-set='en']"); pg.wait_for_timeout(250)

        # one roll in two jobs must ask, not guess
        pg.fill("#roll", "100001"); pg.wait_for_timeout(400)
        jobs = pg.evaluate("[...document.querySelectorAll('.jobpick [data-job]')].map(b=>b.dataset.job).filter(Boolean)")
        r.check("duplicate roll triggers disambiguation", len(jobs) == 2, jobs)
        r.check("both jobs offered", set(jobs) == {"307", "26101"}, jobs)
        r.check("both result cards rendered",
                pg.evaluate("document.querySelectorAll('#result .card').length") == 2)
        pg.click("[data-job='26101']"); pg.wait_for_timeout(300)
        r.check("chosen job is remembered",
                pg.evaluate("localStorage.getItem('bb-job')") == "26101")
        r.check("chosen job floats to the top",
                "26101" in pg.evaluate("document.querySelector('#result .card .jobtag .v').textContent"))
        pg.evaluate("localStorage.removeItem('bb-job')")

        # an unambiguous roll must NOT ask
        pg.fill("#roll", "3104"); pg.wait_for_timeout(350)
        r.check("unambiguous roll shows no disambiguation",
                pg.inner_text("#disambig").strip() == "")

        # every notice kind still resolves
        for q, expect, kind in [("105432", "মোল্লা", "seat"),
                                ("500006", "Reporting time", "viva"),
                                ("501991", "Congratulations", "selected (offer)"),
                                ("213880", "preliminary test", "selected (written)"),
                                ("201246", "Officer", "selected (2nd phase)")]:
            pg.fill("#roll", q); pg.wait_for_timeout(350)
            r.check(f"{kind} notice resolves for {q}",
                    expect.lower() in pg.inner_text("#result").lower(),
                    pg.inner_text("#result")[:80].replace("\n", " "))

        pg.fill("#roll", "999999"); pg.wait_for_timeout(350)
        r.check("unknown roll reports a gap in our index, not a verdict",
                "not in the notices indexed here" in pg.inner_text("#result"))
        pg.fill("#roll", "12"); pg.wait_for_timeout(300)
        r.check("too-short input is handled", "too short" in pg.inner_text("#result"))
        pg.fill("#roll", ""); pg.wait_for_timeout(300)
        r.check("empty input clears the results",
                pg.inner_text("#result").strip() == "")
        ctx.close()

        # ------------------------------------------------------------- dates
        r.section("9  date, countdown and status logic")

        ctx, pg = fresh()
        iso = today.isoformat()
        tomorrow = (today + datetime.timedelta(days=1)).isoformat()
        past = (today - datetime.timedelta(days=5)).isoformat()
        r.check("dayDiff(today) == 0", pg.evaluate(f"dayDiff('{iso}')") == 0)
        r.check("dayDiff(tomorrow) == 1", pg.evaluate(f"dayDiff('{tomorrow}')") == 1)
        r.check("dayDiff(5 days ago) == -5", pg.evaluate(f"dayDiff('{past}')") == -5)
        d, m, y = today.day, today.month, today.year
        r.check("toISO parses dd/mm/yyyy",
                pg.evaluate(f"toISO('{d:02d}/{m:02d}/{y}')") == iso,
                pg.evaluate(f"toISO('{d:02d}/{m:02d}/{y}')"))
        r.check("toISO rejects junk", pg.evaluate("toISO('not-a-date')") is None)
        r.check("countdown for today says today",
                "today" in pg.evaluate(f"countdown('{iso}',null,null)").lower())
        r.check("countdown for a past date is in the past",
                "ago" in pg.evaluate(f"countdown('{past}',null,null)").lower())
        r.check("statusOf returns a known bucket",
                pg.evaluate("notices.every(n=>['today','soon','up','past','open'].includes(statusOf(n).k))"))
        ctx.close()

        # ---------------------------------------------------------- escaping
        r.section("10  HTML escaping of notice-derived text")

        ctx, pg = fresh()
        leaked = pg.evaluate("""() => {
          const n = notices.find(x => x.kind === 'circular');
          const original = n.title;
          window.__xss = false;
          n.title = '<img src=x onerror="window.__xss=true">';
          renderNotices();
          const injected = document.querySelector('#notices img') !== null;
          n.title = original; renderNotices();
          return { injected, fired: window.__xss };
        }""")
        r.check("hostile notice title does not create an element",
                not leaked["injected"], leaked)
        r.check("hostile notice title does not execute",
                not leaked["fired"], leaked)
        r.check("escaped text is still displayed verbatim",
                pg.evaluate("""esc('<b>&"x"</b>')""") == "&lt;b&gt;&amp;&quot;x&quot;&lt;/b&gt;")
        ctx.close()

        # --------------------------------------------------- generated page
        r.section("11-12  generated page completeness and self-containment")

        external = []
        ctx = browser.new_context()
        pg = ctx.new_page()
        pg.on("request", lambda req: external.append(req.url)
              if not req.url.startswith((f"http://127.0.0.1:{port}", "data:", "blob:")) else None)
        pg.goto(URL, wait_until="networkidle"); pg.wait_for_timeout(600)
        r.check("no external network requests on load", not external, external[:3])
        r.check("all 13 notices inlined and rendered",
                pg.evaluate("DATA.notices.length") == 13,
                pg.evaluate("DATA.notices.length"))
        r.check("every notice renders a card",
                pg.evaluate("document.querySelectorAll('.ncard').length") == 13,
                pg.evaluate("document.querySelectorAll('.ncard').length"))
        r.check("CSS is present in the page",
                pg.evaluate("document.styleSheets.length") >= 1)
        r.check("styles actually applied (not unstyled HTML)",
                pg.evaluate("getComputedStyle(document.querySelector('.card,.ncard')).borderRadius") != "0px")
        # 1,401 rolls live in rolls[] arrays (rendered as chips) and 2,803 more
        # are delta-encoded inside sittings — 4,204 searchable numbers in total.
        chips = pg.evaluate("notices.reduce((a,n)=>a+(n.rolls?n.rolls.length:0),0)")
        sittings = pg.evaluate("notices.reduce((a,n)=>a+(n._count||0),0)")
        r.check("roll-list corpus inlined (1,401 chips)", chips == 1401, chips)
        r.check("sitting corpus decoded (2,803 rolls)", sittings == 2803, sittings)
        r.check("full searchable corpus is 4,204", chips + sittings == 4204, chips + sittings)
        ctx.close()

        # ------------------------------------------- theme / mobile / print
        r.section("13  theme, mobile, print, keyboard, offline")

        ctx = browser.new_context(color_scheme="dark")
        pg = ctx.new_page(); pg.goto(URL, wait_until="networkidle")
        r.check("OS dark preference is honoured by default",
                "14, 21, 17" in pg.evaluate("getComputedStyle(document.body).backgroundColor"),
                pg.evaluate("getComputedStyle(document.body).backgroundColor"))
        pg.click("[data-theme-set='light']"); pg.wait_for_timeout(250)
        r.check("manual light overrides OS dark",
                "245, 251, 246" in pg.evaluate("getComputedStyle(document.body).backgroundColor"))
        pg.reload(wait_until="networkidle")
        r.check("theme choice survives a reload",
                pg.evaluate("document.documentElement.getAttribute('data-theme')") == "light")
        pg.click("[data-theme-set='system']"); pg.wait_for_timeout(250)
        r.check("system clears the stored override",
                pg.evaluate("localStorage.getItem('bb-theme')") is None)
        ctx.close()

        ctx = browser.new_context(viewport={"width": 360, "height": 740})
        pg = ctx.new_page(); pg.goto(URL, wait_until="networkidle")
        pg.evaluate("document.querySelectorAll('details').forEach(d=>d.open=true)")
        pg.wait_for_timeout(700)
        sw, cw = (pg.evaluate("document.documentElement.scrollWidth"),
                  pg.evaluate("document.documentElement.clientWidth"))
        r.check(f"no horizontal page scroll at 360px with every list open ({sw} vs {cw})",
                sw <= cw + 1, f"{sw} > {cw}")
        ctx.close()

        ctx, pg = fresh()
        pg.emulate_media(media="print")
        r.check("print hides the controls",
                pg.evaluate("getComputedStyle(document.querySelector('.controls')).display") == "none")
        r.check("print hides the notice archive",
                pg.evaluate("getComputedStyle(document.querySelector('#notices')).display") == "none")
        pg.emulate_media(media="screen")
        r.check("controls return on screen",
                pg.evaluate("getComputedStyle(document.querySelector('.controls')).display") != "none")

        pg.keyboard.press("Tab")
        r.check("keyboard focus reaches an interactive control",
                pg.evaluate("['BUTTON','A','INPUT'].includes(document.activeElement.tagName)"),
                pg.evaluate("document.activeElement.tagName"))
        pg.focus("#roll"); pg.keyboard.type("105432"); pg.wait_for_timeout(350)
        r.check("typing with the keyboard searches",
                pg.evaluate("document.querySelectorAll('#result .card').length") >= 1)
        pg.keyboard.press("Escape"); pg.wait_for_timeout(250)
        r.check("Escape clears the search",
                pg.evaluate("document.querySelector('#roll').value") == "")
        ctx.close()

        # offline, after one successful online visit
        ctx = browser.new_context(service_workers="allow")
        pg = ctx.new_page()
        pg.goto(URL, wait_until="networkidle"); pg.wait_for_timeout(2500)
        controlled = pg.evaluate("!!navigator.serviceWorker.controller")
        r.check("service worker takes control", controlled)
        ctx.set_offline(True)
        try:
            pg.reload(wait_until="load"); pg.wait_for_timeout(1000)
            cards = pg.evaluate("document.querySelectorAll('.ncard').length")
            pg.fill("#roll", "105432"); pg.wait_for_timeout(400)
            found = "মোল্লা" in pg.inner_text("#result")
            r.check(f"offline reload still renders ({cards} notices)", cards == 13, cards)
            r.check("offline search still works", found)
        except Exception as exc:
            r.check("offline reload still renders", False, str(exc)[:90])
        ctx.set_offline(False)
        ctx.close()

        # Service-worker UPDATE behaviour. Bumping CACHE is only half the
        # job: if activate does not evict the old cache, a returning visitor
        # keeps being served the previous shell and the deploy appears to do
        # nothing. This seeds a stale cache, forces a fresh activate, and
        # checks it was cleared.
        ctx = browser.new_context()
        pg = ctx.new_page()
        pg.goto(URL, wait_until="networkidle")
        pg.wait_for_function("navigator.serviceWorker.controller !== null", timeout=15000)
        names = pg.evaluate("() => caches.keys()")
        r.check("the shipped cache is the bumped one",
                names == ["bb-roll-v5"], names)

        pg.evaluate("""async () => {
            const c = await caches.open('bb-roll-v3');
            await c.put('./stale', new Response('old'));
            const regs = await navigator.serviceWorker.getRegistrations();
            await Promise.all(regs.map(r => r.unregister()));
        }""")
        seeded = pg.evaluate("() => caches.keys()")
        r.check("a stale cache can be seeded for the test",
                "bb-roll-v3" in seeded, seeded)

        pg.reload(wait_until="networkidle")
        pg.wait_for_function("navigator.serviceWorker.controller !== null", timeout=15000)
        pg.wait_for_timeout(600)
        after = pg.evaluate("() => caches.keys()")
        r.check("activate evicts the superseded cache",
                after == ["bb-roll-v5"], after)
        r.check("the new shell is still precached",
                pg.evaluate("""async () => {
                    const c = await caches.open('bb-roll-v5');
                    return (await c.keys()).length >= 7;}"""))
        ctx.close()

        # file:// — the project claims local-file usability
        ctx = browser.new_context()
        pg = ctx.new_page()
        file_errs = []
        pg.on("console",
              lambda m: file_errs.append(m.type + ": " + m.text[:100]) if m.type == "error" else None)
        pg.on("pageerror", lambda e: file_errs.append("pageerror: " + str(e)[:100]))
        pg.goto(FILE_URL, wait_until="load"); pg.wait_for_timeout(1200)
        r.check("file:// renders every notice",
                pg.evaluate("document.querySelectorAll('.ncard').length") == 13,
                pg.evaluate("document.querySelectorAll('.ncard').length"))
        pg.fill("#roll", "105432"); pg.wait_for_timeout(450)
        r.check("file:// search works", "মোল্লা" in pg.inner_text("#result"))
        r.check("file:// defaults to English",
                pg.evaluate("document.documentElement.lang") == "en")
        # A font preload must carry crossorigin, which the null file:// origin
        # fails, so static preload tags logged a CORS error per font. They are
        # injected for http(s) only now; the console must be clean.
        r.check("file:// produces no console errors", not file_errs, file_errs[:4])
        r.check("file:// injects no font preloads",
                pg.evaluate("document.querySelectorAll('link[rel=preload]').length") == 0)
        r.check("file:// still loads the webfonts",
                pg.evaluate("document.fonts.size") == 6,
                pg.evaluate("document.fonts.size"))
        ctx.close()

        # ---------------------------------------------------------------
        r.section("semantics and hardening")
        ctx = browser.new_context()
        pg = ctx.new_page()
        pg.goto(URL, wait_until="networkidle"); pg.wait_for_timeout(400)

        r.check("page has a main landmark",
                pg.evaluate("document.querySelectorAll('main').length") == 1)
        r.check("the archive is a section labelled by its heading",
                pg.evaluate("""() => {const s=document.querySelector('section');
                    return !!s && s.getAttribute('aria-labelledby') === 't-allnotices';}"""))
        r.check("the search is a search landmark",
                pg.evaluate("(document.querySelector('form.search')||{}).getAttribute?"
                            "document.querySelector('form.search').getAttribute('role'):null") == "search")
        r.check("the roll field has a real label",
                pg.evaluate("""() => {const l=document.querySelector('label[for=roll]');
                    return !!l && l.textContent.trim().length > 0;}"""))
        r.check("the label is off-screen, not hidden from assistive tech",
                pg.evaluate("""() => {const s=getComputedStyle(document.querySelector('label[for=roll]'));
                    return s.display !== 'none' && s.visibility !== 'hidden';}"""))
        r.check("the filter group is labelled",
                pg.evaluate("!!document.querySelector('#filters[aria-label]')"))

        # the aria-live fix: #result must NOT be a live region any more
        r.check("#result is no longer a live region",
                pg.evaluate("document.querySelector('#result').getAttribute('aria-live')") is None)
        r.check("a dedicated status line carries announcements",
                pg.evaluate("""() => {const s=document.querySelector('#srstatus');
                    return !!s && s.getAttribute('role')==='status'
                        && s.getAttribute('aria-live')==='polite';}"""))
        pg.fill("#roll", "100001"); pg.wait_for_timeout(600)
        status = pg.inner_text("#srstatus")
        r.check("status summarises instead of reading every card",
                "2" in status and len(status) < 90, status)
        result_len = pg.evaluate("document.querySelector('#result').innerText.length")
        r.check("status is far shorter than what #result would have announced",
                len(status) * 10 < result_len,
                f"status={len(status)} chars, result={result_len} chars")
        before_txt = pg.inner_text("#srstatus")
        pg.fill("#roll", "100001")       # same query again
        pg.wait_for_timeout(300)
        r.check("an unchanged outcome is not re-announced",
                pg.inner_text("#srstatus") == before_txt)

        # Enter must not navigate away
        pg.fill("#roll", "105432")
        pg.press("#roll", "Enter"); pg.wait_for_timeout(500)
        r.check("Enter does not submit or reload the page",
                "105432" == pg.input_value("#roll") and "?" not in pg.url)
        r.check("results survive Enter", len(pg.inner_text("#result")) > 50)

        # link hardening
        rels = pg.evaluate("[...new Set([...document.querySelectorAll('a[target=_blank]')].map(a=>a.rel))]")
        r.check("every new-tab link sets noopener noreferrer",
                rels == ["noopener noreferrer"], rels)

        # URL scheme validation
        probes = pg.evaluate("""() => ({
            js:    BB.dom.safeHref('javascript:alert(1)'),
            mixed: BB.dom.safeHref('  JaVaScRiPt:alert(1)'),
            data:  BB.dom.safeHref('data:text/html,<b>x'),
            vb:    BB.dom.safeHref('vbscript:x'),
            tab:   BB.dom.safeHref('java\\tscript:alert(1)'),
            rel:   BB.dom.safeHref('notices/a.pdf'),
            https: BB.dom.safeHref('https://a.example/x.pdf')})""")
        for key in ("js", "mixed", "data", "vb", "tab"):
            r.check(f"safeHref rejects {key}", probes[key] == "", probes[key])
        r.check("safeHref keeps relative pdf paths", probes["rel"] == "notices/a.pdf")
        r.check("safeHref keeps https", probes["https"] == "https://a.example/x.pdf")
        r.check("every rendered pdf link is a relative notices/ path",
                all(h.startswith("notices/") for h in pg.evaluate(
                    "[...document.querySelectorAll('a')].map(a=>a.getAttribute('href'))"
                    ".filter(h=>h && h.endsWith('.pdf'))")))

        # font preload: present over http, absent over file://
        # The expected count is derived from the injector array in
        # app.template.html, so adding or removing a preloaded font does not
        # mean editing a magic number here.
        import re as _re
        _tpl = open(os.path.join(ROOT, "app.template.html"), encoding="utf-8").read()
        _want = len(_re.findall(r'"fonts/[^"]+\.woff2"', _tpl))
        r.check(f"font preloads are injected over http ({_want})",
                pg.evaluate("document.querySelectorAll('link[rel=preload][as=font]').length") == _want)
        ctx.close()

        # ---------------------------------------------------------------
        r.section("module assembly")
        # The scripts are concatenated into one classic <script>. If a file
        # were dropped, mis-ordered or wrapped so its declarations did not
        # reach the shared scope, the page would still parse but some branch
        # would throw at runtime. BB names what each file contributed, so
        # checking it is a direct test that every module really loaded.
        ctx = browser.new_context()
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(URL, wait_until="networkidle"); pg.wait_for_timeout(500)

        EXPECTED = {
            "dom": ["$", "esc"],
            "numbers": ["BN", "AS", "NUM", "JOB"],
            "dates": ["toISO", "dayDiff", "statusOf", "countdown", "dnum"],
            "language": ["t", "STR", "kindLabel"],
            "constants": ["KIND", "POST_RE"],
            "data": ["DATA", "notices", "searchable", "findCentre", "minus60"],
            "maps": ["mapsUrl"],
            "results": ["postOf", "identBlock", "provenance", "outcomeOf",
                        "nextBlock", "seatCard", "sittingCard", "selectedCard"],
            "rolls": ["rollWrapHtml", "paintRolls"],
            "search": ["collectHits", "isPref", "renderResult", "paintHits"],
            "noticeList": ["noticeCard", "renderNotices"],
            "preferences": ["applyTheme", "currentTheme", "renderToggles",
                            "applyLang", "paintStatic"],
        }
        surface = pg.evaluate("() => Object.keys(window.BB || {})")
        r.check("every module reached the shared scope",
                set(surface) == set(EXPECTED),
                f"missing={sorted(set(EXPECTED) - set(surface))} "
                f"extra={sorted(set(surface) - set(EXPECTED))}")
        for mod, names in EXPECTED.items():
            got = pg.evaluate("m => Object.keys(window.BB[m] || {})", mod)
            r.check(f"BB.{mod} exports its members",
                    set(names).issubset(set(got)),
                    f"missing={sorted(set(names) - set(got))}")
        r.check("the dataset decoded at load time",
                pg.evaluate("() => BB.data.notices.length === 13 "
                            "&& BB.data.searchable.length > 0"))
        r.check("no uncaught errors during boot", not errs, errs[:3])
        ctx.close()

        browser.close()

    srv.shutdown()
    print("\n" + "=" * 62)
    if r.failed:
        print(f"{len(r.failed)} of {r.count} FAILED:")
        for f in r.failed:
            print(f"  - {f}")
        return 1
    print(f"ALL {r.count} UI CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
