# Testing the notice fetcher

`tools/fetch_notices.py` has one half I could not test from where I built it: the
**browser half**. Everything I could test offline, I did — and it's scripted so you
can re-run it any time.

The fetcher is split into stages so a failure names one cause instead of "it didn't
work". Run the stages in order. Each one below lists the exact command, the output
you should see (these are real outputs from my runs), and what to do if you see
something else.

---

## 0 · One-time setup

```bash
cd bb-notice
python3 --version                       # need 3.9+
pip install pdfplumber playwright
python3 -m playwright install chromium
```

Then confirm the install is sane:

```bash
python3 tools/test_fetch.py             # offline stages only, no network, ~5 s
```

Expected output — this is verbatim from my run:

```
BB notice fetcher — staged tests

— offline —
  ✓ T1a  PASS  python 3.13.16
  ✓ T1b  PASS  pdfplumber installed
  ✓ T1c  PASS  playwright installed
  … T1d  INFO  no profile yet — first run will need a CAPTCHA
  ✓ T2   PASS  8 rows, 0 malformed, e.g. 20261108_bscs_357_1794134950.pdf
  ✓ T3   PASS  5 classifier fixtures
  ✓ T4   PASS  site builds; committed data matches a fresh parse (13 notices)

7 checks · 7 passed · 0 failed · 0 skipped
```

**Gate:** 7/7 passed before you touch the network. If T1b/T1c fail, the pip install
didn't take. If T4 fails, the local pipeline is broken and fetching more PDFs will
only make it worse — fix that first.

> Note `T1d`: on your very first run there is no browser profile, so a CAPTCHA is
> expected. After that the profile at `~/.bb-fetch-profile` holds the F5 cookie and
> T1d will report a size in KB instead.

---

## 1 · What each stage proves

| Stage | Proves | Needs network |
|---|---|---|
| T1a–d | Python, pdfplumber, playwright, chromium, cookie profile | no |
| T2 | `career.html` still parses into 8 PDF rows | no |
| T3 | the WAF classifier reads real/CAPTCHA/rejected/empty pages correctly | no |
| T4 | site builds, and `data/notices.json` is exactly what the parser produces | no |
| T5 | a Chromium binary actually launches | no (local binary) |
| T6 | the portal answers, and **which** answer you get | yes |
| T7 | the challenge clears once a human solves it | yes + you |
| T8 | live HTML yields as many notice rows as the saved copy | yes |
| T9 | a downloaded file is genuinely a PDF, not a challenge page | yes |

---

## 2 · The offline gates in detail

### T2 — does the saved listing still parse?

```bash
python3 tools/test_fetch.py --only T2
```

Pass: `8 rows, 0 malformed`. This matters because the whole pipeline depends on
`career.html` keeping its shape. If BB redesigns the table, T2 goes red *before*
anything is downloaded, and the fix is `listing_pdf_urls()` in `tools/fetch_notices.py`
(it looks for `<tr>` rows containing an `href="…​.pdf"`).

### T3 — does the WAF classifier tell the pages apart?

```bash
python3 tools/test_fetch.py --only T3
```

Five fixtures: the real listing → `ok`; an F5 CAPTCHA page → `challenge`; a
`Request Rejected` page → `challenge`; empty → `empty`; a maintenance page → `empty`.

This stage earned its keep immediately — it caught a real bug in my own classifier
where a 246-byte `Request Rejected` page was classified `empty` because the length
check ran before the marker check. Without T3 you'd have seen "empty page" and spent
an hour hunting the wrong thing.

### T4 — is the data pipeline still consistent?

```bash
python3 tools/test_fetch.py --only T4
```

Runs `build_data.py` → `build_site.py` → `selftest.py`, then compares the
result against the committed data.

`build_data.py` writes to a **temporary file**, not over `data/notices.json`.
Overwriting it refreshed the `generated` timestamp on every run, so `index.html`
changed every time you ran the tests even when nothing about the site had.
Comparing instead is also stricter: it proves the committed data is exactly what
the current parser produces from the current PDFs and overrides, so curated data
cannot quietly drift from its sources.

Pass: `site builds; committed data matches a fresh parse (13 notices)` and
`ALL PASS` from the selftest.

If T4 reports *"data/notices.json is not what the parser produces"*, the
committed data is stale — run `run.bat` (or `build_data.py`) to refresh it. It
names the notices that differ.

---

## 3 · The live stages

Run this **with a visible browser window** the first time. Do not use `--headless`
for the first run — if a CAPTCHA appears you need to see it to solve it.

```bash
python3 tools/test_fetch.py --live --solve
```

### T5 — does Chromium launch?

Pass: `✓ T5 PASS chromium 158.0.8127.18 launches`

If it fails: `python3 -m playwright install chromium`. On Linux you may also need
`python3 -m playwright install-deps chromium`.

