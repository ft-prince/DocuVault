@echo off
:: ============================================================
:: DocuVault Desktop Agent — Universal Launcher
:: ============================================================
:: Double-click  → GUI status popup (Start / Stop controls)
:: Arguments:
::   --no-tray   Run headless in background (no window)
::   --setup     Force the setup wizard
:: ============================================================
setlocal

:: Resolve paths relative to this .bat file's location
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "AGENT_PY=%SCRIPT_DIR%\agent.py"
set "AGENT_EXE=%SCRIPT_DIR%\DocuVaultAgent.exe"
set "VENV_PYTHON=%SCRIPT_DIR%\..\env\Scripts\python.exe"

:: ── 1. Virtualenv Python (preferred — same environment as development) ─
if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" "%AGENT_PY%" %*
    goto :done
)

:: ── 2. System Python with packages installed ───────────────────────────
python --version >nul 2>&1
if not errorlevel 1 (
    python -c "import watchdog, requests" >nul 2>&1
    if not errorlevel 1 (
        python "%AGENT_PY%" %*
        goto :done
    )
    :: Packages missing — install from requirements.txt then retry
    echo [DocuVault] Installing missing packages...
    python -m pip install -r "%SCRIPT_DIR%\requirements.txt" --quiet
    if not errorlevel 1 (
        python "%AGENT_PY%" %*
        goto :done
    )
)

:: ── 3. Standalone .exe fallback ────────────────────────────────────────
if exist "%AGENT_EXE%" (
    "%AGENT_EXE%" %*
    goto :done
)

:: ── Nothing worked ─────────────────────────────────────────────────────
echo.
echo  ERROR: Cannot launch DocuVault Agent.
echo.
echo  Tried (in order):
echo    1. Virtualenv:  %VENV_PYTHON%  (not found)
echo    2. System Python: not found or missing packages
echo    3. Standalone exe: %AGENT_EXE%  (not found)
echo.
echo  Fix options:
echo    A) Run build.bat to rebuild DocuVaultAgent.exe
echo    B) Install Python and run:  pip install -r requirements.txt
echo.
pause
exit /b 1

:done
endlocal
