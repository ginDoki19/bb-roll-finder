# Architecture & maintainability refactor — final report

Governed by `BB-Roll-Finder-Architecture-AI-Instructions.md`.
Completed in six phases, one at a time, each verified before the next began.

---

## 1. Architecture before and after

**Before.** One file did everything. `app.template.html` was 1,132 lines:
markup, a 335-line `<style>` block, and a 710-line `<script>` block holding 49
top-level declarations covering language, dates, parsing, search, rendering,
preferences and boot. `parser/build_site.py` (1 KB) substituted a single
`/*__DATA__*/` placeholder. To change a colour you opened the same file you
opened to change the search algorithm, and nothing told you which was which.

Two hard violations of the project's own rules were live:

- Bengali was the first-visit default (`<html lang="bn">`, resolver fallback
  `"bn"`, manifest `"lang": "bn-BD"`).
- `Job ID` was translated to `জব আইডি` in Bengali mode, and its digits were
  converted to Bengali numerals.

**After.** The same page, assembled from four sources by an explicit build.

- `app.template.html` → **118 lines**: markup, the early anti-flash theme
  script, and two placeholders.
- `assets/css/` → **6 files, 386 lines**, concatenated in a declared cascade
  order.
- `assets/js/` → **13 files, 861 lines**, in `core/`, `data/`, `features/` and
  `app.js`, concatenated into one classic `<script>` sharing a scope.
- `parser/build_site.py` → **~200 lines** with ordered manifests and eight
  loud failure modes.

What deliberately did **not** change: the page is still a single
self-contained `index.html` with no external CSS, no external JS, no runtime
fetch, no CDN, no bundler, no npm, no framework. It still works from
`file://` and offline.

---

## 2. Final folder tree

```
bb-notice/
├── index.html                  GENERATED — do not edit (152,030 B / 39,613 B gzipped)
├── app.template.html           markup + early theme script + /*__CSS__*/ /*__JS__*/
├── assets/
│   ├── css/                    concatenation order IS the cascade
│   │   ├── tokens.css          @font-face, light/dark custom properties
│   │   ├── base.css            reset, focus rings, .sr-only, reduced motion
│   │   ├── layout.css          page chrome
│   │   ├── components.css      the bulk of the UI
│   │   ├── responsive.css      max-width:620px — must follow components.css
│   │   └── print.css           seat-plan printing
│   └── js/                     one shared scope, order = JS_FILES
│       ├── core/
│       │   ├── constants.js    KIND taxonomy, POST_RE
│       │   ├── dom.js          $(), esc(), safeHref()
│       │   ├── numbers.js      BN, AS, NUM, JOB
│       │   ├── dates.js        TODAY, toISO, dayDiff, statusOf, countdown, dnum
│       │   └── language.js     LANG, t(), the full en/bn STR table
│       ├── data/notices.js     /*__DATA__*/ + derived lookup Maps
│       ├── features/
│       │   ├── maps.js         mapsUrl
│       │   ├── results.js      identity, provenance, outcome panel, 3 card shapes
│       │   ├── rolls.js        lazy roll grid + clipboard
│       │   ├── search.js       collectHits, ranking, render, SR status
│       │   ├── notice-list.js  archive cards + kind filter
│       │   └── preferences.js  theme/language toggles, static repaint
│       └── app.js              event wiring, service worker, boot(), BB surface
├── parser/
│   ├── bbparse.py              PDF → structured data
│   ├── bijoy2unicode.py        legacy Bijoy font → Unicode Bengali
│   ├── build_data.py           listing HTML + PDFs → data/notices.json
│   └── build_site.py           template + css + js + data → index.html
├── tools/
│   ├── selftest.py             data invariants, interface guarantees,
│   │                           language rules, build integrity
│   ├── uitest.py               121 browser checks across the 13 required tests
│   ├── test_fetch.py           fetch-pipeline regressions
│   ├── fetch_notices.py        local fetch (browser, cookie reuse)
│   ├── ocr_rolls.py            scanned-notice roll recovery
│   ├── _shotset.py             12 deterministic screenshots
│   ├── _shotdiff.py            pixel comparison, exits 1 on any difference
│   ├── _jsmap.py               Phase-4 dependency analysis
│   └── _jssplit.py             Phase-4 extractor with conservation proof
├── data/notices.json           13 notices · 4,204 searchable rolls
├── meta/overrides.json         curated Bengali copy, verified roll lists
├── notices/*.pdf               13 source PDFs
├── fonts/*.woff2               Noto Sans + Serif Bengali, 6 files, self-hosted
├── sw.js                       bb-roll-v4
├── manifest.webmanifest        lang "en", theme_color #0f131a
├── _headers                    4 security headers + cache rules
└── *.md, *.bat, icons, robots.txt, sitemap.xml
```

