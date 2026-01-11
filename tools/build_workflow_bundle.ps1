param(
  [string]$ExtractedRoot = "media_pool/pptx",
  [string]$Out = "temp_analysis/workflow_bundle_linux.zip",
  [string]$GammaZipDir = "",
  [string]$ProjectInit = "",
  [string[]]$Pptx = @()
)

$scriptPath = Join-Path $PSScriptRoot "build_workflow_bundle.py"
$argsList = @(
  $scriptPath,
  "--extracted-root", $ExtractedRoot,
  "--out", $Out
)

if ($GammaZipDir -and (Test-Path $GammaZipDir)) {
  $argsList += @("--gamma-zip-dir", $GammaZipDir)
}

if ($ProjectInit -and (Test-Path $ProjectInit)) {
  $argsList += @("--project-init", $ProjectInit)
}

foreach ($n in $Pptx) {
  if ($n) { $argsList += @("--pptx", $n) }
}

python @argsList
