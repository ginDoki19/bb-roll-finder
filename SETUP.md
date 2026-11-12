# Setup on your own machine

Everything below is copy-paste. Windows commands are first; macOS/Linux notes are in
the side comments. Total time: about 10 minutes, of which 2–3 are downloads.

---

## Step 0 · Unzip somewhere permanent

Unzip `bb-notice.zip` so you get:

```
C:\Users\<you>\bb-notice\          ← Windows
~/bb-notice/                       ← macOS / Linux
├── index.html          the app (works by double-clicking, no setup)
├── career.html         saved listing page
├── data/notices.json   parsed data
├── notices/*.pdf       6 source PDFs
├── meta/overrides.json verified Bangla names
├── parser/             bbparse.py · bijoy2unicode.py · build_data.py · build_site.py
├── tools/              fetch_notices.py · selftest.py · test_fetch.py
└── PLAN.md · TESTING.md · README.md
```

Don't put it in Downloads, OneDrive-synced folders, or a path with Bengali
characters — Python and git both get unhappy with some of those.

**Right now you can already use the app:** double-click `index.html`. That part needs
no Python at all.

---

## Step 1 · Install Python 3.9+

Check first — you may already have it:

```cmd
python --version
```

If that prints `Python 3.9` or higher, skip to Step 2.

Otherwise install from <https://www.python.org/downloads/> and **tick
"Add python.exe to PATH"** on the first installer screen. That checkbox is the single
most common source of "python is not recognized" later.

Verify in a **new** terminal window:

```cmd
python --version
pip --version
```

macOS/Linux: `python3 --version`; if missing, `brew install python` (macOS) or
`sudo apt install python3 python3-pip` (Debian/Ubuntu).

---

## Step 2 · Open a terminal inside the project folder

**Windows:** open the folder in File Explorer, click the address bar, type `cmd`,
press Enter. A terminal opens already in `C:\Users\<you>\bb-notice`.

**macOS:** right-click the folder → Services → New Terminal at Folder.
**Linux:** `cd ~/bb-notice`.

Confirm you're in the right place:

```cmd
dir index.html
```

You should see a line for `index.html`. Everything below assumes you're here.

---

## Step 3 · Install the two dependencies

```cmd
pip install pdfplumber playwright
python -m playwright install chromium
```

- `pdfplumber` (~2 MB) parses the PDFs.
- `playwright` + Chromium (~130 MB download) is only needed for fetching new notices.
  If you only ever add PDFs by hand, you can skip it and everything except
  `tools/fetch_notices.py` still works.

If `pip` complains about permissions, use `pip install --user ...` instead.

---

## Step 4 · Prove the install works (offline, 5 s)

```cmd
python tools\test_fetch.py
```

Expected:

```
  ✓ T1a  PASS  python 3.13.16
  ✓ T1b  PASS  pdfplumber installed
  ✓ T1c  PASS  playwright installed
  … T1d  INFO  no profile yet — first run will need a CAPTCHA
  ✓ T2   PASS  8 rows, 0 malformed, e.g. 20261108_bscs_357_1794134950.pdf
  ✓ T3   PASS  5 classifier fixtures
  ✓ T4   PASS  rebuild + selftest OK (6 notices)

7 checks · 7 passed · 0 failed · 0 skipped
```

Then:

```cmd
python tools\selftest.py
```

Expected: `24/24 conversion cases pass`, four `ok` notice lines, `ALL PASS`.

**Stop here if either is red** — nothing after this will work better. Send me the output.

---

## Step 5 · Try the app in a browser

Double-click `index.html`, type `105432`.

You should get two cards:

- **86/2026 · Job 307** → ড. মাহবুবুর রহমান মোল্লা কলেজ, মিরপুর, ঢাকা-১৩৬২,
  13/11/2026, 10:00–11:00, be there 9:00 AM
- **357/2026 · Job 26101** → Milestone College, Diabari, Turag-Dhaka,
  13/11/2026, 3:00–4:00 PM, be there 2:00 PM

Click "Open in Google Maps" — it should land on the right campus. (The inline map
iframe needs internet; the button works regardless.)

---

## Step 6 · Fetch new notices

**Use `run.bat`** (double-click it), or:

```cmd
python tools\fetch_notices.py --build --log logs\fetch.log
```

⚠️ **Do not add `--headless`.** Playwright's bundled Chromium never clears the
firewall — it loops on the CAPTCHA forever. The fetcher auto-detects your installed
**Brave** (then Chrome) and uses that instead, which works. Keep the window visible.

Run this **headed** — a browser window opens; you need to see it:

```cmd
python tools\fetch_notices.py --plan
python tools\fetch_notices.py --build --log logs\fetch.log
```

`--plan` first (reads only the saved `career.html`, no network):

