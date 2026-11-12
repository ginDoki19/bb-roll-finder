#!/usr/bin/env python3
"""
fetch_notices.py — pull new notices from the BB e-recruitment portal, on your PC.

WHY THIS RUNS LOCALLY AND NOT IN GITHUB ACTIONS
    erecruitment.bb.org.bd sits behind an F5 BIG-IP ASM firewall. Tested directly:
      * plain HTTP request     -> "Request Rejected" (246 bytes)
      * browser-shaped headers -> TLS connection reset
      * headless Chromium      -> escalated to an image CAPTCHA
    From a datacenter IP (GitHub's runners) it is always the CAPTCHA. From your
    own Bangladeshi residential IP the JS challenge normally resolves by itself.
    So the fetch has to happen on a real machine, with a real browser profile.

WHAT IT DOES
    1. opens career/jobopportunity.php in a real Chromium window (persistent
       profile, so the F5 cookie survives between runs — usually no CAPTCHA
       after the first time)
    2. if a CAPTCHA appears you solve it once in the window; the script waits
    3. saves the listing page to career.html
    4. downloads any notice PDF not already in notices/
    5. optionally rebuilds data + site, and commits/pushes

USAGE
    python3 tools/fetch_notices.py --plan          # offline: show what's missing
    python3 tools/fetch_notices.py                 # fetch (browser window opens)
    python3 tools/fetch_notices.py --headless      # try without a window
    python3 tools/fetch_notices.py --build --push  # fetch, rebuild, git push

SCHEDULING (Windows): Task Scheduler -> daily 09:00 ->
    pythonw.exe C:\\path\\bb-notice\\tools\\fetch_notices.py --headless --build --push
Leave it on the non-headless mode for the first run of each month.

Requires:  pip install playwright && python -m playwright install chromium
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from urllib.parse import urljoin

LISTING = "https://erecruitment.bb.org.bd/career/jobopportunity.php"
# the original saved listing came from the _bscs page, so try both and merge
LISTINGS = [LISTING, "https://erecruitment.bb.org.bd/career/jobopportunity_bscs.php"]
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROFILE = os.path.join(os.path.expanduser("~"), ".bb-fetch-profile")

# markers that mean the WAF is still in the way
CHALLENGE = ("bobcmn", "TSPD", "What code is in the image", "Request Rejected",
             "Please enable JavaScript")


# A browser's "Save as" rewrites links to absolute URLs, but the live page keeps
# them as written (often relative), so accept both and resolve against LISTING.
PDF_HREF = re.compile(r"""href\s*=\s*["']([^"'<>]+?\.pdf)(?:\?[^"']*)?["']""", re.I)


BROWSER_CANDIDATES = [
    r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe",
    r"%ProgramFiles(x86)%\BraveSoftware\Brave-Browser\Application\brave.exe",
    r"%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe",
    r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
    r"%LocalAppData%\Google\Chrome\Application\chrome.exe",
    "/usr/bin/brave-browser", "/usr/bin/google-chrome",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def find_browser(explicit: str | None = None) -> str | None:
    """Brave first, then Chrome. None -> use Playwright's bundled Chromium."""
    if explicit:
        return explicit if os.path.exists(explicit) else None
    for c in BROWSER_CANDIDATES:
        c = os.path.expandvars(c)
        if os.path.exists(c):
            return c
    return None


def listing_pdf_urls(html: str, base: str = LISTING) -> list[dict]:
    """Pull (jobId, category, title, url, sizeKB) out of the listing HTML."""
    out = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I):
        m = PDF_HREF.search(tr)
        if not m:
            continue
        url = urljoin(base, m.group(1).replace("&amp;", "&").strip())
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "|", tr))
        size = re.search(r"\(([\d,]+)\s*KB\)", text)
        job = re.search(r"\|\s*(\d{4,6})\s*\|", text)
        out.append({
            "jobId": job.group(1) if job else None,
            "url": url,
            "file": url.rsplit("/", 1)[-1],
            "sizeKB": int(size.group(1).replace(",", "")) if size else None,
            "title": max((p.strip() for p in text.split("|")
                          if len(p.strip()) > 25), key=len, default="")[:200],
        })
    return out


