# BB E-Recruitment — Roll Finder

A static site that answers one question in under a second: **"where do I have to
be, and when?"** It indexes seat plans, viva schedules and selected-candidate
lists from the Bangladesh Bank / BSCS recruitment portal.

Status: working, and the automatic fetch is proven against the live portal
(2026-11-11, via Brave). 9 notices, 35 centres, 3,840 searchable rolls, all parsed
from real PDFs and verified against numbers printed inside those PDFs.

---

## 1. The constraint that shaped everything

`erecruitment.bb.org.bd` is behind an F5 BIG-IP ASM firewall. Measured, not guessed:

| Client | Result |
|---|---|
| `curl`, no headers | `Request Rejected` (246 bytes) |
| `curl` + browser headers | TLS connection reset |
| Headless Chromium | escalated to an image CAPTCHA |
| `/career/*.pdf` fetched directly | blocked exactly the same way |

**Consequence:** any plan that starts with "a GitHub Action crawls the portal daily"
is dead. GitHub's runners are datacenter IPs and get the CAPTCHA. Automation has to
run on a real machine with a residential IP — which is what `tools/fetch_notices.py` does.

## 2. Why the data is small

Centre notices publish **ranges**, not 20,000 rows:

```
100001 – 108416  →  Milestone College, Diabari, Turag-Dhaka   (7,200 seats)
```

So "find my roll" is a binary search over 31 numbers. The entire dataset for six
notices — including every viva roll and every selected-candidate roll — is **255 KB**.
That is why the whole site is one file and loads with no network.

## 3. The three notice layouts (all handled)

| Kind | What the PDF contains | Verified against |
|---|---|---|
| `seat` | centre table with `Starting Roll` / `Ending Roll` | 357/2026 → 120,529 seats = `Total= 120529` ✓ · 86/2026 → 16,596 ✓ |
| `viva` / `result` | comma-separated roll lists + date/time column | 85/2026 → 677 rolls, 12 sittings ✓ · 350/2026 → 2,126 rolls, 34 sittings |
| `selected` | flat list of rolls, no table | 319/2026 → 1,037 rolls = `1,037wU` ✓ |

A fourth case exists: notices with a schedule but no roll data (356/2026). They're
indexed and linked, not searchable.

## 4. The two hard problems, and how they were solved

