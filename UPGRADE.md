# Applying a new `bb-notice.zip`

Copy-paste one of the blocks below. Both do the same thing: extract the zip to
a scratch folder, copy it over `H:\bb test\bb-notice`, then verify.

Adjust the two paths at the top if your download folder or project root ever
changes. Everything else can stay as-is.

**Pasting into an interactive PowerShell prompt:** never split an `if {...}`
and its `else {...}` across two lines. The console executes each line the
moment it is complete, so the `if` runs on its own and the next line fails
with `The term 'else' is not recognized`. Keep `} else {` on one line, or
avoid `else` entirely as the block below now does.

---

## PowerShell (recommended)

```powershell
$Zip  = "C:\Users\User\Downloads\Compressed\bb-notice.zip"
$Proj = "H:\bb test\bb-notice"

# 1. extract to a scratch folder (wiped and recreated each time)
Remove-Item "$env:TEMP\bbupd" -Recurse -Force -ErrorAction SilentlyContinue
Expand-Archive -Path $Zip -DestinationPath "$env:TEMP\bbupd" -Force

# 2. copy over the project
robocopy "$env:TEMP\bbupd\bb-notice" $Proj /E /XF listing-cache.json career.html
Write-Host "robocopy exit $LASTEXITCODE  -  0 to 7 means success, 8+ means failure"

# 2b. remove fonts that this release dropped (robocopy never deletes)
Remove-Item "$Proj\fonts\hind-siliguri-*.woff2" -Force -ErrorAction SilentlyContinue

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

robocopy "%TEMP%\bbupd\bb-notice" "%PROJ%" /E /XF listing-cache.json career.html
if %ERRORLEVEL% GEQ 8 (echo robocopy FAILED %ERRORLEVEL%) else (echo copy OK %ERRORLEVEL%)

del /q "%PROJ%\fonts\hind-siliguri-*.woff2" 2>nul

cd /d "%PROJ%"
check.bat
```

---

## Why the flags are what they are

| Flag | Reason |
|---|---|
| `/E` | copy subdirectories, including empty ones |
| `/XF listing-cache.json` | your local fetch cache; the zip's copy is older |
| `/XF ... career.html` | the saved listing page. `fetch_notices.py` refreshes it from the portal on every run, so **your copy is always at least as fresh as the zip's**. Letting the zip overwrite it rewinds it to whenever the archive was built. |
| **no `/PURGE`** | `/PURGE` (and `/MIR`, which implies it) deletes anything in the destination that is not in the source — that would wipe `meta\session.txt`, `logs\` and `.git\`. **Never add it.** |

## Why the extra delete line

`robocopy` copies and overwrites, but it **never removes** a file that the new
release dropped (that is what `/PURGE` would do, and `/PURGE` would also wipe
`meta\session.txt`, `logs\` and `.git\` — see the warning above). So when a
release retires a file, it has to be deleted by name.

The Material 3 release replaced Hind Siliguri with Noto Sans/Serif Bengali.
Without that one line the four old `hind-siliguri-*.woff2` files (175 KB) stay
in `fonts\`, get committed, and get deployed forever — unused but downloaded
by nothing, just dead weight in the repo.

## Reading the robocopy exit code

Robocopy does **not** use `0` for success. It returns a bitmask:

| Bit | Value | Meaning |
|---|---|---|
| 0 | `1` | files were copied |
| 1 | `2` | extra files/dirs exist in the destination (normal — `logs\`, `.git\`) |
| 2 | `4` | mismatched files/dirs (worth a look) |
| 3 | `8` | **some copies failed** |
| 4 | `16` | **fatal error, nothing copied** |

So `0`–`7` all mean success and **`3` is the usual result** for this project.
Test with `-ge 8` / `GEQ 8`. Never test `-ne 0` — it reports false failures.

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
