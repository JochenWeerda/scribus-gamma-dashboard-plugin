# Test Step 0: DLL lädt OHNE scplugin.h (nur pluginapi.h)
# Test ob Qt-Initialisierung das Problem ist

$ErrorActionPreference = "Stop"

Write-Host "=== Test Step 0: DLL ohne Qt ===" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$buildDir = Join-Path $scriptDir "build_step0"

# Finde CMake
$cmakeExe = "C:\Development\bin\cmake.exe"
if (-not (Test-Path $cmakeExe)) {
    Write-Host "❌ CMake nicht gefunden: $cmakeExe" -ForegroundColor Red
    exit 1
}

# Finde Scribus-Header (nur für pluginapi.h)
$scribusHeaderDir = "C:\Development\scribus-1.7\scribus"
if (-not (Test-Path "$scribusHeaderDir\pluginapi.h")) {
    Write-Host "❌ Scribus pluginapi.h nicht gefunden: $scribusHeaderDir" -ForegroundColor Red
    exit 1
}

# Erstelle Build-Verzeichnis
if (Test-Path $buildDir) {
    Remove-Item -Path $buildDir -Recurse -Force | Out-Null
}
New-Item -ItemType Directory -Path $buildDir | Out-Null

Write-Host "Kompiliere Test Step 0..." -ForegroundColor Yellow
Write-Host "  Test: DLL ohne scplugin.h (nur pluginapi.h)" -ForegroundColor Gray
Write-Host "  Ziel: Prüfe ob Qt-Initialisierung das Problem ist" -ForegroundColor Gray
Write-Host ""

# Konvertiere Windows-Pfad zu CMake-Pfad
$scribusHeaderDirCMake = $scribusHeaderDir -replace "\\", "/"

# CMake konfigurieren mit TEST_STEP=0 (ohne Qt)
& $cmakeExe `
    -S $scriptDir `
    -B $buildDir `
    -G "Visual Studio 17 2022" `
    -A x64 `
    -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL `
    -DCMAKE_BUILD_TYPE=Release `
    -DSCRIBUS_INCLUDE_DIR="$scribusHeaderDirCMake" `
    -DTEST_STEP=0 `
    2>&1 | Select-String -Pattern "error|warning|TEST_STEP|Step 0" | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ CMake-Konfiguration fehlgeschlagen!" -ForegroundColor Red
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
    Write-Host "❌ Kompilierung fehlgeschlagen!" -ForegroundColor Red
    exit 1
}

$dllPath = Join-Path $buildDir "Release\gamma_dashboard.dll"
if (Test-Path $dllPath) {
    $dllInfo = Get-Item $dllPath
    Write-Host ""
    Write-Host "✅ Test Step 0 erfolgreich kompiliert!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Details:" -ForegroundColor Cyan
    Write-Host "  DLL: $dllPath" -ForegroundColor White
    Write-Host "  Größe: $([math]::Round($dllInfo.Length / 1KB, 1)) KB" -ForegroundColor White
    Write-Host ""
    Write-Host "Nächster Schritt:" -ForegroundColor Yellow
    Write-Host "  → DLL nach C:\Program Files\Scribus 1.7.1\plugins\ kopieren" -ForegroundColor White
    Write-Host "  → Scribus starten und testen" -ForegroundColor White
    Write-Host ""
    Write-Host "Falls Scribus damit startet:" -ForegroundColor Green
    Write-Host "  → Problem liegt bei Qt-Initialisierung (scplugin.h)" -ForegroundColor White
    Write-Host ""
    Write-Host "Falls Scribus weiterhin abstürzt:" -ForegroundColor Red
    Write-Host "  → Problem liegt tiefer (DLL-Loading, Export-Funktionen)" -ForegroundColor White
} else {
    Write-Host "❌ DLL nicht gefunden: $dllPath" -ForegroundColor Red
    exit 1
}

