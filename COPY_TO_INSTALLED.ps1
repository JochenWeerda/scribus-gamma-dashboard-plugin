# Kopiere gebaute Scribus-Dateien nach installierte Version
# Benötigt Administrator-Rechte!

param(
    [string]$BuildDir = "C:\Development\Scribus-builds\Scribus-Release-x64-v143",
    [string]$InstallDir = "C:\Program Files\Scribus 1.7.1(1)"
)

# Prüfe Administrator-Rechte
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ Dieses Script benötigt Administrator-Rechte!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Starte PowerShell als Administrator und führe dieses Script erneut aus." -ForegroundColor Yellow
    exit 1
}

Write-Host "=== Kopiere gebaute Scribus-Dateien ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quelle: $BuildDir" -ForegroundColor Gray
Write-Host "Ziel: $InstallDir" -ForegroundColor Gray
Write-Host ""

if (-not (Test-Path $BuildDir)) {
    Write-Host "❌ Build-Verzeichnis nicht gefunden: $BuildDir" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $InstallDir)) {
    Write-Host "❌ Installationsverzeichnis nicht gefunden: $InstallDir" -ForegroundColor Red
    exit 1
}

# 1. Kopiere scribus.exe
Write-Host "1. Kopiere scribus.exe..." -ForegroundColor Yellow
$exeSource = Join-Path $BuildDir "scribus.exe"
$exeDest = Join-Path $InstallDir "scribus.exe"
if (Test-Path $exeSource) {
    try {
        Copy-Item $exeSource -Destination $exeDest -Force -ErrorAction Stop
        $srcSize = [math]::Round((Get-Item $exeSource).Length / 1MB, 2)
        Write-Host "   ✅ scribus.exe kopiert ($srcSize MB)" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Fehler beim Kopieren: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   ⚠️  scribus.exe nicht gefunden: $exeSource" -ForegroundColor Yellow
}

# 2. Kopiere Plugin
Write-Host ""
Write-Host "2. Kopiere Plugin..." -ForegroundColor Yellow
$pluginSource = Join-Path $BuildDir "plugins\gamma_dashboard.dll"
$pluginDestDir = Join-Path $InstallDir "plugins"
$pluginDest = Join-Path $pluginDestDir "gamma_dashboard.dll"

if (-not (Test-Path $pluginDestDir)) {
    try {
        New-Item -ItemType Directory -Force -Path $pluginDestDir | Out-Null
        Write-Host "   ✅ plugins-Ordner erstellt" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Fehler beim Erstellen des plugins-Ordners: $_" -ForegroundColor Red
        exit 1
    }
}

if (Test-Path $pluginSource) {
    try {
        Copy-Item $pluginSource -Destination $pluginDest -Force -ErrorAction Stop
        $srcSize = [math]::Round((Get-Item $pluginSource).Length / 1KB, 1)
        Write-Host "   ✅ gamma_dashboard.dll kopiert ($srcSize KB)" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Fehler beim Kopieren: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   ⚠️  gamma_dashboard.dll nicht gefunden: $pluginSource" -ForegroundColor Yellow
}

# 3. Kopiere weitere wichtige Dateien (optional)
Write-Host ""
Write-Host "3. Kopiere weitere Dateien..." -ForegroundColor Yellow
$filesToCopy = @(
    "scribus.pdb",
    "scribusapi.dll",
    "scribusapi.lib"
)

foreach ($file in $filesToCopy) {
    $src = Join-Path $BuildDir $file
    $dst = Join-Path $InstallDir $file
    if (Test-Path $src) {
        try {
            Copy-Item $src -Destination $dst -Force -ErrorAction Stop
            Write-Host "   ✅ $file kopiert" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️  $file konnte nicht kopiert werden: $_" -ForegroundColor Yellow
        }
    }
}

# 4. Finale Prüfung
Write-Host ""
Write-Host "4. Finale Prüfung..." -ForegroundColor Yellow
$allOk = $true

if (Test-Path $exeDest) {
    Write-Host "   ✅ scribus.exe vorhanden" -ForegroundColor Green
} else {
    Write-Host "   ❌ scribus.exe fehlt" -ForegroundColor Red
    $allOk = $false
}

if (Test-Path $pluginDest) {
    Write-Host "   ✅ gamma_dashboard.dll vorhanden" -ForegroundColor Green
} else {
    Write-Host "   ❌ gamma_dashboard.dll fehlt" -ForegroundColor Red
    $allOk = $false
}

Write-Host ""
if ($allOk) {
    Write-Host "✅✅✅ ERFOLGREICH! ✅✅✅" -ForegroundColor Green
    Write-Host ""
    Write-Host "Nächste Schritte:" -ForegroundColor Yellow
    Write-Host "  - Starte Scribus aus: $InstallDir" -ForegroundColor White
    Write-Host "  - Menü → Extras → Gamma Dashboard" -ForegroundColor White
    Write-Host "  - Plugin sollte geladen sein!" -ForegroundColor White
} else {
    Write-Host "❌ Einige Dateien konnten nicht kopiert werden" -ForegroundColor Red
    Write-Host "   Bitte prüfe die Fehlermeldungen oben" -ForegroundColor Yellow
    exit 1
}

