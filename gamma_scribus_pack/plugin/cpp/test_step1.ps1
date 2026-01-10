# Test Step 1: DLL lÃ¤dt ohne Instanz
# Kompiliert Plugin mit nur Export-Funktionen (getPlugin() gibt nullptr zurÃ¼ck)

$ErrorActionPreference = "Stop"

Write-Host "=== Test Step 1: DLL lÃ¤dt ohne Instanz ===" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$buildDir = Join-Path $scriptDir "build"

# Finde CMake
$cmakeExe = "C:\Development\bin\cmake.exe"
if (-not (Test-Path $cmakeExe)) {
    Write-Host "âŒ CMake nicht gefunden: $cmakeExe" -ForegroundColor Red
    exit 1
}

# Finde Scribus-Header
$scribusHeaderDir = "C:\Development\scribus-1.7\scribus"
if (-not (Test-Path "$scribusHeaderDir\scplugin.h")) {
    Write-Host "âŒ Scribus-Header nicht gefunden: $scribusHeaderDir" -ForegroundColor Red
    exit 1
}

# Erstelle Build-Verzeichnis
if (-not (Test-Path $buildDir)) {
    New-Item -ItemType Directory -Path $buildDir | Out-Null
}

Write-Host "Kompiliere Test Step 1..." -ForegroundColor Yellow
Write-Host "  Test: DLL lÃ¤dt ohne Instanz (getPlugin() â†’ nullptr)" -ForegroundColor Gray
Write-Host ""

# CMake konfigurieren mit TEST_STEP=1
Write-Host "  CMake-Parameter:" -ForegroundColor Gray
Write-Host "    SCRIBUS_INCLUDE_DIR: $scribusHeaderDir" -ForegroundColor Gray
Write-Host "    TEST_STEP: 1" -ForegroundColor Gray
Write-Host ""

# Konvertiere Windows-Pfad zu CMake-Pfad (Forward-Slashes)
$scribusHeaderDirCMake = $scribusHeaderDir -replace "\\", "/"

Write-Host "  Pfad-Konvertierung:" -ForegroundColor Gray
Write-Host "    Windows: $scribusHeaderDir" -ForegroundColor Gray
Write-Host "    CMake:   $scribusHeaderDirCMake" -ForegroundColor Gray
Write-Host ""

$prevErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $cmakeExe `
    -S $scriptDir `
    -B $buildDir `
    -G "Visual Studio 17 2022" `
    -A x64 `
    -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL `
    -DCMAKE_BUILD_TYPE=Release `
    -DCMAKE_PREFIX_PATH="C:\Qt\6.5.3\msvc2019_64" `
    -DSCRIBUS_INCLUDE_DIR="$scribusHeaderDirCMake" `
    -DTEST_STEP=1 `
    2>&1 | Select-String -Pattern "error|warning|SCRIBUS_INCLUDE|TEST_STEP|Step 1" | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
$ErrorActionPreference = $prevErrorActionPreference

if ($LASTEXITCODE -ne 0) {
    Write-Host "âŒ CMake-Konfiguration fehlgeschlagen!" -ForegroundColor Red
    exit 1
}

# Kompiliere
$msbuildExe = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe"
& $msbuildExe `
    (Join-Path $buildDir "gamma_dashboard_plugin.vcxproj") `
    /p:Configuration=Release `
    /p:Platform=x64 `
    /t:Build `
    /v:minimal `
    2>&1 | Select-String -Pattern "error|succeeded|dll" | Select-Object -Last 3

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "âŒ Kompilierung fehlgeschlagen!" -ForegroundColor Red
    exit 1
}

$dllPath = Join-Path $buildDir "Release\gamma_dashboard.dll"
if (Test-Path $dllPath) {
    $dllInfo = Get-Item $dllPath
    Write-Host ""
    Write-Host "âœ… Test Step 1 kompiliert!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Details:" -ForegroundColor Cyan
    Write-Host "  Datei: $($dllInfo.Name)" -ForegroundColor White
    Write-Host "  GrÃ¶ÃŸe: $([math]::Round($dllInfo.Length / 1KB, 1)) KB" -ForegroundColor White
    Write-Host ""
    Write-Host "NÃ¤chste Schritte:" -ForegroundColor Yellow
    Write-Host "  1. Plugin installieren (als Admin):" -ForegroundColor White
    Write-Host "     Copy-Item '$dllPath' -Destination 'C:\Program Files\Scribus 1.7.1\plugins\gamma_dashboard.dll' -Force" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  2. Scribus starten und testen:" -ForegroundColor White
    Write-Host "     cd 'C:\Program Files\Scribus 1.7.1'" -ForegroundColor Cyan
    Write-Host "     .\scribus.exe" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Falls Scribus startet:" -ForegroundColor Green
    Write-Host "    â†’ Problem liegt bei Instanziierung (Step 2 testen)" -ForegroundColor White
    Write-Host ""
    Write-Host "  Falls Scribus abstÃ¼rzt:" -ForegroundColor Red
    Write-Host "    â†’ Problem liegt bei DLL-Loading oder Export-Funktionen" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "âŒ DLL nicht gefunden: $dllPath" -ForegroundColor Red
    exit 1
}

