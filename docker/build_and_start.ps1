# Docker Build und Start Script
# Führt alle Builds aus und startet die Services

$ErrorActionPreference = "Stop"

Write-Host "=== Docker Build und Start für SLA Pipeline ===" -ForegroundColor Cyan
Write-Host ""

# Prüfe Docker
Write-Host "Prüfe Docker..." -ForegroundColor Yellow
docker --version | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Docker ist nicht verfügbar!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Docker gefunden" -ForegroundColor Green
Write-Host ""

# Finde Skript-Verzeichnis (docker-Verzeichnis)
$scriptDir = $PSScriptRoot
if (-not $scriptDir) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

Write-Host "Arbeitsverzeichnis: $scriptDir" -ForegroundColor Cyan
Set-Location $scriptDir

# Prüfe docker-compose.yml
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "FEHLER: docker-compose.yml nicht gefunden!" -ForegroundColor Red
    exit 1
}

# Build alle Services
Write-Host "=== Building alle Services ===" -ForegroundColor Cyan
docker compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Build fehlgeschlagen!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Alle Services gebaut" -ForegroundColor Green
Write-Host ""

# Zeige Images
Write-Host "=== Docker Images ===" -ForegroundColor Cyan
docker images | Select-String "sla-pipeline"
Write-Host ""

# Frage ob Services gestartet werden sollen
$start = Read-Host "Services starten? (j/n)"
if ($start -eq "j" -or $start -eq "J" -or $start -eq "y" -or $start -eq "Y") {
    Write-Host "`n=== Starte Services ===" -ForegroundColor Cyan
    docker compose up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FEHLER: Services konnten nicht gestartet werden!" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Services gestartet" -ForegroundColor Green
    Write-Host ""
    Write-Host "Status:" -ForegroundColor Yellow
    docker compose ps
    Write-Host ""
    Write-Host "Logs ansehen: docker compose logs -f" -ForegroundColor White
} else {
    Write-Host "`nServices nicht gestartet. Zum Starten ausführen:" -ForegroundColor Yellow
    Write-Host "  docker compose up -d" -ForegroundColor White
}

Write-Host ""

