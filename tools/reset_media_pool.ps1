param(
    [string]$RepoRoot = ""
)

$ErrorActionPreference = "Stop"

if (-not $RepoRoot) {
    $RepoRoot = Split-Path -Parent $PSScriptRoot
}

$mediaPool = Join-Path $RepoRoot "media_pool\\pptx"
$backupRoot = Join-Path $RepoRoot "backups"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $backupRoot ("media_pool_pptx_" + $stamp)

if (Test-Path $mediaPool) {
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
    Move-Item -Path $mediaPool -Destination $backupDir -Force
}

New-Item -ItemType Directory -Force -Path $mediaPool | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $mediaPool "images") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $mediaPool "json") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $mediaPool "tags") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $mediaPool "renders\\slides") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $mediaPool "renders\\cards") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $mediaPool "renders\\debug") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $mediaPool "renders\\masks") | Out-Null

Write-Output ("Reset media pool at: " + $mediaPool)
Write-Output ("Backup stored at: " + $backupDir)