85 files. **No file was deleted at any point.**

---

## 3. Files created, moved, modified, generated

**Created (25)**

| | |
|---|---|
| `assets/css/` | `tokens.css`, `base.css`, `layout.css`, `components.css`, `responsive.css`, `print.css` |
| `assets/js/core/` | `constants.js`, `dom.js`, `numbers.js`, `dates.js`, `language.js` |
| `assets/js/data/` | `notices.js` |
| `assets/js/features/` | `maps.js`, `results.js`, `rolls.js`, `search.js`, `notice-list.js`, `preferences.js` |
| `assets/js/` | `app.js` |
| `tools/` | `uitest.py`, `_shotset.py`, `_shotdiff.py`, `_jsmap.py`, `_jssplit.py` |
| root | `REFACTOR-REPORT.md` |

**Moved** — content only, no files relocated on disk: 335 CSS lines and 710 JS
lines out of `app.template.html` into `assets/`. Proven to be a pure move: the
extractor refused to write until the output lines were a multiset-identical
permutation of the input (`710 in, 710 out`).

**Modified (9):** `app.template.html`, `parser/build_site.py`,
`tools/selftest.py`, `manifest.webmanifest`, `sw.js`, `README.md`, `SETUP.md`,
`REDESIGN.md`, and the extracted sources themselves for findings #4–#8.

**Generated (1):** `index.html`, now carrying a "GENERATED FILE — DO NOT EDIT"
banner naming its four sources.

**Not moved, deliberately:** `assets/images/` and `docs/`. Icons are referenced
at the root by `manifest.webmanifest`, `sitemap.xml` and the `_headers` rule
`/*.png`; moving them breaks three contracts for no gain. Moving the docs is
the "move unrelated files" the instructions forbid.

---

## 4. The two non-negotiables — confirmed by test

**English is the default.** `<html lang="en" data-lang="en">`, resolver
fallback `"en"`, manifest `"lang": "en"`. A saved `bb-lang=bn` is still
honoured; an invalid stored value falls back to English. Verified over http
and over `file://`.

**`Job ID` stays English in Bengali mode.** `STR.bn.job` was deleted so it
falls through to English, and a dedicated `JOB()` formatter keeps the digits
ASCII at all four render sites. `Job 307`, never `জব আইডি ৩০৭`.

A CSS bug was caught here that a DOM-only assertion missed: `.jobtag .k` had
`text-transform:uppercase`, so the DOM read `Job ID` while users saw `JOB ID`.
Fixed, and `uitest.py` now asserts `innerText`, not `textContent`, so a CSS
transform can never pass this check again.

Roll numbers deliberately still follow the interface language (`২১৩৮৮০` in
Bengali) — candidates read them off Bengali notices.

---

## 5. Commands run, and their real results

```
$ python3 tools/selftest.py
  33 checks ok · ALL PASS

$ python3 tools/uitest.py
  ALL 121 UI CHECKS PASS

$ python3 tools/test_fetch.py
  8 checks · 8 passed · 0 failed · 0 skipped

$ python3 parser/build_data.py --html career.html --pdfs notices --out /tmp/regen.json
  13 notices parsed; output IDENTICAL to the curated data/notices.json
  (ignoring the build timestamp) — curated file left untouched

$ python3 parser/build_site.py
  148 KB · 13 notices · 6 stylesheets (20 KB) + 13 scripts (42 KB) inlined
  rebuild byte-identical → the build is reproducible

$ node --check <extracted bundle>
  syntax OK

$ python3 tools/_shotdiff.py shots/phase3/before shots/phase6/final
  12 compared · 0 differing · worst 0.000%
```

