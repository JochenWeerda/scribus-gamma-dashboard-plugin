# Installiere neue Plugin-Version mit Settings/API Key Features
# Muss als Administrator ausgeführt werden!

$ErrorActionPreference = "Stop"

Write-Host "=== Installiere Gamma Dashboard Plugin (mit Settings/API Key) ===" -ForegroundColor Cyan
Write-Host ""

$sourceDll = "C:\Development\Scribus-builds\Scribus-Release-x64-v143\plugins\gamma_dashboard.dll"
$targetDir = "C:\Program Files\Scribus 1.7.1(1)\plugins"
$targetDll = Join-Path $targetDir "gamma_dashboard.dll"

Write-Host "Quelle: $sourceDll" -ForegroundColor Gray
Write-Host "Ziel: $targetDll" -ForegroundColor Gray
Write-Host ""

# Prüfe ob Quelldatei existiert
if (-not (Test-Path $sourceDll)) {
    Write-Host "❌ Quelldatei nicht gefunden: $sourceDll" -ForegroundColor Red
    Write-Host ""
    Write-Host "Bitte stellen Sie sicher, dass das Plugin gebaut wurde." -ForegroundColor Yellow
    exit 1
}

# Erstelle Ziel-Verzeichnis falls nötig
if (-not (Test-Path $targetDir)) {
    Write-Host "Erstelle Ziel-Verzeichnis..." -ForegroundColor Yellow
    try {
        New-Item -ItemType Directory -Path $targetDir -Force -ErrorAction Stop | Out-Null
        Write-Host "✅ Verzeichnis erstellt" -ForegroundColor Green
    } catch {
        Write-Host "❌ Konnte Verzeichnis nicht erstellen: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "Bitte stellen Sie sicher, dass Sie Administrator-Rechte haben." -ForegroundColor Yellow
        exit 1
    }
}

# Kopiere DLL
Write-Host "Kopiere Plugin..." -ForegroundColor Yellow
try {
    # Prüfe ob alte Version existiert
    if (Test-Path $targetDll) {
        $oldFile = Get-Item $targetDll
        $oldSize = [math]::Round($oldFile.Length / 1KB, 2)
        Write-Host "  Alte Version: $oldSize KB ($($oldFile.LastWriteTime))" -ForegroundColor Gray
    }
    
    Copy-Item $sourceDll -Destination $targetDll -Force -ErrorAction Stop
    
    if (Test-Path $targetDll) {
        $fileInfo = Get-Item $targetDll
        $sizeKB = [math]::Round($fileInfo.Length / 1KB, 2)
        
        Write-Host ""
        Write-Host "=== ✅ Plugin erfolgreich installiert ===" -ForegroundColor Green
        Write-Host ""
        Write-Host "Installiert nach:" -ForegroundColor Cyan
        Write-Host "  $targetDll" -ForegroundColor White
        Write-Host ""
        Write-Host "Details:" -ForegroundColor Cyan
        Write-Host "  Größe: $sizeKB KB" -ForegroundColor White
        Write-Host "  Erstellt: $($fileInfo.LastWriteTime)" -ForegroundColor White
        Write-Host ""
        Write-Host "✅ Neue Features:" -ForegroundColor Green
        Write-Host "  • Settings-Dialog für API Key Konfiguration" -ForegroundColor White
        Write-Host "  • Backend-API-Client für echte HTTP-Verbindungen" -ForegroundColor White
        Write-Host "  • QSettings Integration für persistente Einstellungen" -ForegroundColor White
        Write-Host "  • Mock-Mode Toggle in Settings" -ForegroundColor White
        Write-Host "  • Verbindungs-Test-Funktion" -ForegroundColor White
        Write-Host ""
        Write-Host "📌 Nächster Schritt:" -ForegroundColor Yellow
        Write-Host "  1. Scribus neu starten" -ForegroundColor White
        Write-Host "  2. Extras → Gamma Dashboard → Settings..." -ForegroundColor White
        Write-Host "  3. Backend URL und API Key konfigurieren" -ForegroundColor White
    } else {
        Write-Host "❌ Installation fehlgeschlagen - Datei nicht gefunden" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Installation fehlgeschlagen: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Bitte stellen Sie sicher, dass Sie Administrator-Rechte haben." -ForegroundColor Yellow
    Write-Host "Rechtsklick auf PowerShell → 'Als Administrator ausführen'" -ForegroundColor Yellow
    exit 1
}

