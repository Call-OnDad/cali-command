# Launch Cali Security Findings & Threat Radar
$Host.UI.RawUI.WindowTitle = "Cali Security Findings & Threat Radar (Port 8797)"
Set-Location $PSScriptRoot
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  CALI SECURITY FINDINGS & THREAT RADAR" -ForegroundColor Yellow
Write-Host "  URL: http://127.0.0.1:8797" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Start-Process -FilePath "cmd.exe" -ArgumentList '/c timeout /t 2 /nobreak >nul && start http://127.0.0.1:8797' -WindowStyle Hidden
python server.py

