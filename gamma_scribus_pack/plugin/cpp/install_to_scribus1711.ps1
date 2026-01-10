# Installiert Gamma Dashboard Plugin nach Scribus 1.7.1(1)
# ERFORDERT: Admin-Rechte

$ErrorActionPreference = "Stop"

# Prüfe Admin-Rechte
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "=== Admin-Rechte erforderlich! ===" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Bitte PowerShell als Administrator starten:" -ForegroundColor White
    Write-Host "  1. Windows-Taste + X" -ForegroundColor Cyan
    Write-Host "  2. 'Windows PowerShell (Administrator)' wählen" -ForegroundColor Cyan
    Write-Host "  3. Dieses Script erneut ausführen" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "ODER:" -ForegroundColor Yellow
    Write-Host "  Start-Process powershell -Verb RunAs -ArgumentList '-File', '$PSCommandPath'" -ForegroundColor Cyan
    exit 1
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceDll = Join-Path $ScriptDir "build\Release\gamma_dashboard.dll"
$targetDir = "C:\Program Files\Scribus 1.7.1(1)\plugins"
$targetDll = Join-Path $targetDir "gamma_dashboard.dll"

Write-Host "=== Installation nach Scribus 1.7.1(1) ===" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $sourceDll)) {
    Write-Host "FEHLER: DLL nicht gefunden: $sourceDll" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $targetDir)) {
    Write-Host "FEHLER: Ziel-Verzeichnis nicht gefunden: $targetDir" -ForegroundColor Red
    exit 1
}

# Backup vorhandener DLL
if (Test-Path $targetDll) {
    $backup = "$targetDll.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Copy-Item $targetDll $backup -Force
    Write-Host "Backup erstellt: $backup" -ForegroundColor Yellow
}

# Kopiere DLL
try {
    Copy-Item $sourceDll $targetDll -Force
    Write-Host ""
    Write-Host "=== Installation erfolgreich! ===" -ForegroundColor Green
    Write-Host "Ziel: $targetDll" -ForegroundColor Cyan
    $dll = Get-Item $targetDll
    Write-Host "Datum: $($dll.LastWriteTime)" -ForegroundColor White
    Write-Host "Größe: $([math]::Round($dll.Length/1KB, 2)) KB" -ForegroundColor White
    Write-Host ""
    Write-Host "Nächste Schritte:" -ForegroundColor Yellow
    Write-Host "  1. Scribus komplett schließen" -ForegroundColor White
    Write-Host "  2. Scribus neu starten" -ForegroundColor White
    Write-Host "  3. Plugin testen: Extras > Tools > Settings..." -ForegroundColor White
} catch {
    Write-Host ""
    Write-Host "FEHLER: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}


