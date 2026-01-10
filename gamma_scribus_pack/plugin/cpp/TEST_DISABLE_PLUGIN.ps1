# Deaktiviert das Plugin temporär zum Testen (erfordert Admin-Rechte)

$ErrorActionPreference = "Stop"

Write-Host "=== Plugin temporär deaktivieren ===" -ForegroundColor Cyan
Write-Host ""

# Prüfe Admin-Rechte
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️  Admin-Rechte erforderlich!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Bitte PowerShell als Administrator starten." -ForegroundColor White
    exit 1
}

$pluginDll = "C:\Program Files\Scribus 1.7.1\plugins\gamma_dashboard.dll"
$disabledDll = "C:\Program Files\Scribus 1.7.1\plugins\gamma_dashboard.dll.disabled"

if (Test-Path $pluginDll) {
    Write-Host "Deaktiviere Plugin..." -ForegroundColor Cyan
    Write-Host "  Von: $pluginDll" -ForegroundColor White
    Write-Host "  Nach: $disabledDll" -ForegroundColor White
    Write-Host ""
    
    try {
        Rename-Item -Path $pluginDll -NewName "gamma_dashboard.dll.disabled" -Force -ErrorAction Stop
        Write-Host "✅ Plugin deaktiviert!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Nächste Schritte:" -ForegroundColor Cyan
        Write-Host "  1. Scribus starten" -ForegroundColor White
        Write-Host "  2. Prüfen ob Scribus ohne Plugin startet" -ForegroundColor White
        Write-Host ""
        Write-Host "Falls Scribus ohne Plugin startet:" -ForegroundColor Green
        Write-Host "  → Problem liegt beim Plugin" -ForegroundColor White
        Write-Host ""
        Write-Host "Falls Scribus auch ohne Plugin abstürzt:" -ForegroundColor Red
        Write-Host "  → Problem liegt woanders" -ForegroundColor White
        Write-Host ""
        Write-Host "Zum Reaktivieren:" -ForegroundColor Yellow
        Write-Host "  Rename-Item '$disabledDll' -NewName 'gamma_dashboard.dll' -Force" -ForegroundColor Cyan
        
    } catch {
        Write-Host "❌ Fehler: $_" -ForegroundColor Red
        exit 1
    }
} elseif (Test-Path $disabledDll) {
    Write-Host "Plugin ist bereits deaktiviert: $disabledDll" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Zum Reaktivieren:" -ForegroundColor Cyan
    Write-Host "  Rename-Item '$disabledDll' -NewName 'gamma_dashboard.dll' -Force" -ForegroundColor Cyan
} else {
    Write-Host "❌ Plugin nicht gefunden: $pluginDll" -ForegroundColor Red
    exit 1
}

