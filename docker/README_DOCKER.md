# Docker Setup für SLA Pipeline

Anleitung zum Erstellen und Starten der Docker-Container.

---

## Voraussetzungen

- Docker Desktop installiert und gestartet
- PowerShell (Windows) oder Bash (Linux/Mac)

---

## Quick Start

### 1. Docker Desktop starten

**Windows:**
- Starte Docker Desktop aus dem Startmenü
- Warte bis Docker bereit ist (Icon in der Taskleiste)

**Prüfen:**
```powershell
docker --version
docker ps
```

### 2. Images bauen

**PowerShell (Windows):**
```powershell
cd docker
.\build_all.ps1
```

**Bash (Linux/Mac):**
```bash
cd docker
chmod +x build_all.sh
./build_all.sh
```

**Oder einzeln:**
```bash
# API Gateway
docker build -f docker/api/Dockerfile -t sla-pipeline-api:latest .

# Sidecar-MCP
docker build -f docker/sidecar/Dockerfile -t sla-pipeline-sidecar:latest .

# Worker-Scribus
docker build -f docker/worker/Dockerfile -t sla-pipeline-worker:latest .
```

### 3. Services starten

```bash
cd docker
docker compose up -d
```

### 4. Status prüfen

```bash
docker compose ps
docker compose logs -f
```

---

## Services

| Service | Port | Beschreibung |
|---------|------|--------------|
| API Gateway | 8000 | FastAPI REST API |
| Sidecar-MCP | 8004 | MCP Service für Digital Twin |
| PostgreSQL | 5432 | Datenbank |
| Redis | 6379 | Queue & Cache |
| MinIO | 9000 | Object Storage (S3) |
| MinIO Console | 9001 | MinIO Web UI |

---

## Docker Compose

### Development

```bash
docker compose up -d
```

### Production

```bash
docker compose -f docker-compose.prod.yml up -d
```

---

## Troubleshooting

### Docker Desktop läuft nicht

1. Starte Docker Desktop
2. Warte bis Status "Running" ist
3. Prüfe: `docker ps`

### Build-Fehler

1. Prüfe Docker Desktop läuft
2. Prüfe verfügbarer Speicherplatz
3. Prüfe Logs: `docker compose logs`

### Port-Konflikte

Falls Ports bereits belegt sind, ändere in `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"  # Statt 8000:8000
```

---

## Nützliche Befehle

```bash
# Alle Services stoppen
docker compose down

# Services neu starten
docker compose restart

# Logs ansehen
docker compose logs -f api-gateway
docker compose logs -f worker-scribus

# In Container gehen
docker compose exec api-gateway /bin/bash

# Images löschen
docker compose down --rmi all

# Volumes löschen (ACHTUNG: Daten gehen verloren!)
docker compose down -v
```

---

*Letzte Aktualisierung: 2025-01-27*