### T6 — what does the portal actually say to you?

Expected pass (from a residential BD IP, after the profile has been warmed once):

```
… T6   INFO  HTTP 200 · 43 KB · state=ok · 4.7s
```

What I get from a datacenter IP, and what you'll get on the first run of a fresh
profile — this is my real output:

```
… T6   INFO  HTTP 200 · 43 KB · state=challenge · 4.7s
```

`state=challenge` means the firewall served the JS challenge or a CAPTCHA.
**HTTP 200 is normal even when you're blocked** — the WAF answers 200 with a
challenge page, so never judge by status code, only by `state`.

If `state=empty`: the page loaded but has no `.pdf` links. Either the site is down
for maintenance, or the listing markup changed. Open `https://erecruitment.bb.org.bd/career/jobopportunity.php`
in your normal browser — if you see the table there but the script doesn't, it's a
markup change (send me the saved HTML).

### T7 — clearing the challenge

With `--solve`, the script waits up to `--timeout` seconds (default 300) while:

```
      ┌─────────────────────────────────────────────┐
      │ solve the CAPTCHA in the browser window now │
      └─────────────── waiting up to 300s ───────────────┘
```

**What to do:** look at the browser window. If you see *"What code is in the image?"*
type the code and submit. If you see a blank page with a spinner, just wait — the JS
challenge usually resolves in 2–5 seconds. Do not close the window.

Pass: `✓ T7 PASS challenge cleared`.

If it times out: `✗ T7 FAIL still blocked`. Try, in order:
1. Re-run — F5 challenges are sometimes one-shot.
2. Delete the profile and start clean: `rm -rf ~/.bb-fetch-profile` (on Windows:
   delete `C:\Users\<you>\.bb-fetch-profile`). A corrupted cookie is worse than none.
3. Make sure no other Chromium/Playwright instance is holding the profile. Only one
   process may use `~/.bb-fetch-profile` at a time.
4. Try your phone as a hotspot — mobile carrier IPs are sometimes treated better than
   home broadband.

### T8 — live rows vs saved rows

Expected:

```
✓ T8   PASS  8 rows live vs 8 saved · 0 new
```

or with new notices published:

```
✓ T8   PASS  9 rows live vs 8 saved · 1 new
```

`N new` is exactly what the real fetch will download. If it says `0 new` but you can
see a fresh notice on the portal, the row's filename is already in `notices/` — check
`ls notices/`.

### T9 — is the downloaded file really a PDF?

This is the most important live check, because the WAF will happily return a
**challenge page with HTTP 200** instead of the PDF. The stage downloads one file
(never a new one — it re-tests an existing row) and inspects the bytes.

Expected:

```
✓ T9   PASS  HTTP 200 · 196 KB (listing says 196 KB) · magic=b'%PDF-' · 20261108_bscs_357_1794134950.pdf
```

Failure modes and what they mean:

| What T9 prints | Meaning | Fix |
|---|---|---|
| `magic=b'<htm'` or `b'<!DO'` | you got an HTML challenge instead of the PDF | your cookie expired mid-session — re-run `--solve` |
| `HTTP 403` / `HTTP 302` | the WAF refused the direct request path | download via the browser context (the script does) rather than `requests`/`curl` — this is why the code uses `ctx.request`, not `requests` |
| size 40–60 KB when listing says 196 KB | truncated/challenge body | same as above |
| `TimeoutError` | slow link | raise `timeout` in the call |

---

## 4 · First real fetch, and how to know it worked

Once T1–T9 are green:

```bash
python3 tools/fetch_notices.py --build --log logs/fetch.log
```

Expected (numbers from your current state — 4 notices are missing):

```
→ https://erecruitment.bb.org.bd/career/jobopportunity.php
  ✓ listing saved -> career.html (42 KB)
  ↓ 20261027_bscs_348_1793084047.pdf  (93 KB)
  ↓ 20260621_bscs_217.pdf  (91 KB)
  ↓ 20260506_bscs_163.pdf  (279 KB)
  ↓ 20260505_bscs_159.pdf  (97 KB)
wrote data/notices.json: 10 notices, ...
wrote index.html  (... KB, 10 notices inlined)
```

**Five acceptance checks, in order:**

```bash
ls notices/*.pdf | wc -l          # A1  10  (6 you had + 4 fetched)
python3 tools/selftest.py         # A2  ALL PASS
git diff --stat data/notices.json # A3  changed, and the new notices are the ones you expected
python3 tools/test_fetch.py       # A4  7/7 offline still green
```

**A5 — the site.** Open `index.html`, and search a roll from a newly fetched notice.
To find one: expand the notice card → the centre table shows roll ranges. Type the
first roll of a range and confirm it names that centre. Then check a roll from the
*old* notices still resolves (e.g. `105432` → two cards, 86/2026 and 357/2026).

