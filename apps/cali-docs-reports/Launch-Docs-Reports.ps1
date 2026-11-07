# Launch Cali Documents, Reports & Knowledge Centre
$Host.UI.RawUI.WindowTitle = "Cali Documents, Reports & Knowledge Centre (Port 8798)"
Set-Location $PSScriptRoot
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  CALI DOCUMENTS, REPORTS & KNOWLEDGE CENTRE" -ForegroundColor Yellow
Write-Host "  URL: http://127.0.0.1:8798" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Start-Process -FilePath "cmd.exe" -ArgumentList '/c timeout /t 2 /nobreak >nul && start http://127.0.0.1:8798' -WindowStyle Hidden
python server.py

