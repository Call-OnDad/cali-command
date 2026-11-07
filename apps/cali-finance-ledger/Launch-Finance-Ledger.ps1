$Host.UI.RawUI.WindowTitle = "Cali Commercial & Finance Ledger (Port 8799)"
Set-Location -Path $PSScriptRoot
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Starting Cali Commercial & Finance Ledger on port 8799..." -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Cyan
python server.py

