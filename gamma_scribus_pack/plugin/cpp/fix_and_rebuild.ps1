# Fix: Complete rebuild with TEST_STEP=3
# This solves the problem that .vcxproj still uses test_step1

$ErrorActionPreference = "Stop"

Write-Host "=== Fix: Complete Rebuild with TEST_STEP=3 ===" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$buildDir = Join-Path $scriptDir "build"

# Clean: Delete build directory completely (except .vs for Visual Studio)
if (Test-Path $buildDir) {
    Write-Host "Deleting build directory..." -ForegroundColor Yellow
    Get-ChildItem $buildDir -Exclude ".vs" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  Build directory deleted" -ForegroundColor Green
}

New-Item -ItemType Directory -Force -Path $buildDir | Out-Null

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
    Write-Host "ERROR: CMake not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install CMake or add it to PATH" -ForegroundColor Yellow
    exit 1
}

Write-Host "CMake: $($cmakeExe.FullName)" -ForegroundColor Green

# Find Qt 6.10.1
$qtPath = "C:\Development\Qt\6.10.1\msvc2022_64"
if (-not (Test-Path (Join-Path $qtPath "bin\qmake.exe"))) {
    Write-Host "ERROR: Qt 6.10.1 not found in $qtPath" -ForegroundColor Red
    exit 1
}

Write-Host "Qt 6.10.1: $qtPath" -ForegroundColor Green

# Find Scribus includes
$scribusInclude = "C:\Development\scribus-1.7\scribus\plugins"
if (-not (Test-Path (Join-Path $scribusInclude "scplugin.h"))) {
    Write-Host "WARNING: Scribus headers not found in $scribusInclude" -ForegroundColor Yellow
    $scribusInclude = $null
} else {
    Write-Host "Scribus Include: $scribusInclude" -ForegroundColor Green
}

Write-Host ""
Write-Host "Configuring CMake with:" -ForegroundColor Cyan
Write-Host "  - TEST_STEP=3 (full plugin)" -ForegroundColor White
Write-Host "  - Qt 6.10.1" -ForegroundColor White
Write-Host "  - Release build" -ForegroundColor White
Write-Host ""

# Configure CMake
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
    Write-Host ""
    Write-Host "ERROR: CMake configuration failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "CMake configured" -ForegroundColor Green
Write-Host ""

# Verify TEST_STEP
$cacheFile = Join-Path $buildDir "CMakeCache.txt"
if (Test-Path $cacheFile) {
    $testStep = Select-String "TEST_STEP:STRING" $cacheFile | Select-Object -First 1
    if ($testStep -and $testStep.Line -like "*=3*") {
        Write-Host "TEST_STEP=3 confirmed" -ForegroundColor Green
    } else {
        Write-Host "WARNING: TEST_STEP not correctly set!" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Compiling plugin..." -ForegroundColor Yellow

& $cmakeExe.FullName --build $buildDir --config Release

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Compilation failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Build completed! ===" -ForegroundColor Green

$dll = Join-Path $buildDir "Release\gamma_dashboard.dll"
if (Test-Path $dll) {
    $dllFile = Get-Item $dll
    Write-Host ""
    Write-Host "DLL Details:" -ForegroundColor Cyan
    Write-Host "  Path: $($dllFile.FullName)" -ForegroundColor White
    $sizeKB = [math]::Round($dllFile.Length/1KB, 2)
    Write-Host "  Size: $sizeKB KB" -ForegroundColor White
    Write-Host "  Created: $($dllFile.LastWriteTime)" -ForegroundColor White
    Write-Host ""
    
    if ($dllFile.Length -gt 50000) {
        Write-Host "SUCCESS: Full plugin compiled successfully!" -ForegroundColor Green
        Write-Host "  DLL is now properly sized!" -ForegroundColor Green
    } elseif ($dllFile.Length -gt 20000) {
        Write-Host "WARNING: Plugin compiled, but may still be incomplete" -ForegroundColor Yellow
    } else {
        Write-Host "ERROR: DLL is still too small!" -ForegroundColor Red
        Write-Host "  Check .vcxproj file - which source files are compiled?" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Install DLL: .\install_latest_dll.ps1" -ForegroundColor White
    Write-Host "  2. Restart Scribus" -ForegroundColor White
    Write-Host "  3. Plugin should now work!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "ERROR: DLL not found!" -ForegroundColor Red
    exit 1
}
