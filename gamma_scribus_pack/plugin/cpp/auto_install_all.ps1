# Automatische Installation aller Voraussetzungen
# Installiert Qt5 und lädt Scribus-Quellcode herunter

param(
    [switch]$Force,
    [string]$QtVersion = "5.15.2",
    [string]$InstallDir = "C:\Development"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Automatische Installation - Gamma Dashboard Plugin ===" -ForegroundColor Cyan
Write-Host ""

# Prüfe Admin-Rechte
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "WARNUNG: Nicht als Administrator ausgeführt." -ForegroundColor Yellow
    Write-Host "Einige Installationen erfordern Admin-Rechte." -ForegroundColor Yellow
    Write-Host ""
}

# 1. Prüfe/Installiere Chocolatey
Write-Host "1. Prüfe Chocolatey..." -ForegroundColor Yellow
$chocoInstalled = Get-Command choco -ErrorAction SilentlyContinue

if (-not $chocoInstalled) {
    Write-Host "  Installiere Chocolatey..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    
    # Aktualisiere PATH
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
    
    $chocoInstalled = Get-Command choco -ErrorAction SilentlyContinue
}

if ($chocoInstalled) {
    Write-Host "  ✓ Chocolatey gefunden" -ForegroundColor Green
} else {
    Write-Host "  ✗ Chocolatey konnte nicht installiert werden" -ForegroundColor Red
    exit 1
}

# 2. Prüfe/Installiere CMake
Write-Host ""
Write-Host "2. Prüfe CMake..." -ForegroundColor Yellow
$cmakePath = Get-Command cmake -ErrorAction SilentlyContinue

if (-not $cmakePath) {
    Write-Host "  Installiere CMake über Chocolatey..." -ForegroundColor Yellow
    if ($isAdmin) {
        choco install cmake -y
    } else {
        Write-Host "  Bitte führe aus als Administrator: choco install cmake -y" -ForegroundColor Yellow
    }
    
    # Warte und aktualisiere PATH
    Start-Sleep -Seconds 3
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
    $cmakePath = Get-Command cmake -ErrorAction SilentlyContinue
}

if ($cmakePath) {
    $cmakeVersion = & cmake --version | Select-Object -First 1
    Write-Host "  ✓ CMake gefunden: $cmakeVersion" -ForegroundColor Green
} else {
    Write-Host "  ✗ CMake nicht verfügbar" -ForegroundColor Red
}

# 3. Prüfe/Installiere Git (für Scribus-Quellcode)
Write-Host ""
Write-Host "3. Prüfe Git..." -ForegroundColor Yellow
$gitPath = Get-Command git -ErrorAction SilentlyContinue

if (-not $gitPath) {
    Write-Host "  Installiere Git über Chocolatey..." -ForegroundColor Yellow
    if ($isAdmin) {
        choco install git -y
    } else {
        Write-Host "  Bitte führe aus als Administrator: choco install git -y" -ForegroundColor Yellow
    }
    
    Start-Sleep -Seconds 3
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
    $gitPath = Get-Command git -ErrorAction SilentlyContinue
}

if ($gitPath) {
    Write-Host "  ✓ Git gefunden" -ForegroundColor Green
} else {
    Write-Host "  ✗ Git nicht verfügbar" -ForegroundColor Red
}

# 4. Installiere Qt5 (vereinfacht - Info)
Write-Host ""
Write-Host "4. Qt5 Installation..." -ForegroundColor Yellow
Write-Host "  Qt5 muss manuell installiert werden:" -ForegroundColor Yellow
Write-Host "  1. Gehe zu: https://www.qt.io/download" -ForegroundColor White
Write-Host "  2. Installiere Qt $QtVersion für Visual Studio" -ForegroundColor White
Write-Host "  3. Wähle: msvc2019_64 oder msvc2022_64" -ForegroundColor White
Write-Host "  4. Standard-Pfad: C:\Qt\$QtVersion\msvc2019_64" -ForegroundColor White
Write-Host ""
Write-Host "  Alternative: Verwende vcpkg für Qt5" -ForegroundColor Cyan

# Prüfe ob Qt bereits installiert ist
$qtPaths = @(
    "C:\Qt\$QtVersion\msvc2019_64",
    "C:\Qt\$QtVersion\msvc2022_64",
    "C:\Qt\6.5.0\msvc2019_64"
)

$qtFound = $false
$QtPath = ""
foreach ($path in $qtPaths) {
    if (Test-Path (Join-Path $path "bin\qmake.exe")) {
        $QtPath = $path
        $qtFound = $true
        Write-Host "  ✓ Qt gefunden: $QtPath" -ForegroundColor Green
        break
    }
}

if (-not $qtFound) {
    Write-Host "  ⚠ Qt5 noch nicht installiert" -ForegroundColor Yellow
}

