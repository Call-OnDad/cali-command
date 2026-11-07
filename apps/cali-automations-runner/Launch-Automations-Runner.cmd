@echo off
title Cali Daily Briefing ^& Automations Runner (Port 8794)
color 0E
echo ==============================================================
echo    CALI DAILY BRIEFING ^& AUTOMATIONS RUNNER - PORT 8794
echo ==============================================================
echo [INFO] Starting Automations Runner server on http://127.0.0.1:8794 ...
cd /d "%~dp0"
python server.py
pause

