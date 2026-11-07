@echo off
title Cali Documents, Reports & Knowledge Centre (Port 8798)
cd /d "%~dp0"
echo ========================================================
echo   CALI DOCUMENTS, REPORTS & KNOWLEDGE CENTRE
echo   OnlyOffice Workspace - Companies House - Policy Vault
echo   URL: http://127.0.0.1:8798
echo ========================================================
echo.
start /b "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8798"
python server.py
pause

