# Docker Build Status

**Datum:** 2025-01-27
**Status:** Docker Desktop läuft ✅

---

## ✅ Docker Desktop Status

- **Docker Version:** 29.0.1
- **Status:** Running
- **Container laufend:** Mehrere Container aktiv (valeo-neuro-erp, paperless, etc.)

---

## 📦 Docker Images Status

Die SLA Pipeline Images wurden noch nicht gebaut.

**Erwartete Images:**
- `sla-pipeline-api:latest` (API Gateway)
- `sla-pipeline-sidecar:latest` (Sidecar-MCP)
- `sla-pipeline-worker:latest` (Worker-Scribus)

---

## 🚀 Builds durchführen

### Option 1: Docker Compose Build (Empfohlen)

```powershell
# Navigiere zum Projekt-Verzeichnis
cd "C:\Users\Jochen\Documents\Die verborgene Uhr Gottes\Gottes geheimer Zeitcode"

# Wechsle ins docker-Verzeichnis
cd docker

# Builds durchführen
docker compose build
```

### Option 2: Build-Script

```powershell
# Navigiere zum Projekt-Verzeichnis
cd "C:\Users\Jochen\Documents\Die verborgene Uhr Gottes\Gottes geheimer Zeitcode"

# Führe Build-Script aus
.\BUILD_DOCKER.ps1
```

### Option 3: Einzelne Builds

```powershell
# Navigiere zum Projekt-Root
cd "C:\Users\Jochen\Documents\Die verborgene Uhr Gottes\Gottes geheimer Zeitcode"

# API Gateway
docker build -f docker/api/Dockerfile -t sla-pipeline-api:latest .

# Sidecar-MCP
docker build -f docker/sidecar/Dockerfile -t sla-pipeline-sidecar:latest .

# Worker-Scribus
docker build -f docker/worker/Dockerfile -t sla-pipeline-worker:latest .
```

---

## 📋 Nächste Schritte

Nach erfolgreichen Builds:

1. **Services starten:**
   ```powershell
   cd docker
   docker compose up -d
   ```

2. **Status prüfen:**
   ```powershell
   docker compose ps
   docker images | Select-String "sla-pipeline"
   ```

3. **Logs ansehen:**
   ```powershell
   docker compose logs -f
   ```

---

## 🔍 Troubleshooting

### Problem: Build fehlschlägt

- Prüfe, ob alle Requirements-Dateien vorhanden sind
- Prüfe Docker Desktop Speicherplatz
- Prüfe Logs: `docker compose build --progress=plain`

### Problem: Ports bereits belegt

- Ändere Ports in `docker-compose.yml` (z.B. 8001:8000 statt 8000:8000)
- Oder stoppe andere Container, die die Ports nutzen

---

*Erstellt: 2025-01-27*

