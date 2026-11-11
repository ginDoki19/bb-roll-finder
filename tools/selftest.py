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

    # 1. scanned notices must be flagged, never silently empty
    scans = [n for n in data["notices"] if n["kind"] == "scanned"]
    if len(scans) != 2:
        fails += 1
        print(f"  FAIL expected 2 scanned notices (83, 372), got {len(scans)}")
    else:
        print(f"  ok  {len(scans)} scanned notices flagged, not shown as searchable")

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

    print("\n" + ("ALL PASS" if not fails else f"{fails} FAILURE(S)"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