That fifth check is the real one: it proves the whole chain — fetch → parse →
convert → data → page.

---

## 5 · Verifying an individual PDF by hand

If you ever doubt a specific file, three independent checks:

```bash
# 1. header bytes: a real PDF starts with %PDF-
head -c 5 notices/20261110_bb_86_1794286537.pdf ; echo

# 2. size versus what the listing page claims
ls -l notices/20261110_bb_86_1794286537.pdf      # 777 KB here matches "(777 KB)" on the page

# 3. does the parser see the expected content?
python3 parser/bbparse.py notices/20261110_bb_86_1794286537.pdf
```

Expected third command:

```
  notice 86/2026 · kind=centre · 1p · exam=13/11/2026 10:00 AM/11:00 AM
  centres=4 seats=16596 span=100001–116596
    100001–108000  ড. মাহবুবুর রহমান মোল্লা কলেজ ...
```

The `seats` number must equal the total printed inside the PDF (`= 16,596`). That's
the strongest single signal that the parse is faithful.

---

## 6 · Scheduling it, and verifying the schedule

Windows Task Scheduler, daily 09:00:

```
Program:   pythonw.exe    (no console window)
Arguments: C:\path\to\bb-notice\tools\fetch_notices.py --headless --build --push --log C:\path\to\bb-notice\logs\fetch.log
Start in:  C:\path\to\bb-notice
```

macOS/Linux cron:

```
0 9 * * * cd /path/bb-notice && python3 tools/fetch_notices.py --headless --build --push --log logs/fetch.log
```

**How to verify a scheduled run actually happened** — three independent traces:

```bash
tail -40 logs/fetch.log          # B1  a "=== 2026-11-12 09:00:03 ===" block with ✓ lines
git log --oneline -5             # B2  "notices: auto-update" commits on the days it ran
git status --short               # B3  clean — nothing left uncommitted
```

If B1 shows `state=challenge` every day, your profile expired: run once interactively
with `--solve`, then the schedule resumes. That's the one recurring manual task, and
it's why the non-headless mode exists.

---

## 7 · Failure table

| Symptom | Cause | Fix |
|---|---|---|
| T5 fails: "Executable doesn't exist" | Chromium not installed | `python3 -m playwright install chromium` |
| T6 `state=challenge` forever, headed | CAPTCHA on screen, unsolved | solve it; or `rm -rf ~/.bb-fetch-profile` and retry |
| T6 `state=challenge` only in `--headless` | headless fingerprint is suspect | use headed mode for the first run each month |
| T6 `state=empty` | site maintenance or markup change | check the URL in your normal browser; send me a saved copy |
| T7 times out | profile lock, stale cookie, or IP reputation | close other runs → delete profile → try phone hotspot |
| T8 `0 rows live` | you're on a challenge page that slipped through | re-run T6; check `page_state()` output |
| T9 `magic=b'<htm'` | WAF served HTML with HTTP 200 | re-warm the cookie with `--solve`; confirm the code uses `ctx.request` |
| Downloads OK but `selftest` fails | a new PDF has a layout the parser hasn't seen | `python3 parser/bbparse.py <that.pdf>` and check `kind` — send me the output |
| `data/notices.json` unchanged after a green fetch | all PDFs were already present | expected: `--plan` lists what's missing |
| Site search finds nothing after a rebuild | `index.html` not rebuilt | `python3 parser/build_site.py` |

---

## 8 · If something fails, send me exactly this

```bash
python3 tools/test_fetch.py --live --solve --log logs/diag.log   # let it finish
cat logs/diag.log
```

Paste the log. The stage tags (T1–T9) make it unambiguous which layer broke, so the
fix is usually a one-line change rather than a guessing round-trip.

---

## 9 · What is already proven, and what isn't

| Claim | Evidence |
|---|---|
| The parser is faithful | `selftest.py`: 357/2026 → 120,529 seats = `Total= 120529` printed in the PDF; 85/2026 → 677 rolls = `677 …Rb`; 86/2026 → 16,596 |
| Bangla conversion works | 24/24 cases in `selftest.py`, strings taken from your six PDFs |
| The WAF classification is correct | T3's five fixtures, incl. the 246-byte rejection page that found a real bug |
| The listing parses | T2: 8 rows from your saved `career.html` |
| Data → site pipeline is consistent | T4: rebuild + invariants |
| Chromium launches, page loads, state detected | T5/T6 run here: `HTTP 200 · 43 KB · state=challenge · 4.7s` |
| **A real notice gets downloaded from the live portal** | **not yet** — needs your IP. T9 is that proof, and it is the one line I want to see green. |
| **End-to-end on a new notice** | **not yet** — acceptance check A5 |
