# Docker Desktop Start Script
# Verwendung: .\start_docker.ps1

Write-Host "=== Docker Desktop Start Script ===" -ForegroundColor Green
Write-Host ""

# Prüfe ob Docker Desktop bereits läuft
Write-Host "Prüfe Docker-Status..." -ForegroundColor Yellow
$dockerRunning = docker info 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Docker läuft bereits!" -ForegroundColor Green
    docker version
    exit 0
}

Write-Host "Docker läuft nicht. Starte Docker Desktop..." -ForegroundColor Yellow

# Mögliche Docker Desktop-Pfade
$dockerPaths = @(
    "C:\Program Files\Docker\Docker\Docker Desktop.exe",
    "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe",
    "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe",
    "$env:LOCALAPPDATA\Docker\Docker Desktop.exe"
)

$dockerPath = $null
foreach ($path in $dockerPaths) {
    if (Test-Path $path) {
        $dockerPath = $path
        break
    }
}

if (-not $dockerPath) {
    Write-Host "Fehler: Docker Desktop nicht gefunden!" -ForegroundColor Red
    Write-Host "Bitte installiere Docker Desktop oder starte es manuell." -ForegroundColor Yellow
    exit 1
}

Write-Host "Starte Docker Desktop: $dockerPath" -ForegroundColor Cyan
Start-Process $dockerPath

Write-Host "Warte auf Docker Desktop Start..." -ForegroundColor Yellow
$maxWait = 60  # Maximal 60 Sekunden warten
$waited = 0
$interval = 2  # Alle 2 Sekunden prüfen

while ($waited -lt $maxWait) {
    Start-Sleep -Seconds $interval
    $waited += $interval
    
    $dockerRunning = docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Docker Desktop ist bereit!" -ForegroundColor Green
        docker version
        exit 0
    }
    
    Write-Host "  Warte... ($waited/$maxWait Sekunden)" -ForegroundColor Gray
}

Write-Host "Timeout: Docker Desktop startet zu langsam." -ForegroundColor Yellow
Write-Host "Bitte prüfe Docker Desktop manuell." -ForegroundColor Yellow
exit 1