**Cumulative visual result: zero differing pixels** across 12 rendered states
(home / disambiguation / congratulations / written / not-found / expanded roll
grid, across both themes and both languages, plus 390 px mobile and print
emulation) between the start of the structural refactor and the finished
build.

**Size:** 143,683 B → 152,030 B raw; **36,534 B → 39,613 B gzipped**.

The project had carried a self-imposed 40,960 B gzipped ceiling, which the
Phase-5 additions briefly breached (41,306 B). The owner has since released
that ceiling as a hard gate. The build-time header stripping introduced under
that pressure was kept anyway, on its own merits — see §7.1.

**Reproducibility, precisely stated:** `build_site.py` is byte-deterministic —
two consecutive builds from identical sources produce the same md5. It is not
true that `index.html` is stable across a full test run, because
`tools/test_fetch.py` (T4) regenerates `data/notices.json` in place and that
file carries a `generated` timestamp. Verified that regeneration changes the
timestamp and **nothing else**: 13 notices, 1,401 chip rolls, notice content
compares equal.

### Build failure modes, each verified by deliberately breaking it

| Broken on purpose | Result |
|---|---|
| Missing `/*__CSS__*/` or `/*__JS__*/` | build exits 1 |
| `.css`/`.js` on disk not in the manifest | build exits 1 (drift guard) |
| A module dropped from `JS_FILES` | build exits 1 |
| `/*__DATA__*/` removed | build exits 1 |
| Literal `</script>` in a source | build exits 1 |
| A file that is only its header comment | build exits 1 |
| Invalid JSON / empty notices | build exits 1 |
| `prefers-reduced-motion` deleted | selftest fails |
| `import`/`export` added | selftest fails |
| `#result` regains `aria-live` | selftest fails |
| Bare `rel="noopener"` | selftest fails |
| `href` bypassing `safeHref()` | selftest fails |
| Service worker not bumped | selftest fails |
| Stale `theme_color` | selftest fails |
| Static `<link rel=preload>` returns | selftest fails |

### Findings #4–#8

- **Landmarks and labels:** `<main>`, `<section aria-labelledby>`,
  `<form role="search">`, a `clip-path` hidden `<label for="roll">`, labelled
  filter group. The form cancels submit so Enter cannot discard the query.
- **URL-scheme validation:** `safeHref()` rejects `javascript:`, `data:`,
  `vbscript:`, mixed-case variants and control-character smuggling; relative
  and https paths pass. Wired into all 8 data-derived hrefs.
- **`rel="noopener noreferrer"`** on all 10 new-tab links.
- **Targeted `aria-live`:** `#result` is no longer a live region. A dedicated
  `#srstatus` carries a one-line summary, written only when it changes —
  measured at >10× shorter than the markup it replaced.
- **Manifest and console:** `theme_color`/`background_color` → `#0f131a`;
  font preloads injected for http(s) only, taking `file://` from **4 console
  errors to 0** with all 4 fonts still loading.
- `sw.js` → `bb-roll-v4`, with a test that activate evicts the superseded
  cache and the new shell is still precached.

---

## 6. What could not be verified

- **`git diff` could not be inspected.** §8 asks for it; the sandbox copy is
  not a git repository (`.git` was removed earlier in the project). Substituted
  byte-level comparison of every rebuild, a line-conservation proof on the JS
  extraction, and the 12-state pixel harness.
- **Real assistive-technology output.** The ARIA structure, the status text and
  its length are asserted programmatically, but no screen reader was run. The
  `aria-live` change should be confirmed once with NVDA or VoiceOver.
- **Real mobile hardware.** Tested at 390 px and 360 px in headless Chromium;
  no physical device, no iOS Safari, no Android Chrome.
- **A live deploy.** Everything was verified locally and over `file://`. The
  Cloudflare Pages deploy, the `_headers` rules as served, and the
  service-worker upgrade path on the live origin were not exercised.
