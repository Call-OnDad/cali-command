# Launch Cali Website Health Checker & Review Centre
$Host.UI.RawUI.WindowTitle = "Cali Website Health Checker & Review (Port 8796)"
Set-Location $PSScriptRoot
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  CALI WEBSITE HEALTH CHECKER & REVIEW CENTRE" -ForegroundColor Yellow
Write-Host "  URL: http://127.0.0.1:8796" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Start-Process -FilePath "cmd.exe" -ArgumentList '/c timeout /t 2 /nobreak >nul && start http://127.0.0.1:8796' -WindowStyle Hidden
python server.py

