#!/usr/bin/env python3
"""
build_data.py — assemble data/notices.json from the listing page + notice PDFs.

Inputs
    career.html          a saved copy of  https://erecruitment.bb.org.bd/career/jobopportunity.php
                         (Ctrl+S in the browser; the live page is behind a CAPTCHA WAF)
    notices/*.pdf        the PDFs, named exactly as the site serves them

Output
    data/notices.json    everything the static site needs; no server, no scraping at runtime

Usage
    python3 build_data.py --html ../career.html --pdfs ../notices --out ../data/notices.json
"""

from __future__ import annotations

import argparse
import html as html_mod
import json
import os
import re
import sys
from urllib.parse import urljoin

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbparse  # noqa: E402


# ------------------------------------------------------------------ html index
_BASE = "https://erecruitment.bb.org.bd/career/jobopportunity.php"
_PDF_HREF = re.compile(r"""href\s*=\s*["']([^"'<>]+?\.pdf)(?:\?[^"']*)?["']""", re.I)


def parse_listing(path: str) -> list[dict]:
    h = open(path, encoding="utf-8", errors="replace").read()
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", h, re.S | re.I):
        pdf = _PDF_HREF.search(tr)
        if not pdf:
            continue
        pdf_url = urljoin(_BASE, pdf.group(1).replace("&amp;", "&").strip())
        text = html_mod.unescape(re.sub(r"<[^>]+>", "|", tr))
        text = re.sub(r"\|+", "|", text)
        parts = [p.strip() for p in text.split("|") if p.strip()]

        # job ids run 3-6 digits, and one row can carry several ("280, 282, 289")
        job = next((p for p in parts if re.fullmatch(r"\d{3,6}", p)), None)
        if job is None:
            multi = next((p for p in parts
                          if re.fullmatch(r"\d{3,6}(\s*,\s*\d{3,6})+\s*,?", p)), None)
            if multi:
                job = re.sub(r"\s*,\s*", ", ", multi.strip().rstrip(","))
        dates = [p for p in parts if re.fullmatch(r"\d{2}/\d{2}/\d{4}", p)]
        size = re.search(r"\(([\d,]+)\s*KB\)", text)
        # the human title is the longest non-boilerplate fragment
        junk = {"Details", "Download PDF", "View Details"}
        title = max((p for p in parts if p not in junk and not re.fullmatch(r"[\d/,()\sKB]+", p)
                     and p not in dates and p != job), key=len, default="")
        cat = None
        for c in ("MCQ", "VIVA", "Selected Candidate", "Written", "Offer Letter", "Practical"):
            if re.search(rf"\b{c}\b", text, re.I):
                cat = c
                break
        rows.append({
            "jobId": job,
            "category": cat,
            "title": re.sub(r"\s+", " ", title),
            "pdfUrl": pdf_url,
            "file": pdf_url.rsplit("/", 1)[-1],
            "sizeKB": int(size.group(1).replace(",", "")) if size else None,
            "published": dates[0] if dates else None,
            "closing": dates[1] if len(dates) > 1 else None,
        })
    return rows


# ---------------------------------------------------------------- normalisation
def kind_label(row: dict, parsed: dict) -> str:
    if parsed.get("scanned"):
        return "scanned"          # a photo of a notice: nothing to index
    if parsed["kind"] == "centre":
        return "seat"
    if parsed["kind"] == "list":
        return "selected"
    if parsed["kind"] == "batch":
        return "viva" if row.get("category") == "VIVA" else "result"
    return "circular"


def _exam_date(parsed: dict, row: dict, kind: str):
    """
    Pick the one date worth showing on the card.
      seat      : the date in the text, else the listing's close date (BB closes
                  the circular on exam day) -- some Bangla notices only write the
                  exam date in words, so this fallback matters.
      viva/result: the first sitting in the schedule, not a payment deadline that
                  happens to be mentioned earlier in the text.
      selected  : none; "exam date" is meaningless for a pass list.
    """
    if kind in ("viva", "result") and parsed["batches"]:
        return parsed["batches"][0]["date"]
    if kind == "seat":
        return parsed["examDate"] or row.get("closing")
    return None


