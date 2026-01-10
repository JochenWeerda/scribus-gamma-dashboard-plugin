# Installiert die neueste DLL nach Scribus 1.7.1(1)
# ERFORDERT: Admin-Rechte

$ErrorActionPreference = "Stop"

# Prüfe Admin-Rechte
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "=== Admin-Rechte erforderlich! ===" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Bitte PowerShell als Administrator starten und erneut ausführen" -ForegroundColor White
    exit 1
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceDll = Join-Path $scriptDir "build\Release\gamma_dashboard.dll"
$targetDll = "C:\Program Files\Scribus 1.7.1(1)\plugins\gamma_dashboard.dll"

if (-not (Test-Path $sourceDll)) {
    Write-Host "FEHLER: DLL nicht gefunden: $sourceDll" -ForegroundColor Red
    exit 1
}

$source = Get-Item $sourceDll
Write-Host "=== Installiere DLL ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quelle: $($source.FullName)" -ForegroundColor White
Write-Host "  Erstellt: $($source.LastWriteTime)" -ForegroundColor Gray
Write-Host "  Größe: $([math]::Round($source.Length/1KB, 2)) KB" -ForegroundColor Gray
Write-Host ""
Write-Host "Ziel: $targetDll" -ForegroundColor White

# Backup vorhandener DLL
if (Test-Path $targetDll) {
    $backup = "$targetDll.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Copy-Item $targetDll $backup -Force
    Write-Host "Backup erstellt: $backup" -ForegroundColor Yellow
}

# Kopiere DLL
try {
    Copy-Item $sourceDll $targetDll -Force
    $installed = Get-Item $targetDll
    Write-Host ""
    Write-Host "=== Installation erfolgreich! ===" -ForegroundColor Green
    Write-Host "Installiert: $targetDll" -ForegroundColor Cyan
    Write-Host "Datum: $($installed.LastWriteTime)" -ForegroundColor White
    Write-Host "Größe: $([math]::Round($installed.Length/1KB, 2)) KB" -ForegroundColor White
    Write-Host ""
    Write-Host "Nächste Schritte:" -ForegroundColor Yellow
    Write-Host "  1. Scribus komplett schließen" -ForegroundColor White
    Write-Host "  2. Scribus neu starten" -ForegroundColor White
    Write-Host "  3. Plugin sollte ohne Fehler laden!" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "FEHLER: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}


