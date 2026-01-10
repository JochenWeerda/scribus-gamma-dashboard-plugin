param(
    [string]$ProjectRoot = ".",
    [switch]$CreateProjectStructure,
    [string]$ZipSource = "",
    [string]$PptxSource = ""
)

$ErrorActionPreference = "Stop"

Write-Output "Gamma Scribus Pack - Install"

if ($CreateProjectStructure) {
    $proj = Resolve-Path -Path $ProjectRoot
    $gamma = Join-Path $proj "gamma_exports"
    $pptx = Join-Path $proj "pptx"
    New-Item -ItemType Directory -Force -Path $gamma | Out-Null
    New-Item -ItemType Directory -Force -Path $pptx | Out-Null
    Write-Output "Project structure created under: $proj"
}

if ($ZipSource) {
    $proj = Resolve-Path -Path $ProjectRoot
    $gamma = Join-Path $proj "gamma_exports"
    New-Item -ItemType Directory -Force -Path $gamma | Out-Null
    if (Test-Path $ZipSource) {
        Get-ChildItem -Path $ZipSource -Filter *.zip | Copy-Item -Destination $gamma -Force
        Write-Output "Copied ZIPs from: $ZipSource"
    } else {
        Write-Output "ZipSource not found: $ZipSource"
    }
}

if ($PptxSource) {
    $proj = Resolve-Path -Path $ProjectRoot
    $pptx = Join-Path $proj "pptx"
    New-Item -ItemType Directory -Force -Path $pptx | Out-Null
    if (Test-Path $PptxSource) {
        Get-ChildItem -Path $PptxSource -Filter *.pptx | Copy-Item -Destination $pptx -Force
        Write-Output "Copied PPTX from: $PptxSource"
    } else {
        Write-Output "PptxSource not found: $PptxSource"
    }
}

if (-not (Test-Path ".\\.venv")) {
    py -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Write-Output "Install done."
