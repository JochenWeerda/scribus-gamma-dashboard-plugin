# Installiert das Gamma Dashboard Plugin nach Scribus
param(
    [string]$ScribusPluginPath = "",
    [switch]$SkipBackup
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$dllSource = Join-Path $ScriptDir "build\Release\gamma_dashboard.dll"

if (-not (Test-Path $dllSource)) {
    Write-Host "❌ DLL nicht gefunden: $dllSource" -ForegroundColor Red
    Write-Host "   Bitte zuerst das Plugin bauen!" -ForegroundColor Yellow
    exit 1
}

# Finde Scribus Plugin-Verzeichnis
$pluginDir = $ScribusPluginPath
if (-not $pluginDir) {
    $searchPaths = @(
        "C:\Program Files\Scribus 1.7.1\lib\scribus\plugins",
        "C:\Program Files (x86)\Scribus 1.7.1\lib\scribus\plugins",
        "$env:LOCALAPPDATA\Programs\Scribus\lib\scribus\plugins"
    )
    
    foreach ($path in $searchPaths) {
        if (Test-Path $path) {
            $pluginDir = $path
            break
        }
    }
}

if (-not $pluginDir) {
    Write-Host "❌ Scribus Plugin-Verzeichnis nicht gefunden!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Bitte manuell kopieren:" -ForegroundColor Yellow
    Write-Host "  Quelle: $dllSource" -ForegroundColor Cyan
    Write-Host "  Ziel:   <Scribus-Installation>\lib\scribus\plugins\gamma_dashboard.dll" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Oder verwende: -ScribusPluginPath <Pfad>" -ForegroundColor Yellow
    exit 1
}

$dllTarget = Join-Path $pluginDir "gamma_dashboard.dll"

# Backup vorhandener DLL
if ((Test-Path $dllTarget) -and (-not $SkipBackup)) {
    $backupPath = "$dllTarget.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Copy-Item -Path $dllTarget -Destination $backupPath -Force
    Write-Host "✅ Backup erstellt: $backupPath" -ForegroundColor Green
}

# Kopiere DLL
try {
    Copy-Item -Path $dllSource -Destination $dllTarget -Force
    Write-Host ""
    Write-Host "✅ Plugin erfolgreich installiert!" -ForegroundColor Green
    Write-Host "   Ziel: $dllTarget" -ForegroundColor Cyan
    Write-Host "   Größe: $([math]::Round((Get-Item $dllTarget).Length/1KB, 2)) KB" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Nächste Schritte:" -ForegroundColor Yellow
    Write-Host "  1. Scribus starten" -ForegroundColor White
    Write-Host "  2. Plugin testen: Extras > Tools > Gamma Dashboard" -ForegroundColor White
    Write-Host "  3. Prüfen: Extras > Plugins" -ForegroundColor White
} catch {
    Write-Host ""
    Write-Host "❌ Installation fehlgeschlagen: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Tipp: Führe PowerShell als Administrator aus:" -ForegroundColor Yellow
    Write-Host "  Start-Process powershell -Verb RunAs" -ForegroundColor Cyan
    exit 1
}

