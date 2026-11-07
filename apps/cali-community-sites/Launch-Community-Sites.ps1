# Launch Cali Community Sites & Shop
$Host.UI.RawUI.WindowTitle = "Cali Community Sites & Shop (Port 8795)"
Set-Location $PSScriptRoot
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  CALI COMMUNITY SITES & SHOP SUITE" -ForegroundColor Yellow
Write-Host "  URL: http://127.0.0.1:8795" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Start-Process -FilePath "cmd.exe" -ArgumentList '/c timeout /t 2 /nobreak >nul && start http://127.0.0.1:8795' -WindowStyle Hidden
python server.py

