# Launch-Dev-Workbench.ps1
$Host.UI.RawUI.WindowTitle = "Cali Dev & Code Release Workbench (Port 8792)"
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "       CALI DEV & CODE RELEASE WORKBENCH - PORT 8792" -ForegroundColor White
Write-Host "==============================================================" -ForegroundColor Cyan
Set-Location -Path $PSScriptRoot
python server.py

