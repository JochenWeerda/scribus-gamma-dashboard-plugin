# Rebuild Plugin with Qt 6.10.1 (same as Scribus)
# This script configures CMake to use the correct Qt version

$ErrorActionPreference = "Stop"

Write-Host "=== Rebuild Plugin mit Qt 6.10.1 ===" -ForegroundColor Cyan
Write-Host ""

# Find Qt 6.10.1
$qtPath = $null
$qtPaths = @(
    "C:\Development\Qt\6.10.1\msvc2022_64",
    "C:\Development\Qt\6.10.1\msvc2019_64",
    "C:\Qt\6.10.1\msvc2022_64",
    "C:\Qt\6.10.1\msvc2019_64",
    "C:\Development\Qt\6.10.1\msvc2022_64\bin\qmake.exe",
    "C:\Development\Qt\6.10.1\msvc2019_64\bin\qmake.exe",
    "C:\Qt\6.10.1\msvc2022_64\bin\qmake.exe",
    "C:\Qt\6.10.1\msvc2019_64\bin\qmake.exe"
)

foreach ($path in $qtPaths) {
    if (Test-Path $path) {
        if ($path -like "*qmake.exe") {
            $qtPath = Split-Path (Split-Path $path -Parent) -Parent
        } else {
            $qtPath = $path
        }
        if (Test-Path (Join-Path $qtPath "bin\qmake.exe")) {
            Write-Host "Qt 6.10.1 gefunden: $qtPath" -ForegroundColor Green
            break
        }
    }
}

if (-not $qtPath) {
    Write-Host "FEHLER: Qt 6.10.1 nicht gefunden!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Bitte Qt 6.10.1 installieren:" -ForegroundColor Yellow
    Write-Host "  1. Qt Online Installer herunterladen: https://www.qt.io/download-qt-installer" -ForegroundColor White
    Write-Host "  2. Qt 6.10.1 installieren" -ForegroundColor White
    Write-Host "  3. Oder Script anpassen mit korrektem Qt-Pfad" -ForegroundColor White
    exit 1
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$buildDir = Join-Path $scriptDir "build"

Write-Host ""
Write-Host "Konfiguriere CMake mit Qt 6.10.1..." -ForegroundColor Yellow

# Find CMake
$cmakeExe = $null
$cmakePaths = @(
    "C:\Development\cmake-4.2.1\bin\cmake.exe",
    "C:\Program Files\CMake\bin\cmake.exe",
    "C:\Program Files (x86)\CMake\bin\cmake.exe"
)

foreach ($path in $cmakePaths) {
    if (Test-Path $path) {
        $cmakeExe = Get-Item $path
        Write-Host "CMake gefunden: $($cmakeExe.FullName)" -ForegroundColor Green
        break
    }
}

if (-not $cmakeExe) {
    $cmakeInPath = Get-Command cmake -ErrorAction SilentlyContinue
    if ($cmakeInPath) {
        $cmakeExe = Get-Item $cmakeInPath.Source
        Write-Host "CMake im PATH: $($cmakeExe.FullName)" -ForegroundColor Green
    } else {
        Write-Host "FEHLER: CMake nicht gefunden!" -ForegroundColor Red
        exit 1
    }
}

# Clean build directory
if (Test-Path $buildDir) {
    Write-Host "Lösche altes Build-Verzeichnis..." -ForegroundColor Gray
    Remove-Item $buildDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null

# Configure CMake
$cmakeArgs = @(
    "-S", $scriptDir,
    "-B", $buildDir,
    "-DCMAKE_PREFIX_PATH=$qtPath",
    "-DCMAKE_BUILD_TYPE=Release"
)

# Add Scribus include directory if found
$scribusIncludes = @(
    "C:\Development\scribus-1.7\scribus\plugins",
    "F:\Scribus for Windows\scribus-1.7.x-svn\Scribus\scribus\plugins",
    "C:\Development\scribus-1.7\scribus"
)

foreach ($include in $scribusIncludes) {
    $scplugin = Join-Path $include "scplugin.h"
    if (Test-Path $scplugin) {
        $cmakeArgs += "-DSCRIBUS_INCLUDE_DIR=$include"
        Write-Host "Scribus Include: $include" -ForegroundColor Green
        break
    }
}

& $cmakeExe.FullName @cmakeArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: CMake-Konfiguration fehlgeschlagen!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Kompiliere Plugin..." -ForegroundColor Yellow
& $cmakeExe.Source --build $buildDir --config Release

if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Kompilierung fehlgeschlagen!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Build erfolgreich! ===" -ForegroundColor Green
$dll = Join-Path $buildDir "Release\gamma_dashboard.dll"
if (Test-Path $dll) {
    $dllFile = Get-Item $dll
    Write-Host "DLL: $($dllFile.FullName)" -ForegroundColor Cyan
    Write-Host "Größe: $([math]::Round($dllFile.Length/1KB, 2)) KB" -ForegroundColor Cyan
    Write-Host "Erstellt: $($dllFile.LastWriteTime)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Nächste Schritte:" -ForegroundColor Yellow
    Write-Host "  1. DLL installieren:" -ForegroundColor White
    Write-Host "     .\install_to_scribus1711.ps1" -ForegroundColor Cyan
    Write-Host "  2. Scribus neu starten" -ForegroundColor White
}

