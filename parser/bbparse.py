#!/usr/bin/env python3
"""
bbparse.py — extract structured data from Bangladesh Bank / BSCS recruitment PDFs.

Verified against six real notices. Three genuinely different layouts exist:

  1. CENTRE  — a table with "Starting Roll" / "Ending Roll" columns:
               roll number -> which school/college.        (357/2026, 86/2026)
  2. BATCH   — a table of comma-separated 6-digit rolls beside a date/time
               column: pass list / viva schedule.          (85/2026, 350/2026)
  3. LIST    — a bare list of individual rolls, no table at all:
               "primarily selected candidates".            (1/2026)
  Anything else is indexed and linked but not searchable (356/2026).

Design notes
------------
* Every one of these PDFs embeds a legacy 8-bit Bengali font (Bijoy/SutonnyMJ),
  so extract_text() returns mojibake for Bangla: "mKvj 10:00 Uv" = "সকাল ১০:০০ টা".
  Digits are plain ASCII; English titles and addresses come through perfectly.
  So the searchable core of every notice survives intact.
* Bold runs are duplicated glyph-by-glyph ("110088000000" = 108000), hence
  collapse(). Needed only where values come from raw text rather than table cells.
* Tables are read with pdfplumber's column detection, so "Milestone College" and
  "Diabari, Turag-Dhaka" stay separate instead of being guessed apart by regex.
* Wrapped cells split one visual row across several table rows; parse_batches()
  therefore carries the last-seen date forward instead of trusting row alignment.

CLI
    python3 bbparse.py notice.pdf [...]       # human summary
    python3 bbparse.py --json notice.pdf      # full JSON
"""

from __future__ import annotations

import json
import os
import re
import sys

try:
    import pdfplumber
except ImportError:
    sys.exit("pip install pdfplumber")

try:
    from bijoy2unicode import convert as bn
except ImportError:                                     # converter is optional
    def bn(s):
        return s

# a Bangla venue name ends at one of these words; everything after is the address
BN_INSTITUTION = re.compile(
    r"(কলেজ|বিদ্যালয়|ইনস্টিটিউট|স্কুল|কেন্দ্র|একাডেমি|মহাবিদ্যালয়"
    r"|ভবন|হল|ক্যাম্পাস|প্রতিষ্ঠান|মিলনায়তন|অডিটোরিয়াম|বিশ্ববিদ্যালয়|মাদ্রাসা)")


# ----------------------------------------------------------------- primitives
def collapse(s: str) -> str:
    """Repair duplicated bold glyphs: '110088000000' -> '108000'."""
    s = (s or "").strip()
    if len(s) >= 4 and len(s) % 2 == 0 and all(s[i] == s[i + 1] for i in range(0, len(s), 2)):
        return s[::2]
    return s


def cell(v) -> str:
    return re.sub(r"\s+", " ", (v or "")).strip()


def as_int(v):
    v = re.sub(r"[^\d]", "", cell(v))
    return int(v) if v else None


def rolls_in(text: str) -> list[int]:
    seen, out = set(), []
    for r in re.findall(r"\b(\d{6})\b", text or ""):
        n = int(r)
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


# Mojibake period words -> 12h meridian.  These are the Bijoy-encoded forms.
PERIODS = [
    ("mKvj", "AM"),      # সকাল
    ("`ycyi", "PM"),     # দুপুর
    ("weKvj", "PM"),     # বিকাল
    ("we‡Kvj", "PM"),    # বিকাল (alt)
    ("we‡K‡j", "PM"),    # বিকেলে
    ("‡ejv", "PM"),      # বেলা
    ("ivZ", "PM"),       # রাত
]
TIME_RE = re.compile(r"(?<!\d)(\d{1,2})[.:](\d{2})(?!\d)")

MONTHS = None  # dates in these notices are numeric dd/mm/yyyy only

DATE_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")


