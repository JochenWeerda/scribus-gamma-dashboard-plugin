# Installiert Gamma Dashboard Plugin ins System-Verzeichnis (erfordert Admin-Rechte)

$ErrorActionPreference = "Stop"

Write-Host "=== Gamma Dashboard Plugin - System-Installation ===" -ForegroundColor Cyan
Write-Host ""

# Prüfe Admin-Rechte
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️  Admin-Rechte erforderlich!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Bitte PowerShell als Administrator starten und dieses Script erneut ausführen." -ForegroundColor White
    Write-Host ""
    Write-Host "Alternativ: Plugin manuell kopieren:" -ForegroundColor Yellow
    Write-Host "  Quelle: $PSScriptRoot\build\Release\gamma_dashboard.dll" -ForegroundColor Cyan
    Write-Host "  Ziel:   C:\Program Files\Scribus 1.7.1\plugins\gamma_dashboard.dll" -ForegroundColor Cyan
    exit 1
}

$sourceDll = "$PSScriptRoot\build\Release\gamma_dashboard.dll"
$targetDir = "C:\Program Files\Scribus 1.7.1\plugins"
$targetDll = Join-Path $targetDir "gamma_dashboard.dll"

# Prüfe ob Quelle existiert
if (-not (Test-Path $sourceDll)) {
    Write-Host "❌ Quelle nicht gefunden: $sourceDll" -ForegroundColor Red
    exit 1
}

# Prüfe ob Ziel-Verzeichnis existiert
if (-not (Test-Path $targetDir)) {
    Write-Host "❌ Ziel-Verzeichnis nicht gefunden: $targetDir" -ForegroundColor Red
    Write-Host "   Bitte Scribus-Installation prüfen!" -ForegroundColor Yellow
    exit 1
}

Write-Host "Kopiere Plugin..." -ForegroundColor Cyan
Write-Host "  Von: $sourceDll" -ForegroundColor White
Write-Host "  Nach: $targetDll" -ForegroundColor White
Write-Host ""

try {
    Copy-Item -Path $sourceDll -Destination $targetDll -Force
    Write-Host "✅ Plugin erfolgreich installiert!" -ForegroundColor Green
    Write-Host ""
    
    $dll = Get-Item $targetDll
    Write-Host "Details:" -ForegroundColor Cyan
    Write-Host "  Datei: $($dll.Name)" -ForegroundColor White
    Write-Host "  Größe: $([math]::Round($dll.Length/1KB, 2)) KB" -ForegroundColor White
    Write-Host "  Erstellt: $($dll.LastWriteTime)" -ForegroundColor White
    Write-Host ""
    Write-Host "Scribus sollte das Plugin beim nächsten Start laden!" -ForegroundColor Green
    Write-Host "Prüfe: Extras > Einstellungen > Plug-Ins" -ForegroundColor Yellow
    
} catch {
    Write-Host "❌ Fehler beim Kopieren: $_" -ForegroundColor Red
    exit 1
}

