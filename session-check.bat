@echo off
setlocal
cd /d "%~dp0"
echo.
echo  Checking meta\session.txt ...
echo.
python tools\fetch_notices.py --session-test
echo.
pause
