# PowerShell Launcher for Cali SEO & Search Radar Suite
Set-Location -Path $PSScriptRoot

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Starting Cali SEO and Search Radar Suite (Standalone) " -ForegroundColor Green
Write-Host "  Multi-Domain Fleet + SerpBear CT120 Integration       " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

Start-Sleep -Seconds 1
Start-Process "http://127.0.0.1:8791"
python server.py
