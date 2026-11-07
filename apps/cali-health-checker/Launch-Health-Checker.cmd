@echo off
title Cali Website Health Checker & Review (Port 8796)
cd /d "%~dp0"
echo ========================================================
echo   CALI WEBSITE HEALTH CHECKER & REVIEW CENTRE
echo   Multi-Domain Uptime - SSL Expiry - Overwatch Queue
echo   URL: http://127.0.0.1:8796
echo ========================================================
echo.
start /b "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8796"
python server.py
pause

