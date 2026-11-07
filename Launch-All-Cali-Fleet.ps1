# Master Autonomous Fleet Launcher for Cali Command
$Host.UI.RawUI.WindowTitle = "Cali Command - Master Autonomous Fleet Launcher"
Set-Location $PSScriptRoot

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  CALI COMMAND -- MASTER AUTONOMOUS FLEET LAUNCHER" -ForegroundColor Yellow
Write-Host "  Booting Central Mission Control & All Department Suites" -ForegroundColor White
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$modules = @(
    @{ Name = "Website Creator (Port 8789)"; Dir = "apps\cali-website-creator" },
    @{ Name = "Mission Control Central Hub (Port 8800)"; Dir = "apps\cali-central-hub" },
    @{ Name = "Video Studio (Port 8790)"; Dir = "apps\cali-video-studio" },
    @{ Name = "SEO Radar (Port 8791)"; Dir = "apps\cali-seo-radar" },
    @{ Name = "Social Hub (Port 8793)"; Dir = "apps\cali-social-hub" },
    @{ Name = "Community Sites (Port 8795)"; Dir = "apps\cali-community-sites" },
    @{ Name = "Health Checker (Port 8796)"; Dir = "apps\cali-health-checker" },
    @{ Name = "Security Radar (Port 8797)"; Dir = "apps\cali-security-radar" },
    @{ Name = "Docs & Reports (Port 8798)"; Dir = "apps\cali-docs-reports" },
    @{ Name = "Commercial & Finance Ledger (Port 8799)"; Dir = "apps\cali-finance-ledger" },
    @{ Name = "Dev & Code Release Workbench (Port 8792)"; Dir = "apps\cali-dev-workbench" },
    @{ Name = "Daily Briefing & Automations (Port 8794)"; Dir = "apps\cali-automations-runner" }
)

foreach ($m in $modules) {
    Write-Host "  Starting $($m.Name)..." -ForegroundColor Gray
    Start-Process -FilePath "python.exe" -ArgumentList "server.py" -WorkingDirectory (Join-Path $PSScriptRoot $m.Dir) -WindowStyle Hidden
}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  All Engines Running! Opening Mission Control at http://127.0.0.1:8800" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Green
Start-Sleep -Seconds 3
Start-Process "http://127.0.0.1:8800"
