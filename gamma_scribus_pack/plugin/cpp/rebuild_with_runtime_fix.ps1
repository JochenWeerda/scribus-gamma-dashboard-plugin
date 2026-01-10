# Rebuild Plugin mit Runtime-Fix (/MD)
# Dieses Script generiert das CMake-Projekt neu mit korrekter MSVC Runtime-Library

param(
    [string]$BuildType = "Release",
    [string]$Generator = "Visual Studio 17 2022",
    [string]$ScribusLibDir = ""
)

$ErrorActionPreference = "Stop"

Write-Host "=== Rebuild Plugin mit Runtime-Fix (/MD) ===" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$buildDir = Join-Path $scriptDir "build"

# Finde CMake
$cmakeExe = $null
$cmakePaths = @(
    "C:\Development\bin\cmake.exe",  # Bekannter Pfad aus Suche
    "C:\Development\share\cmake-4.2\bin\cmake.exe",
    "C:\Development\cmake-4.2.1\bin\cmake.exe",
    "C:\Program Files\CMake\bin\cmake.exe",
    "C:\Program Files (x86)\CMake\bin\cmake.exe",
    "cmake.exe"
)

foreach ($path in $cmakePaths) {
    if (Test-Path $path) {
        $cmakeExe = $path
        break
    }
}

# Falls nicht in Standard-Pfaden: Suche rekursiv in C:\Development
if (-not $cmakeExe) {
    $found = Get-ChildItem -Path "C:\Development" -Filter "cmake.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) {
        $cmakeExe = $found.FullName
    }
}

# Falls immer noch nicht gefunden: Versuche PATH
if (-not $cmakeExe) {
    $cmakeInPath = Get-Command cmake.exe -ErrorAction SilentlyContinue
    if ($cmakeInPath) {
        $cmakeExe = $cmakeInPath.Source
    }
}