```
8 notices in the saved listing
  [ have  ]  26101  20261108_bscs_357_1794134950.pdf   196 KB
  [MISSING]  26101  20261027_bscs_348_1793084047.pdf    93 KB
  ...
```

Then the real fetch. Expected:

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

If a CAPTCHA appears in the window — type the code, submit, wait. It usually clears
by itself in 2–5 seconds. Full walkthrough and failure table: **TESTING.md**.

Verify:

```cmd
dir notices\*.pdf | find /c ".pdf"     :: A1 -> 10
python tools\selftest.py               :: A2 -> ALL PASS
python tools\test_fetch.py             :: A4 -> 7/7
```

Then reopen `index.html`, expand a **new** notice, and search a roll from its centre
table. If that resolves to the right centre, the whole chain works.

**Two notices will show an orange SCANNED card** (83/2026 and 372/2026). That is
correct, not a bug: those PDFs are photographs with no text layer, so their roll
numbers cannot be indexed. The card tells you to open the PDF by eye.

**Never commit `logs/`.** The log records your session cookies verbatim when a
download fails. `.gitignore` already excludes it — leave that line alone.

---

## Step 7 · Put it on the internet (GitHub Pages, free)

One-time:

```cmd
git init
git add -A
git commit -m "BB roll finder"
```

Create an empty repo on GitHub named `bb-roll-finder` (no README, no .gitignore),
then:

```cmd
git remote add origin https://github.com/<your-username>/bb-roll-finder.git
git branch -M main
git push -u origin main
```

On GitHub: **Settings → Pages → Source: Deploy from a branch → Branch: `main` / `/ (root)` → Save.**

Wait ~60 seconds, then open:

```
https://<your-username>.github.io/bb-roll-finder/
```

Test it on your phone. That URL is what you share with other candidates.

If `git` says "not found": <https://git-scm.com/download/win>.
If `git push` asks for a password, GitHub wants a **Personal Access Token**
(Settings → Developer settings → Tokens (classic) → Generate new token, scope `repo`)
— paste that as the password.

---

## Step 8 · Make it automatic (optional, 10 min)

Windows Task Scheduler:

1. Open **Task Scheduler** → **Create Basic Task** → name it `BB notices` → Daily → 09:00.
2. Action: **Start a program**
   - Program: `pythonw.exe`  (the `w` version runs without a console window)
     — note: the *browser* window still appears, and must, so the WAF is satisfied
   - Arguments: `tools\fetch_notices.py --build --push --log logs\fetch.log`
   - Start in: `C:\Users\<you>\bb-notice`
3. Finish, then right-click the task → **Run** to test it now.

macOS/Linux cron — `crontab -e`:

```
0 9 * * * cd ~/bb-notice && python3 tools/fetch_notices.py --build --push --log logs/fetch.log
```

**Check it actually ran** (three independent traces):

```cmd
type logs\fetch.log
git log --oneline -5
git status --short
```

If the log says `state=challenge` every day, the cached cookie expired: run
`python tools\fetch_notices.py --build --push` once by hand, in a window, and solve
the CAPTCHA. That's the only recurring manual task.

---

## Adding a notice by hand (works today, no browser needed)

If fetching ever fails, this path always works:

1. Open <https://erecruitment.bb.org.bd/career/jobopportunity.php> in Chrome.
2. Right-click the "Download PDF" button for the notice → **Save link as** →
   save into `notices\` keeping the exact filename.
3. `Ctrl+S` the listing page into the project folder as `career.html` (overwrite).
4. Run:

```cmd
python parser\build_data.py --html career.html --pdfs notices --out data\notices.json
python parser\build_site.py
git add -A && git commit -m "notice added" && git push
```

---

## Nearest-term checklist

| Time | Do this | Done when |
|---|---|---|
| now | double-click `index.html`, search `105432` | two cards appear |
| 10 min | Steps 1–4 (Python, deps, offline tests) | `7 checks · 7 passed` |
| 15 min | Step 6 (fetch) | `↓` lines for 4 PDFs, `10 notices` |
| 10 min | Step 7 (GitHub Pages) | the `.github.io` URL opens on your phone |
| 10 min | Step 8 (schedule) | `logs\fetch.log` has today's block |
| ongoing | nothing | `git log` shows auto-update commits on days notices publish |

---

## When something breaks

```cmd
python tools\test_fetch.py --live --solve --log logs\diag.log
```

Paste `logs\diag.log`. The stage tags (T1–T9) tell me which layer failed, so it's
usually a one-line fix rather than a guessing round-trip.


## Reading a scanned notice automatically (`tools/ocr_rolls.py`)

Some notices are photographs of paper — no text to extract. This script reads
the roll numbers off the image, but only publishes them when the notice's own
figures agree.

```
pip install pytesseract pypdfium2
```
plus Tesseract itself: <https://github.com/UB-Mannheim/tesseract/wiki>
(click through the installer; the script finds it automatically on Windows).

```
python tools\ocr_rolls.py notices\20261111_bb_87_1794395117.pdf --expect 334 ^
       --post "সহকারী ব্যবস্থাপক (জেনারেল)" --job-id 303 --published 11/11/2026