def _iso(d):
    """'13/11/2026' -> '2026-11-13'. Returns None for anything unparseable.

    The client cannot compare DD/MM/YYYY strings, so every date that drives a
    countdown, a status badge or the archive split ships in ISO form as well.
    The human-readable DD/MM/YYYY field is kept untouched for display.
    """
    if not d:
        return None
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", str(d).strip())
    if not m:
        return None
    dd, mm, yy = m.groups()
    return f"{yy}-{int(mm):02d}-{int(dd):02d}"


def _merge_listing_cache(listing: list[dict], root: str) -> dict:
    """
    Accumulate listing rows across runs instead of trusting one snapshot.

    The portal publishes notices on TWO pages — jobopportunity.php (Bangladesh
    Bank) and jobopportunity_bscs.php (BSCS) — and they share no entries. Each
    page also drops older notices over time. So a single career.html can never
    describe every PDF in notices/, and overwriting it silently strips the
    English titles, job ids and published dates from everything it omits.

    The cache is keyed by PDF filename, is append-only, and a fresh row always
    wins over a cached one. Delete meta/listing-cache.json to rebuild it.
    """
    path = os.path.join(root, "meta", "listing-cache.json")
    cache = {}
    if os.path.exists(path):
        try:
            cache = json.load(open(path, encoding="utf-8"))
        except Exception:
            cache = {}
    for r in listing:
        cache[r["file"]] = {**cache.get(r["file"], {}),
                            **{k: v for k, v in r.items() if v not in (None, "")}}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(cache, fh, ensure_ascii=False, indent=1, sort_keys=True)
    return cache


