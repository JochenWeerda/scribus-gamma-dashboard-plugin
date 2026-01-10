# Docker Build Script für alle Services
# Erstellt Docker-Images für API-Gateway, Sidecar-MCP, Worker-Scribus
# PowerShell Script für Windows

param(
    [switch]$NoCache,
    [string]$Tag = "latest"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Docker Build Script ===" -ForegroundColor Cyan
Write-Host "Tag: $Tag" -ForegroundColor Yellow
if ($NoCache) {
    Write-Host "No-Cache Build" -ForegroundColor Yellow
}

# Prüfe Docker
Write-Host "`nPrüfe Docker..." -ForegroundColor Yellow
$dockerVersion = docker --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Docker ist nicht verfügbar!" -ForegroundColor Red
    Write-Host "Bitte starte Docker Desktop und versuche es erneut." -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Docker gefunden: $dockerVersion" -ForegroundColor Green

# Finde Projektroot (ein Verzeichnis nach oben vom docker-Verzeichnis)
$scriptPath = $PSScriptRoot
if (-not $scriptPath) {
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$projectRoot = Split-Path -Parent $scriptPath

Write-Host "`nArbeitsverzeichnis: $projectRoot" -ForegroundColor Cyan
Set-Location $projectRoot

# Prüfe ob Dockerfiles existieren
$dockerfiles = @(
    "docker/api/Dockerfile",
    "docker/sidecar/Dockerfile",
    "docker/worker/Dockerfile"
)

foreach ($dockerfile in $dockerfiles) {
    if (-not (Test-Path $dockerfile)) {
        Write-Host "FEHLER: Dockerfile nicht gefunden: $dockerfile" -ForegroundColor Red
        exit 1
    }
}

# Build API Gateway
Write-Host "`n=== Building API Gateway ===" -ForegroundColor Cyan
$buildArgs = @("-f", "docker/api/Dockerfile", "-t", "sla-pipeline-api:$Tag", ".")
if ($NoCache) {
    $buildArgs += "--no-cache"
}
docker build @buildArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: API Gateway Build fehlgeschlagen!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ API Gateway gebaut" -ForegroundColor Green

# Build Sidecar-MCP
Write-Host "`n=== Building Sidecar-MCP ===" -ForegroundColor Cyan
$buildArgs = @("-f", "docker/sidecar/Dockerfile", "-t", "sla-pipeline-sidecar:$Tag", ".")
if ($NoCache) {
    $buildArgs += "--no-cache"
}
docker build @buildArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Sidecar-MCP Build fehlgeschlagen!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Sidecar-MCP gebaut" -ForegroundColor Green

# Build Worker-Scribus
Write-Host "`n=== Building Worker-Scribus ===" -ForegroundColor Cyan
$buildArgs = @("-f", "docker/worker/Dockerfile", "-t", "sla-pipeline-worker:$Tag", ".")
if ($NoCache) {
    $buildArgs += "--no-cache"
}
docker build @buildArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Worker-Scribus Build fehlgeschlagen!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Worker-Scribus gebaut" -ForegroundColor Green

# Zusammenfassung
Write-Host "`n=== Build Zusammenfassung ===" -ForegroundColor Cyan
Write-Host ""
docker images | Select-String "sla-pipeline"
Write-Host ""
Write-Host "✓ Alle Images erfolgreich gebaut!" -ForegroundColor Green
Write-Host ""
Write-Host "Nächste Schritte:" -ForegroundColor Yellow
Write-Host "  1. Wechsle ins docker-Verzeichnis: cd docker" -ForegroundColor White
Write-Host "  2. Starte Services: docker compose up -d" -ForegroundColor White
Write-Host "  3. Prüfe Status: docker compose ps" -ForegroundColor White
Write-Host "  4. Logs ansehen: docker compose logs -f" -ForegroundColor White
Write-Host ""

