@echo off
:: ============================================================
:: DocuVault Desktop Agent — Build standalone .exe
:: Run this ONCE on the server to produce DocuVaultAgent.exe
::
:: Usage:
::   build.bat           → Silent GUI exe (normal distribution)
::   build.bat --debug   → Console exe (shows errors on crash)
:: ============================================================
setlocal
cd /d "%~dp0"

set "DEBUG_BUILD=0"
if /I "%~1"=="--debug" set "DEBUG_BUILD=1"

echo.
echo  DocuVault Agent Builder
echo  ========================
echo.

:: ── Prefer virtualenv Python if available ────────────────────────────
set "VENV_PYTHON=..\env\Scripts\python.exe"
if exist "%VENV_PYTHON%" (
    set "PYTHON=%VENV_PYTHON%"
    echo  Using virtualenv Python: %VENV_PYTHON%
) else (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo  ERROR: Python not found in PATH.
        echo  Download from https://www.python.org/downloads/
        pause & exit /b 1
    )
    set "PYTHON=python"
    echo  Using system Python
)
echo.

:: ── Install build deps ───────────────────────────────────────────────
echo  Installing dependencies...
%PYTHON% -m pip install --quiet --upgrade pip
%PYTHON% -m pip install --quiet -r requirements.txt
%PYTHON% -m pip install --quiet pyinstaller
echo  Done.
echo.

:: ── Build ────────────────────────────────────────────────────────────
echo  Building DocuVaultAgent.exe ...
if "%DEBUG_BUILD%"=="1" (
    echo  [DEBUG MODE - console window will be visible]
    echo.
    %PYTHON% -m PyInstaller ^
        --onefile ^
        --console ^
        --name DocuVaultAgent ^
        --add-data "setup_wizard.py;." ^
        --hidden-import setup_wizard ^
        --hidden-import tkinter ^
        --hidden-import tkinter.filedialog ^
        --hidden-import pystray ^
        --hidden-import PIL ^
        --hidden-import PIL.Image ^
        --hidden-import PIL.ImageDraw ^
        --hidden-import watchdog ^
        --hidden-import watchdog.observers ^
        --hidden-import watchdog.observers.winapi ^
        --hidden-import watchdog.events ^
        --hidden-import requests ^
        --hidden-import dateutil ^
        --hidden-import winreg ^
        agent.py
) else (
    echo  (This takes 1-2 minutes on first run)
    echo.
    %PYTHON% -m PyInstaller ^
        --onefile ^
        --noconsole ^
        --name DocuVaultAgent ^
        --add-data "setup_wizard.py;." ^
        --hidden-import setup_wizard ^
        --hidden-import tkinter ^
        --hidden-import tkinter.filedialog ^
        --hidden-import pystray ^
        --hidden-import PIL ^
        --hidden-import PIL.Image ^
        --hidden-import PIL.ImageDraw ^
        --hidden-import watchdog ^
        --hidden-import watchdog.observers ^
        --hidden-import watchdog.observers.winapi ^
        --hidden-import watchdog.events ^
        --hidden-import requests ^
        --hidden-import dateutil ^
        --hidden-import winreg ^
        agent.py
)

if errorlevel 1 (
    echo.
    echo  BUILD FAILED — check errors above.
    pause & exit /b 1
)

:: ── Copy result ──────────────────────────────────────────────────────
if exist dist\DocuVaultAgent.exe (
    copy /y dist\DocuVaultAgent.exe DocuVaultAgent.exe >nul
    echo.
    echo  ============================================
    echo   SUCCESS!  DocuVaultAgent.exe is ready.
    echo  ============================================
    echo.
    if "%DEBUG_BUILD%"=="1" (
        echo  [DEBUG build — shows a console window]
        echo  Rebuild without --debug for silent distribution.
    ) else (
        echo  Share this file with your users.
        echo  They just double-click it — no Python needed.
    )
    echo.
    echo  Tip: if the exe still misbehaves, build with:
    echo    build.bat --debug
    echo  to see error messages in the console window.
    echo.
) else (
    echo  Build output not found.
)

pause
