# PowerShell Launcher for Cali Social Hub
Set-Location -Path $PSScriptRoot

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Starting Cali Social Media and Publishing Hub         " -ForegroundColor Green
Write-Host "  Powered by Next-Gen Agent Echo (Generation 2)        " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

Start-Sleep -Seconds 1
Start-Process "http://127.0.0.1:8793"
python server.py
