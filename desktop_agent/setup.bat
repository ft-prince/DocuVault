@echo off
:: DocuVault Desktop Agent — First-time setup
echo.
echo ===================================
echo  DocuVault Desktop Agent Setup
echo ===================================
echo.

set AGENT_DIR=%~dp0

:: Install Python dependencies
echo Installing Python dependencies...
pip install -r "%AGENT_DIR%requirements.txt"
if errorlevel 1 (
    echo ERROR: pip install failed. Make sure Python and pip are installed.
    pause
    exit /b 1
)

:: Run interactive config wizard
echo.
echo Running configuration wizard...
python "%AGENT_DIR%agent.py" --setup

echo.
echo Setup complete! To start the agent:
echo   python agent.py
echo.
echo To add to Windows startup:
echo   install_startup.bat
echo.
pause
