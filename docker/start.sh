#!/bin/bash
# Docker Compose Start Script

set -e

echo "=== Docker Compose Start für SLA Pipeline ==="
echo ""

# Prüfe ob Docker läuft
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker läuft nicht. Bitte starte Docker Desktop."
    echo ""
    echo "Tipp: Öffne Docker Desktop und warte bis es vollständig gestartet ist."
    exit 1
fi

echo "✅ Docker läuft"
echo ""

# Wechsle ins docker-Verzeichnis
cd "$(dirname "$0")"

# Prüfe ob docker-compose.yml existiert
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml nicht gefunden"
    exit 1
fi

echo "📁 Starte Services aus: $(pwd)"
echo ""

# Starte Docker Compose
echo "🚀 Starte Docker Compose..."
docker compose up -d

echo ""
echo "✅ Services gestartet"
echo ""

# Warte kurz
sleep 2

# Zeige Status
echo "📊 Service-Status:"
docker compose ps

echo ""
echo "=== ✅ Setup abgeschlossen ==="
echo ""
echo "Nützliche Befehle:"
echo "  Status prüfen:     docker compose ps"
echo "  Logs anzeigen:     docker compose logs -f"
echo "  Services stoppen:  docker compose down"
echo ""
echo "Services:"
echo "  API Gateway:       http://localhost:8000"
echo "  API Docs:          http://localhost:8000/docs"
echo "  MinIO Console:     http://localhost:9001"
echo "  PostgreSQL:        localhost:5432"