def plan(html_path: str) -> list[dict]:
    html = open(html_path, encoding="utf-8", errors="replace").read()
    pdfs = listing_pdf_urls(html)
    have = set(os.listdir(os.path.join(ROOT, "notices")))
    for p in pdfs:
        p["have"] = p["file"] in have
    return pdfs


def page_state(html: str) -> str:
    """
    Classify a fetched page. Pure function — unit-tested in tools/test_fetch.py.

      "ok"        the real listing: it carries PDF rows
      "challenge" the firewall is still in the way (JS challenge or CAPTCHA)
      "empty"     no markers but also no PDFs — wrong page, or a layout change

    CONTENT FIRST, markers second. This used to be the other way round and it
    was wrong: F5 injects its TSPD/bobcmn script into *legitimate* responses
    too, so the real listing page contains "TSPD" and was classified as a
    challenge forever — the wait loop could never exit and every run ended in
    a bogus "CAPTCHA NEEDED" while the table sat visible on screen.

    F5's own guidance agrees: do not infer a block from the status code or from
    a cookie/script signature, verify that the expected data is present.
    TS* / TSPD_101* identify a BIG-IP deployment, not a blocked request.
    """
    if not html or not html.strip():
        return "empty"
    if PDF_HREF.search(html):        # hard evidence of the real page
        return "ok"
    if any(c in html for c in CHALLENGE):
        return "challenge"           # e.g. "Request Rejected" is only 246 bytes
    return "empty"


def wait_for_page(page, timeout=300, quiet=False, grace=15):
    """Block until the challenge clears (or the user solves the CAPTCHA)."""
    t0 = time.time()
    warned = False
    while time.time() - t0 < timeout:
        try:
            html = page.content()
        except Exception as e:           # page is mid-navigation (e.g. right after
            if "navigating" not in str(e) and "context" not in str(e).lower():
                raise                    # the CAPTCHA is solved) — just try again
            time.sleep(1)
            continue
        state = page_state(html)
        if state == "ok":
            spent = time.time() - t0
            if warned or spent > 5:
                print(f"  ✓ challenge cleared after {spent:.0f}s", flush=True)
            return True, html
        if state == "empty" and time.time() - t0 > 20:
            return True, html            # clean page, no PDF rows: not a CAPTCHA
        # With a pasted session the interstitial usually clears itself in a few
        # seconds. Shouting "solve the CAPTCHA" on the very first poll made a
        # normal, self-resolving wait look like a failure.
        if not quiet and not warned and time.time() - t0 > grace:
            print(f"  ⏳ still on the F5 interstitial after {grace}s. It normally "
                  f"clears itself — only type a CAPTCHA if you can see one.",
                  flush=True)
            warned = True
        time.sleep(2)
    try:
        return False, page.content()
    except Exception:
        return False, ""


SESSION_FILE = os.path.join(ROOT, "meta", "session.txt")


_LAST_FORMAT = "none"


