@echo off
title Cali Dev ^& Code Release Workbench (Port 8792)
color 0B
echo ==============================================================
echo        CALI DEV ^& CODE RELEASE WORKBENCH - PORT 8792
echo ==============================================================
echo [INFO] Starting Dev Workbench server on http://127.0.0.1:8792 ...
cd /d "%~dp0"
python server.py
pause
