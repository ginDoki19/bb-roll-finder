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

      "ok"        the real listing: no WAF markers and at least one .pdf link
      "challenge" the firewall is still in the way (JS challenge or CAPTCHA)
      "empty"     no markers but also no PDFs — wrong page, or a layout change
    """
    # markers first: the real "Request Rejected" page is only 246 bytes
    if html and any(c in html for c in CHALLENGE):
        return "challenge"
    if not html or len(html.strip()) < 200:
        return "empty"
    if not PDF_HREF.search(html):
        return "empty"
    return "ok"


def wait_for_page(page, timeout=300, quiet=False):
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
            return True, html
        if state == "empty" and time.time() - t0 > 20:
            return True, html            # clean page, no PDF rows: not a CAPTCHA
        stuck = True
        if stuck and not quiet:
            if not warned:
                print("  ⏳ WAF challenge on screen — solve the CAPTCHA in the "
                      "browser window if one appears. Waiting…", flush=True)
                warned = True
        time.sleep(2)
    try:
        return False, page.content()
    except Exception:
        return False, ""


def fetch(headless: bool, timeout: int = 300, download: bool = True,
          browser: str | None = None) -> str | None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("pip install playwright && python -m playwright install chromium")

    with sync_playwright() as pw:
        exe = browser
        print(f"  browser: {exe or 'Playwright Chromium (no Brave/Chrome found)'}")
        kw = {"executable_path": exe} if exe else {}
        ctx = pw.chromium.launch_persistent_context(
            PROFILE, headless=headless, locale="en-US", **kw,
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
            viewport={"width": 1400, "height": 900},
        )
        page = ctx.new_page()
        have = set(os.listdir(os.path.join(ROOT, "notices")))
        rows, pages = [], []
        for url in LISTINGS:
            print(f"→ {url}")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=90_000)
            except Exception as e:
                print(f"  ✗ {type(e).__name__}: {str(e)[:100]}")
                continue
            ok, html = wait_for_page(page, timeout=timeout)
            if not ok:
                print("  ✗ CAPTCHA NEEDED — still blocked after waiting, nothing downloaded.\n"
                      "    Run again WITHOUT --headless and solve it in the window.")
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
                rows += [r for r in got if r["file"] not in {x["file"] for x in rows}]
            else:
                dbg = os.path.join(ROOT, "career.debug.html")
                open(dbg, "w", encoding="utf-8").write(html)
                links = re.findall(r"""href\s*=\s*["']([^"']+)["']""", html)
                print(f"    saved this page -> career.debug.html "
                      f"({len(links)} links, e.g. {links[:3]})")

        if not rows:
            print("  ✗ no PDF rows on any listing page — career.html left untouched.")
            ctx.close()
            return None
        dest = os.path.join(ROOT, "career.html")
        open(dest, "w", encoding="utf-8").write("\n<!-- ==== next listing ==== -->\n".join(pages))
        print(f"  ✓ listing saved -> career.html ({len(rows)} PDFs)")
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

        for p in new:
            try:
                r = ctx.request.get(p["url"], timeout=60_000)
                if r.ok and r.body()[:4] == b"%PDF":
                    open(os.path.join(ROOT, "notices", p["file"]), "wb").write(r.body())
                    print(f"  ↓ {p['file']}  ({len(r.body())//1024} KB)")
                else:
                    print(f"  ✗ {p['file']} — HTTP {r.status}, not a PDF")
            except Exception as e:
                print(f"  ✗ {p['file']} — {type(e).__name__}: {e}")
        ctx.close()
        return dest


def build(push: bool):
    for cmd in ([sys.executable, "parser/build_data.py", "--html", "career.html",
                 "--pdfs", "notices", "--out", "data/notices.json"],
                [sys.executable, "parser/build_site.py"]):
        r = subprocess.run(cmd, cwd=ROOT, env={**os.environ, "PYTHONUTF8": "1"})
        if r.returncode:
            sys.exit(f"failed: {' '.join(map(str, cmd))}")
    if push:
        subprocess.run(["git", "add", "-A"], cwd=ROOT)
        diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
        if diff.returncode:                                    # something changed
            subprocess.run(["git", "commit", "-m", "notices: auto-update"], cwd=ROOT)
            subprocess.run(["git", "push"], cwd=ROOT)
            print("  ✓ pushed")
        else:
            print("  ✓ nothing to commit")


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
    ap.add_argument("--no-download", action="store_true",
                    help="run the fetch but stop before downloading PDFs")
    a = ap.parse_args()

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
    if fetch(a.headless, a.timeout, download=not a.no_download, browser=exe) is None:
        return 1
    if a.build or a.push:
        build(a.push)
    return 0


if __name__ == "__main__":
    sys.exit(main())