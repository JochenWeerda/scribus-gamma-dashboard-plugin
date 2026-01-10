# Quick Start: Docker Builds

**Status:** Docker Desktop läuft ✅

## Builds durchführen

### Option 1: Docker Compose Build (Empfohlen)

Öffne ein Terminal im **Projekt-Root-Verzeichnis** und führe aus:

```powershell
cd docker
docker compose build
```

Oder von jedem Verzeichnis:

```powershell
docker compose -f docker/docker-compose.yml build
```

### Option 2: Einzelne Builds

Von **Projekt-Root-Verzeichnis**:

```powershell
# API Gateway
docker build -f docker/api/Dockerfile -t sla-pipeline-api:latest .

# Sidecar-MCP
docker build -f docker/sidecar/Dockerfile -t sla-pipeline-sidecar:latest .

# Worker-Scribus
docker build -f docker/worker/Dockerfile -t sla-pipeline-worker:latest .
```

### Option 3: Build-Script (PowerShell)

Von **docker-Verzeichnis**:

```powershell
.\build.ps1
```

## Services starten

Nach erfolgreichen Builds:

```powershell
cd docker
docker compose up -d
```

## Status prüfen

```powershell
docker compose ps
docker images | Select-String "sla-pipeline"
```

---

*Hinweis: Stelle sicher, dass du im Projekt-Root-Verzeichnis bist, bevor du die Build-Befehle ausführst.*

