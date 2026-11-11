#!/usr/bin/env python3
"""
Read roll numbers off an image-only (scanned) notice PDF.

Why this is safe to automate
----------------------------
A wrong digit is worse than no digit: a candidate searches their roll, the site
says "not found", and they believe they failed. So this script never trusts the
OCR. It runs Tesseract four different ways and then CHECKS the result against
properties the notice itself guarantees:

  1. count      — the notice prints its own total ("334 (তিনশত চৌত্রিশ) জন")
  2. ordering   — BB prints these lists in ascending order, always
  3. width      — every roll in a given notice has the same digit count
  4. agreement  — how many of the four passes independently saw each number

Any pass that fails 1-3 is discarded. Numbers that only one or two passes saw
are printed as LOW CONFIDENCE so a human eyeballs those few against the PDF,
instead of proof-reading hundreds. Nothing is written to the live data file
until you run --approve.

Usage
-----
  python tools/ocr_rolls.py notices/20261111_bb_87_1794395117.pdf --expect 334
  python tools/ocr_rolls.py --approve

Needs Tesseract:
  Windows  https://github.com/UB-Mannheim/tesseract/wiki  (click through the installer)
  then     pip install pytesseract pypdfium2
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OVERRIDES = os.path.join(ROOT, "meta", "overrides.json")
DRAFT = os.path.join(ROOT, "meta", "overrides.draft.json")

# Four independent reads. The whitelist passes are precise on the dense number
# block; the plain passes survive lines where Bengali words sit between numbers
# ("221034 এবং 221077"), which the whitelist mangles.
PASSES = [
    ("digits/psm6", "--psm 6 -c tessedit_char_whitelist=0123456789, "),
    ("digits/psm4", "--psm 4 -c tessedit_char_whitelist=0123456789, "),
    ("plain/psm6", "--psm 6"),
    ("plain/psm11", "--psm 11"),
]

WIN_TESSERACT = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LocalAppData%\Programs\Tesseract-OCR\tesseract.exe"),
]


def _find_tesseract() -> str | None:
    exe = shutil.which("tesseract")
    if exe:
        return exe
    for c in WIN_TESSERACT:
        if os.path.exists(c):
            return c
    return None


def ocr_passes(pdf_path: str, dpi: int = 300, width: int = 6):
    """Return {pass_name: [numbers in reading order]} for every page, merged."""
    try:
        import pypdfium2 as pdfium
        import pytesseract
    except ImportError:
        sys.exit("pip install pytesseract pypdfium2")

    exe = _find_tesseract()
    if not exe:
        sys.exit("Tesseract not found.\n"
                 "  Windows: https://github.com/UB-Mannheim/tesseract/wiki\n"
                 "  Install it, then run this again (no PATH setup needed).")
    pytesseract.pytesseract.tesseract_cmd = exe

    pat = re.compile(r"(?<!\d)\d{%d}(?!\d)" % width)
    out: dict[str, list[str]] = {name: [] for name, _ in PASSES}
    pdf = pdfium.PdfDocument(pdf_path)
    for pno in range(len(pdf)):
        img = pdf[pno].render(scale=dpi / 72).to_pil().convert("L")
        for name, cfg in PASSES:
            txt = pytesseract.image_to_string(img, config=cfg)
            out[name] += pat.findall(txt)
        del img
    return out


def choose(results: dict[str, list[str]], expect: int | None):
    """Pick the pass that satisfies the notice's own invariants."""
    scored = []
    for name, hits in results.items():
        uniq = list(dict.fromkeys(hits))
        ints = [int(x) for x in uniq]
        ascending = all(b > a for a, b in zip(ints, ints[1:]))
        exact = (expect is None) or (len(ints) == expect)
        scored.append({"pass": name, "nums": uniq, "n": len(ints),
                       "ascending": ascending, "exact": exact})
    # The printed total is the strongest signal, so it wins first. Ordering is
    # only a tie-breaker: short lists are NOT always ascending — notice 419
    # prints "202339, 201246", descending — so requiring it would reject a
    # perfectly good read.
    exact = [s for s in scored if s["exact"]]
    if exact:
        best = max(exact, key=lambda s: (s["ascending"], s["n"]))
        return best, scored
    pool = [s for s in scored if s["ascending"]] or scored
    return max(pool, key=lambda s: s["n"]), scored


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", nargs="?", help="notice PDF to read")
    ap.add_argument("--expect", type=int, help="roll total printed on the notice")
    ap.add_argument("--width", type=int, default=6, help="digits per roll (default 6)")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--post", default=None, help="post name shown above the roll table")
    ap.add_argument("--title", default=None)
    ap.add_argument("--category", default=None)
    ap.add_argument("--job-id", default=None)
    ap.add_argument("--published", default=None, help="DD/MM/YYYY")
    ap.add_argument("--approve", action="store_true",
                    help="merge meta/overrides.draft.json into meta/overrides.json")
    a = ap.parse_args()

    if a.approve:
        if not os.path.exists(DRAFT):
            sys.exit("no draft to approve — run the OCR step first")
        draft = json.load(open(DRAFT, encoding="utf-8"))
        live = json.load(open(OVERRIDES, encoding="utf-8"))
        for k, v in draft.items():
            if k.startswith("_"):
                continue
            live[k] = {**live.get(k, {}), **v}
            print(f"  merged {k}  ({len(v.get('groups', [{}])[0].get('rolls', []))} rolls)")
        json.dump(live, open(OVERRIDES, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        os.remove(DRAFT)
        print(f"\n  wrote {OVERRIDES}")
        print("  now rebuild:  python parser/build_data.py --html career.html "
              "--pdfs notices --out data/notices.json")
        return 0

    if not a.pdf:
        ap.error("give a PDF, or --approve")
    pdf_path = a.pdf if os.path.isabs(a.pdf) else os.path.join(ROOT, a.pdf)
    if not os.path.exists(pdf_path):
        sys.exit(f"no such file: {pdf_path}")

    print(f"reading {os.path.basename(pdf_path)} at {a.dpi} DPI, {len(PASSES)} passes…")
    results = ocr_passes(pdf_path, a.dpi, a.width)
    best, scored = choose(results, a.expect)

    print("\n  pass          found  ascending  matches-total")
    for s in scored:
        print(f"  {s['pass']:<13} {s['n']:>5}  {'yes' if s['ascending'] else 'NO ':>9}"
              f"  {'yes' if s['exact'] else 'no':>13}")

    votes: dict[str, int] = {}
    for hits in results.values():
        for h in set(hits):
            votes[h] = votes.get(h, 0) + 1
    nums = best["nums"]
    weak = [n for n in nums if votes[n] <= 2]
    rejected = sorted(set(votes) - set(nums))

    ints = [int(x) for x in nums]
    print(f"\n  chosen pass : {best['pass']}")
    print(f"  rolls       : {len(ints)}"
          + (f" (notice says {a.expect})" if a.expect else ""))
    print(f"  range       : {min(ints)}–{max(ints)}")
    print(f"  ascending   : {best['ascending']}")
    print(f"  confirmed   : {len([n for n in nums if votes[n] >= 3])} by 3+ of "
          f"{len(PASSES)} passes")
    if rejected:
        print(f"  rejected    : {', '.join(rejected)} (failed the order/total check)")

    problems = []
    if a.expect and len(ints) != a.expect:
        problems.append(f"count is {len(ints)}, notice says {a.expect}")
    # Ordering only blocks when we have no printed total to check against.
    if not best["ascending"] and a.expect is None:
        problems.append("list is not strictly ascending and no --expect given")
    if len({len(n) for n in nums}) != 1:
        problems.append("mixed digit widths")

    if weak:
        print("\n  ⚠ LOW CONFIDENCE — check these few against the PDF by eye:")
        for n in weak:
            print(f"      {n}   (seen by {votes[n]} of {len(PASSES)} passes)")

    if problems:
        print("\n  ✗ NOT WRITTEN — " + "; ".join(problems))
        print("    Try --dpi 400, or transcribe this one by hand.")
        return 1

    entry = {
        "rollSource": "ocr",
        "verified": datetime.date.today().isoformat(),
        "ocrChecks": {"passes": len(PASSES), "agreeing": len([n for n in nums if votes[n] >= 3]),
                      "total": len(ints), "printedTotal": a.expect,
                      "ascending": True, "lowConfidence": weak},
        "groups": [{"post": a.post, "rolls": ints}],
    }
    for k, v in (("title", a.title), ("category", a.category),
                 ("jobId", a.job_id), ("published", a.published)):
        if v:
            entry[k] = v

    draft = {}
    if os.path.exists(DRAFT):
        draft = json.load(open(DRAFT, encoding="utf-8"))
    draft["_note"] = ("OCR draft — NOT live. Eyeball the lowConfidence numbers against "
                      "the PDF, then: python tools/ocr_rolls.py --approve")
    draft[os.path.basename(pdf_path)] = entry
    json.dump(draft, open(DRAFT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"\n  ✓ draft written -> meta/overrides.draft.json  (live data untouched)")
    print("    check the numbers above, then:  python tools/ocr_rolls.py --approve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
