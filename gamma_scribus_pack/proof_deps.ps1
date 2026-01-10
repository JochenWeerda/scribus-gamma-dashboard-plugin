param(
    [string]$VenvPython = ".\\.venv\\Scripts\\python.exe"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $VenvPython)) {
    Write-Error "Python not found: $VenvPython"
}

& $VenvPython - << 'PY'
import cv2, numpy, PIL, pptx
print("OK: deps loaded")
PY
