# Docker Build Anleitung

## Status
✅ Docker Desktop läuft
✅ Docker-Konfiguration vorhanden
⚠️ PowerShell hat Probleme mit Umlauten im Pfad

## Lösung: Manuelle Builds

### Option 1: Docker Compose (Empfohlen)

1. **Öffne ein neues PowerShell-Fenster** (als Administrator)
2. **Navigiere zum Projektverzeichnis** (manuell im Explorer öffnen und dann PowerShell dort öffnen)
3. **Wechsle ins docker-Verzeichnis:**
   ```powershell
   cd docker
   ```
4. **Führe die Builds aus:**
   ```powershell
   docker compose build
   ```
5. **Starte die Services:**
   ```powershell
   docker compose up -d
   ```

### Option 2: Einzelne Builds

Falls docker-compose nicht funktioniert:

```powershell
# Vom Projektroot aus:
docker build -f docker/api/Dockerfile -t sla-pipeline-api:latest .
docker build -f docker/sidecar/Dockerfile -t sla-pipeline-sidecar:latest .
docker build -f docker/worker/Dockerfile -t sla-pipeline-worker:latest .
```

### Option 3: Git Bash oder WSL

Falls PowerShell weiterhin Probleme hat, verwende Git Bash oder WSL:

```bash
cd docker
docker compose build
docker compose up -d
```

## Services

Nach dem Start sind folgende Services verfügbar:

| Service | Port | URL |
|---------|------|-----|
| API Gateway | 8000 | http://localhost:8000 |
| Sidecar-MCP | 8004 | http://localhost:8004 |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |
| MinIO | 9000 | http://localhost:9000 |
| MinIO Console | 9001 | http://localhost:9001 |

## Nützliche Befehle

```powershell
# Status prüfen
docker compose ps

# Logs ansehen
docker compose logs -f

# Services stoppen
docker compose down

# Services neu starten
docker compose restart
```

## Troubleshooting

### Build-Fehler
- Prüfe ob alle Requirements-Dateien vorhanden sind
- Prüfe Docker Desktop läuft: `docker ps`
- Prüfe verfügbarer Speicherplatz

### Port-Konflikte
Falls Ports bereits belegt sind, ändere in `docker-compose.yml` die Port-Mappings.

### Pfad-Probleme
- Verwende Git Bash oder WSL statt PowerShell
- Oder öffne PowerShell direkt im Projektverzeichnis (Rechtsklick → PowerShell hier öffnen)