# 5. Lade Scribus-Quellcode herunter
Write-Host ""
Write-Host "5. Lade Scribus-Quellcode herunter..." -ForegroundColor Yellow

$scribusDir = Join-Path $InstallDir "scribus-1.7"
$scribusSourcePath = Join-Path $scribusDir "Scribus\scribus\plugins"

if (Test-Path (Join-Path $scribusSourcePath "scplugin.h")) {
    Write-Host "  ✓ Scribus-Quellcode bereits vorhanden: $scribusSourcePath" -ForegroundColor Green
} else {
    Write-Host "  Lade Scribus-Quellcode von GitHub..." -ForegroundColor Yellow
    
    # Erstelle Verzeichnis
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    
    if ($gitPath) {
        # Klone Scribus Repository
        $scribusRepo = "https://github.com/scribusproject/scribus.git"
        $scribusTemp = Join-Path $env:TEMP "scribus-temp"
        
        if (Test-Path $scribusTemp) {
            Remove-Item $scribusTemp -Recurse -Force
        }
        
        Write-Host "  Klone Scribus Repository (kann einige Minuten dauern)..." -ForegroundColor Yellow
        try {
            & git clone --depth 1 --branch "1.7" $scribusRepo $scribusTemp
            
            if (Test-Path $scribusTemp) {
                # Verschiebe nach InstallDir
                if (Test-Path $scribusDir) {
                    Remove-Item $scribusDir -Recurse -Force
                }
                Move-Item $scribusTemp $scribusDir
                
                if (Test-Path (Join-Path $scribusSourcePath "scplugin.h")) {
                    Write-Host "  ✓ Scribus-Quellcode heruntergeladen: $scribusSourcePath" -ForegroundColor Green
                } else {
                    Write-Host "  ⚠ Scribus-Quellcode heruntergeladen, aber Header nicht gefunden" -ForegroundColor Yellow
                    Write-Host "    Suche Header..." -ForegroundColor Yellow
                    
                    # Suche Header-Dateien
                    $foundHeaders = Get-ChildItem $scribusDir -Filter "scplugin.h" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
                    if ($foundHeaders) {
                        $scribusSourcePath = $foundHeaders.Directory.FullName
                        Write-Host "  ✓ Header gefunden: $scribusSourcePath" -ForegroundColor Green
                    }
                }
            }
        } catch {
            Write-Host "  ✗ Fehler beim Klonen: $_" -ForegroundColor Red
            Write-Host "  Alternative: Lade manuell herunter von: https://github.com/scribusproject/scribus" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ✗ Git nicht verfügbar für automatischen Download" -ForegroundColor Red
        Write-Host "  Bitte lade Scribus-Quellcode manuell herunter:" -ForegroundColor Yellow
        Write-Host "  https://github.com/scribusproject/scribus/archive/refs/heads/1.7.zip" -ForegroundColor White
        Write-Host "  Extrahiere nach: $InstallDir" -ForegroundColor White
    }
}

# 6. Zusammenfassung
Write-Host ""
Write-Host "=== Zusammenfassung ===" -ForegroundColor Cyan
Write-Host ""

if ($cmakePath) {
    Write-Host "✓ CMake: Verfügbar" -ForegroundColor Green
} else {
    Write-Host "✗ CMake: Nicht verfügbar" -ForegroundColor Red
}

if ($qtFound) {
    Write-Host "✓ Qt5: $QtPath" -ForegroundColor Green
} else {
    Write-Host "✗ Qt5: Bitte installiere Qt $QtVersion" -ForegroundColor Red
    Write-Host "  https://www.qt.io/download" -ForegroundColor White
}

if (Test-Path (Join-Path $scribusSourcePath "scplugin.h")) {
    Write-Host "✓ Scribus-Header: $scribusSourcePath" -ForegroundColor Green
} else {
    Write-Host "✗ Scribus-Header: Nicht gefunden" -ForegroundColor Red
    Write-Host "  Erwartet: $scribusSourcePath" -ForegroundColor White
}

Write-Host ""
Write-Host "Nächste Schritte:" -ForegroundColor Cyan
if ($cmakePath -and $qtFound -and (Test-Path (Join-Path $scribusSourcePath "scplugin.h"))) {
    Write-Host "  Alle Voraussetzungen erfüllt!" -ForegroundColor Green
    Write-Host "  Führe aus: .\build_plugin.ps1 -QtPath `"$QtPath`" -ScribusSourcePath `"$scribusDir`"" -ForegroundColor White
} else {
    Write-Host "  1. Installiere fehlende Komponenten (siehe oben)" -ForegroundColor White
    Write-Host "  2. Führe dann aus: .\build_plugin.ps1" -ForegroundColor White
}

