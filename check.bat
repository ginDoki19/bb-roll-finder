@echo off
cd /d "%~dp0"
title BB Roll Finder - health check
echo Running offline checks (no network needed)...
echo.
python tools\test_fetch.py
echo.
python tools\selftest.py
echo.
echo Which notices are published but not downloaded:
python tools\fetch_notices.py --plan
echo.
pause
