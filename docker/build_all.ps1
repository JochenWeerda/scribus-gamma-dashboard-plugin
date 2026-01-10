# Build all Docker Images für SLA Pipeline
# PowerShell Script für Windows

Write-Host "=== SLA Pipeline Docker Build ===" -ForegroundColor Cyan
Write-Host ""

# Prüfe Docker
Write-Host "Prüfe Docker..." -ForegroundColor Yellow
$dockerVersion = docker --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Docker ist nicht verfügbar!" -ForegroundColor Red
    Write-Host "Bitte starte Docker Desktop und versuche es erneut." -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Docker gefunden: $dockerVersion" -ForegroundColor Green
Write-Host ""

# Wechsle ins docker-Verzeichnis
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $scriptPath

Write-Host "Arbeitsverzeichnis: $(Get-Location)" -ForegroundColor Cyan
Write-Host ""

# Build API Gateway
Write-Host "=== Building API Gateway ===" -ForegroundColor Cyan
Set-Location $projectRoot
docker build -f docker/api/Dockerfile -t sla-pipeline-api:latest .
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: API Gateway Build fehlgeschlagen!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ API Gateway gebaut" -ForegroundColor Green
Write-Host ""

# Build Sidecar-MCP
Write-Host "=== Building Sidecar-MCP ===" -ForegroundColor Cyan
Set-Location $projectRoot
docker build -f docker/sidecar/Dockerfile -t sla-pipeline-sidecar:latest .
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Sidecar-MCP Build fehlgeschlagen!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Sidecar-MCP gebaut" -ForegroundColor Green
Write-Host ""

# Build Worker-Scribus
Write-Host "=== Building Worker-Scribus ===" -ForegroundColor Cyan
Set-Location $projectRoot
docker build -f docker/worker/Dockerfile -t sla-pipeline-worker:latest .
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Worker-Scribus Build fehlgeschlagen!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Worker-Scribus gebaut" -ForegroundColor Green
Write-Host ""

# Zusammenfassung
Write-Host "=== Build Zusammenfassung ===" -ForegroundColor Cyan
Write-Host ""
docker images | Select-String "sla-pipeline"
Write-Host ""
Write-Host "✓ Alle Images erfolgreich gebaut!" -ForegroundColor Green
Write-Host ""
Write-Host "Nächste Schritte:" -ForegroundColor Yellow
Write-Host "  1. Starte Services: docker compose up -d" -ForegroundColor White
Write-Host "  2. Prüfe Status: docker compose ps" -ForegroundColor White
Write-Host "  3. Logs ansehen: docker compose logs -f" -ForegroundColor White
Write-Host ""