def _parse_session(path: str):
    """Read a hand-supplied browser session.

    Why this exists: the script drives Brave with its OWN profile directory
    (PROFILE, below), which is a different cookie jar from the Brave you browse
    in. Solving the F5 challenge in your normal window therefore does nothing
    for the fetcher -- it has to pass the challenge separately. Pasting the
    session from DevTools hands it the one you already solved.

    Accepts anything DevTools produces. Right-click a request -> Copy as:
      * cURL (bash)    ->  -b $'a=b; c=d'      <- Chromium 115+ / Brave
      * cURL (bash)    ->  -H 'cookie: a=b'    <- older Chromium, Firefox
      * cURL (cmd)     ->  -b "a=b; c=d"
      * fetch / Node   ->  "cookie": "a=b; c=d"
      * PowerShell     ->  "Cookie"="a=b"  /  $session.Cookies.Add((New-Object
                           System.Net.Cookie("k","v","/","host")))
      * a raw header line:   cookie: a=b; c=d
      * just the value:      a=b; c=d

    The $'...' form is bash ANSI-C quoting: Chromium escapes bytes it cannot
    put in a plain single-quoted string, so  bb_cookie=!Uh/..  arrives as
    bb_cookie=\\u0021Uh/..  . Those escapes MUST be decoded or F5 sees a
    corrupted token and rejects the session.

    Lines starting with # are ignored. A UTF-8 BOM (Notepad) is tolerated.

    Returns (cookies, user_agent). The user-agent matters: F5 ties TSPD_101 to
    the browser that was issued it, so we replay theirs, not ours.
    """
    global _LAST_FORMAT
    _LAST_FORMAT = "none"
    if not path or not os.path.exists(path):
        return [], None
    raw = open(path, encoding="utf-8-sig", errors="replace").read()
    raw = "\n".join(l for l in raw.splitlines() if not l.lstrip().startswith("#"))

    def _ansi_c(v):
        """Decode bash $'...' escapes: \\uXXXX \\xXX \\\\ \\' \\\" """
        v = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), v)
        v = re.sub(r"\\x([0-9a-fA-F]{2})", lambda m: chr(int(m.group(1), 16)), v)
        return (v.replace("\\'", "'").replace('\\"', '"')
                 .replace("\\t", "\t").replace("\\\\", "\\"))

    def _find(pats, flags=re.I | re.M):
        for label, pat in pats:
            m = re.search(pat, raw, flags)
            if m and m.group("v").strip():
                return label, _ansi_c(m.group("v").strip())
        return None, None

    # ---- cookies ---------------------------------------------------------
    label, cs = _find((
        ("curl -b $'' (Chromium 115+)", r"(?:-b|--cookie)\s+\$'(?P<v>(?:[^'\\]|\\.)*)'"),
        ("curl -b ''",                  r"(?:-b|--cookie)\s+'(?P<v>[^']*)'"),
        ('curl -b ""',                  r'(?:-b|--cookie)\s+"(?P<v>(?:[^"\\]|\\.)*)"'),
        ("curl -H 'cookie:'",           r"-H\s+'cookie:\s*(?P<v>[^']*)'"),
        ('curl -H "cookie:"',           r'-H\s+"cookie:\s*(?P<v>[^"]*)"'),
        ("fetch / PowerShell header",   r'''["']?cookie["']?\s*[:=]\s*["'](?P<v>(?:[^"'\\]|\\.)*)["']'''),
        ("raw header line",             r"^\s*cookie:\s*(?P<v>.+)$"),
    ))

    def _split(text):
        out = []
        for part in text.split(";"):
            part = part.strip()
            if "=" not in part:
                continue
            k, v = part.split("=", 1)
            k = k.strip().strip('"').strip("'")
            v = v.strip().strip('"').strip("'")
            if k and re.fullmatch(r"[!#$%&'*+\-.^_`|~0-9A-Za-z]+", k):
                out.append((k, v))
        return out

    pairs = _split(cs) if cs else []
    if pairs:
        _LAST_FORMAT = label
    if not pairs:                       # PowerShell cookie objects
        pairs = [(k.strip(), v.strip()) for k, v in re.findall(
            r"""New-Object\s+System\.Net\.Cookie\(\s*["']([^"']+)["']\s*,\s*["']([^"']*)["']""",
            raw, re.I)]
        if pairs:
            _LAST_FORMAT = "PowerShell cookie objects"
    if not pairs:                       # bare "a=b; c=d" paste
        cand = " ".join(raw.split())
        if "=" in cand and "curl" not in cand.lower() and "{" not in cand:
            pairs = _split(cand)
            if pairs:
                _LAST_FORMAT = "bare cookie value"
    if not pairs:
        return [], None

    cookies = [{"name": k, "value": v, "url": "https://erecruitment.bb.org.bd/"}
               for k, v in pairs]

    # ---- user-agent ------------------------------------------------------
    _, ua = _find((
        ("h", r"-H\s+\$?'user-agent:\s*(?P<v>[^']*)'"),
        ("h", r'-H\s+"user-agent:\s*(?P<v>[^"]*)"'),
        ("h", r'''["']?user-agent["']?\s*[:=]\s*["'](?P<v>(?:[^"'\\]|\\.)*)["']'''),
        ("h", r"^\s*user-agent:\s*(?P<v>.+)$"),
        ("h", r"""UserAgent\s*=\s*["'](?P<v>[^"']+)["']"""),
    ))
    return cookies, ua


