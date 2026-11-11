# BB E-Recruitment Roll Finder

Enter your roll number → get your exam centre, seat range, date, time and a map link.
Static site, no server, works offline. Covers seat plans, viva schedules and selected lists.

**Open `index.html`.** 80 KB, 19.9 KB gzipped, works offline after one visit.

Double-click **`run.bat`** to fetch new notices and push; **`check.bat`** to verify.
Deployment: see `DEPLOY.md`. Design rationale and benchmarks: `AUDIT.md`.

```bash
python3 tools/selftest.py                       # 24 converter cases + data invariants
python3 parser/build_data.py --html career.html --pdfs notices --out data/notices.json
python3 parser/build_site.py                    # inline data -> index.html
python3 tools/fetch_notices.py --plan           # which listed PDFs aren't downloaded
python3 tools/fetch_notices.py --build --push   # fetch (auto-uses Brave/Chrome), rebuild, push
```

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
