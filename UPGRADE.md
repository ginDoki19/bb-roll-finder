# Applying a new `bb-notice.zip`

Copy-paste one of the blocks below. Both do the same thing: extract the zip to
a scratch folder, copy it over `H:\bb test\bb-notice`, then verify.

Adjust the two paths at the top if your download folder or project root ever
changes. Everything else can stay as-is.

---

## PowerShell (recommended)

```powershell
$Zip  = "C:\Users\User\Downloads\Compressed\bb-notice.zip"
$Proj = "H:\bb test\bb-notice"

# 1. extract to a scratch folder (wiped and recreated each time)
Remove-Item "$env:TEMP\bbupd" -Recurse -Force -ErrorAction SilentlyContinue
Expand-Archive -Path $Zip -DestinationPath "$env:TEMP\bbupd" -Force

# 2. copy over the project
robocopy "$env:TEMP\bbupd\bb-notice" $Proj /E /XF listing-cache.json
if ($LASTEXITCODE -ge 8) { Write-Host "robocopy FAILED ($LASTEXITCODE)" -ForegroundColor Red }
else                     { Write-Host "copy OK ($LASTEXITCODE)"        -ForegroundColor Green }

# 3. verify
Set-Location $Proj
.\check.bat
```

## Command Prompt (`cmd.exe`)

Needs Windows 10 1803 or newer for `tar`.

```bat
set ZIP=C:\Users\User\Downloads\Compressed\bb-notice.zip
set PROJ=H:\bb test\bb-notice

rmdir /s /q "%TEMP%\bbupd" 2>nul
mkdir "%TEMP%\bbupd"
tar -xf "%ZIP%" -C "%TEMP%\bbupd"

robocopy "%TEMP%\bbupd\bb-notice" "%PROJ%" /E /XF listing-cache.json
if %ERRORLEVEL% GEQ 8 (echo robocopy FAILED %ERRORLEVEL%) else (echo copy OK %ERRORLEVEL%)

cd /d "%PROJ%"
check.bat
```

---

## Why the flags are what they are

| Flag | Reason |
|---|---|
| `/E` | copy subdirectories, including empty ones |
| `/XF listing-cache.json` | your local fetch cache; the zip's copy is older |
| **no `/PURGE`** | `/PURGE` (and `/MIR`, which implies it) deletes anything in the destination that is not in the source — that would wipe `meta\session.txt`, `logs\` and `.git\`. **Never add it.** |

Because there is no `/PURGE`, local-only files survive the upgrade untouched:

- `meta\session.txt` — your live browser session, never shipped in the zip
- `logs\` — gitignored
- `.git\` — your repository

## Reading the exit code

robocopy does **not** use 0 for success. It is a bitmask:

| Code | Meaning |
|---|---|
| 0 | nothing needed copying |
| 1 | files copied successfully |
| 2 | extra files/dirs in the destination (expected — those are your local-only files) |
| 3 | 1 + 2, the usual result |
| **0–7** | **success** |
| 8+ | real failure |

So `copy OK 3` is a good outcome, not an error.

## After upgrading

1. `check.bat` — runs `test_fetch.py`, `selftest.py` and `fetch_notices.py --plan`.
2. `run.bat` — only when you want to fetch new notices, rebuild and push.
3. **Hard-refresh the live site once** (Ctrl+F5). The service worker cache name
   is bumped on releases that change the shell, so the first load re-caches it;
   without a hard refresh you can briefly see stale styling.

## If `check.bat` reports T4 failing

> `data/notices.json is not what the parser produces`

The committed data is out of date relative to the PDFs in `notices\`. Run
`run.bat` (or `python3 parser/build_data.py --html career.html --pdfs notices
--out data/notices.json`) to refresh it. The message names the notices that
differ.
