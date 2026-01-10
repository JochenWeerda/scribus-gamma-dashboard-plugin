# Aktualisiert das Plugin mit der neuesten Version (erfordert Admin-Rechte)

$ErrorActionPreference = "Stop"

Write-Host "=== Gamma Dashboard Plugin - Update ===" -ForegroundColor Cyan
Write-Host ""

# Prüfe Admin-Rechte
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️  Admin-Rechte erforderlich!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Bitte PowerShell als Administrator starten und dieses Script erneut ausführen." -ForegroundColor White
    exit 1
}

$sourceDll = "$PSScriptRoot\build\Release\gamma_dashboard.dll"
$targetDll = "C:\Program Files\Scribus 1.7.1\plugins\gamma_dashboard.dll"

# Prüfe ob Quelle existiert
if (-not (Test-Path $sourceDll)) {
    Write-Host "❌ Quell-DLL nicht gefunden: $sourceDll" -ForegroundColor Red
    exit 1
}

# Prüfe ob Ziel-Verzeichnis existiert
$targetDir = Split-Path $targetDll -Parent
if (-not (Test-Path $targetDir)) {
    Write-Host "❌ Ziel-Verzeichnis nicht gefunden: $targetDir" -ForegroundColor Red
    exit 1
}

Write-Host "Update Plugin..." -ForegroundColor Cyan
Write-Host "  Von: $sourceDll" -ForegroundColor White

if (Test-Path $targetDll) {
    $old = Get-Item $targetDll
    Write-Host "  Alte Version: $([math]::Round($old.Length/1KB, 2)) KB - $($old.LastWriteTime)" -ForegroundColor Yellow
}

$new = Get-Item $sourceDll
Write-Host "  Neue Version: $([math]::Round($new.Length/1KB, 2)) KB - $($new.LastWriteTime)" -ForegroundColor Cyan
Write-Host "  Nach: $targetDll" -ForegroundColor White
Write-Host ""

try {
    Copy-Item -Path $sourceDll -Destination $targetDll -Force
    Write-Host "✅ Plugin erfolgreich aktualisiert!" -ForegroundColor Green
    Write-Host ""
    
    $dll = Get-Item $targetDll
    Write-Host "Details:" -ForegroundColor Cyan
    Write-Host "  Datei: $($dll.Name)" -ForegroundColor White
    Write-Host "  Größe: $([math]::Round($dll.Length/1KB, 2)) KB" -ForegroundColor White
    Write-Host "  Erstellt: $($dll.LastWriteTime)" -ForegroundColor White
    Write-Host ""
    Write-Host "Scribus sollte das Plugin beim nächsten Start mit dem Fix laden!" -ForegroundColor Green
    Write-Host "Der Absturz sollte jetzt behoben sein." -ForegroundColor Green
    
} catch {
    Write-Host "❌ Fehler beim Kopieren: $_" -ForegroundColor Red
    exit 1
}

