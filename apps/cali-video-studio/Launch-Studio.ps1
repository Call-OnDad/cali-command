# PowerShell Launcher for Cali Video Studio
Set-Location -Path $PSScriptRoot

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Starting Cali Video Studio (Standalone Suite)" -ForegroundColor Green
Write-Host "  Local Piper TTS + Fast CPU / Colab GPU Engine" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

Start-Process "http://127.0.0.1:8790"
python server.py

