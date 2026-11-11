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
