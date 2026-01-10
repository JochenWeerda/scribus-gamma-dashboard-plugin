# Build-Script für Gamma Dashboard Plugin
# Erfordert: Visual Studio mit C++-Tools, CMake, Qt5

param(
    [string]$ScribusSourcePath = "",
    [string]$QtPath = "",
    [string]$BuildType = "Release"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Gamma Dashboard Plugin Build ===" -ForegroundColor Cyan

# 1. Prüfe CMake
Write-Host "`n1. Prüfe CMake..." -ForegroundColor Yellow
$cmakeExe = ""
$cmakePath = Get-Command cmake -ErrorAction SilentlyContinue
if ($cmakePath) {
    $cmakeExe = $cmakePath.Source
    Write-Host "  CMake gefunden im PATH: $cmakeExe" -ForegroundColor Green
} else {
    # Versuche lokalen CMake-Pfad
    $localCmakePaths = @(
        "C:\Development\cmake-4.2.1\bin\cmake.exe",
        "C:\Program Files\CMake\bin\cmake.exe",
        "C:\Program Files (x86)\CMake\bin\cmake.exe"
    )
    
    foreach ($path in $localCmakePaths) {
        if (Test-Path $path) {
            $cmakeExe = $path
            Write-Host "  CMake gefunden: $cmakeExe" -ForegroundColor Green
            break
        }
    }
    
    if (-not $cmakeExe) {
        Write-Host "CMake nicht gefunden!" -ForegroundColor Red
        Write-Host "Bitte installiere CMake von: https://cmake.org/download/" -ForegroundColor Yellow
        Write-Host "Oder extrahiere nach: C:\Development\cmake-4.2.1\" -ForegroundColor Yellow
        exit 1
    }
}

# 2. Finde Scribus-Quellcode
Write-Host "`n2. Finde Scribus-Header..." -ForegroundColor Yellow
$scribusInclude = ""

if ($ScribusSourcePath) {
    $testPath = Join-Path $ScribusSourcePath "scribus\plugins"
    if (Test-Path (Join-Path $testPath "scplugin.h")) {
        $scribusInclude = $testPath
    }
}

# Versuche Standard-Pfade
if (-not $scribusInclude) {
    $possiblePaths = @(
        "F:\Scribus for Windows\scribus-1.7.x-svn\Scribus\scribus\plugins",
        "C:\Scribus\scribus-1.7.x-svn\Scribus\scribus\plugins",
        "$env:USERPROFILE\Downloads\scribus-1.7.x-svn\Scribus\scribus\plugins"
    )
    
    foreach ($path in $possiblePaths) {
        if (Test-Path (Join-Path $path "scplugin.h")) {
            $scribusInclude = $path
            break
        }
    }
}

if (-not $scribusInclude) {
    Write-Host "  FEHLER: Scribus-Header nicht gefunden!" -ForegroundColor Red
    Write-Host "  Bitte gib den Pfad zum Scribus-Quellcode an:" -ForegroundColor Yellow
    Write-Host "  .\build_plugin.ps1 -ScribusSourcePath 'C:\Path\To\Scribus\Source'" -ForegroundColor White
    Write-Host "`nOder lade den Scribus-Quellcode herunter:" -ForegroundColor Yellow
    Write-Host "  https://www.scribus.net/downloads/source/" -ForegroundColor White
    exit 1
}

Write-Host "  Scribus-Header gefunden: $scribusInclude" -ForegroundColor Green

# 3. Finde Qt
Write-Host "`n3. Finde Qt5..." -ForegroundColor Yellow
$qtPath = ""

if ($QtPath) {
    if (Test-Path (Join-Path $QtPath "bin\qmake.exe")) {
        $qtPath = $QtPath
    }
}

if (-not $qtPath) {
    $possibleQtPaths = @(
        "C:\Qt\5.15.2\msvc2019_64",
        "C:\Qt\5.15.2\msvc2022_64",
        "C:\Qt\6.5.0\msvc2019_64",
        "C:\Program Files\Qt\5.15.2\msvc2019_64"
    )
    
    foreach ($path in $possibleQtPaths) {
        if (Test-Path (Join-Path $path "bin\qmake.exe")) {
            $qtPath = $path
            break
        }
    }
}

if (-not $qtPath) {
    Write-Host "  FEHLER: Qt5 nicht gefunden!" -ForegroundColor Red
    Write-Host "  Bitte gib den Qt-Pfad an:" -ForegroundColor Yellow
    Write-Host "  .\build_plugin.ps1 -QtPath 'C:\Qt\5.15.2\msvc2019_64'" -ForegroundColor White
    exit 1
}

Write-Host "  Qt5 gefunden: $qtPath" -ForegroundColor Green

# 4. Erstelle Build-Verzeichnis
Write-Host "`n4. Erstelle Build-Verzeichnis..." -ForegroundColor Yellow
$buildDir = Join-Path $PSScriptRoot "build"
if (Test-Path $buildDir) {
    Remove-Item $buildDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null
Write-Host "  Build-Verzeichnis: $buildDir" -ForegroundColor Green

# 5. Konfiguriere CMake
Write-Host "`n5. Konfiguriere CMake..." -ForegroundColor Yellow
$cmakeArgs = @(
    "-S", $PSScriptRoot,
    "-B", $buildDir,
    "-DSCRIBUS_INCLUDE_DIR=$scribusInclude",
    "-DCMAKE_PREFIX_PATH=$qtPath",
    "-DCMAKE_INSTALL_PREFIX=C:\Program Files\Scribus 1.7.1",
    "-DCMAKE_BUILD_TYPE=$BuildType"
)

if ($cmakeExe) {
    & $cmakeExe @cmakeArgs
} else {
    & cmake @cmakeArgs
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FEHLER: CMake-Konfiguration fehlgeschlagen!" -ForegroundColor Red
    exit 1
}
Write-Host "  CMake konfiguriert" -ForegroundColor Green

# 6. Build
Write-Host "`n6. Kompiliere Plugin..." -ForegroundColor Yellow
if ($cmakeExe) {
    & $cmakeExe --build $buildDir --config $BuildType
} else {
    & cmake --build $buildDir --config $BuildType
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FEHLER: Kompilierung fehlgeschlagen!" -ForegroundColor Red
    exit 1
}
Write-Host "  Plugin kompiliert" -ForegroundColor Green

# 7. Finde erstellte DLL
Write-Host "`n7. Suche erstellte DLL..." -ForegroundColor Yellow
$dllPath = Get-ChildItem $buildDir -Filter "gamma_dashboard.dll" -Recurse | Select-Object -First 1
if ($dllPath) {
    Write-Host "  DLL gefunden: $($dllPath.FullName)" -ForegroundColor Green
    Write-Host "`n=== Build erfolgreich! ===" -ForegroundColor Green
    Write-Host "`nNächste Schritte:" -ForegroundColor Cyan
    Write-Host "  1. Kopiere die DLL nach:" -ForegroundColor White
    Write-Host "     C:\Program Files\Scribus 1.7.1\lib\scribus\plugins\" -ForegroundColor Yellow
    Write-Host "  2. Starte Scribus neu" -ForegroundColor White
    Write-Host "  3. Plugin sollte unter 'Extras → Gamma Dashboard' erscheinen" -ForegroundColor White
} else {
    Write-Host "  WARNUNG: DLL nicht gefunden!" -ForegroundColor Yellow
}