def _scrub(e) -> str:
    """One-line, cookie-free rendering of a Playwright exception.

    Playwright puts the entire 'Call log' in str(e), request headers included,
    so a failed PDF download dumped live TSPD_101 / bb_cookie / session values
    into logs/fetch.log. The log is gitignored, but people paste logs into chat
    when asking for help, so the secret should never be written at all.
    """
    first = str(e).split("\n", 1)[0]
    first = re.sub(r"(cookie|set-cookie|authorization)\s*:.*", r"\1: <redacted>",
                   first, flags=re.I)
    return first[:160]


_TRANSPORT = "not attempted"


def _cookie_header(cookies) -> str:
    return "; ".join(f"{c['name']}={c['value']}" for c in cookies)


def _http_get(url: str, cookies, ua: str | None, timeout: int = 60,
              referer: str | None = None):
    """Plain HTTPS GET replaying the pasted session. Returns (status, body).

    Uses curl_cffi when it is installed so the TLS handshake matches real
    Chrome. This matters more than any header: F5 fingerprints the TLS
    ClientHello (JA3/JA4), and Python's OpenSSL handshake is flagged before a
    single header is read — which is why a perfectly valid cookie still came
    back as a 6 KB JS challenge. curl_cffi binds curl-impersonate and replays
    Chrome's exact ClientHello and HTTP/2 settings.

    Falls back to urllib if curl_cffi is absent; the caller then falls back to
    the real browser, so nothing breaks, it is just slower and less likely to
    get through.
    """
    global _TRANSPORT
    headers = {
        "User-Agent": ua or ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                             "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                  "image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.7",
        "Cookie": _cookie_header(cookies),
        "Referer": referer or "https://erecruitment.bb.org.bd/",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
    }
    try:
        from curl_cffi import requests as _cffi
        _TRANSPORT = "curl_cffi (Chrome TLS fingerprint)"
        r = _cffi.get(url, headers={**headers, "Accept-Encoding": "gzip, deflate, br"},
                      impersonate="chrome", timeout=timeout, allow_redirects=True)
        return r.status_code, r.content
    except ImportError:
        _TRANSPORT = "urllib (Python TLS — F5 often rejects this)"

    import urllib.error
    import urllib.request
    req = urllib.request.Request(url, headers={**headers, "Accept-Encoding": "identity",
                                               "Connection": "close"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def _http_pass(cookies, ua, download: bool, retries: int = 3):
    """Try the whole fetch over plain HTTP, no browser window at all.

    Returns the career.html path on success, or None to fall back to the
    browser. Deliberately all-or-nothing on the listing: a partial listing
    would make career.html advertise PDFs we never got.
    """
    rows, pages, counts = [], [], []
    for url in LISTINGS:
        print(f"→ {url}")
        try:
            status, body = _http_get(url, cookies, ua)
        except Exception as e:
            print(f"  · no-browser attempt failed — {type(e).__name__}: {_scrub(e)}")
            return None
        html = body.decode("utf-8", "replace")
        state = page_state(html)
        if state != "ok":
            print(f"  · HTTP {status}, {len(html)//1024} KB, state={state}"
                  f"  [{_TRANSPORT}]")
            if "urllib" in _TRANSPORT:
                print("  · tip: pip install curl_cffi  — lets this step copy Chrome's TLS")
                print("         fingerprint, which F5 checks before it reads any header.")
            return None
        got = listing_pdf_urls(html, url)
        print(f"  · HTTP {status}, {len(html)//1024} KB, {len(got)} PDF row(s)"
              f"  [{_TRANSPORT}]")
        if not got:
            print("  · that listing parsed to zero rows — falling back to the browser\n"
                  "    rather than saving a career.html that is missing a whole source.")
            return None
        pages.append(html)
        counts.append((url, len(got)))
        rows += [r for r in got if r["file"] not in {x["file"] for x in rows}]

    if not rows:
        return None
    dest = os.path.join(ROOT, "career.html")
    open(dest, "w", encoding="utf-8").write(
        "\n<!-- ==== next listing ==== -->\n".join(pages))
    print(f"  ✓ listing saved -> career.html ({len(rows)} PDFs = "
          + " + ".join(str(c) for _, c in counts)
          + f" across {len(counts)} listings) — no browser needed")

    have = set(os.listdir(os.path.join(ROOT, "notices")))
    new = [p for p in rows if p["file"] not in have]
    if not download:
        print(f"  · --no-download: {len(new)} PDF(s) would be fetched")
        return dest
    if not new:
        print("  ✓ no new PDFs")
        return dest

    failed = []
    for p in new:
        for attempt in range(1, retries + 1):
            try:
                status, body = _http_get(p["url"], cookies, ua, timeout=90, referer=LISTING)
                if status == 200 and body[:4] == b"%PDF":
                    open(os.path.join(ROOT, "notices", p["file"]), "wb").write(body)
                    print(f"  ↓ {p['file']}  ({len(body)//1024} KB)")
                    break
                reason = f"HTTP {status}, not a PDF"
            except Exception as e:
                reason = f"{type(e).__name__}: {_scrub(e)}"
            if attempt < retries:
                wait = 2 ** attempt
                print(f"  · {p['file']} — {reason}; retry {attempt}/{retries - 1} in {wait}s")
                time.sleep(wait)
            else:
                print(f"  ✗ {p['file']} — {reason} (gave up after {retries} tries)")
                failed.append(p["file"])
    if failed:
        print(f"  ! {len(failed)} PDF(s) missing — rerun to pick them up: "
              + ", ".join(failed[:3]) + ("…" if len(failed) > 3 else ""))
    return dest


def fetch(headless: bool, timeout: int = 300, download: bool = True,
          browser: str | None = None, session: str | None = None,
          force_browser: bool = False) -> str | None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("pip install playwright && python -m playwright install chromium")

    cookies, ua = _parse_session(session)

    # Fast path: if a session was pasted, try plain HTTP first. When F5 accepts
    # the cookie there is no reason to open a window at all — the browser only
    # exists to execute the JS challenge we cannot replay ourselves.
    if cookies and not force_browser:
        names = ", ".join(sorted({c["name"] for c in cookies})[:4])
        print(f"  🍪 session: {len(cookies)} cookie(s) [{names}"
              f"{'…' if len(cookies) > 4 else ''}]"
              + (", UA replayed" if ua else "") + " — trying without a browser")
        try:
            dest = _http_pass(cookies, ua, download)
        except Exception as e:
            print(f"  · no-browser attempt failed — {type(e).__name__}: {_scrub(e)}")
            dest = None
        if dest:
            return dest
        print("  · cookie alone did not clear F5 — opening the browser window")

    with sync_playwright() as pw:
        exe = browser
        print(f"  browser: {exe or 'Playwright Chromium (no Brave/Chrome found)'}")
        kw = {"executable_path": exe} if exe else {}
        ctx = pw.chromium.launch_persistent_context(
            PROFILE, headless=headless, locale="en-US", **kw,
            user_agent=ua or ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
            viewport={"width": 1400, "height": 900},
        )
        if cookies:
            try:
                ctx.add_cookies(cookies)
                names = ", ".join(sorted({c["name"] for c in cookies})[:4])
                print(f"  🍪 session injected: {len(cookies)} cookie(s) [{names}"
                      f"{'…' if len(cookies) > 4 else ''}]"
                      + (f", UA replayed" if ua else ""))
            except Exception as e:
                print(f"  ! could not inject session: {_scrub(e)}")
        page = ctx.new_page()
        have = set(os.listdir(os.path.join(ROOT, "notices")))
        rows, pages = [], []
        counts, missed = [], []          # per-listing tallies for the summary
        for url in LISTINGS:
            print(f"→ {url}")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=90_000)
            except Exception as e:
                print(f"  ✗ {type(e).__name__}: {_scrub(e)}")
                missed.append(url)
                continue
            ok, html = wait_for_page(page, timeout=timeout)
            if not ok:
                # The advice depends on how we were actually launched. Telling a
                # user already running with a visible window to "run without
                # --headless" sent them hunting for a flag that was never set.
                if headless:
                    tip = ("    You ran with --headless, so there was no window to solve it in.\n"
                           "    Run again without --headless (run.bat already does this).")
                else:
                    have_sess = bool(cookies)
                    tip = ("    A window WAS open, so the F5 challenge did not clear in "
                           f"{timeout}s.\n"
                           "    Things that actually work, in order:\n"
                           "      1. HAND IT YOUR SOLVED SESSION — most reliable fix.\n"
                           "         This script uses its own browser profile, so the CAPTCHA you\n"
                           "         solved in normal Brave does not count for it. Copy yours over:\n"
                           "           · open the portal in normal Brave, solve it, see the table\n"
                           "           · F12 > Network > F5 > click the jobopportunity.php row\n"
                           "           · right-click > Copy > Copy as cURL (bash)\n"
                           "           · paste into meta/session.txt  (see meta/session.txt.example)\n"
                           + ("         You already have a session file, but it did not get through —\n"
                              "         it has probably expired. Re-copy a fresh one.\n"
                              if have_sess else "")
                           + "      2. Check your internet. ERR_INTERNET_DISCONNECTED / ENOTFOUND /\n"
                           "         ECONNRESET in the log above are dropped connections, not blocks.\n"
                           "      3. Wait 15-30 min. F5 rate-limits by IP after repeated attempts;\n"
                           "         retrying immediately makes it worse.\n"
                           "      4. Nothing is lost — your existing notices and site are untouched.")
                print("  ✗ CAPTCHA NEEDED — still blocked after waiting, nothing downloaded.\n" + tip)
                ctx.close()
                return None
            try:                          # rows may be filled in by script after load
                page.wait_for_selector('a[href*=".pdf"]', timeout=15_000)
            except Exception:
                pass
            try:                          # make every link absolute, like "Save as" does
                page.evaluate("document.querySelectorAll('a[href]').forEach("
                              "a => a.setAttribute('href', a.href))")
                html = page.content()
            except Exception:
                pass
            got = listing_pdf_urls(html, url)
            print(f"  · {len(html)//1024} KB, {len(got)} PDF row(s)")
            if got:
                pages.append(html)
                counts.append((url, len(got)))
                rows += [r for r in got if r["file"] not in {x["file"] for x in rows}]
            else:
                missed.append(url)
                dbg = os.path.join(ROOT, "career.debug.html")
                open(dbg, "w", encoding="utf-8").write(html)
                links = re.findall(r"""href\s*=\s*["']([^"']+)["']""", html)
                print(f"    saved this page -> career.debug.html "
                      f"({len(links)} links, e.g. {links[:3]})")

        if not rows:
            print("  ✗ no PDF rows on any listing page — career.html left untouched.")
            ctx.close()
            return None
        # All-or-nothing, matching _http_pass. Bangladesh Bank publishes across
        # two listings; writing career.html from only the one that answered
        # would quietly delete every notice belonging to the other, and the
        # next build would drop them from the site with no error anywhere.
        if missed:
            print(f"  ✗ {len(missed)} of {len(LISTINGS)} listings returned no rows:")
            for u in missed:
                print(f"      · {u}")
            print("    career.html left untouched — saving a partial listing would\n"
                  "    silently drop every notice published on the missing page.\n"
                  "    Re-run when the portal answers; nothing has been lost.")
            ctx.close()
            return None
        dest = os.path.join(ROOT, "career.html")
        open(dest, "w", encoding="utf-8").write("\n<!-- ==== next listing ==== -->\n".join(pages))
        print(f"  ✓ listing saved -> career.html ({len(rows)} PDFs = "
              + " + ".join(str(c) for _, c in counts)
              + f" across {len(counts)} listings)")
        html = "\n".join(pages)
        new = [p for p in rows if p["file"] not in have]
        if not download:
            print(f"  · --no-download: {len(new)} PDF(s) would be fetched")
            ctx.close()
            return dest
        if not new:
            print("  ✓ no new PDFs")
            ctx.close()
            return dest

        failed = []
        for p in new:
            for attempt in range(1, 4):
                try:
                    r = ctx.request.get(p["url"], timeout=60_000)
                    if r.ok and r.body()[:4] == b"%PDF":
                        open(os.path.join(ROOT, "notices", p["file"]), "wb").write(r.body())
                        print(f"  ↓ {p['file']}  ({len(r.body())//1024} KB)")
                        break
                    reason = f"HTTP {r.status}, not a PDF"
                except Exception as e:
                    reason = f"{type(e).__name__}: {_scrub(e)}"
                if attempt < 3:
                    wait = 2 ** attempt
                    print(f"  · {p['file']} — {reason}; retry {attempt}/2 in {wait}s")
                    time.sleep(wait)
                else:
                    print(f"  ✗ {p['file']} — {reason} (gave up after 3 tries)")
                    failed.append(p["file"])
        if failed:
            print(f"  ! {len(failed)} PDF(s) missing — just rerun to pick them up: "
                  + ", ".join(failed[:3]) + ("…" if len(failed) > 3 else ""))
        ctx.close()
        return dest


def build(push: bool):
    for cmd in ([sys.executable, "parser/build_data.py", "--html", "career.html",
                 "--pdfs", "notices", "--out", "data/notices.json"],
                [sys.executable, "parser/build_site.py"]):
        r = subprocess.run(cmd, cwd=ROOT, env={**os.environ, "PYTHONUTF8": "1"})
        if r.returncode:
            sys.exit(f"failed: {' '.join(map(str, cmd))}")
    if not push:
        return

    # --- guard rails, because every one of these has bitten a first-timer ---
    if not os.path.isdir(os.path.join(ROOT, ".git")):
        print("  ! not a git repository yet — skipping push.\n"
              "    Follow HOSTING.md step 3 once, then --push works from then on.")
        return

    who = subprocess.run(["git", "config", "user.email"], cwd=ROOT,
                         capture_output=True, text=True).stdout.strip()
    if not who:
        # a commit with no identity fails outright; set a sane local default
        subprocess.run(["git", "config", "user.email", "bb-roll-finder@local"], cwd=ROOT)
        subprocess.run(["git", "config", "user.name", "BB Roll Finder"], cwd=ROOT)
        print("  · set a local git identity (first run only)")

    remote = subprocess.run(["git", "remote"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip()

    subprocess.run(["git", "add", "-A"], cwd=ROOT)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
    if not diff.returncode:
        print("  ✓ nothing changed, nothing to push")
        return

    subprocess.run(["git", "commit", "-m", "notices: auto-update"], cwd=ROOT)
    if not remote:
        print("  ! committed locally, but no GitHub remote is configured.\n"
              "    See HOSTING.md step 3 — then run this again to publish.")
        return

    r = subprocess.run(["git", "push"], cwd=ROOT)
    if r.returncode:
        print("  ! commit saved, but the push failed.\n"
              "    Usually this is the GitHub login. Run:  git push\n"
              "    and complete the sign-in window, then try again.")
    else:
        print("  ✓ pushed — your site rebuilds in about 30 seconds")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true", help="offline: list what's missing")
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--log", metavar="FILE", help="append a timestamped log line")
    ap.add_argument("--browser", metavar="EXE",
                    help="path to brave.exe / chrome.exe (default: auto-detect Brave, then Chrome)")
    ap.add_argument("--bundled", action="store_true",
                    help="use Playwright's own Chromium instead of Brave/Chrome")
    ap.add_argument("--session", metavar="FILE", default=SESSION_FILE,
                    help="browser session to replay (DevTools cookie or 'Copy as cURL'); "
                         f"default {os.path.relpath(SESSION_FILE, ROOT)} if present")
    ap.add_argument("--force-browser", action="store_true",
                    help="skip the no-browser fast path, always open a window")
    ap.add_argument("--session-test", action="store_true",
                    help="parse the session file, print cookie NAMES only, exit")
    ap.add_argument("--no-download", action="store_true",
                    help="run the fetch but stop before downloading PDFs")
    a = ap.parse_args()

    if a.session_test:
        ck, ua = _parse_session(a.session)
        print("session file: %s" % a.session)
        if not ck:
            print("  no cookies found.")
            print("  Any row from erecruitment.bb.org.bd will do, as long as the")
            print("  paste contains a cookie: DevTools -> Network -> right-click")
            print("  -> Copy -> Copy as cURL (bash). Check the file is not empty.")
            raise SystemExit(1)
        print("  format      : %s" % _LAST_FORMAT)
        print("  %d cookie(s): %s" % (len(ck), ", ".join(c["name"] for c in ck)))
        tspd = [c["name"] for c in ck if c["name"].upper().startswith("TS")]
        print("  F5 token    : " + (", ".join(tspd) if tspd
                                    else "MISSING - wrong request row?"))
        print("  user-agent  : " + ((ua[:58] + "...") if ua
                                    else "not found (default used)"))
        raise SystemExit(0)

    if a.log:
        class _Tee:
            def __init__(self, fh): self.fh = fh
            def write(self, s):
                sys.__stdout__.write(s); self.fh.write(s); self.fh.flush()
            def flush(self):
                sys.__stdout__.flush(); self.fh.flush()
        d = os.path.dirname(os.path.abspath(a.log))
        if d:
            os.makedirs(d, exist_ok=True)
        fh = open(a.log, "a", encoding="utf-8")
        fh.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        sys.stdout = _Tee(fh)

    if a.plan:
        rows = plan(os.path.join(ROOT, "career.html"))
        print(f"{len(rows)} notices in the saved listing\n")
        for r in rows:
            mark = "have" if r["have"] else "MISSING"
            print(f"  [{mark:^7}] {str(r['jobId']):>6}  {r['file']:<42} {r['sizeKB'] or '?':>4} KB")
        return 0

    exe = None if a.bundled else find_browser(a.browser)
    if a.browser and not exe:
        sys.exit(f"browser not found: {a.browser}")
    if fetch(a.headless, a.timeout, download=not a.no_download, browser=exe,
             session=a.session, force_browser=a.force_browser) is None:
        return 1
    if a.build or a.push:
        build(a.push)
    return 0


if __name__ == "__main__":
    sys.exit(main())