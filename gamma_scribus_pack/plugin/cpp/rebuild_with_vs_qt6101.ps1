# Rebuild Plugin with Visual Studio and Qt 6.10.1
# This script reconfigures CMake with Qt 6.10.1 and then opens Visual Studio

$ErrorActionPreference = "Stop"

Write-Host "=== Rebuild Plugin mit Visual Studio und Qt 6.10.1 ===" -ForegroundColor Cyan
Write-Host ""

# Find Qt 6.10.1
$qtPath = "C:\Development\Qt\6.10.1\msvc2022_64"

if (-not (Test-Path (Join-Path $qtPath "bin\qmake.exe"))) {
    Write-Host "FEHLER: Qt 6.10.1 nicht gefunden in $qtPath" -ForegroundColor Red
    exit 1
}

Write-Host "Qt 6.10.1: $qtPath" -ForegroundColor Green

# Find CMake
$cmakeExe = $null
$cmakePaths = @(
    "C:\Development\cmake-4.2.1\bin\cmake.exe",
    "C:\Program Files\CMake\bin\cmake.exe"
)

foreach ($path in $cmakePaths) {
    if (Test-Path $path) {
        $cmakeExe = Get-Item $path
        break
    }
}

if (-not $cmakeExe) {
    $cmakeInPath = Get-Command cmake -ErrorAction SilentlyContinue
    if ($cmakeInPath) {
        $cmakeExe = Get-Item $cmakeInPath.Source
    } else {
        Write-Host "FEHLER: CMake nicht gefunden!" -ForegroundColor Red
        Write-Host "Tipp: CMake wird nur für Konfiguration benötigt, dann öffnen wir Visual Studio" -ForegroundColor Yellow
        exit 1
    }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$buildDir = Join-Path $scriptDir "build"

Write-Host ""
Write-Host "Konfiguriere CMake mit Qt 6.10.1..." -ForegroundColor Yellow

# Reconfigure CMake with Qt 6.10.1
$cmakeArgs = @(
    "-S", $scriptDir,
    "-B", $buildDir,
    "-DCMAKE_PREFIX_PATH=$qtPath",
    "-DCMAKE_BUILD_TYPE=Release"
)

# Add Scribus include directory if found
$scribusIncludes = @(
    "C:\Development\scribus-1.7\scribus\plugins",
    "F:\Scribus for Windows\scribus-1.7.x-svn\Scribus\scribus\plugins"
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
Write-Host "=== CMake konfiguriert ===" -ForegroundColor Green
Write-Host ""
Write-Host "Öffne Visual Studio Solution..." -ForegroundColor Yellow

$solutionPath = Join-Path $buildDir "gamma_dashboard_plugin.sln"
if (Test-Path $solutionPath) {
    Start-Process $solutionPath
    Write-Host ""
    Write-Host "Visual Studio wurde geöffnet!" -ForegroundColor Green
    Write-Host ""
    Write-Host "In Visual Studio:" -ForegroundColor Cyan
    Write-Host "  1. Configuration: Release" -ForegroundColor White
    Write-Host "  2. Platform: x64" -ForegroundColor White
    Write-Host "  3. Build > Build Solution (F7)" -ForegroundColor White
    Write-Host ""
    Write-Host "Die DLL wird erstellt in: build\Release\gamma_dashboard.dll" -ForegroundColor Gray
} else {
    Write-Host "FEHLER: Solution nicht gefunden: $solutionPath" -ForegroundColor Red
}