**a) The Bangla is a legacy encoding.** All six PDFs embed a Bijoy/SutonnyMJ font
with no ToUnicode map, so `extract_text()` returns `evsjv‡`k e¨vsK`. Digits survive
as ASCII, which is why roll ranges were always readable.

`parser/bijoy2unicode.py` now converts properly, with the four rules that make this.
more than a lookup table:

- ি and ে are stored *before* their consonant and must move after it (`wgicyi` → মিরপুর)
- ে + া collapse into ো (`†ivW` → রোড)
- © is a reph that swaps with the preceding consonant (`Kvh©` → কার্য)
- bold runs duplicate every glyph (`মমাাততুয়াইল`), so de-duplication runs on the
  raw ANSI *before* conversion — after conversion the ি-reordering interleaves it

**24/24 regression cases pass** (`tools/selftest.py`), covering real strings pulled
from the notices. Latin runs are shielded first, so `info.bscs@bb.org.bd` comes out
intact instead of turning into plausible-looking Bangla.

**b) The listings are behind a CAPTCHA.** Solved by not fighting it: fetch locally,
cache the cookie, commit the result. See §6.

## 5. Layout & commands

```
bb-notice/
├── index.html              the app — data inlined, 80 KB / 19.9 KB gzipped
├── sw.js                   service worker — works with no internet
├── manifest.webmanifest    installable to home screen
├── _headers                Cloudflare/Netlify cache rules
├── run.bat / check.bat     one-click update / one-click verify
├── app.template.html       same app with a /*__DATA__*/ placeholder
├── career.html             saved listing page (fixture for the pipeline)
├── data/notices.json       6 notices · 35 centres · 3,840 rolls · 255 KB
├── meta/overrides.json     verified Bangla names, titles, venue text
├── notices/*.pdf           source PDFs, linked from every card
├── parser/
│   ├── bbparse.py          PDF → structured data (3 layouts + Bangla fallback)
│   ├── bijoy2unicode.py    legacy font → Unicode Bengali
│   ├── build_data.py       listing HTML + PDFs → data/notices.json
│   └── build_site.py       data + template → index.html
└── tools/
    ├── fetch_notices.py    local fetch (browser, cookie reuse, --build --push)
    └── selftest.py         converter + data invariants
```

```bash
python3 tools/selftest.py                                        # does it still work?
python3 parser/build_data.py --html career.html --pdfs notices --out data/notices.json
python3 parser/build_site.py
python3 tools/fetch_notices.py --plan                            # what's not downloaded yet
```

**Adding a notice by hand** (~40 s): drop the PDF in `notices/` → run the two build
commands → push. Titles come from `career.html`; if the notice isn't there yet, add
it to `meta/overrides.json`.

## 6. Automation tiers

| Tier | How | Effort | Reliability |
|---|---|---|---|
| **A — manual drop** | download PDF, 2 commands, push | none | 100 % |
| **B — local fetch** ⭐ | `fetch_notices.py` — **uses your installed Brave/Chrome**, persistent profile keeps the F5 cookie, solve a CAPTCHA once, then Task Scheduler runs `--build --push` daily | one evening | proven 2026-11-11 |
| **C — cloud cron** | GitHub Actions | — | **blocked by CAPTCHA** |

Deploy:
```bash
cd bb-notice && git init && git add -A && git commit -m "BB roll finder"
gh repo create bb-roll-finder --public --source=. --push
# Settings → Pages → main / (root)
```

## 7. What's still imperfect — the honest list

1. **Bangla addresses carry small artifacts.** `মিরপুরুর-২` instead of `মিরপুর-২`:
   the PDF's doubling is irregular in those cells (`wwggiiccyiyi`). Names are clean;
   addresses are ~95 %. The four 86/2026 centres use verified overrides.
2. **Row 4 of 86/2026 needs its override** — the cell wraps, so the parsed name is
   empty and `meta/overrides.json` supplies `ল্যাবরেটরি ইনস্টিটিউট`.
3. **Titles for 85 & 86 are overrides** — your saved `career.html` predates them;
   a fresh save fills them in automatically.
4. **Headless mode does not clear the WAF.** Playwright's bundled Chromium gets the
   CAPTCHA forever (confirmed in `logs/fetch.log`, 09:54 and 10:00 runs). The fetcher
   now auto-detects **Brave, then Chrome**, which passes. Run it windowed, not headless.
5. **Two of the nine notices are photographs.** 83/2026 and 372/2026 are full-page
   scans — 100 % image coverage, no real text layer. Their rolls cannot be indexed;
   the site shows an explicit SCANNED card instead of pretending they are searchable.
   372/2026 is a selected-candidate list, so this one hurts: you must open that PDF
   by eye. Real Bengali OCR is the only fix and it is not free.
6. **350/2026 sitting order** is sorted by date+time; the PDF's own row order
   interleaves three column groups per page.

## 8. Next steps, by payoff

| # | Task | Effort | Why |
|---|---|---|---|
| 1 | Schedule `run.bat` daily (fetch already proven to work) | 20 min | Removes the only manual step |
| 2 | PWA manifest + service worker | 1 h | Installable; works in an exam hall with no signal |
| 3 | `ntfy.sh` alert when a new notice is committed | 1 h | Phone notification, no account |
| 4 | Bijoy address cleanup (irregular doubling) | 2 h | Cosmetic; names already correct |
| 5 | Share link with roll baked in (`#roll=105432`) | done | — |

> **The disclaimer stays.** This is a convenience layer over the official PDFs —
> every result card links to the source PDF, because a wrong centre means a missed exam.
