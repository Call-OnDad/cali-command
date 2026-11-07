@echo off
title Cali SEO and Search Radar
cd /d "%~dp0"
echo ========================================================
echo   Starting Cali SEO and Search Radar Suite (Standalone)
echo   Multi-Domain Tracker + CT120 SerpBear Integration
echo ========================================================
echo Starting server on http://127.0.0.1:8791 ...
start /b "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8791"
python server.py
pause
