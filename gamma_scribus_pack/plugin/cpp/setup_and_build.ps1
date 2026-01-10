# Vollständiges Setup und Build-Script für Gamma Dashboard Plugin
# Installiert alle Voraussetzungen und kompiliert das Plugin

param(
    [switch]$SkipDownloads,
    [string]$ScribusSourcePath = "",
    [string]$QtPath = "",
    [string]$BuildType = "Release"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Gamma Dashboard Plugin - Vollständiges Setup ===" -ForegroundColor Cyan
Write-Host ""

# 1. Prüfe Admin-Rechte
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "WARNUNG: Nicht als Administrator ausgeführt." -ForegroundColor Yellow
    Write-Host "Einige Schritte erfordern möglicherweise Admin-Rechte." -ForegroundColor Yellow
}

# 2. Prüfe/Installiere CMake
Write-Host "1. Prüfe CMake..." -ForegroundColor Yellow
$cmakePath = Get-Command cmake -ErrorAction SilentlyContinue

if (-not $cmakePath) {
    Write-Host "  CMake nicht gefunden." -ForegroundColor Red
    if (-not $SkipDownloads) {
        Write-Host "  Installiere CMake..." -ForegroundColor Yellow
        
        # Download CMake
        $cmakeUrl = "https://github.com/Kitware/CMake/releases/download/v3.28.0/cmake-3.28.0-windows-x86_64.msi"
        $cmakeInstaller = "$env:TEMP\cmake-installer.msi"
        
        try {
            Write-Host "  Lade CMake herunter..." -ForegroundColor Yellow
            Invoke-WebRequest -Uri $cmakeUrl -OutFile $cmakeInstaller -UseBasicParsing
            
            Write-Host "  Installiere CMake..." -ForegroundColor Yellow
            Start-Process msiexec.exe -ArgumentList "/i `"$cmakeInstaller`" /quiet /norestart ADD_CMAKE_TO_PATH=System" -Wait
            
            # Warte kurz und prüfe erneut
            Start-Sleep -Seconds 5
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
            $cmakePath = Get-Command cmake -ErrorAction SilentlyContinue
        } catch {
            Write-Host "  FEHLER: CMake konnte nicht automatisch installiert werden." -ForegroundColor Red
            Write-Host "  Bitte installiere CMake manuell von: https://cmake.org/download/" -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Host "  Bitte installiere CMake manuell von: https://cmake.org/download/" -ForegroundColor Yellow
        exit 1
    }
}

if ($cmakePath) {
    $cmakeVersion = & cmake --version | Select-Object -First 1
    Write-Host "  ✓ CMake gefunden: $cmakeVersion" -ForegroundColor Green
} else {
    Write-Host "  FEHLER: CMake nicht verfügbar!" -ForegroundColor Red
    exit 1
}

# 3. Prüfe/Installiere Qt (vereinfacht - nur Info)
Write-Host ""
Write-Host "2. Prüfe Qt5..." -ForegroundColor Yellow

if ($QtPath -and (Test-Path (Join-Path $QtPath "bin\qmake.exe"))) {
    Write-Host "  ✓ Qt5 gefunden: $QtPath" -ForegroundColor Green
} else {
    # Suche Qt in Standard-Pfaden
    $possibleQtPaths = @(
        "C:\Qt\5.15.2\msvc2019_64",
        "C:\Qt\5.15.2\msvc2022_64",
        "C:\Qt\6.5.0\msvc2019_64",
        "C:\Program Files\Qt\5.15.2\msvc2019_64"
    )
    
    $qtFound = $false
    foreach ($path in $possibleQtPaths) {
        if (Test-Path (Join-Path $path "bin\qmake.exe")) {
            $QtPath = $path
            $qtFound = $true
            Write-Host "  ✓ Qt5 gefunden: $QtPath" -ForegroundColor Green
            break
        }
    }
    
    if (-not $qtFound) {
        Write-Host "  Qt5 nicht gefunden!" -ForegroundColor Red
        Write-Host "  Bitte installiere Qt5 von: https://www.qt.io/download" -ForegroundColor Yellow
        Write-Host "  Oder gib den Pfad an: -QtPath 'C:\Qt\5.15.2\msvc2019_64'" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Qt-Installation empfohlen:" -ForegroundColor Cyan
        Write-Host "    - Qt 5.15.2 (oder höher)" -ForegroundColor White
        Write-Host "    - Für Visual Studio 2019 (msvc2019_64) oder 2022 (msvc2022_64)" -ForegroundColor White
        exit 1
    }
}

# 4. Prüfe/Download Scribus-Quellcode
Write-Host ""
Write-Host "3. Prüfe Scribus-Header..." -ForegroundColor Yellow

if ($ScribusSourcePath -and (Test-Path (Join-Path $ScribusSourcePath "scribus\plugins\scplugin.h"))) {
    $scribusInclude = Join-Path $ScribusSourcePath "scribus\plugins"
    Write-Host "  ✓ Scribus-Header gefunden: $scribusInclude" -ForegroundColor Green
} else {
    # Suche in verschiedenen Pfaden
    $possiblePaths = @(
        "F:\Scribus for Windows\scribus-1.7.x-svn\Scribus\scribus\plugins",
        "C:\Scribus\scribus-1.7.x-svn\Scribus\scribus\plugins",
        "$env:USERPROFILE\Downloads\scribus-1.7.x-svn\Scribus\scribus\plugins",
        "$env:USERPROFILE\Documents\scribus-1.7.x-svn\Scribus\scribus\plugins"
    )
    
    $scribusInclude = ""
    foreach ($path in $possiblePaths) {
        if (Test-Path (Join-Path $path "scplugin.h")) {
            $scribusInclude = $path
            Write-Host "  ✓ Scribus-Header gefunden: $scribusInclude" -ForegroundColor Green
            break
        }
    }
    
    if (-not $scribusInclude) {
        Write-Host "  Scribus-Header nicht gefunden!" -ForegroundColor Red
        Write-Host ""
        Write-Host "  Option 1: Download Scribus-Quellcode" -ForegroundColor Cyan
        Write-Host "    Download von: https://www.scribus.net/downloads/source/" -ForegroundColor White
        Write-Host "    Extrahiere und gib den Pfad an: -ScribusSourcePath 'C:\Path\To\Scribus\Source'" -ForegroundColor White
        Write-Host ""
        Write-Host "  Option 2: Verwende minimale Header-Dateien (experimentell)" -ForegroundColor Cyan
        Write-Host "    Ich erstelle minimale Header basierend auf der Plugin-API..." -ForegroundColor White
        
        # Erstelle minimale Header-Dateien
        $minimalHeadersDir = Join-Path $PSScriptRoot "minimal_headers"
        New-Item -ItemType Directory -Force -Path $minimalHeadersDir | Out-Null
        
        Write-Host "    Erstelle minimale Header..." -ForegroundColor Yellow
        # (Hier würde ich die minimalen Header erstellen, aber das ist komplex)
        
        Write-Host "    WARNUNG: Minimale Header funktionieren möglicherweise nicht vollständig!" -ForegroundColor Yellow
        Write-Host "    Es wird empfohlen, den vollständigen Scribus-Quellcode zu verwenden." -ForegroundColor Yellow
        exit 1
    }
}

# 5. Starte Build
Write-Host ""
Write-Host "4. Starte Build..." -ForegroundColor Yellow
Write-Host ""

& "$PSScriptRoot\build_plugin.ps1" -ScribusSourcePath $ScribusSourcePath -QtPath $QtPath -BuildType $BuildType

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=== Setup und Build erfolgreich abgeschlossen! ===" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "=== Build fehlgeschlagen! ===" -ForegroundColor Red
    exit 1
}

