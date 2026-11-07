@echo off
title Cali Video Studio
cd /d "%~dp0"
echo ========================================================
echo   Starting Cali Video and Media Studio (Standalone)
echo   Local Piper TTS + CPU/Colab GPU Engine
echo ========================================================
echo Starting server on http://127.0.0.1:8790 ...
start /b "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8790"
python server.py
pause
