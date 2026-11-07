# Launch-Automations-Runner.ps1
$Host.UI.RawUI.WindowTitle = "Cali Daily Briefing & Automations Runner (Port 8794)"
Write-Host "==============================================================" -ForegroundColor Yellow
Write-Host "   CALI DAILY BRIEFING & AUTOMATIONS RUNNER - PORT 8794" -ForegroundColor White
Write-Host "==============================================================" -ForegroundColor Yellow
Set-Location -Path $PSScriptRoot
python server.py

