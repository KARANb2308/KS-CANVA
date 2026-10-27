@echo off
title Material Selection helper
cd /d "%~dp0"

rem Opened straight from inside the ZIP? Windows then copies only this file, without server.ps1.
if not exist "%~dp0server.ps1" (
  echo.
  echo   [!] server.ps1 was not found next to start.bat.
  echo.
  echo       Please EXTRACT the ZIP file first:
  echo       right-click the ZIP  ^>  Extract All...  ^>  Extract
  echo       then open the new folder and double-click start.bat there.
  echo.
  pause
  exit /b 1
)

"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0server.ps1"

rem 2 = the helper was already running; the page has been reopened, nothing else to do.
if "%errorlevel%"=="2" exit /b 0

echo.
echo The helper has stopped. Press any key to close this window.
pause >nul