if (-not $cmakeExe) {
    Write-Host "❌ CMake nicht gefunden!" -ForegroundColor Red
    Write-Host "Bitte CMake installieren oder Pfad in Script anpassen" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ CMake gefunden: $cmakeExe" -ForegroundColor Green
Write-Host ""

# Lösche alte CMake-Cache
if (Test-Path $buildDir) {
    Write-Host "Lösche alte CMake-Cache..." -ForegroundColor Yellow
    Remove-Item -Path (Join-Path $buildDir "CMakeCache.txt") -ErrorAction SilentlyContinue
    Remove-Item -Path (Join-Path $buildDir "CMakeFiles") -Recurse -ErrorAction SilentlyContinue -Force
}

# Erstelle Build-Verzeichnis
if (-not (Test-Path $buildDir)) {
    New-Item -ItemType Directory -Path $buildDir | Out-Null
}

Write-Host "Generiere CMake-Projekt mit Runtime-Fix..." -ForegroundColor Yellow
Write-Host "  Generator: $Generator" -ForegroundColor Gray
Write-Host "  Build-Type: $BuildType" -ForegroundColor Gray
Write-Host "  Runtime: MultiThreadedDLL (/MD)" -ForegroundColor Gray
Write-Host ""

# Finde Scribus-Header
$scribusHeaderDir = $null
$headerPaths = @(
    "C:\Development\scribus-1.7\scribus",
    "C:\Development\scribus-1.7\scribus\plugins",
    "C:\Development\scribus-1.7\Scribus\scribus",
    "C:\Development\scribus-1.7\Scribus\scribus\plugins",
    "F:\Scribus for Windows\scribus-1.7.x-svn\Scribus\scribus",
    "F:\Scribus for Windows\scribus-1.7.x-svn\Scribus\scribus\plugins"
)

foreach ($path in $headerPaths) {
    if (Test-Path "$path\scplugin.h") {
        $scribusHeaderDir = $path
        Write-Host "  Scribus-Header: $scribusHeaderDir" -ForegroundColor Gray
        break
    }
}

# Falls nicht gefunden: Suche rekursiv
if (-not $scribusHeaderDir) {
    $header = Get-ChildItem -Path "C:\Development" -Filter "scplugin.h" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($header) {
        $scribusHeaderDir = $header.DirectoryName
        Write-Host "  Scribus-Header (gefunden): $scribusHeaderDir" -ForegroundColor Gray
    }
}

if (-not $scribusHeaderDir) {
    Write-Host "⚠️  Warnung: Scribus-Header nicht gefunden - CMake wird sie suchen müssen" -ForegroundColor Yellow
}

Write-Host ""

# Finde Scribus Library-Verzeichnis (falls nicht angegeben)
if ([string]::IsNullOrEmpty($ScribusLibDir)) {
    $possibleLibDirs = @(
        "C:\Development\scribus-1.7\build\Release",
        "C:\Development\scribus-1.7\build\Debug",
        "C:\Development\scribus-1.7\build",
        "C:\Development\scribus-1.7\build\lib",
        "F:\Scribus for Windows\scribus-1.7.x-svn\build\Release",
        "F:\Scribus for Windows\scribus-1.7.x-svn\build\Debug"
    )
    
    foreach ($dir in $possibleLibDirs) {
        if (Test-Path "$dir\scribuscore.lib") {
            $ScribusLibDir = $dir
            Write-Host "  Scribus Lib-Dir (gefunden): $ScribusLibDir" -ForegroundColor Gray
            break
        }
    }
    
    # Falls nicht gefunden: Suche rekursiv
    if ([string]::IsNullOrEmpty($ScribusLibDir)) {
        $scribuscoreLib = Get-ChildItem -Path "C:\Development\scribus-1.7" -Filter "scribuscore.lib" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($scribuscoreLib) {
            $ScribusLibDir = $scribuscoreLib.DirectoryName
            Write-Host "  Scribus Lib-Dir (rekursiv gefunden): $ScribusLibDir" -ForegroundColor Gray
        }
    }
}

if ([string]::IsNullOrEmpty($ScribusLibDir)) {
    Write-Host "  ⚠️  Scribus Lib-Dir nicht gefunden - Build wird fehlschlagen!" -ForegroundColor Yellow
    Write-Host "     Bitte -ScribusLibDir angeben oder Scribus bauen" -ForegroundColor Yellow
} else {
    Write-Host "  ✅ Scribus Lib-Dir: $ScribusLibDir" -ForegroundColor Green
}

Write-Host ""

# CMake konfigurieren mit expliziter Runtime-Library
$cmakeArgs = @(
    "-S", $scriptDir,
    "-B", $buildDir,
    "-G", $Generator,
    "-A", "x64",
    "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL",
    "-DCMAKE_BUILD_TYPE=$BuildType",
    "-DCMAKE_PREFIX_PATH=C:\Qt\6.5.3\msvc2019_64"
)

if ($scribusHeaderDir) {
    $cmakeArgs += "-DSCRIBUS_INCLUDE_DIR=$scribusHeaderDir"
}

if (-not [string]::IsNullOrEmpty($ScribusLibDir)) {
    $cmakeArgs += "-DSCRIBUS_LIB_DIR=$ScribusLibDir"
}

& $cmakeExe $cmakeArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ CMake-Konfiguration fehlgeschlagen!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ CMake-Projekt erfolgreich generiert!" -ForegroundColor Green
Write-Host ""
Write-Host "Kompiliere Plugin..." -ForegroundColor Yellow

# Kompiliere mit MSBuild
$msbuildExe = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe"
if (-not (Test-Path $msbuildExe)) {
    Write-Host "❌ MSBuild nicht gefunden!" -ForegroundColor Red
    Write-Host "Bitte Visual Studio Build Tools installieren" -ForegroundColor Yellow
    exit 1
}

& $msbuildExe `
    (Join-Path $buildDir "gamma_dashboard_plugin.vcxproj") `
    /p:Configuration=$BuildType `
    /p:Platform=x64 `
    /t:Build `
    /v:minimal

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Kompilierung fehlgeschlagen!" -ForegroundColor Red
    exit 1
}

$dllPath = Join-Path $buildDir "$BuildType\gamma_dashboard.dll"
if (Test-Path $dllPath) {
    $dllInfo = Get-Item $dllPath
    Write-Host ""
    Write-Host "✅ Plugin erfolgreich kompiliert!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Details:" -ForegroundColor Cyan
    Write-Host "  Datei: $($dllInfo.Name)" -ForegroundColor White
    Write-Host "  Größe: $([math]::Round($dllInfo.Length / 1KB, 1)) KB" -ForegroundColor White
    Write-Host "  Pfad: $($dllInfo.FullName)" -ForegroundColor White
    Write-Host ""
    Write-Host "Nächste Schritte:" -ForegroundColor Yellow
    Write-Host "  1. Plugin installieren:" -ForegroundColor White
    Write-Host "     .\INSTALL_SYSTEM_PLUGIN.ps1" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  2. Runtime-Dependencies prüfen:" -ForegroundColor White
    Write-Host "     dumpbin /DEPENDENTS `"$dllPath`"" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "❌ DLL nicht gefunden: $dllPath" -ForegroundColor Red
    exit 1
}

