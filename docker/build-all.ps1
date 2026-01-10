# Docker Build Script für alle Services (PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "=== Docker Build für SLA Pipeline ===" -ForegroundColor Cyan
Write-Host ""

# Prüfe ob Docker läuft
try {
    docker info | Out-Null
    Write-Host "✅ Docker läuft" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker läuft nicht. Bitte starte Docker Desktop." -ForegroundColor Red
    exit 1
}

Write-Host ""

# Wechsle ins docker-Verzeichnis
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "📁 Projekt-Root: $ProjectRoot" -ForegroundColor Cyan
Write-Host ""

Set-Location $ScriptDir

# Build API Gateway
Write-Host "🔨 Baue API Gateway..." -ForegroundColor Yellow
docker build `
    -f api/Dockerfile `
    -t sla-pipeline-api:latest `
    --build-arg BUILDKIT_INLINE_CACHE=1 `
    $ProjectRoot
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ API Gateway Build fehlgeschlagen" -ForegroundColor Red
    exit 1
}
Write-Host "✅ API Gateway gebaut" -ForegroundColor Green
Write-Host ""

# Build Sidecar-MCP
Write-Host "🔨 Baue Sidecar-MCP..." -ForegroundColor Yellow
docker build `
    -f sidecar/Dockerfile `
    -t sla-pipeline-sidecar:latest `
    --build-arg BUILDKIT_INLINE_CACHE=1 `
    $ProjectRoot
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Sidecar-MCP Build fehlgeschlagen" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Sidecar-MCP gebaut" -ForegroundColor Green
Write-Host ""

# Build Worker-Scribus
Write-Host "🔨 Baue Worker-Scribus..." -ForegroundColor Yellow
docker build `
    -f worker/Dockerfile `
    -t sla-pipeline-worker:latest `
    --build-arg BUILDKIT_INLINE_CACHE=1 `
    $ProjectRoot
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Worker-Scribus Build fehlgeschlagen" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Worker-Scribus gebaut" -ForegroundColor Green
Write-Host ""

Write-Host "=== ✅ Alle Docker Images erfolgreich gebaut ===" -ForegroundColor Green
Write-Host ""
Write-Host "Nächste Schritte:" -ForegroundColor Cyan
Write-Host "  1. Starte Docker Compose: docker compose up -d"
Write-Host "  2. Prüfe Status: docker compose ps"
Write-Host "  3. Logs anzeigen: docker compose logs -f"

