# Rebuild Plugin mit vollständiger Konfiguration (TEST_STEP=3)
# Löscht Build-Verzeichnis und konfiguriert neu

$ErrorActionPreference = "Stop"

Write-Host "=== Rebuild Plugin mit vollständiger Konfiguration ===" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$buildDir = Join-Path $scriptDir "build"

# Find Qt 6.10.1
$qtPath = "C:\Development\Qt\6.10.1\msvc2022_64"
if (-not (Test-Path (Join-Path $qtPath "bin\qmake.exe"))) {
    Write-Host "FEHLER: Qt 6.10.1 nicht gefunden in $qtPath" -ForegroundColor Red
    exit 1
}

Write-Host "Qt 6.10.1: $qtPath" -ForegroundColor Green

# Find Scribus includes
$scribusIncludes = @(
    "C:\Development\scribus-1.7\scribus\plugins",
    "F:\Scribus for Windows\scribus-1.7.x-svn\Scribus\scribus\plugins"
)

$scribusInclude = $null
foreach ($include in $scribusIncludes) {
    $scplugin = Join-Path $include "scplugin.h"
    if (Test-Path $scplugin) {
        $scribusInclude = $include
        Write-Host "Scribus Include: $scribusInclude" -ForegroundColor Green
        break
    }
}

if (-not $scribusInclude) {
    Write-Host "WARNUNG: Scribus-Header nicht gefunden" -ForegroundColor Yellow
}

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
    }
}

if (-not $cmakeExe) {
    Write-Host "FEHLER: CMake nicht gefunden!" -ForegroundColor Red
    exit 1
}

Write-Host "CMake: $($cmakeExe.FullName)" -ForegroundColor Green
Write-Host ""

# Clean build directory
if (Test-Path $buildDir) {
    Write-Host "Lösche Build-Verzeichnis..." -ForegroundColor Yellow
    Remove-Item $buildDir -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $buildDir | Out-Null

# Configure CMake with TEST_STEP=3
Write-Host "Konfiguriere CMake mit TEST_STEP=3 (vollständiges Plugin)..." -ForegroundColor Yellow

$cmakeArgs = @(
    "-S", $scriptDir,
    "-B", $buildDir,
    "-DCMAKE_PREFIX_PATH=$qtPath",
    "-DCMAKE_BUILD_TYPE=Release",
    "-DTEST_STEP=3"
)

if ($scribusInclude) {
    $cmakeArgs += "-DSCRIBUS_INCLUDE_DIR=$scribusInclude"
}

& $cmakeExe.FullName @cmakeArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: CMake-Konfiguration fehlgeschlagen!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Kompiliere Plugin..." -ForegroundColor Yellow
& $cmakeExe.FullName --build $buildDir --config Release

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
    
    if ($dllFile.Length -gt 50000) {
        Write-Host ""
        Write-Host "✓ Vollständiges Plugin erfolgreich kompiliert!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "⚠ DLL ist immer noch zu klein - prüfe TEST_STEP in CMakeCache.txt" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Nächste Schritte:" -ForegroundColor Yellow
    Write-Host "  1. DLL installieren: .\install_latest_dll.ps1" -ForegroundColor White
    Write-Host "  2. Scribus neu starten" -ForegroundColor White
}


