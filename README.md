**Live: <https://bb-roll-finder.pages.dev>**

# BB E-Recruitment Roll Finder

Enter your roll number → get your exam centre, seat range, date, time and a map link.
Static site, no server, works offline. Covers seat plans, viva schedules and selected lists.

**Open `index.html`.** 90 KB, 23 KB gzipped, works offline after one visit.

Double-click **`run.bat`** to fetch new notices and push; **`check.bat`** to verify.
Applying a new `bb-notice.zip` over your copy: **`UPGRADE.md`** (exact commands).
Audit & backlog: `ROADMAP.md`.
Deployment: **`HOSTING.md`** (beginner, step by step) or `DEPLOY.md` (short). Design rationale and benchmarks: `AUDIT.md`.

```bash
python3 tools/selftest.py                       # converter cases, data invariants, build integrity
python3 tools/uitest.py                         # 121 browser checks (needs playwright)
python3 parser/build_data.py --html career.html --pdfs notices --out data/notices.json
python3 parser/build_site.py                    # markup + css + js + data -> index.html
python3 tools/fetch_notices.py --plan           # which listed PDFs aren't downloaded
python3 tools/fetch_notices.py --build --push   # fetch (auto-uses Brave/Chrome), rebuild, push
```

### Where things live

`index.html` is **generated — never edit it.** `parser/build_site.py` assembles it
from four sources and inlines everything, so the page is one self-contained file
that works from `file://` and offline.

```
app.template.html          markup + the early theme script; /*__CSS__*/ and /*__JS__*/ placeholders
assets/css/                tokens → base → layout → components → responsive → print
                           (concatenation order is the cascade; see CSS_FILES)
assets/js/
  core/constants.js        notice-kind taxonomy, post-name regex
  core/dom.js              $(), esc(), safeHref()
  core/numbers.js          Bengali/ASCII digit conversion
  core/dates.js            exam dates, status, countdown
  core/language.js         LANG, t(), and the full en/bn STR table  ← edit copy here
  data/notices.js          /*__DATA__*/ placeholder + the derived lookup Maps
  features/                maps · results · rolls · search · notice-list · preferences
  app.js                   event wiring, service worker, boot(), the BB surface
```

The scripts are concatenated into **one classic `<script>`** sharing a scope —
not ES modules, because `import` over `file://` is blocked by CORS. `JS_FILES`
in `build_site.py` is the load order; the build fails if a file on disk is
missing from it.

| notice kind | the PDF publishes | the site does |
|---|---|---|
| `seat` | centre table with roll ranges | roll → centre, date, time, map |
| `viva` / `result` | roll lists grouped by sitting | roll → date, reporting time, batch |
| `selected` | flat list of selected rolls | roll → "you are selected" |
| `circular` | schedule only | indexed + linked |
| `scanned` | a photograph, no text layer | flagged as unsearchable, links to PDF |

Notes on the tricky parts: see `PLAN.md` §4 (the PDFs use a legacy Bijoy font) and
§6 (the portal's WAF blocks cloud crawlers, so fetching runs locally).

Requires `pdfplumber`; `playwright` only for `tools/fetch_notices.py`.
