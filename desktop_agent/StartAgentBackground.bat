@echo off
:: ============================================================
:: DocuVault Desktop Agent — Silent Background Launcher
:: ============================================================
:: Runs the agent headlessly (no window, no tray icon).
:: Suitable for: Windows Startup folder, Task Scheduler,
::               server deployments, CI environments.
::
:: The agent keeps running until the process is killed.
:: Logs are written to desktop_agent.log in this folder.
:: ============================================================
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "AGENT_PY=%SCRIPT_DIR%\agent.py"
set "AGENT_EXE=%SCRIPT_DIR%\DocuVaultAgent.exe"
set "VENV_PYTHON=%SCRIPT_DIR%\..\env\Scripts\python.exe"

:: ── 1. Virtualenv Python ───────────────────────────────────────────────
if exist "%VENV_PYTHON%" (
    start "" /B "%VENV_PYTHON%" "%AGENT_PY%" --no-tray
    goto :done
)

:: ── 2. System Python ──────────────────────────────────────────────────
python --version >nul 2>&1
if not errorlevel 1 (
    python -c "import watchdog, requests" >nul 2>&1
    if not errorlevel 1 (
        start "" /B python "%AGENT_PY%" --no-tray
        goto :done
    )
)

:: ── 3. Standalone .exe ────────────────────────────────────────────────
if exist "%AGENT_EXE%" (
    start "" /B "%AGENT_EXE%" --no-tray
    goto :done
)

echo ERROR: DocuVault Agent could not be started. See desktop_agent.log.
exit /b 1

:done
endlocal