- **One sub-perceptual rendering artifact.** During Phases 4 and 5, individual
  snapshots sometimes differed by 43 or 37 pixels at **exactly ±1/255 in one
  channel**, on the antialiased curve of one rounded border. I proved the DOM,
  computed styles and geometry were identical to four decimal places, and a
  controlled experiment showed document byte length can flip it. I could not
  isolate the exact rasteriser mechanism. It resolved to zero in the final
  build and never corresponded to a product change.

---

## 7. Remaining technical debt and recommended next steps

1. **Page weight — no longer a gate, still worth watching.** The 40 KB
   gzipped ceiling has been released by the owner, so nothing in the build
   should fail on size and no future work needs to budget against it.

   The header stripping in `build_site.py` was introduced only because Phase 5
   breached that ceiling, but it was kept after the ceiling was lifted because
   it stands on its own: it saves **4,698 B raw / ~1.8 KB gzipped** for an
   audience largely on mobile data, and the only thing it removes is
   boilerplate addressed to source maintainers ("assembled by build_site.py…
   do not link this file directly") which is meaningless to a browser. The 19
   `/* ===== filename ===== */` boundary markers are retained, so any rule or
   function in the generated file can still be traced back to its source file
   in DevTools, and the source files keep their headers in full. Reverting it
   is a two-line change if the tradeoff is ever judged differently.

   The real driver of page weight is `data/notices.json`, which dominates the
   payload and grows with every notice. If it ever becomes a problem, the fix
   is to fetch the roll corpus separately and keep the inline copy as the
   offline fallback — but that changes the "one self-contained file" property,
   so it should be a deliberate decision rather than a silent build tweak.
2. ~~**`for … else` in the selftest.**~~ **Fixed.** Three loops used
   `for … else`, where the `else` binds to the `for` rather than the `if`, so
   the success line printed even when a check in that block had failed. (One
   of the three was introduced during this refactor — the pattern was copied.)
   All three now compare the failure count before and after the loop. Verified
   by breaking an interface guarantee, a landmark and the English default in
   turn and confirming the misleading `ok` line no longer appears. A stale
   message that pointed at `app.template.html` for a check that now lives in
   `assets/` was corrected at the same time.
3. **Multi-value `jobId` is still unsplit.** `20261029_bb_372` carries
   `"280, 282, 289, 294, 295, 296, 299, 300"` as one string. Splitting on the
   comma would let each group be disambiguated individually.
4. **`esc()` does not escape `'`.** It handles `& < > "`, which is sufficient
   because every interpolation sits in a double-quoted attribute or in text.
   It is one character away from being unconditionally safe.
5. **No CSP.** `_headers` carries four security headers but no
   Content-Security-Policy. One cannot be added without `'unsafe-inline'`
   while the CSS and JS are inlined, which would weaken rather than
   strengthen the page — hence the inlining decision stands. Revisit only if
   the site stops being single-file.
6. **`PLAN.md` and `ROADMAP.md` describe older states** (6 notices, an 80 KB
   page, a `/*__DATA__*/`-only template). Left as historical records rather
   than rewritten; `README.md`, `SETUP.md` and `REDESIGN.md` were corrected
   because they are the living references and now pointed at the wrong files.
7. ~~**T4 rewrites `data/notices.json` in place.**~~ **Fixed.** It regenerated
   the data as part of its rebuild check, refreshing the `generated` timestamp
   and so changing `index.html` on every test run — diff noise immediately
   before a deploy. `build_data.py` now writes to a temporary file and the
   result is **compared** against the committed data instead of overwriting
   it. Verified: `index.html` has the same md5 before and after a full test
   run, and `data/notices.json` is untouched.

   This also made the check stricter rather than weaker. T4 now proves the
   committed data is exactly what the current parser produces from the current
   PDFs and overrides, so curated data cannot quietly drift from its sources.
   Verified by tampering with one notice title: T4 fails and names the
   offending notice, telling you to re-run the build.

8. **`_jsmap.py` and `_jssplit.py` have served their purpose.** They are kept
   because nothing is deleted in this project, but they are one-shot Phase-4
   tools and should not be mistaken for part of the build.
