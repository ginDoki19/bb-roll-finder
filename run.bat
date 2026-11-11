@echo off
setlocal
cd /d "%~dp0"
title BB Roll Finder - update

echo ============================================
echo   BB Roll Finder - fetching new notices
echo ============================================
echo.
echo A browser window will open. If a CAPTCHA appears,
echo type the code and submit it. Do not close the window.
echo.

python tools\fetch_notices.py --build --push --log logs\fetch.log
set RC=%errorlevel%

echo.
if %RC%==0 (
  echo   DONE - notices updated and pushed.
  echo   Your site rebuilds automatically in about a minute.
) else (
  echo   FAILED ^(exit %RC%^).
  echo   If it said CAPTCHA NEEDED, just run this again and solve it.
  echo   Full log: logs\fetch.log
)
echo.
pause
