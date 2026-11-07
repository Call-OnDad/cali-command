@echo off
title Cali Community Sites & Shop (Port 8795)
cd /d "%~dp0"
echo ========================================================
echo   CALI COMMUNITY SITES & SHOP SUITE
echo   Call-On Dad - Call-On Mom - Call-On Shop
echo   URL: http://127.0.0.1:8795
echo ========================================================
echo.
start /b "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8795"
python server.py
pause

