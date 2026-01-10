#!/bin/bash
# Docker Build Script für alle Services

set -e

echo "=== Docker Build für SLA Pipeline ==="
echo ""

# Prüfe ob Docker läuft
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker läuft nicht. Bitte starte Docker Desktop."
    exit 1
fi

echo "✅ Docker läuft"
echo ""

# Wechsle ins docker-Verzeichnis
cd "$(dirname "$0")"
SCRIPT_DIR=$(pwd)
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

echo "📁 Projekt-Root: $PROJECT_ROOT"
echo ""

# Build API Gateway
echo "🔨 Baue API Gateway..."
docker build \
    -f api/Dockerfile \
    -t sla-pipeline-api:latest \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    "$PROJECT_ROOT"
echo "✅ API Gateway gebaut"
echo ""

# Build Sidecar-MCP
echo "🔨 Baue Sidecar-MCP..."
docker build \
    -f sidecar/Dockerfile \
    -t sla-pipeline-sidecar:latest \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    "$PROJECT_ROOT"
echo "✅ Sidecar-MCP gebaut"
echo ""

# Build Worker-Scribus
echo "🔨 Baue Worker-Scribus..."
docker build \
    -f worker/Dockerfile \
    -t sla-pipeline-worker:latest \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    "$PROJECT_ROOT"
echo "✅ Worker-Scribus gebaut"
echo ""

echo "=== ✅ Alle Docker Images erfolgreich gebaut ==="
echo ""
echo "Nächste Schritte:"
echo "  1. Starte Docker Compose: docker compose up -d"
echo "  2. Prüfe Status: docker compose ps"
echo "  3. Logs anzeigen: docker compose logs -f"