```

`--expect` is the total printed on the notice ("৩৩৪ (তিনশত চৌত্রিশ) জন"). It
runs Tesseract four different ways and keeps the read that matches:

```
  pass          found  ascending  matches-total
  digits/psm6     332        yes             no
  digits/psm4     332        yes             no
  plain/psm6      334        yes            yes      <- chosen
  plain/psm11     333        NO              no

  confirmed   : 332 by 3+ of 4 passes
  rejected    : 217751, 235993 (failed the order/total check)
  ⚠ LOW CONFIDENCE — check these few against the PDF by eye:
      221034   (seen by 2 of 4 passes)
```

**Nothing goes live yet.** It writes `meta/overrides.draft.json`. Open the PDF,
check only the low-confidence numbers, then:

```
python tools\ocr_rolls.py --approve
run.bat
```

If the count does not match the printed total, it refuses to write anything and
tells you to transcribe that one by hand. A wrong digit tells a candidate they
failed, so the bar is deliberately high. The site labels these lists "Read
automatically from a scanned notice" and links the official PDF.

## Optional: `pip install curl_cffi` (recommended)

One command, and most runs finish with **no browser window at all**:

```
pip install curl_cffi
```

F5 fingerprints the TLS handshake itself (JA3/JA4) before it reads a single
header, and Python's default handshake is instantly recognisable as "not a
browser" — which is why a perfectly valid cookie could still come back as a
6 KB challenge page. `curl_cffi` replays Chrome's exact handshake, so the
cookie actually gets evaluated. Measured:

```
urllib     ja3n: 50bc0abcbaf93e723c87ee44564256f5   (Python-urllib)
curl_cffi  ja3n: bd4930bd9b000ee684830e44bab76fdf   (real Chrome)
```

Without it everything still works — the script falls back to urllib, then to
the browser window.

## Why a browser window opens at all

Two different things have to get past Bangladesh Bank's F5 firewall:

| What | How it is fetched | Needs a browser? |
|---|---|---|
| the listing page | `jobopportunity.php` | only if the cookie is refused |
| the notice PDFs | plain HTTPS GET | no |

With a session pasted into `meta/session.txt` the script now tries the whole run
over **plain HTTP first — no window at all**. You will see:

```
🍪 session: 10 cookie(s) [...], UA replayed — trying without a browser
✓ listing saved -> career.html (7 PDFs) — no browser needed
```

The browser only opens if that cookie is refused, because F5 can also demand a
JavaScript challenge that cannot be replayed from a script — a real browser has
to execute it. In that case the window appears and you will see:

```
· cookie alone did not clear F5 — opening the browser window
```

That window usually clears **by itself** within a few seconds. Only type a
CAPTCHA if one is actually visible on screen. The script waits 15 s before it
says anything, then reports `✓ challenge cleared after 6s` once it is through.

Use `--force-browser` to skip the fast path deliberately.

## When the fetch keeps saying "CAPTCHA NEEDED"

The fetcher drives Brave with **its own profile** (`~/.bb-fetch-profile`), which is a
separate cookie jar from the Brave you browse in. So solving the challenge in your
normal window does **not** help it — it has to pass the challenge on its own.

You can just hand it the session you already solved:

1. In normal Brave open
   <https://erecruitment.bb.org.bd/career/jobopportunity.php> and solve the CAPTCHA
   until you can see the notice table.
2. `F12` → **Network** tab → press `F5` to reload.
3. Click the first row (`jobopportunity.php`).
4. Right-click it → **Copy** → **Copy as cURL (bash)**.
5. Paste the whole thing into `meta/session.txt` and save.
6. Run `run.bat` as usual. You should see:

   ```
   🍪 session injected: 7 cookie(s) [TSPD_101, bb_cookie, TS01cf43c8, …], UA replayed
   ```

**Any Copy-as format works** — cURL (bash), cURL (cmd), fetch, fetch (Node.js) or
PowerShell. A plain `cookie: a=b; c=d` line works too if you prefer.

Note that Chromium 115+ (so Brave 157) writes the cookie as a `-b` flag in bash
ANSI-C quoting rather than as a `cookie:` header:

```
-b $'PHPSESSID=...; bb_cookie=\u0021Uh/...; TSPD_101=...'
```

The `\u0021` is an escaped `!`. Both forms are parsed, and the escapes are
decoded — if they were not, F5 would see a corrupted token and reject it.

To confirm the paste parsed before running a whole fetch:

```
session-check.bat
```

It prints the cookie **names** only, never the values, so the output is safe to
share when asking for help:

```
session file: meta\session.txt
  7 cookie(s): TSPD_101, bb_cookie, TS01cf43c8, PHPSESSID, ...
  F5 token    : TSPD_101, TS01cf43c8
  user-agent  : Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/142...
