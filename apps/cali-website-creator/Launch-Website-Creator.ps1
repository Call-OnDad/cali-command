# Launch Cali Website Creator & Page Builder
$Host.UI.RawUI.WindowTitle = "Cali Website Creator (Port 8789)"
Set-Location -Path $PSScriptRoot
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  🌐 Launching Cali Website Creator (Port 8789)" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
python server.py
