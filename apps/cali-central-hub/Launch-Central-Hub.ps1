# Launch Cali Mission Control & Central Command Hub
$Host.UI.RawUI.WindowTitle = "Cali Mission Control - Central Command Hub (Port 8800)"
Set-Location $PSScriptRoot
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  CALI MISSION CONTROL - CENTRAL COMMAND HUB" -ForegroundColor Yellow
Write-Host "  Executive Overview and Management Portal" -ForegroundColor White
Write-Host "  URL: http://127.0.0.1:8800" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Launching Executive Dashboard in browser..." -ForegroundColor Gray
Start-Process -FilePath "cmd.exe" -ArgumentList '/c timeout /t 2 /nobreak >nul && start http://127.0.0.1:8800' -WindowStyle Hidden
python server.py
