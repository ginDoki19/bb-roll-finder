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
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "parser"))

from bijoy2unicode import convert                                   # noqa: E402


def _all_sources() -> str:
    """Every hand-maintained front-end source, concatenated.

    The interface guarantees below must hold for the site as a whole. Which
    file a rule lives in is a refactoring detail, so they are checked against
    the template plus everything under assets/ rather than against one file.
    """
    paths = [os.path.join(ROOT, "app.template.html")]
    assets = os.path.join(ROOT, "assets")
    for base, _dirs, files in os.walk(assets):
        for f in sorted(files):
            if f.endswith((".css", ".js")):
                paths.append(os.path.join(base, f))
    return "\n".join(open(p, encoding="utf-8").read() for p in paths if os.path.exists(p))


def _dict_keys(tpl: str, lang: str) -> set:
    """Top-level keys of the STR.<lang> dictionary in app.template.html.

    Walks the object body with an explicit context stack so that keys nested
    inside arrays, arrow bodies, strings or template literals are not counted.
    The dictionary contains nested template literals such as
    `...${tot ? ` (${tot})` : ""}...`, which a naive brace counter miscounts.
    """
    m = re.search(r"\n(%s):\s*\{" % lang, tpl)
    if not m:
        return set()
    i, stack, keys = m.end(), [], set()
    while i < len(tpl):
        c, nxt = tpl[i], tpl[i + 1:i + 2]
        top = stack[-1] if stack else None
        if top == "`":                                   # inside a template literal
            if c == "\\":
                i += 2
            elif c == "`":
                stack.pop(); i += 1
            elif c == "$" and nxt == "{":
                stack.append("${"); i += 2
            else:
                i += 1
            continue
        if top in ("'", '"'):                            # inside a plain string
            if c == "\\":
                i += 2
            else:
                if c == top:
                    stack.pop()
                i += 1
            continue
        if c == "/" and nxt == "*":                      # block comment
            j = tpl.find("*/", i)
            i = (j + 2) if j > 0 else len(tpl)
            continue
        if c == "/" and nxt == "/":                      # line comment
            j = tpl.find("\n", i)
            i = (j + 1) if j > 0 else len(tpl)
            continue
        if c in "'\"`" or c in "{[(":
            stack.append(c); i += 1
            continue
        if c == "}":
            if not stack:                                # closes the dictionary
                break
            stack.pop(); i += 1
            continue
        if c in "])":
            if stack:
                stack.pop()
            i += 1
            continue
        if not stack:
            km = re.match(r"([A-Za-z_$][\w$]*)\s*:", tpl[i:])
            if km:
                keys.add(km.group(1))
                i += km.end()
                continue
        i += 1
    return keys

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

    # 7. UI guarantees that live in the front-end sources. These are string
    #    checks, not taste checks: each one maps to a bug that actually
    #    shipped once. Checked against every source file rather than just the
    #    template, so moving a rule between app.template.html and assets/ is
    #    free but deleting it is not.
    print("\n— interface guarantees —")
    src = _all_sources()
    ui = [
        ('data-theme',                  'theme override hook'),
        ('prefers-color-scheme: dark',  'OS dark-mode default'),
        ('color-scheme: light dark',    'native control theming'),
        ('localStorage.getItem("bb-theme")', 'theme read before first paint (no flash)'),
        ('Noto Sans Bengali',           'Bengali/Latin webfont declared'),
        ('unicode-range',               'font split by script'),
        ('repeat(auto-fill,minmax(min(100%', 'roll grid cannot overflow its container'),
        ('STR = {',                     'bilingual string table'),
        ('disambigWhy',                 'job disambiguation copy'),
        ('prefers-reduced-motion',      'motion opt-out'),
        ('@media print',                'printable seat plan'),
    ]
    before = fails
    for needle, what in ui:
        if needle not in src:
            fails += 1
            print(f"  FAIL front-end sources lost: {what}  ({needle!r})")
    if fails == before:
        print(f"  ok  {len(ui)} interface guarantees present across the sources")

    # 7b. language defaults and the fixed English identifier.
    print("\n— language rules —")
    lang_checks = [
        ('<html lang="en" data-lang="en">', 'document starts in English'),
        ('return "en";',                    'first visit falls back to English'),
    ]
    before = fails
    for needle, what in lang_checks:
        if needle not in src:
            fails += 1
            print(f"  FAIL {what} — expected {needle!r} somewhere in "
                  f"app.template.html or assets/")
    if fails == before:
        print("  ok  English is the first-visit default")

    en_keys, bn_keys = _dict_keys(src, "en"), _dict_keys(src, "bn")
    if not en_keys or not bn_keys:
        fails += 1
        print(f"  FAIL could not read the STR dictionaries (en={len(en_keys)}, bn={len(bn_keys)})")
    else:
        # "Job ID" is a fixed English label: it must exist in English and must
        # NOT be translated in Bengali. Everything else needs both languages.
        FIXED_ENGLISH = {"job"}
        missing_bn = (en_keys - bn_keys) - FIXED_ENGLISH
        stray_bn = bn_keys - en_keys
        if missing_bn:
            fails += 1
            print(f"  FAIL {len(missing_bn)} key(s) missing a Bengali translation: {sorted(missing_bn)}")
        elif stray_bn:
            fails += 1
            print(f"  FAIL Bengali keys with no English counterpart: {sorted(stray_bn)}")
        else:
            print(f"  ok  {len(en_keys)} EN / {len(bn_keys)} BN keys, parity holds")

        if "job" not in en_keys:
            fails += 1
            print("  FAIL the English dictionary has no 'job' label")
        elif "job" in bn_keys:
            fails += 1
            print("  FAIL 'Job ID' is translated in the Bengali dictionary — it must stay English")
        else:
            print("  ok  'Job ID' is a fixed English label in both locales")

    # A Job ID is an identifier, not prose: it must never be run through the
    # Bengali-digit converter, or 307 is shown to the candidate as ৩০৭.
    if re.search(r'dnum\(\s*n\.jobId|dnum\(\s*j\s*\)', src):
        fails += 1
        print("  FAIL a Job ID is being localised to Bengali digits (use JOB(), not dnum())")
    else:
        print("  ok  Job ID numbers stay ASCII in both locales")

    man = json.load(open(os.path.join(ROOT, "manifest.webmanifest"), encoding="utf-8"))
    if man.get("lang") != "en":
        fails += 1
        print(f"  FAIL manifest lang is {man.get('lang')!r}, expected 'en'")
    else:
        print("  ok  manifest declares the English default")

    # the old build joined rolls into one string inside a table cell, which is
    # what forced the whole page to scroll sideways. It must not come back.
    if '.map(BN).join(", ")' in src:
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

    # 9. The build contract. index.html is assembled from the template plus
    #    assets/, and every one of these guards maps to a way that assembly
    #    can break quietly rather than loudly.
    print("\n— build integrity —")
    sys.path.insert(0, os.path.join(ROOT, "parser"))
    import build_site

    tpl_only = open(os.path.join(ROOT, "app.template.html"), encoding="utf-8").read()
    for marker in ("/*__CSS__*/", "/*__JS__*/"):
        if marker not in tpl_only:
            fails += 1
            print(f"  FAIL app.template.html has lost the {marker} placeholder")
    if "/*__CSS__*/" in tpl_only and "/*__JS__*/" in tpl_only:
        print("  ok  template carries both the CSS and JS placeholders")

    # Nothing may be hand-written into the generated file.
    out = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    if "GENERATED FILE — DO NOT EDIT" not in out:
        fails += 1
        print("  FAIL index.html has no 'do not edit' banner")
    else:
        print("  ok  index.html is marked as generated")

    # The page must stay one self-contained file: an external stylesheet or
    # script would break file://, offline use and the sandboxed preview.
    ext = []
    if 'rel="stylesheet"' in out:
        ext.append("<link rel=stylesheet>")
    if "<script src" in out:
        ext.append("<script src>")
    if ext:
        fails += 1
        print(f"  FAIL index.html is no longer self-contained: {ext}")
    else:
        print("  ok  index.html is self-contained (no external css/js)")

    # ES module syntax is fatal here: `import` over file:// is blocked by
    # CORS, and these files are concatenated into one classic <script>.
    mods = []
    for name in build_site.JS_FILES:
        body = open(os.path.join(ROOT, "assets", "js", name), encoding="utf-8").read()
        if re.search(r"^\s*(import|export)\s", body, re.M):
            mods.append(name)
    if mods:
        fails += 1
        print(f"  FAIL ES module syntax would break file://: {mods}")
    else:
        print(f"  ok  all {len(build_site.JS_FILES)} scripts are classic, no import/export")

    # The data placeholder has to survive wherever it lives.
    datajs = open(os.path.join(ROOT, "assets", "js", "data", "notices.js"), encoding="utf-8").read()
    if "/*__DATA__*/" not in datajs:
        fails += 1
        print("  FAIL assets/js/data/notices.js no longer declares the /*__DATA__*/ placeholder")
    else:
        print("  ok  the data placeholder is in assets/js/data/notices.js")

    # Accessibility and link-safety rules that are easy to undo by accident.
    html_src = open(os.path.join(ROOT, "app.template.html"), encoding="utf-8").read()
    before = fails
    for frag, what in [
        ("<main", "main landmark"),
        ("<section", "section landmark"),
        ('role="search"', "search landmark"),
        ('<label class="sr-only" for="roll"', "label for the roll field"),
        ('id="srstatus"', "screen-reader status line"),
        ('aria-label="Filter notices by type"', "labelled filter group"),
    ]:
        if frag not in html_src:
            fails += 1
            print(f"  FAIL markup lost the {what}  ({frag!r})")
    if fails == before:
        print("  ok  landmarks, field label and status line present")

    if re.search(r'id="result"[^>]*aria-live', html_src):
        fails += 1
        print("  FAIL #result is a live region again — it re-announces every card per keystroke")
    else:
        print("  ok  #result is not a live region")

    js_all = "\n".join(
        open(os.path.join(ROOT, "assets", "js", n), encoding="utf-8").read()
        for n in build_site.JS_FILES)
    bare = len(re.findall(r'rel="noopener"', js_all))
    if bare:
        fails += 1
        print(f"  FAIL {bare} link(s) still use bare rel=\"noopener\" without noreferrer")
    else:
        print(f"  ok  all {len(re.findall(r'noopener noreferrer', js_all))} new-tab links set noopener noreferrer")

    unsafe = re.findall(r'href="\$\{esc\([^)]*\)\}"', js_all)
    if unsafe:
        fails += 1
        print(f"  FAIL href interpolated without scheme validation: {unsafe[:3]}")
    else:
        print("  ok  every interpolated href goes through safeHref()")

    # A stale service-worker cache name means returning visitors keep the old
    # shell after a deploy.
    sw = open(os.path.join(ROOT, "sw.js"), encoding="utf-8").read()
    m = re.search(r'CACHE\s*=\s*"bb-roll-v(\d+)"', sw)
    if not m or int(m.group(1)) < 4:
        fails += 1
        print(f"  FAIL service-worker cache not bumped for this release ({m.group(0) if m else 'not found'})")
    else:
        print(f"  ok  service worker uses bb-roll-v{m.group(1)}")

    # theme_color must be a colour the page actually paints.
    mani = json.load(open(os.path.join(ROOT, "manifest.webmanifest"), encoding="utf-8"))
    tokens = open(os.path.join(ROOT, "assets", "css", "tokens.css"), encoding="utf-8").read()
    if mani.get("theme_color", "").lower() not in tokens.lower():
        fails += 1
        print(f"  FAIL manifest theme_color {mani.get('theme_color')} is not in the palette")
    else:
        print(f"  ok  manifest theme_color {mani['theme_color']} matches the palette")

    # Static font preloads reintroduce the file:// CORS errors.
    if re.search(r'<link[^>]+rel="preload"', html_src):
        fails += 1
        print("  FAIL static <link rel=preload> is back — it logs CORS errors over file://")
    else:
        print("  ok  font preloads are injected for http(s) only")

    # Every font referenced by @font-face must exist, and the display family
    # that paints h1/h2/.panel .big must be in the preload list — otherwise
    # the largest text on the page renders in Georgia and then swaps.
    faces = set(re.findall(r'url\("fonts/([^"]+\.woff2)"\)', src))
    missing = sorted(f for f in faces
                     if not os.path.exists(os.path.join(ROOT, "fonts", f)))
    if missing:
        fails += 1
        print(f"  FAIL @font-face points at missing files: {', '.join(missing)}")
    else:
        print(f"  ok  all {len(faces)} @font-face files are present")

    display = re.search(r'--font-display:"([^"]+)"', src)
    disp_files = sorted(f for f in faces
                        if display and display.group(1).lower().replace(" ", "-") in f)
    if disp_files and not any(f in html_src for f in disp_files):
        fails += 1
        print(f"  FAIL the display family {display.group(1)!r} is never preloaded")
    else:
        print(f"  ok  the display family is preloaded")

    # Font filenames carry their version, so they must be cached immutably.
    hdr = open(os.path.join(ROOT, "_headers"), encoding="utf-8").read()
    if not re.search(r"^/fonts/\*", hdr, re.M):
        fails += 1
        print("  FAIL _headers has no /fonts/* rule — renamed fonts refetch every visit")
    elif "immutable" not in hdr.split("/fonts/*")[1].split("\n\n")[0]:
        fails += 1
        print("  FAIL the /fonts/* rule does not set immutable")
    else:
        print("  ok  _headers caches /fonts/* immutably")

    # Structured "what happens next" rows: a box with a blank label or a
    # blank value renders as an empty grey band, which looks like a bug.
    bad = []
    for n in data["notices"]:
        for key in ("details", "detailsBn"):
            for i, row in enumerate(n.get(key) or []):
                if not str(row.get("k", "")).strip() or not str(row.get("v", "")).strip():
                    bad.append(f"{n['id']}.{key}[{i}]")
    if bad:
        fails += 1
        print(f"  FAIL detail rows missing k or v: {', '.join(bad)}")
    else:
        ndet = sum(len(n.get("details") or []) for n in data["notices"])
        print(f"  ok  all {ndet} detail rows carry a label and a value")

    # Every module named in the BB surface must actually be built.
    surface = set(re.findall(r"^  ([A-Za-z]+):\s*\{", 
                             open(os.path.join(ROOT, "assets", "js", "app.js"),
                                  encoding="utf-8").read(), re.M))
    if len(surface) < 12:
        fails += 1
        print(f"  FAIL the BB surface lists only {len(surface)} modules")
    else:
        print(f"  ok  BB surface declares {len(surface)} modules")

    print("\n" + ("ALL PASS" if not fails else f"{fails} FAILURE(S)"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
