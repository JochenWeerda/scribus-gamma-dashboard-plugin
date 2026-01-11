param(
  [switch]$Apply
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$archiveRoot = Join-Path $repoRoot "docs\\archive\\root_md"
New-Item -ItemType Directory -Force $archiveRoot | Out-Null

$keep = @(
  "README.md",
  "LICENSE",
  "INSTALLATION.md",
  "PROJECT_STRUCTURE.md",
  "requirements.txt",
  "requirements-dev.txt"
)

$candidates = Get-ChildItem -Path $repoRoot -File -Filter "*.md" |
  Where-Object { $keep -notcontains $_.Name }

Write-Host ("Found {0} root .md candidates." -f $candidates.Count)
if (-not $Apply) {
  Write-Host "Dry-run. Re-run with -Apply to move them into docs/archive/root_md (ignored by git)."
  $candidates | Select-Object Name,Length,LastWriteTime
  exit 0
}

foreach ($f in $candidates) {
  $dest = Join-Path $archiveRoot $f.Name
  Move-Item -Force $f.FullName $dest
}

Write-Host "Moved root markdown notes into docs/archive/root_md."

