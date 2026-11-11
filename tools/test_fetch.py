#!/usr/bin/env python3
"""
test_fetch.py — staged verification of the notice fetcher.

Each stage isolates one failure mode, so a red result points at a single cause
instead of "it didn't work". Stages T1–T4 need no network and no browser, and are
safe to run anywhere. Stages T5–T9 open a real browser against the live portal.

    python3 tools/test_fetch.py             # T1–T4  (offline, ~2 s)
    python3 tools/test_fetch.py --live      # T1–T9  (opens a browser window)
    python3 tools/test_fetch.py --live --headless
    python3 tools/test_fetch.py --live --solve   # wait for you to solve a CAPTCHA
    python3 tools/test_fetch.py --only T9 --live # re-run one stage

Exit code 0 = every attempted stage passed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import fetch_notices as fn                                       # noqa: E402

RESULTS: list[tuple[str, str, str]] = []      # (stage, status, detail)


def record(stage: str, status: str, detail: str = ""):
    RESULTS.append((stage, status, detail))
    icon = {"PASS": "✓", "FAIL": "✗", "SKIP": "·", "INFO": "…"}[status]
    print(f"  {icon} {stage:<4} {status:<5} {detail}")


# --------------------------------------------------------------------- offline
def t1_environment():
    """Python, pdfplumber, playwright, chromium — the four things that must exist."""
    ok = True
    v = sys.version_info
    if v >= (3, 9):
        record("T1a", "PASS", f"python {v.major}.{v.minor}.{v.micro}")
    else:
        record("T1a", "FAIL", f"python {v.major}.{v.minor} — need 3.9+"); ok = False

    try:
        import pdfplumber  # noqa: F401
        record("T1b", "PASS", "pdfplumber installed")
    except ImportError:
        record("T1b", "FAIL", "pip install pdfplumber"); ok = False

    try:
        import playwright  # noqa: F401
        record("T1c", "PASS", "playwright installed")
    except ImportError:
        record("T1c", "FAIL", "pip install playwright"); ok = False

    try:
        import curl_cffi  # noqa: F401
        record("T1e", "PASS", "curl_cffi installed — no-browser fetch can use Chrome TLS")
    except ImportError:
        record("T1e", "INFO", "curl_cffi missing (optional) — pip install curl_cffi "
                              "lets the fetch skip the browser more often")

    if os.path.isdir(fn.PROFILE):
        size = sum(os.path.getsize(os.path.join(dp, f))
                   for dp, _, fs in os.walk(fn.PROFILE) for f in fs
                   if os.path.exists(os.path.join(dp, f)))
        record("T1d", "INFO", f"browser profile exists ({size//1024} KB) — F5 cookie likely cached")
    else:
        record("T1d", "INFO", "no profile yet — first run will need a CAPTCHA")
    return ok


def t2_listing_parse():
    """The saved listing page must still yield the expected PDF rows."""
    path = os.path.join(ROOT, "career.html")
    if not os.path.exists(path):
        record("T2", "FAIL", "career.html missing"); return False
    rows = fn.listing_pdf_urls(open(path, encoding="utf-8", errors="replace").read())
    if not rows:
        record("T2", "FAIL", "0 PDF rows parsed — listing layout changed?"); return False
    bad = [r for r in rows if not r["file"].endswith(".pdf") or not r["url"].startswith("https://")]
    record("T2", "PASS" if not bad else "FAIL",
           f"{len(rows)} rows, {len(bad)} malformed, e.g. {rows[0]['file']}")
    return not bad


def t3_page_state():
    """The WAF classifier, against known-good and known-bad HTML."""
    fixtures = {
        "real listing": ('<html><body><table><tr><td>26101</td><td>Seat plan notice for the exam</td>'
                         '<td><a href="https://erecruitment.bb.org.bd/career/20261108_bscs_357_1.pdf">PDF</a>'
                         ' (196 KB)</td></tr></table>' + "x" * 200 + "</body></html>", "ok"),
        # THE REGRESSION: the real listing still carries F5's injected TSPD
        # script after the challenge clears. Classifying on the marker made
        # every successful fetch look like a block.
        "real listing + F5 TSPD script": (
            '<html><head><script type="text/javascript" src="/TSPD/08f4a2b1c3'
            '00005a?type=12"></script></head><body><table><tr><td>303</td>'
            '<td>Circular regarding Preliminary Test Result and Schedule</td>'
            '<td><a href="https://erecruitment.bb.org.bd/career/20261111_bb_303_1.pdf">'
            'Download PDF</a> (600 KB)</td></tr></table>' + "x" * 200
            + '</body></html>', "ok"),
        "bobcmn JS challenge, no rows": (
            '<html><head><script>window["bobcmn"]="11201111";</script></head>'
            '<body><noscript>Please enable JavaScript</noscript>' + "x" * 300
            + '</body></html>', "challenge"),
        "css-only .pdf": ("<html><style>.pdf button, .x {color:red}</style><body>" + "x" * 300
                          + "</body></html>", "empty"),
        "F5 captcha": ('<html><head><script>window["bobcmn"]="1011111010";</script></head>'
                       '<body>What code is in the image? <input id="x"/></body></html>', "challenge"),
        "req rejected": ("<html><head><title>Request Rejected</title></head>"
                         "<body>The requested URL was rejected.</body></html>", "challenge"),
        "empty response": ("", "empty"),
        "wrong page": ("<html><body><h1>Portal down for maintenance</h1></body></html>", "empty"),
    }
    bad = 0
    for name, (html, want) in fixtures.items():
        got = fn.page_state(html)
        if got != want:
            bad += 1
            record("T3", "FAIL", f"{name}: got {got!r}, expected {want!r}")
    if not bad:
        record("T3", "PASS", f"{len(fixtures)} classifier fixtures")
    return not bad


def t4_build_pipeline():
    """data/notices.json must rebuild and satisfy the invariants."""
    steps = [[sys.executable, "parser/build_data.py", "--html", "career.html",
              "--pdfs", "notices", "--out", "data/notices.json"],
             [sys.executable, "parser/build_site.py"],
             [sys.executable, "tools/selftest.py"]]
    for cmd in steps:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           env={**os.environ, "PYTHONUTF8": "1"})
        if r.returncode:
            record("T4", "FAIL", f"{' '.join(map(str, cmd))} → exit {r.returncode}: "
                                 f"{(r.stderr or r.stdout).strip().splitlines()[-1][:90]}")
            return False
    n = len(json.load(open(os.path.join(ROOT, "data", "notices.json"), encoding="utf-8"))["notices"])
    record("T4", "PASS", f"rebuild + selftest OK ({n} notices)")
    return True


# ------------------------------------------------------------------------ live
def live_stages(headless: bool, solve: bool, timeout: int):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        record("T5", "SKIP", "playwright not installed")
        return

    with sync_playwright() as pw:
        # T5 — does a browser exist at all?
        try:
            browser_probe = pw.chromium.launch(headless=True, args=["--no-sandbox"])
            version = browser_probe.version
            browser_probe.close()
            record("T5", "PASS", f"chromium {version} launches")
        except Exception as e:
            record("T5", "FAIL", f"cannot launch chromium: {type(e).__name__} — "
                                 "run: py -m playwright install chromium")
            return

        # T6 — navigate and classify
        ctx = pw.chromium.launch_persistent_context(
            fn.PROFILE, headless=headless, locale="en-US",
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
            viewport={"width": 1400, "height": 900},
        )
        page = ctx.new_page()
        t0 = time.time()
        try:
            resp = page.goto(fn.LISTING, wait_until="domcontentloaded", timeout=90_000)
            status = resp.status if resp else None
        except Exception as e:
            record("T6", "FAIL", f"navigation error: {type(e).__name__}: {str(e)[:80]}")
            ctx.close(); return
        page.wait_for_timeout(3000)
        html = page.content()
        state = fn.page_state(html)
        record("T6", "INFO" if state != "ok" else "PASS",
               f"HTTP {status} · {len(html)//1024} KB · state={state} · {time.time()-t0:.1f}s")

        # T7 — wait it out / let the human solve it
        if state != "ok":
            if solve:
                print("      ┌─────────────────────────────────────────────┐")
                print("      │ solve the CAPTCHA in the browser window now │")
                print(f"      └─────────────── waiting up to {timeout}s ───────────────┘")
                ok, html = fn.wait_for_page(page, timeout=timeout, quiet=False)
                state = fn.page_state(html)
                record("T7", "PASS" if ok else "FAIL",
                       "challenge cleared" if ok else "still blocked — see TESTING.md #1")
            else:
                record("T7", "SKIP", "challenge present; re-run with --solve to clear it")
                ctx.close(); return
        else:
            record("T7", "SKIP", "no challenge to clear")

        # T8 — does the live page yield the same number of rows as the saved copy?
        live_rows = fn.listing_pdf_urls(html)
        saved = fn.listing_pdf_urls(open(os.path.join(ROOT, "career.html"),
                                         encoding="utf-8", errors="replace").read())
        new = [r for r in live_rows if r["file"] not in {s["file"] for s in saved}]
        record("T8", "PASS" if live_rows else "FAIL",
               f"{len(live_rows)} rows live vs {len(saved)} saved · {len(new)} new")

        # T9 — download ONE pdf and prove it's really a PDF
        target = (new or live_rows or [None])[0]
        if not target:
            record("T9", "SKIP", "no PDF url to test")
            ctx.close(); return
        try:
            r = ctx.request.get(target["url"], timeout=60_000)
            body = r.body()
            magic = body[:5]
            is_pdf = magic == b"%PDF-"
            stated = target["sizeKB"]
            got_kb = len(body) // 1024
            detail = (f"HTTP {r.status} · {got_kb} KB (listing says {stated or '?'} KB) · "
                      f"magic={magic!r} · {target['file']}")
            if is_pdf and (not stated or abs(got_kb - stated) <= max(5, stated * 0.05)):
                record("T9", "PASS", detail)
            else:
                record("T9", "FAIL", detail + " — got an HTML challenge page, not a PDF")
        except Exception as e:
            record("T9", "FAIL", f"{type(e).__name__}: {str(e)[:90]}")
        ctx.close()


# ------------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="include browser stages T5–T9")
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--solve", action="store_true", help="wait for you to solve the CAPTCHA")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--only", help="run a single stage, e.g. T9")
    a = ap.parse_args()

    print("\nBB notice fetcher — staged tests\n")
    only = (a.only or "").upper()

    def want(stage):
        return not only or only.startswith(stage) or stage.startswith(only)

    if want("T1"):
        print("— offline —")
        t1_environment()
        t2_listing_parse()
        t3_page_state()
        t4_build_pipeline()

    if a.live and want("T5"):
        print(f"\n— live ({'headless' if a.headless else 'headed browser'}) —")
        live_stages(a.headless, a.solve, a.timeout)

    fails = [r for r in RESULTS if r[1] == "FAIL"]
    skipped = [r for r in RESULTS if r[1] == "SKIP"]
    print(f"\n{len(RESULTS)} checks · {len(RESULTS) - len(fails) - len(skipped)} passed · "
          f"{len(fails)} failed · {len(skipped)} skipped")
    if fails:
        print("see TESTING.md for the failure table")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())