def dkey(d: str) -> tuple[int, int, int] | None:
    m = DATE_RE.fullmatch(d.strip()) if d else None
    return (int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else None


def _tkey(label: str) -> str:
    """Comparison key for a clock label.

    Sittings are split when a row's time differs from the current one. Doing
    that on the raw string meant "10:00 AM", "10:00AM" and "10:00  am" read as
    three different sittings and the batch numbering drifted for the rest of
    the notice. Only the digits and the meridian letter carry meaning here.
    """
    return re.sub(r"[^0-9apAP]", "", (label or "")).lower()


def times_in(text: str) -> list[dict]:
    """All clock times in a blob, each tagged with the meridian from its period word."""
    text = text or ""
    marks = [(m.start(), mer, " ".join(m.groups())) for m in re.finditer(
        "|".join(re.escape(p) for p, _ in PERIODS), text) for mer in
        [next(v for p, v in PERIODS if p in m.group(0))]]
    out = []
    for m in TIME_RE.finditer(text):
        h, mi = int(m.group(1)), m.group(2)
        if not (0 <= h <= 23):
            continue
        mer = None
        for pos, mk, _ in marks:
            if pos < m.start():
                mer = mk
        hh = h
        if mer == "PM" and hh < 12:
            hh += 12
        if mer == "AM" and hh == 12:
            hh = 0
        label = f"{(hh % 12) or 12}:{mi} {'AM' if hh < 12 else 'PM'}"
        out.append({"h": h, "m": mi, "meridian": mer, "24": f"{hh:02d}:{mi}", "label": label})
    return out


# ------------------------------------------------------------------- detectors
def _hdr(table) -> str:
    return " ".join(cell(c) for c in (table[0] if table else [])).lower()


def is_centre_table(t) -> bool:
    h = _hdr(t)
    return ("starting" in h and "ending" in h) or ("roll" in h and "start" in h and "end" in h)


def is_rolllist_table(t) -> bool:
    return any(c and len(re.findall(r"\b\d{6}\b", c)) >= 3 for row in t[:4] for c in row)


# --------------------------------------------------------------- centre notices
def parse_centres_tables(tables) -> list[dict]:
    out = []
    for t in tables:
        if not is_centre_table(t):
            continue
        for row in t[1:]:
            cells = [cell(c) for c in row]
            if len(cells) < 5:
                continue
            six = [i for i, c in enumerate(cells) if re.fullmatch(r"\d{6}", c.replace(" ", ""))]
            if len(six) < 2:
                continue
            a, b = six[0], six[1]
            start, end = as_int(cells[a]), as_int(cells[b])
            if not start or not end or start >= end:
                continue
            # layout A: Sl | Name | Address | Start | End | Total
            sl = as_int(cells[0])
            name, address = cells[1], cells[2]
            if a < 3:  # layout B: Name | Address | Start | End | Total
                sl = None
                name, address = cells[0], cells[1]
            total = as_int(cells[b + 1]) if b + 1 < len(cells) else None
            out.append({"sl": sl, "name": name, "address": address,
                        "from": start, "to": end, "seats": total})
    return out


RANGE_TXT = re.compile(r"(\d{5,7})\s*[-–]{1,2}\s*(\d{5,16})")
SEATS_TXT = re.compile(r"\b\d{1,3}(?:,\d{3})+\b")


def parse_centres_text(text: str) -> list[dict]:
    """Fallback for Bangla notices whose table has no ruling lines (86/2026)."""
    out = []
    prev_institution = ""      # name wrapped onto its own line above the ranges
    for ln in text.splitlines():
        if not RANGE_TXT.search(ln):
            readable = bn(ln).strip()
            if readable and BN_INSTITUTION.search(readable) and len(readable) < 70:
                prev_institution = readable.strip(" ,|।")
            continue
        for m in RANGE_TXT.finditer(ln):
            a, b = collapse(m.group(1)), collapse(m.group(2))
            if not (a.isdigit() and b.isdigit()) or len(a) != len(b):
                continue
            start, end = int(a), int(b)
            if not (1 <= start < end <= 9_999_999):
                continue
            head = ln[: m.start()].strip()
            head = re.sub(r"^\s*\d+\.\s*", "", head)
            seats = SEATS_TXT.findall(ln[m.end():])

            # legacy font -> Unicode, then split "নাম কলেজ" from "ঠিকানা"
            readable = re.sub(r"\s+", " ", bn(head)).strip(" ,|।")
            m2 = list(BN_INSTITUTION.finditer(readable))
            if m2:
                cut = m2[-1].end()
                name_bn, address_bn = readable[:cut].strip(), readable[cut:].strip(" ,।|")
            else:
                # the cell wrapped: name sits on the previous line, this is the address
                name_bn, address_bn = prev_institution, readable.strip(" ,।|")
                if not name_bn:
                    # Nothing was carried over, so there is no name to attribute.
                    # Better to show the row's own text as the centre than to
                    # render an empty "Your centre:" heading on a seat card.
                    name_bn, address_bn = readable.strip(" ,।|"), ""
            prev_institution = ""
            if not name_bn:
                continue

            out.append({
                "sl": len(out) + 1,
                "name": name_bn, "address": address_bn,
                "nameRaw": head,
                "from": start, "to": end,
                "seats": int(seats[-1].replace(",", "")) if seats else None,
            })
    return out


# ----------------------------------------------------------- batch/roll notices
def parse_batches(tables) -> list[dict]:
    """
    Walk table rows in reading order and group rolls into sittings.

    A wrapped list spreads one sitting across many table rows, so the date and
    time appear only on the sitting's first row. A new sitting therefore starts
    when a row carries a date or a time that differs from the current one --
    not when the date changes, because 85/2026 holds three separate sittings on
    28/11/2026 (08:30, 10:30 and 13:30) that a date-only key would fuse.
    """
    groups: list[dict] = []
    cur = None

    for t in tables:
        if not is_rolllist_table(t):
            continue
        for row in t:
            cells = [cell(c) for c in row]
            blob = " ".join(cells)
            rolls = rolls_in(blob)
            d = DATE_RE.search(blob)
            tl = [x["label"] for x in times_in(blob)]
            if not rolls and not (d or tl):
                continue

            new = cur is None
            if cur is not None:
                if d and cur.get("date") and d.group(0) != cur["date"]:
                    new = True
                elif tl and cur.get("times") and _tkey(tl[0]) != _tkey(cur["times"][0]):
                    new = True

            if new:
                prev = groups[-1]["date"] if groups else None
                cur = {"sl": f"{len(groups) + 1:02d}",
                       "date": d.group(0) if d else prev,
                       "times": tl, "rolls": []}
                groups.append(cur)
            else:
                if d and not cur.get("date"):
                    cur["date"] = d.group(0)
                if tl and not cur.get("times"):
                    cur["times"] = tl

            if cur is not None:
                cur["rolls"].extend(r for r in rolls if r not in cur["rolls"])

    for i, g in enumerate(groups, 1):
        g["sl"] = f"{i:02d}"
        g["count"] = len(g["rolls"])
    return groups


# --------------------------------------------------------------------- notice
def _looks_scanned(page, txt: str = "") -> bool:
    """
    True when the page is a photograph of a document rather than real text.

    Signal: a single image covering >=90% of the page.

    Measured across all 9 notices, the separation is absolute — the two scans
    (83/2026, 372/2026) cover 100.0% of the page, while every real text notice
    peaks at 1.0% (logos and signature stamps). Nothing lands in between, so a
    90% threshold cannot misfire on the Bijoy pages the converter handles.

    Text-quality heuristics were tried and rejected: a Bengali scan's OCR layer
    is 72% alphanumeric (`fi {rifa3falB fart3`), indistinguishable from real text.
    """
    try:
        area = float(page.width) * float(page.height)
        cover = 0.0
        for im in page.images:
            w = abs(float(im["x1"]) - float(im["x0"]))
            h = abs(float(im["bottom"]) - float(im["top"]))
            cover = max(cover, (w * h) / area if area else 0.0)
    except Exception:
        return False
    return cover >= 0.90


def parse_pdf(path: str, published: str | None = None) -> dict:
    tables, texts = [], []
    scanned_pages = 0
    with pdfplumber.open(path) as pdf:
        for p in pdf.pages:
            t = p.extract_text() or ""
            texts.append(t)
            if _looks_scanned(p, t):
                scanned_pages += 1
            try:
                tables.extend(p.extract_tables() or [])
            except Exception:
                pass
    text = "\n".join(texts)
    scanned = bool(texts) and scanned_pages == len(texts)

    centres = parse_centres_tables(tables) or parse_centres_text(text)
    batches = parse_batches(tables)

    rolls: dict[int, dict] = {}
    for b in batches:
        for r in b["rolls"]:
            rolls[r] = {"date": b["date"], "time": (b["times"] or [None])[0], "batch": b["sl"]}

    kind = "centre" if centres else ("batch" if rolls else "generic")
    if scanned:
        kind = "scanned"          # nothing reliable to extract; link to the PDF

    # bare pass/shortlist list with no table and no date column
    if kind == "generic":
        allr = rolls_in(text)
        if len(allr) >= 20:
            kind = "list"
            rolls = {r: {} for r in allr}

    dates = [m.group(0) for m in DATE_RE.finditer(text)]
    exam = None
    if published:
        pk = dkey(published)
        later = sorted({d for d in dates if dkey(d) and pk and dkey(d) >= pk}, key=dkey)
        exam = later[0] if later else None
    else:
        exam = dates[0] if dates else None

    window = times_in(text)
    return {
        "file": os.path.basename(path),
        "noticeNo": (re.search(r"\b(\d{1,4}/\d{4})\b", text) or [None, None])[1],
        "kind": kind,
        "pages": len(texts),
        "examDate": exam,
        "examWindow": [window[0]["label"], window[-1]["label"]] if len(window) >= 2 else None,
        "centres": centres,
        "batches": batches,
        "rolls": rolls,
        "rollCount": len(rolls),
        "seats": sum(c["seats"] or 0 for c in centres) if centres else None,
        "datesSeen": sorted(set(dates), key=lambda d: (dkey(d) or (0, 0, 0))),
        "scanned": scanned,
        "_mojibake": True,
    }


# ------------------------------------------------------------------------ cli
def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    if argv[1] == "--json":
        print(json.dumps(parse_pdf(argv[2]), ensure_ascii=False, indent=2))
        return 0

    for path in argv[1:]:
        d = parse_pdf(path)
        print(f"\n{d['file']}")
        print(f"  notice {d['noticeNo']} · kind={d['kind']} · {d['pages']}p · exam={d['examDate']} "
              f"{'/'.join(d['examWindow']) if d['examWindow'] else ''}")
        if d["centres"]:
            print(f"  centres={len(d['centres'])} seats={d['seats']} "
                  f"span={d['centres'][0]['from']}–{d['centres'][-1]['to']}")
            for c in d["centres"][:3]:
                print(f"    {c['from']}–{c['to']}  {c['name'][:52]:<52} {c['address'][:26]}")
        if d["batches"]:
            print(f"  batches={len(d['batches'])} rolls={d['rollCount']}")
            for b in d["batches"][:4]:
                print(f"    {b['sl']}  {b['date']}  {(b['times'] or ['?'])[0]:>8}  {b['count']:>3} rolls")
        if d["kind"] == "list":
            print(f"  flat roll list: {d['rollCount']} rolls")
        if d["kind"] == "generic":
            print(f"  indexed only · dates {', '.join(d['datesSeen'][:4])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
