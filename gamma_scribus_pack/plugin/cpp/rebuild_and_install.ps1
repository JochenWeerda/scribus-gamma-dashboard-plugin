# Rebuild and Install Gamma Dashboard Plugin
# Automatisiertes Script für Build -> Install Workflow

$ErrorActionPreference = "Stop"

Write-Host "=== Rebuild & Install Gamma Dashboard Plugin ===" -ForegroundColor Cyan
Write-Host ""

# Konfiguration
$solutionPath = "C:\Development\scribus-1.7\win32\msvc2022\Scribus.sln"
$projectName = "gamma_dashboard"
$sourceDll = "C:\Development\Scribus-builds\Scribus-Release-x64-v143\plugins\gamma_dashboard.dll"
$targetDll = "C:\Program Files\Scribus 1.7.1(1)\plugins\gamma_dashboard.dll"
$msbuildPath = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe"

# Prüfe ob MSBuild vorhanden
if (-not (Test-Path $msbuildPath)) {
    $msbuildPath = "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe"
}
if (-not (Test-Path $msbuildPath)) {
    Write-Host "Fehler: MSBuild nicht gefunden!" -ForegroundColor Red
    Write-Host "Bitte Visual Studio 2022 Build Tools installieren." -ForegroundColor Yellow
    exit 1
}

# Schritt 1: Plugin bauen
Write-Host "1. Baue Plugin..." -ForegroundColor Yellow
Write-Host "   Projekt: $projectName" -ForegroundColor Gray
Write-Host "   Solution: $solutionPath" -ForegroundColor Gray
Write-Host ""

Push-Location (Split-Path $solutionPath)
try {
    & $msbuildPath $solutionPath /t:$projectName /p:Configuration=Release /p:Platform=x64 /m:1 /v:minimal 2>&1 | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   Fehler: Build fehlgeschlagen (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
        exit 1
    }
    
    if (-not (Test-Path $sourceDll)) {
        Write-Host "   Fehler: DLL wurde nicht erstellt: $sourceDll" -ForegroundColor Red
        exit 1
    }
    
    $dllInfo = Get-Item $sourceDll
    Write-Host "   Erfolg: DLL erstellt ($([math]::Round($dllInfo.Length/1KB, 2)) KB)" -ForegroundColor Green
} finally {
    Pop-Location
}

Write-Host ""

# Schritt 2: Scribus beenden
Write-Host "2. Prüfe ob Scribus läuft..." -ForegroundColor Yellow
$scribusProcesses = Get-Process -Name "scribus" -ErrorAction SilentlyContinue
if ($scribusProcesses) {
    Write-Host "   Scribus läuft noch, beende Prozess..." -ForegroundColor Yellow
    $scribusProcesses | Stop-Process -Force
    Start-Sleep -Seconds 2
    Write-Host "   Scribus beendet" -ForegroundColor Green
} else {
    Write-Host "   Scribus läuft nicht" -ForegroundColor Green
}

Write-Host ""

# Schritt 3: Plugin installieren
Write-Host "3. Installiere Plugin..." -ForegroundColor Yellow
Write-Host "   Quelle: $sourceDll" -ForegroundColor Gray
Write-Host "   Ziel: $targetDll" -ForegroundColor Gray
Write-Host ""

try {
    # Prüfe ob Ziel-Verzeichnis existiert
    $targetDir = Split-Path $targetDll
    if (-not (Test-Path $targetDir)) {
        Write-Host "   Erstelle Ziel-Verzeichnis..." -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }
    
    # Backup der alten Version (falls vorhanden)
    if (Test-Path $targetDll) {
        $backupPath = "$targetDll.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Copy-Item $targetDll -Destination $backupPath -Force
        Write-Host "   Backup erstellt: $(Split-Path $backupPath -Leaf)" -ForegroundColor Gray
    }
    
    # Kopiere neue Version
    Copy-Item $sourceDll -Destination $targetDll -Force -ErrorAction Stop
    
    $targetInfo = Get-Item $targetDll
    Write-Host "   Erfolg: Plugin installiert ($([math]::Round($targetInfo.Length/1KB, 2)) KB)" -ForegroundColor Green
} catch {
    Write-Host "   Fehler: Installation fehlgeschlagen: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Bitte als Administrator ausführen!" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "=== Fertig! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Nächste Schritte:" -ForegroundColor Cyan
Write-Host "  1. Scribus starten" -ForegroundColor White
Write-Host "  2. Im 'Extras'-Menü sollte 'Gamma Dashboard' erscheinen" -ForegroundColor White
Write-Host "  3. Plugin testen" -ForegroundColor White
Write-Host ""

