param(
    [string]$LibsRoot = "C:\\Development\\scribus-1.7.x-libs-msvc",
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

Write-Host "=== Build Scribus Libs (MSVC 2022, x64) ===" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $LibsRoot)) {
    Write-Host "ERROR: Libs root not found: $LibsRoot" -ForegroundColor Red
    exit 1
}

$sln = Join-Path $LibsRoot "scribus-libs-msvc2022.sln"
if (-not (Test-Path $sln)) {
    Write-Host "ERROR: Solution not found: $sln" -ForegroundColor Red
    exit 1
}

# Locate VS installation (vswhere preferred).
$vswhere = "C:\\Program Files (x86)\\Microsoft Visual Studio\\Installer\\vswhere.exe"
$vsPath = ""
if (Test-Path $vswhere) {
    $vsPath = & $vswhere -latest -products * -requires Microsoft.Component.MSBuild -property installationPath
}
if (-not $vsPath) {
    $candidates = @(
        "C:\\Program Files\\Microsoft Visual Studio\\2022\\Community",
        "C:\\Program Files\\Microsoft Visual Studio\\2022\\Professional",
        "C:\\Program Files\\Microsoft Visual Studio\\2022\\Enterprise",
        "C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools"
    )
    foreach ($cand in $candidates) {
        if (Test-Path $cand) {
            $vsPath = $cand
            break
        }
    }
}
if (-not $vsPath) {
    Write-Host "ERROR: Visual Studio 2022 not found." -ForegroundColor Red
    exit 1
}

$vcvarsall = Join-Path $vsPath "VC\\Auxiliary\\Build\\vcvarsall.bat"
$msbuild = Join-Path $vsPath "MSBuild\\Current\\Bin\\MSBuild.exe"
if (-not (Test-Path $vcvarsall)) {
    Write-Host "ERROR: vcvarsall.bat not found: $vcvarsall" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $msbuild)) {
    Write-Host "ERROR: MSBuild not found: $msbuild" -ForegroundColor Red
    exit 1
}

Write-Host "VS: $vsPath" -ForegroundColor Green
Write-Host "MSBuild: $msbuild" -ForegroundColor Green
Write-Host ""

$targets = "Build"
if ($Clean) {
    $targets = "Clean;Build"
}

# Use cmd.exe so vcvarsall can set env for msbuild.
$cmd = '"' + $vcvarsall + '" x64 && "' + $msbuild + '" "' + $sln + '" /t:' + $targets + ' /p:Configuration=Release /p:Platform=x64 /p:PlatformToolset=v143 /m'
Write-Host "Command:" -ForegroundColor Yellow
Write-Host "  $cmd"
Write-Host ""

cmd /c $cmd
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Libs build failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "OK: Libs build finished." -ForegroundColor Green
Write-Host ""
Write-Host "Checking for key libs (podofo/poppler)..." -ForegroundColor Yellow

$podofoLibs = Get-ChildItem -Path $LibsRoot -Recurse -Filter "*podofo*.lib" -ErrorAction SilentlyContinue | Select-Object -First 5
$popplerLibs = Get-ChildItem -Path $LibsRoot -Recurse -Filter "*poppler*.lib" -ErrorAction SilentlyContinue | Select-Object -First 5

if ($podofoLibs) {
    Write-Host "Found podofo libs:" -ForegroundColor Green
    $podofoLibs | ForEach-Object { Write-Host "  $($_.FullName)" }
} else {
    Write-Host "WARN: No podofo libs found yet." -ForegroundColor Yellow
}

if ($popplerLibs) {
    Write-Host "Found poppler libs:" -ForegroundColor Green
    $popplerLibs | ForEach-Object { Write-Host "  $($_.FullName)" }
} else {
    Write-Host "WARN: No poppler libs found yet." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next:" -ForegroundColor Cyan
Write-Host "  .\\build_scribus.ps1 -ScribusLibsDir `\"$LibsRoot`\"" -ForegroundColor White
