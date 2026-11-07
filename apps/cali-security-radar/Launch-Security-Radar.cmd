@echo off
title Cali Security Findings & Threat Radar (Port 8797)
cd /d "%~dp0"
echo ========================================================
echo   CALI SECURITY FINDINGS & THREAT RADAR
echo   Perimeter Recon - Cloudflare WAF - CrowdSec Bans
echo   URL: http://127.0.0.1:8797
echo ========================================================
echo.
start /b "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8797"
python server.py
pause