```

If it says **no cookies found**, you copied the wrong row — it must be the
`jobopportunity.php` document request, not a `.css`, `.js` or image row.

**Why the user-agent is copied as well:** F5 ties `TSPD_101` to the browser that was
issued it. Replaying the cookie with a different UA string is a mismatch F5 can spot,
so the script now uses yours instead of its hardcoded default.

> ⚠️ `meta/session.txt` is a **live login**. `.gitignore` already excludes it so it
> cannot reach GitHub, but never paste its contents into a chat, issue or log. It
> expires on its own — usually hours to a few days. When fetching starts failing
> again, repeat the steps above.

**What this does and does not fix.** PDF downloads are plain HTTP requests, so a valid
cookie makes those work every time. The listing page also runs an F5 JavaScript
challenge, so a pasted cookie usually gets you straight through but is not guaranteed
forever — if it still challenges, the window is open and you can solve it there.

---

## Interface: themes, language and fonts

### Light / dark
A three-state control in the header: **System · Light · Dark**. "System" follows
the phone or OS setting; picking Light or Dark stores an override in
`localStorage` under `bb-theme`, and picking System again removes it.

The stored choice is read by a small blocking script in `<head>` *before* any
CSS, so a dark-mode visitor never sees a white flash on load. Colours are
semantic custom properties (`--surface-0…3`, `--text-primary/secondary/muted`,
`--accent`, `--ok/--warn/--bad`) defined once per theme. **Never put a raw hex
value in a component rule** — it will be wrong in one of the two themes.

Every text/surface pair was checked with the WCAG relative-luminance formula
against the *lightest* surface that text can appear on, not just the page
background. All clear 4.5:1. `--border-control` exists separately because
interactive outlines need 3:1 and the decorative `--border` does not meet it.

### Bengali / English
Toggle in the header; stored as `bb-lang`. English is the default for a
first-time visitor; a saved Bengali preference is always honoured. All interface
copy lives in the `STR` table in `assets/js/core/language.js` — **add new strings
to both `en` and `bn`**, or the Bengali side silently falls back to English
(`tools/selftest.py` fails the build if the two dictionaries drift apart).

`Job ID` is the one deliberate exception: it stays English in both languages,
with ASCII digits, because it is a system identifier cross-referenced against
the official portal. Roll numbers are *not* treated that way — they follow the
interface language, because candidates read them off Bengali notices. Digits follow the language: Bengali
shows ০-৯, English shows 0-9. Search accepts ০-৯, ٠-٩, full-width and ASCII
regardless of the interface language.

Content pulled out of the PDFs (post names, centre names, notice titles) is
shown as published and is not translated.

### Fonts
Two families, self-hosted in `fonts/`, split by script with `unicode-range`
so Latin text never drags the Bengali file along.

**Noto Sans Bengali** — body text, weights 400 and 600:

| file | size |
|---|---|
| `noto-sans-bengali-bengali-400-normal.woff2` | 43 KB |
| `noto-sans-bengali-bengali-600-normal.woff2` | 47 KB |
| `noto-sans-bengali-latin-400-normal.woff2` | 10 KB |
| `noto-sans-bengali-latin-600-normal.woff2` | 10 KB |

**Noto Serif Bengali** — the display family (`--font-display`): `h1`, `h2`,
`.panel .big` and the logo mark. Weight 600 only:

| file | size |
|---|---|
| `noto-serif-bengali-bengali-600-normal.woff2` | 69 KB |
| `noto-serif-bengali-latin-600-normal.woff2` | 11 KB |

All six are SIL OFL; the licence travels with them in `fonts/OFL-Noto.txt`.
The two 400-weight sans files and the Latin serif are preloaded by the
injector in `app.template.html` — if you change the display family, update
that list too or `selftest.py` fails.

To change weights, download from `@fontsource/noto-sans-bengali` and update both the
`@font-face` blocks and the `SHELL` array in `sw.js` — **and bump `CACHE`**, or
returning visitors keep the old files.

### Roll lists
Long lists render as a wrapping grid of chips inside a height-capped,
independently scrolling box, built lazily when the list is opened. Do **not**
go back to joining rolls into a single comma-separated string inside a table
cell: table cells do not wrap unbroken content, so a 1,037-roll notice stretched
the cell until the entire page scrolled sideways. `tools/selftest.py` fails if
that pattern reappears.
