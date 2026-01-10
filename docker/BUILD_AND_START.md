# Docker Build & Start - Schnellanleitung

**Für Windows (PowerShell)**

---

## 1. Docker Desktop starten

### Option A: Manuell
1. Öffne **Docker Desktop** aus dem Startmenü
2. Warte bis Docker läuft (Icon in Taskbar zeigt "Docker Desktop is running")
3. Prüfe mit: `docker info`

### Option B: Automatisch (wenn Docker Desktop installiert ist)
Docker Desktop startet automatisch beim Windows-Start (wenn aktiviert).

---

## 2. Docker Images bauen

**PowerShell-Befehl:**
```powershell
cd docker
.\build.ps1
```

**Oder manuell:**
```powershell
cd docker
docker compose build
```

**Oder einzeln:**
```powershell
# Vom Projekt-Root aus
docker build -f docker/api/Dockerfile -t sla-pipeline-api:latest .
docker build -f docker/sidecar/Dockerfile -t sla-pipeline-sidecar:latest .
docker build -f docker/worker/Dockerfile -t sla-pipeline-worker:latest .
```

---

## 3. Services starten

**PowerShell-Befehl:**
```powershell
cd docker
.\start.ps1
```

**Oder direkt:**
```powershell
cd docker
docker compose up -d
```

---

## 4. Status prüfen

```powershell
cd docker
docker compose ps
docker compose logs -f
```

---

## 5. Services verwenden

Nach dem Start sind folgende Services verfügbar:

- **API Gateway:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs
- **MinIO Console:** http://localhost:9001 (minioadmin/minioadmin)
- **PostgreSQL:** localhost:5432 (sla_user/sla_password)

---

## 6. Services stoppen

```powershell
cd docker
docker compose down
```

---

## Troubleshooting

### Docker läuft nicht
```
Error: Cannot connect to the Docker daemon
```

**Lösung:**
1. Öffne Docker Desktop manuell
2. Warte bis Docker vollständig gestartet ist
3. Prüfe mit: `docker info`

### Build fehlgeschlagen
```
Error during build
```

**Lösung:**
1. Prüfe Logs: `docker compose build --no-cache`
2. Prüfe ob alle Requirements-Dateien vorhanden sind
3. Prüfe Dockerfile auf Fehler

### Port bereits belegt
```
Error: port is already allocated
```

**Lösung:**
1. Finde Prozess: `netstat -ano | findstr :8000`
2. Stoppe Prozess oder ändere Port in `docker-compose.yml`

---

*Siehe `README_DOCKER.md` für detaillierte Dokumentation*

