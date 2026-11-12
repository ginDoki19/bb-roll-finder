#!/usr/bin/env python3
"""
_jssplit.py — one-shot Phase-4 extractor: move the main <script> body out of
app.template.html into assets/js/.

This is a PURE MOVE. Not one line of JavaScript is rewritten, renamed or
reformatted; lines are only relocated into files and, in two places,
reordered (POST_RE moves next to the rest of the constants, mapsUrl moves into
features/maps.js). The script proves that by comparing the multiset of output
lines against the multiset of input lines before it writes anything.

    python3 tools/_jssplit.py          # dry run, reports only
    python3 tools/_jssplit.py --write  # actually write the files

Safe to re-run: it reads the template's <script> block, which the --write pass
replaces with a /*__JS__*/ placeholder, so a second --write is a no-op error
rather than a double extraction.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(ROOT, "app.template.html")
OUT = os.path.join(ROOT, "assets", "js")

# (first_line, last_line, destination)  — 1-indexed, inclusive, template coords.
# These must tile the <script> body exactly: no gaps, no overlaps.
RANGES = [
    # ---- the data and its derived lookup structures ----
    ( 85,  88, "data/notices.js"),        # inline-at-build-time comment + DATA
    # ---- core helpers ----
    ( 89,  90, "core/dom.js"),            # $, esc
    ( 91,  92, "core/numbers.js"),        # BN
    ( 93, 101, "core/numbers.js"),        # AS (+ its explanatory comment)
    (102, 122, "core/language.js"),       # banner, LANG, NUM?, JOB?, t
    (123, 240, "core/language.js"),       # STR
    (241, 248, "core/constants.js"),      # KIND taxonomy
    (249, 250, "core/language.js"),       # kindLabel
    (251, 287, "core/dates.js"),          # TODAY..dnum
    (288, 291, "core/constants.js"),      # identity banner -> sits above POST_RE
    (292, 292, "core/constants.js"),      # POST_RE
    (293, 321, "features/results.js"),    # postOf, identBlock
    (322, 362, "data/notices.js"),        # index: notices, decode, searchable, findCentre, minus60
    (363, 364, "features/maps.js"),       # mapsUrl
    (365, 395, "features/results.js"),    # provenance, outcome panel
    (396, 421, "features/rolls.js"),      # roll chips
    (422, 507, "features/results.js"),    # cards
    (508, 588, "features/search.js"),
    (589, 672, "features/notice-list.js"),
    (673, 723, "features/preferences.js"),
    (724, 794, "app.js"),                 # interactions, SW registration, boot
]

# Concatenation order. The only hard constraint is that data/notices.js runs
# `DATA.notices.slice()` at load time, so it must come after nothing in
# particular but before nothing that reads `notices` at load time — in practice
# every other cross-file reference lives inside a function body and is not
# evaluated until boot() runs, which is the last statement in app.js.
JS_FILES = [
    "core/constants.js",
    "core/dom.js",
    "core/numbers.js",
    "core/dates.js",
    "core/language.js",
    "data/notices.js",
    "features/maps.js",
    "features/results.js",
    "features/rolls.js",
    "features/search.js",
    "features/notice-list.js",
    "features/preferences.js",
    "app.js",
]

HEADERS = {
    "core/constants.js": """/* constants.js
 * Inert lookup data shared across features: the notice-kind taxonomy and the
 * post-name regex. No behaviour lives here.
 *
 * KIND carries the two badge labels (labEn/labBn) because they are part of the
 * taxonomy rather than prose; all other translatable copy is in
 * core/language.js under STR.
 */""",
    "core/dom.js": """/* dom.js
 * The two primitives every render path uses: an element lookup and the HTML
 * escaper. esc() handles & < > " — it is applied to every interpolated value
 * that reaches innerHTML.
 */""",
    "core/numbers.js": """/* numbers.js
 * Digit systems. The UI and the source PDFs both use Bengali numerals, so
 * every number crossing into or out of the interface passes through here.
 */""",
    "core/dates.js": """/* dates.js
 * Exam-date parsing, relative-day status and the countdown wording.
 */""",
    "core/language.js": """/* language.js
 * The interface language: the current LANG, the lookup helper t(), and STR —
 * the full English/Bengali copy. This is the file to edit for wording.
 *
 * Both dictionaries must stay at parity; tools/selftest.py enforces that and
 * allows exactly one deliberate exception ("job", which is fixed English).
 */""",
    "data/notices.js": """/* notices.js
 * The notice dataset and the lookup structures derived from it.
 *
 * DATA is substituted at build time by parser/build_site.py — the JSON is
 * inlined rather than fetched so the page works from file://, offline, and
 * inside sandboxed previews.
 *
 * This file does real work at load time (it decodes the delta-encoded sittings
 * into Maps), so it must be concatenated before anything that reads `notices`
 * outside a function body.
 */""",
    "features/maps.js": """/* maps.js
 * Google Maps links for exam centres. The embedded iframe is built in app.js
 * when a centre row is expanded.
 */""",
    "features/results.js": """/* results.js
 * The result cards a candidate sees after a hit: identity (which job and post
 * this is), provenance (how the roll list was obtained), the outcome panel,
 * and the three card shapes — seat, sitting and selected.
 */""",
    "features/rolls.js": """/* rolls.js
 * The expandable roll-number grid, including copy-to-clipboard.
 *
 * Chips are painted lazily: a 1,037-roll notice only builds its chips when
 * somebody actually opens that list.
 */""",
    "features/search.js": """/* search.js
 * Roll lookup: collecting hits across every notice, ranking the preferred job
 * first, and rendering the result area.
 *
 * A roll number is only unique within a job, so a search can legitimately
 * match more than one notice; that ambiguity is surfaced, never guessed at.
 */""",
    "features/notice-list.js": """/* notice-list.js
 * The archive below the search: every notice as a card, with the kind filter.
 */""",
    "features/preferences.js": """/* preferences.js
 * Theme and language preferences, the segmented toggles that set them, and the
 * static text repaint that a language change triggers.
 */""",
    "app.js": """/* app.js
 * Wiring. Delegated event handlers, service-worker registration and boot().
 *
 * Loaded last: boot() runs immediately and calls into every feature, so every
 * other file must already have been concatenated above this one.
 */""",
}


def main():
    write = "--write" in sys.argv
    text = open(TPL, encoding="utf-8").read()
    lines = text.split("\n")

    if "/*__JS__*/" in text:
        sys.exit("_jssplit: template already has /*__JS__*/ — already extracted")

    # locate the main <script> body
    starts = [i for i, l in enumerate(lines) if l.strip() == "<script>"]
    ends = [i for i, l in enumerate(lines) if l.strip() == "</script>"]
    s, e = starts[-1], ends[-1]
    first, last = s + 2, e          # 1-indexed inclusive body bounds
    print(f"<script> body: lines {first}–{last} ({last - first + 1} lines)")

    # --- the ranges must tile the body exactly ---
    covered = []
    for a, b, dest in RANGES:
        covered.extend(range(a, b + 1))
    expected = list(range(first, last + 1))
    if sorted(covered) != expected:
        miss = sorted(set(expected) - set(covered))
        dup = sorted({x for x in covered if covered.count(x) > 1})
        sys.exit(f"_jssplit: ranges do not tile the body.\n  missing: {miss[:20]}\n  duplicated: {dup[:20]}")
    print(f"ranges tile the body exactly: {len(RANGES)} ranges, {len(covered)} lines")

    # --- build file contents ---
    files = {}
    for a, b, dest in RANGES:
        files.setdefault(dest, []).extend(lines[a - 1 : b])

    if set(files) != set(JS_FILES):
        sys.exit(f"_jssplit: JS_FILES mismatch\n  only in RANGES: {sorted(set(files) - set(JS_FILES))}"
                 f"\n  only in JS_FILES: {sorted(set(JS_FILES) - set(files))}")

    # --- conservation proof: same lines out as in, nothing lost or invented ---
    out_lines = []
    for name in JS_FILES:
        out_lines.extend(files[name])
    src_lines = lines[first - 1 : last]
    if sorted(out_lines) != sorted(src_lines):
        lost = sorted(set(src_lines) - set(out_lines))
        made = sorted(set(out_lines) - set(src_lines))
        sys.exit(f"_jssplit: line conservation FAILED\n  lost: {lost[:10]}\n  invented: {made[:10]}")
    print(f"line conservation holds: {len(src_lines)} in, {len(out_lines)} out, identical multisets")

    for name in JS_FILES:
        body = "\n".join(files[name]).strip("\n")
        print(f"  {name:<28} {len(files[name]):>4} lines")
        if write:
            path = os.path.join(OUT, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, "w", encoding="utf-8").write(HEADERS[name] + "\n" + body + "\n")

    if write:
        new = lines[: s + 1] + ["/*__JS__*/"] + lines[e:]
        open(TPL, "w", encoding="utf-8").write("\n".join(new))
        print(f"\nwrote {len(JS_FILES)} files and replaced the body with /*__JS__*/")
        print(f"template: {len(lines)} -> {len(new)} lines")
    else:
        print("\ndry run — pass --write to apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
