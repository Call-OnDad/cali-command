@echo off
title Cali Mission Control - Central Command Hub (Port 8800)
cd /d "%~dp0"
echo ========================================================
echo   CALI MISSION CONTROL - CENTRAL COMMAND HUB
echo   Executive Overview and Management Portal
echo   URL: http://127.0.0.1:8800
echo ========================================================
echo.
echo Launching Executive Dashboard in browser...
start /b "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8800"
python server.py
pause
