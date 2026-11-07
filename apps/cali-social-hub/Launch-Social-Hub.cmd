@echo off
title Cali Social Hub
cd /d "%~dp0"
echo ========================================================
echo   Starting Cali Social Media and Publishing Hub (Standalone)
echo   Agent Echo (Gen 2) + Video Studio Asset Bridge
echo ========================================================
echo Starting server on http://127.0.0.1:8793 ...
start /b "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8793"
python server.py
pause
