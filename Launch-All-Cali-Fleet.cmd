@echo off
title Cali Command - Master Fleet Launcher
cd /d "%~dp0"
echo ========================================================
echo   CALI COMMAND -- SOVEREIGN AUTONOMOUS FLEET LAUNCHER
echo   Booting Central Hub ^& All Department Suites
echo ========================================================
echo.
echo [1/12] Starting Website Creator Studio (Port 8789)...
start /b "" cmd /c "cd apps\cali-website-creator && python server.py"

echo [2/12] Starting Cali Mission Control Central Hub (Port 8800)...
start /b "" cmd /c "cd apps\cali-central-hub && python server.py"

echo [3/12] Starting Video and Media Studio (Port 8790)...
start /b "" cmd /c "cd apps\cali-video-studio && python server.py"

echo [4/12] Starting SEO and Search Radar (Port 8791)...
start /b "" cmd /c "cd apps\cali-seo-radar && python server.py"

echo [5/12] Starting Social Media Publishing Hub (Port 8793)...
start /b "" cmd /c "cd apps\cali-social-hub && python server.py"

echo [6/12] Starting Community Sites ^& Shop Manager (Port 8795)...
start /b "" cmd /c "cd apps\cali-community-sites && python server.py"

echo [7/12] Starting System Health ^& Review Radar (Port 8796)...
start /b "" cmd /c "cd apps\cali-health-checker && python server.py"

echo [8/12] Starting Security ^& Threat Radar (Port 8797)...
start /b "" cmd /c "cd apps\cali-security-radar && python server.py"

echo [9/12] Starting Docs ^& Reports Knowledge Vault (Port 8798)...
start /b "" cmd /c "cd apps\cali-docs-reports && python server.py"

echo [10/12] Starting Commercial ^& Finance Ledger (Port 8799)...
start /b "" cmd /c "cd apps\cali-finance-ledger && python server.py"

echo [11/12] Starting Dev ^& Code Release Workbench (Port 8792)...
start /b "" cmd /c "cd apps\cali-dev-workbench && python server.py"

echo [12/12] Starting Automations ^& Task Runner (Port 8794)...
start /b "" cmd /c "cd apps\cali-automations-runner && python server.py"

echo.
echo ========================================================
echo   All 12 Cali Department Engines Booted!
echo   Launching Central Mission Control in your browser...
echo ========================================================
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8800"
echo.
echo Keep this window open or minimize it.
pause >nul
