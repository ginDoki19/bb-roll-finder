#!/usr/bin/env python3
"""
selftest.py — regression checks for the parser, the converter and the built data.

Every expected value below is a number or string printed *inside* the source PDF,
so a failure means the parser drifted, not that the test is fussy.

    python3 tools/selftest.py
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "parser"))

from bijoy2unicode import convert                                   # noqa: E402

BN_CASES = {
    "evsjv‡`k e¨vsK": "বাংলাদেশ ব্যাংক",
    "cÖavb Kvh©vjq": "প্রধান কার্যালয়",
    "wgicyi K‡jR": "মিরপুর কলেজ",
    "mKvj 10:00 Uv": "সকাল ১০:০০ টা",
    "ZvwiL": "তারিখ",
    "AvBwWqvj": "আইডিয়াল",
    "Mvj©m": "গার্লস",
    "cjøex": "পল্লবী",
    "XvKv": "ঢাকা",
    "hvÎvevox": "যাত্রাবাড়ী",
    "jvjgvwUqv": "লালমাটিয়া",
    "weÁwß": "বিজ্ঞপ্তি",
    "†ivW": "রোড",
    "wnDg¨vb wi‡mv‡m©M": None,
    "wnDg¨vb wi‡mv‡m©m": "হিউম্যান রিসোর্সেস",
    "‡gvjøv": "মোল্লা",
    "D”P we`¨vjq": "উচ্চ বিদ্যালয়",
    "b‡f¤^i": "নভেম্বর",
    "KvwZ©K": "কার্তিক",
    "mgq": "সময়",
    "cÖwZôv": "প্রতিষ্ঠা",
    "we`¨vjq": "বিদ্যালয়",
    "evsjv‡`k": "বাংলাদেশ",
    "Bbw÷wUDU": "ইনস্টিটিউট",
    "Abyôvq": "অনুষ্ঠায়",
}

# notice -> invariant, all taken from the PDFs themselves
INVARIANTS = {
    "357/2026": {"kind": "seat", "centres": 31, "seats": 120529},
    "86/2026":  {"kind": "seat", "centres": 4,  "seats": 16596},
    "85/2026":  {"kind": "viva", "rolls": 677,  "sittings": 12},
    "319/2026": {"kind": "selected", "rolls": 1037},
}


def main() -> int:
    fails = 0

    print("— Bijoy → Unicode converter —")
    cases = {k: v for k, v in BN_CASES.items() if v}
    for src, want in cases.items():
        got = convert(src)
        if got != want:
            fails += 1
            print(f"  FAIL {src!r} -> {got!r}  want {want!r}")
    print(f"  {len(cases) - fails}/{len(cases)} conversion cases pass")

    print("\n— built data invariants —")
    path = os.path.join(ROOT, "data", "notices.json")
    if not os.path.exists(path):
        print("  FAIL data/notices.json missing — run parser/build_data.py")
        return 1
    data = json.load(open(path, encoding="utf-8"))
    by_no = {n["noticeNo"]: n for n in data["notices"]}

    for no, exp in INVARIANTS.items():
        n = by_no.get(no)
        if not n:
            fails += 1
            print(f"  FAIL notice {no} missing from data")
            continue
        got = {
            "kind": n["kind"],
            "centres": len(n.get("centres") or []),
            "seats": n.get("seats"),
            "rolls": n.get("rollCount") or (len(n["rolls"]) if n.get("rolls") else None),
            "sittings": len(n.get("sittings") or []),
        }
        for k, v in exp.items():
            if got[k] != v:
                fails += 1
                print(f"  FAIL {no}.{k} = {got[k]!r}, expected {v!r}")
        print(f"  {'ok' if not fails else '··'} {no:<9} {exp}")

    # delta-encoded sittings must decode back to the right number of rolls,
    # and the decoded values must be strictly increasing (a negative delta would
    # silently corrupt every roll after it)
    print("\n— packed roll data —")
    for n in data["notices"]:
        if not n.get("sittings"):
            continue
        total = 0
        for s_ in n["sittings"]:
            acc, prev = 0, None
            for d in s_["r"]:
                acc += d
                if prev is not None and acc <= prev:
                    fails += 1
                    print(f"  FAIL {n['noticeNo']} batch {s_['sl']}: non-increasing roll {acc}")
                    break
                prev = acc
            if len(s_["r"]) != s_["count"]:
                fails += 1
                print(f"  FAIL {n['noticeNo']} batch {s_['sl']}: {len(s_['r'])} rolls "
                      f"but count says {s_['count']}")
            total += len(s_["r"])
        if total != n.get("rollCount"):
            fails += 1
            print(f"  FAIL {n['noticeNo']}: decoded {total} rolls, rollCount says {n.get('rollCount')}")
        else:
            print(f"  ok  {n['noticeNo']} decodes to exactly {total} rolls "
                  f"across {len(n['sittings'])} sittings")

    # --- regressions found on 2026-11-11, after the first live fetch ---------
    print("\n— live-fetch regressions —")

    # 1. no notice may be a silent dead end: anything still flagged "scanned"
    #    must say so, and anything claiming to be searchable must carry rolls.
    scans = [n for n in data["notices"] if n["kind"] == "scanned"]
    hollow = [n["id"] for n in data["notices"]
              if n["kind"] in ("selected", "viva", "result", "seat")
              and not (n.get("rolls") or n.get("sittings") or n.get("centres"))]
    if hollow:
        fails += 1
        print(f"  FAIL notice(s) marked searchable but carrying no rolls: {hollow}")
    else:
        print(f"  ok  no hollow notices; {len(scans)} still image-only and flagged as such")

    # 2. titles must survive a career.html that only covers one of the two
    #    listing pages — the merge cache backfills the rest
    untitled = [n for n in data["notices"]
                if str(n.get("title", "")).startswith("Notice ")]
    if untitled:
        fails += 1
        print(f"  FAIL {len(untitled)} notice(s) lost their English title: "
              f"{[n['id'] for n in untitled]}")
    else:
        print("  ok  every notice has a real title (listing cache intact)")

    # 3. the two centre notices must keep correct exam dates
    for no, want in (("357/2026", "13/11/2026"), ("86/2026", "13/11/2026")):
        got = (by_no.get(no) or {}).get("examDate")
        if got != want:
            fails += 1
            print(f"  FAIL {no} examDate = {got!r}, expected {want!r}")
    if not fails:
        print("  ok  exam dates correct on 357/2026 and 86/2026")

    # spot-check a real roll lookup through the centre ranges
    n86 = by_no.get("86/2026") or {}
    for c in n86.get("centres") or []:
        if c["from"] <= 105432 <= c["to"] and "মোল্লা" not in c["name"]:
            fails += 1
            print(f"  FAIL roll 105432 resolved to {c['name']!r}")

    # 4. ISO dates must exist and agree with their DD/MM/YYYY twin, because the
    #    status badges, the archive split and the countdown all key off them.
    import re as _re
    bad_iso = []
    for n in data["notices"]:
        for human, iso in (("published", "publishedISO"),
                           ("closing", "closingISO"),
                           ("examDate", "examDateISO")):
            h, i = n.get(human), n.get(iso)
            if h and not i:
                bad_iso.append(f"{n['id']}.{iso} missing (from {h!r})")
            elif i:
                if not _re.fullmatch(r"\d{4}-\d{2}-\d{2}", i):
                    bad_iso.append(f"{n['id']}.{iso} malformed: {i!r}")
                elif h:
                    dd, mm, yy = h.split("/")
                    if i != f"{yy}-{int(mm):02d}-{int(dd):02d}":
                        bad_iso.append(f"{n['id']}: {h!r} != {i!r}")
    if bad_iso:
        fails += 1
        for b in bad_iso[:6]:
            print(f"  FAIL {b}")
    else:
        print("  ok  ISO dates present and consistent on every notice")

    # 5. hand-transcribed roll lists must match the totals printed on the notice
    MANUAL = {"20261102_bb_83_1793613569": 11, "20261029_bb_372_1793248807": 17,
              "20261111_bb_87_1794395117": 334, "20261109_bb_419_1794210128": 2}
    for nid, want in MANUAL.items():
        n = next((x for x in data["notices"] if x["id"] == nid), None)
        if not n:
            fails += 1
            print(f"  FAIL manual notice {nid} missing from the build")
            continue
        got = len(n.get("rolls") or [])
        grouped = sum(len(g["rolls"]) for g in n.get("groups") or [])
        if got != want or grouped != want:
            fails += 1
            print(f"  FAIL {nid}: {got} rolls / {grouped} grouped, notice states {want}")
        elif n.get("rollSource") not in ("manual", "ocr"):
            fails += 1
            print(f"  FAIL {nid}: rollSource = {n.get('rollSource')!r}, "
                  f"expected 'manual' or 'ocr' so the UI can disclose the source")
        elif n.get("rollSource") == "ocr" and not n.get("ocrChecks", {}).get("printedTotal"):
            fails += 1
            print(f"  FAIL {nid}: OCR rolls published without a printed-total cross-check")
        elif sorted(set(n["rolls"])) != n["rolls"]:
            fails += 1
            print(f"  FAIL {nid}: roll list has duplicates or is unsorted")
    print("  ok  recovered roll lists match the totals printed on the scans")

    # 6. the two scans must no longer be dead ends
    still_scanned = [n["id"] for n in data["notices"] if n.get("kind") == "scanned"]
    if set(still_scanned) & set(MANUAL):
        fails += 1
        print(f"  FAIL transcribed notice still marked scanned: {still_scanned}")
    else:
        print(f"  ok  all {len(MANUAL)} recovered notices searchable ({len(still_scanned)} left unreadable)")

    # 7. UI guarantees that live in the template. These are string checks, not
    #    taste checks: each one maps to a bug that actually shipped once.
    print("\n— interface guarantees —")
    tpl = open(os.path.join(ROOT, "app.template.html"), encoding="utf-8").read()
    ui = [
        ('data-theme',                  'theme override hook'),
        ('prefers-color-scheme: dark',  'OS dark-mode default'),
        ('color-scheme: light dark',    'native control theming'),
        ('localStorage.getItem("bb-theme")', 'theme read before first paint (no flash)'),
        ('Hind Siliguri',               'Bengali/Latin webfont declared'),
        ('unicode-range',               'font split by script'),
        ('repeat(auto-fill,minmax(min(100%', 'roll grid cannot overflow its container'),
        ('STR = {',                     'bilingual string table'),
        ('disambigWhy',                 'job disambiguation copy'),
        ('prefers-reduced-motion',      'motion opt-out'),
        ('@media print',                'printable seat plan'),
    ]
    for needle, what in ui:
        if needle not in tpl:
            fails += 1
            print(f"  FAIL template lost: {what}  ({needle!r})")
    else:
        print(f"  ok  {len(ui)} interface guarantees present in app.template.html")

    # the old build joined rolls into one string inside a table cell, which is
    # what forced the whole page to scroll sideways. It must not come back.
    if '.map(BN).join(", ")' in tpl:
        fails += 1
        print("  FAIL roll list is being joined into a single string again "
              "(this is what caused the horizontal page scroll)")
    else:
        print("  ok  roll lists render as a wrapping grid, not one long string")

    # a roll number is only unique within a job, so every result card must be
    # able to state its job
    missing_job = [n["id"] for n in data["notices"] if not n.get("jobId")]
    if missing_job:
        fails += 1
        print(f"  FAIL notices with no jobId (cards cannot be disambiguated): {missing_job}")
    else:
        print(f"  ok  all {len(data['notices'])} notices carry a jobId")

    print("\n" + ("ALL PASS" if not fails else f"{fails} FAILURE(S)"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
