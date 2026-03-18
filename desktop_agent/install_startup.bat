@echo off
:: DocuVault Desktop Agent — Add to Windows startup
:: Run this once as Administrator to register the agent as a startup task.

set AGENT_DIR=%~dp0
set PYTHON=python

echo.
echo Installing DocuVault Desktop Agent to Windows startup...

:: Create a VBScript launcher so the window stays hidden
set VBS=%AGENT_DIR%start_agent_hidden.vbs
echo Set WshShell = CreateObject("WScript.Shell") > "%VBS%"
echo WshShell.Run "cmd /c cd /d ""%AGENT_DIR%"" && %PYTHON% agent.py", 0, False >> "%VBS%"

:: Register in HKCU Run (no admin required)
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" ^
    /v "DocuVaultAgent" ^
    /t REG_SZ ^
    /d "wscript.exe \"%VBS%\"" ^
    /f

echo.
echo Done! The agent will start automatically on next login.
echo To run it now:  python agent.py
echo.
pause
