@echo off
REM Double-click or run from CMD to start Shashwat Capstone Retail (Windows)
cd /d "%~dp0"

echo ============================================
echo  Shashwat Capstone Retail - Quick Start
echo ============================================
echo.
echo 1. Open PowerShell HERE (Shift+Right-click in folder)
echo 2. Run:  .\start-api.ps1
echo 3. Open NEW PowerShell, run:  .\start-ui.ps1
echo.
echo Or in VS Code: Run and Debug -^> "API + Streamlit" -^> F5
echo.
echo On Linux VM:
echo   chmod +x deploy/setup-vm.sh ^&^& ./deploy/setup-vm.sh
echo   ./start-api.sh
echo   ./start-ui.sh
echo ============================================
pause