def build(html_path: str, pdf_dir: str, out_path: str) -> dict:
    listing = parse_listing(html_path)
    # anchor the cache to the project root, not to wherever the html happens to be
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    by_file = _merge_listing_cache(listing, root)
    if len(by_file) > len(listing):
        print(f"  listing: {len(listing)} row(s) in career.html, "
              f"{len(by_file)} known after merging meta/listing-cache.json")
    ov_path = os.path.join(os.path.dirname(os.path.abspath(html_path)), "meta", "overrides.json")
    overrides = {}
    if os.path.exists(ov_path):
        overrides = {k: v for k, v in json.load(open(ov_path, encoding="utf-8")).items()
                     if not k.startswith("_")}
    notices = []

    for fn in sorted(os.listdir(pdf_dir)):
        if not fn.lower().endswith(".pdf"):
            continue
        row = {**overrides.get(fn, {}), **by_file.get(fn, {})}
        parsed = bbparse.parse_pdf(os.path.join(pdf_dir, fn), published=row.get("published"))

        notice = {
            "id": fn.replace(".pdf", ""),
            "noticeNo": parsed["noticeNo"],
            "kind": "selected" if row.get("groups") or row.get("rolls") else kind_label(row, parsed),
            "jobId": row.get("jobId"),
            "category": row.get("category"),
            "title": row.get("title") or f"Notice {parsed['noticeNo']}",
            "pdf": f"notices/{fn}",
            "pdfUrl": row.get("pdfUrl"),
            "sizeKB": row.get("sizeKB"),
            "published": row.get("published"),
            "closing": row.get("closing"),
            "examDate": _exam_date(parsed, row, kind_label(row, parsed)),
            "examWindow": parsed["examWindow"],
            "pages": parsed["pages"],
            "seats": parsed["seats"],
            "venue": row.get("venue"),
            "venueMapQuery": row.get("venueMapQuery"),
        }
        notice["publishedISO"] = _iso(row.get("published"))
        notice["closingISO"]   = _iso(row.get("closing"))
        notice["examDateISO"]  = _iso(notice["examDate"])

        if parsed["centres"]:
            # human-verified names win over the mojibake the legacy font produces
            fixes = {c.get("from"): c for c in row.get("centres", []) or []}
            notice["centres"] = [
                {**c, **{k: v for k, v in fixes.get(c["from"], {}).items() if k in ("name", "address", "mapQuery")}}
                for c in parsed["centres"]
            ]
            notice["rollFrom"] = parsed["centres"][0]["from"]
            notice["rollTo"] = parsed["centres"][-1]["to"]

        if parsed["batches"]:
            def _slot(x):
                d, m, y = (x["date"] or "01/01/1970").split("/")
                import re as _re
                t = _re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", x["times"][0] if x["times"] else "")
                hh = 0
                if t:
                    hh = int(t.group(1)) % 12 + (12 if t.group(3) == "PM" else 0)
                    hh = hh * 60 + int(t.group(2))
                return (y, m, d, hh)
            parsed["batches"].sort(key=_slot)

            # One record per SITTING, not per roll.
            #
            # The old shape repeated the date, time and batch for every single
            # roll ({"522567":{"d":...,"t":...,"b":...}}) — 58 bytes each, 160 KB
            # across the site. A sitting already owns all three, so the rolls
            # collapse to a plain list, delta-encoded because they arrive sorted
            # and the gaps are small. Measured on this dataset: 160.5 KB -> 28.4 KB
            # raw (5.6x), 17.5 KB -> 10.8 KB gzipped. Raw size is what the phone
            # has to JSON.parse before the search box answers.
            by_batch: dict[str, list[int]] = {}
            for r, v in parsed["rolls"].items():
                by_batch.setdefault(str(v["batch"]), []).append(int(r))

            sittings = []
            for sb in parsed["batches"]:
                rolls_here = sorted(by_batch.get(str(sb["sl"]), []))
                prev = 0
                deltas = []
                for r in rolls_here:
                    deltas.append(r - prev)
                    prev = r
                sittings.append({
                    "sl": sb["sl"],
                    "date": sb["date"],
                    "time": (sb["times"] or [None])[0],
                    "count": sb["count"],
                    "r": deltas,
                })
            notice["sittings"] = sittings

        if parsed["kind"] == "list":
            notice["rolls"] = sorted(parsed["rolls"])

        # Hand-transcribed rolls for notices the parser cannot read (image-only
        # scans). These override whatever the PDF yielded, and are flagged so the
        # UI can tell the user the numbers were typed in, not machine-extracted.
        if row.get("groups") or row.get("rolls"):
            groups = row.get("groups") or [{"post": None, "rolls": row["rolls"]}]
            allr = sorted({int(r) for g in groups for r in g["rolls"]})
            notice["rolls"] = allr
            notice["groups"] = [{"post": g.get("post"),
                                 "rolls": sorted(int(r) for r in g["rolls"])}
                                for g in groups]
            notice["rollSource"] = row.get("rollSource", "manual")
            notice["verified"] = row.get("verified")
            # provenance for OCR-recovered lists: what was cross-checked, and
            # which numbers only one or two passes agreed on. The UI shows the
            # printed total so a reader can judge the claim for themselves.
            if row.get("ocrChecks"):
                notice["ocrChecks"] = row["ocrChecks"]
            # Not every roll list means "you are hired". A preliminary-test
            # result calls people to a written exam; saying "primarily
            # selected" there would mislead. Let the override say what it is.
            for k in ("headline", "note"):
                if row.get(k):
                    notice[k] = row[k]

        if notice.get("rollSource") in ("manual", "ocr"):
            notice["rollCount"] = len(notice["rolls"])
        else:
            notice["rollCount"] = parsed["rollCount"] if parsed["kind"] != "centre" else None
        notices.append(notice)

    # newest first
    def key(n):
        d = n.get("published") or "01/01/1970"
        dd, mm, yy = d.split("/")
        return (yy, mm, dd, n["id"])

    notices.sort(key=key, reverse=True)

    data = {
        "generated": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "https://erecruitment.bb.org.bd/career/jobopportunity.php",
        "notices": notices,
    }
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    return data


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", default="../career.html")
    ap.add_argument("--pdfs", default="../notices")
    ap.add_argument("--out", default="../data/notices.json")
    a = ap.parse_args()
    d = build(a.html, a.pdfs, a.out)
    print(f"wrote {a.out}: {len(d['notices'])} notices, {os.path.getsize(a.out)//1024} KB")
    for n in d["notices"]:
        extra = ""
        if n.get("centres"):
            extra = f"{len(n['centres'])} centres, rolls {n['rollFrom']}–{n['rollTo']}"
        elif n.get("sittings"):
            tot = sum(len(s["r"]) for s in n["sittings"])
            extra = f"{tot} rolls in {len(n['sittings'])} sittings"
        elif n.get("rolls"):
            extra = f"{len(n['rolls'])} rolls"
        print(f"  [{n['kind']:<8}] {n['noticeNo'] or '?':>9}  {str(n['title'])[:62]:<62} {extra}")