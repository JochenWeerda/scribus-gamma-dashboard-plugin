# Docker Compose Start Script (PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "=== Docker Compose Start für SLA Pipeline ===" -ForegroundColor Cyan
Write-Host ""

# Prüfe ob Docker läuft
try {
    docker info | Out-Null
    Write-Host "✅ Docker läuft" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker läuft nicht. Bitte starte Docker Desktop." -ForegroundColor Red
    Write-Host ""
    Write-Host "Tipp: Öffne Docker Desktop und warte bis es vollständig gestartet ist." -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Wechsle ins docker-Verzeichnis
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Prüfe ob docker-compose.yml existiert
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "❌ docker-compose.yml nicht gefunden in $ScriptDir" -ForegroundColor Red
    exit 1
}

Write-Host "📁 Starte Services aus: $ScriptDir" -ForegroundColor Cyan
Write-Host ""

# Starte Docker Compose
Write-Host "🚀 Starte Docker Compose..." -ForegroundColor Yellow
docker compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker Compose Start fehlgeschlagen" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Services gestartet" -ForegroundColor Green
Write-Host ""

# Warte kurz
Start-Sleep -Seconds 2

# Zeige Status
Write-Host "📊 Service-Status:" -ForegroundColor Cyan
docker compose ps

Write-Host ""
Write-Host "=== ✅ Setup abgeschlossen ===" -ForegroundColor Green
Write-Host ""
Write-Host "Nützliche Befehle:" -ForegroundColor Cyan
Write-Host "  Status prüfen:     docker compose ps"
Write-Host "  Logs anzeigen:     docker compose logs -f"
Write-Host "  Services stoppen:  docker compose down"
Write-Host ""
Write-Host "Services:" -ForegroundColor Cyan
Write-Host "  API Gateway:       http://localhost:8000"
Write-Host "  API Docs:          http://localhost:8000/docs"
Write-Host "  MinIO Console:     http://localhost:9001"
Write-Host "  PostgreSQL:        localhost:5432"

