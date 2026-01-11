param(
    [string]$ScribusRoot = $env:SCRIBUS_SRC_ROOT,
    [string]$SourceDir = $PSScriptRoot,
    [switch]$Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $ScribusRoot) {
    $ScribusRoot = "C:\\Development\\scribus-1.7\\scribus"
}

$targetDir = Join-Path $ScribusRoot "plugins\\gamma_dashboard"

$filesToCopy = @(
    "gamma_dashboard_plugin.cpp",
    "gamma_dashboard_plugin.h",
    "gamma_dashboard_dock.cpp",
    "gamma_dashboard_dock.h",
    "gamma_dashboard_exports.cpp",
    "gamma_api_client.cpp",
    "gamma_api_client.h",
    "gamma_api_settings_dialog.cpp",
    "gamma_api_settings_dialog.h",
    "gamma_figma_browser.cpp",
    "gamma_figma_browser.h",
    "gamma_rag_search_dialog.cpp",
    "gamma_rag_search_dialog.h",
    "gamma_sla_inserter.cpp",
    "gamma_sla_inserter.h",
    "gamma_debug_log.h",
    "CMakeLists.txt"
)

if (-not $Quiet) {
    Write-Host "=== Update Scribus Source Tree ===" -ForegroundColor Cyan
    Write-Host "Quelle: $SourceDir" -ForegroundColor Gray
    Write-Host "Ziel:   $targetDir" -ForegroundColor Gray
    Write-Host ""
}

if (-not (Test-Path $SourceDir)) {
    throw "Source directory not found: $SourceDir"
}

if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
}

$copied = 0
$missing = 0

foreach ($file in $filesToCopy) {
    $src = Join-Path $SourceDir $file
    $dst = Join-Path $targetDir $file

    if (-not (Test-Path $src)) {
        if (-not $Quiet) { Write-Host "  MISSING: $file" -ForegroundColor Yellow }
        $missing++
        continue
    }

    Copy-Item -Force -Path $src -Destination $dst
    if (-not $Quiet) { Write-Host "  OK: $file" -ForegroundColor Green }
    $copied++
}

if (-not $Quiet) {
    Write-Host ""
    Write-Host "=== Fertig ===" -ForegroundColor Green
    Write-Host "Kopiert: $copied" -ForegroundColor Cyan
    if ($missing -gt 0) { Write-Host "Fehlend: $missing" -ForegroundColor Yellow }
}

if ($missing -gt 0) {
    throw "Update incomplete: $missing file(s) missing in $SourceDir"
}

