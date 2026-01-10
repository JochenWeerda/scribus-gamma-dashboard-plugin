# Docker Quickstart

Schnellstart-Anleitung für Docker Setup.

---

## 1. Docker Desktop starten

### Windows

1. Öffne **Docker Desktop** aus dem Startmenü
2. Warte bis Docker läuft (Icon in Taskbar zeigt "Docker Desktop is running")
3. Prüfe: `docker info`

### macOS

1. Öffne **Docker Desktop** aus Applications
2. Warte bis Docker läuft
3. Prüfe: `docker info`

---

## 2. Docker Images bauen

**Windows (PowerShell):**
```powershell
cd docker
.\build.ps1
```

**Linux/macOS:**
```bash
cd docker
chmod +x build.sh
./build.sh
```

**Oder direkt:**
```bash
cd docker
docker compose build
```

---

## 3. Services starten

**Windows (PowerShell):**
```powershell
cd docker
.\start.ps1
```

**Linux/macOS:**
```bash
cd docker
chmod +x start.sh
./start.sh
```

**Oder direkt:**
```bash
cd docker
docker compose up -d
```

---

## 4. Status prüfen

```bash
cd docker
docker compose ps
docker compose logs -f
```

---

## 5. Services verwenden

- **API Gateway:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **MinIO Console:** http://localhost:9001
- **PostgreSQL:** localhost:5432

---

## Services stoppen

```bash
cd docker
docker compose down
```

---

*Siehe `README_DOCKER.md` für detaillierte Anleitung*

