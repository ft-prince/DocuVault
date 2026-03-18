@echo off
:: ============================================================
:: DocuVault Desktop Agent — Build standalone .exe
:: Run this ONCE on the server to produce DocuVaultAgent.exe
:: ============================================================
setlocal
cd /d "%~dp0"

echo.
echo  DocuVault Agent Builder
echo  ========================
echo.

:: ── Check Python ────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found in PATH.
    echo  Download from https://www.python.org/downloads/
    pause & exit /b 1
)

:: ── Install build deps ───────────────────────────────────────
echo  Installing dependencies...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
python -m pip install --quiet pyinstaller

:: ── Build ────────────────────────────────────────────────────
echo.
echo  Building DocuVaultAgent.exe ...
echo  (This takes 1-2 minutes on first run)
echo.

python -m PyInstaller ^
    --onefile ^
    --noconsole ^
    --name DocuVaultAgent ^
    --add-data "setup_wizard.py;." ^
    --hidden-import pystray ^
    --hidden-import PIL ^
    --hidden-import watchdog ^
    --hidden-import requests ^
    --hidden-import dateutil ^
    agent.py

if errorlevel 1 (
    echo.
    echo  BUILD FAILED — check errors above.
    pause & exit /b 1
)

:: ── Copy result ──────────────────────────────────────────────
if exist dist\DocuVaultAgent.exe (
    copy /y dist\DocuVaultAgent.exe DocuVaultAgent.exe >nul
    echo.
    echo  ============================================
    echo   SUCCESS!  DocuVaultAgent.exe is ready.
    echo  ============================================
    echo.
    echo  Share this file with your users.
    echo  They just double-click it — no Python needed.
    echo.
) else (
    echo  Build output not found.
)

pause
