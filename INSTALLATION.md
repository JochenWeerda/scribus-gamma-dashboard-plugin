# Installation

Diese Anleitung beschreibt die Installation des Gamma Dashboard Plugins (Scribus) und des Backends (Docker).

## Voraussetzungen
- Windows 10/11 (für Plugin-Build), oder nur Backend via Docker
- Docker Desktop (inkl. Compose)
- Scribus 1.7.x (für das Plugin)

## Backend (empfohlen)
```powershell
cd docker
docker compose up -d --build
```

Checks:
- API Gateway: `http://localhost:8003/health`

## Plugin (Windows / VS2022)
Für Build, Installation und Troubleshooting:
- `gamma_scribus_pack/plugin/cpp/SCRIBUS_PLUGIN_COOKBOOK.md`

## Workflow (Bundle → Run)
1. Bundle bauen:
```powershell
pwsh tools/build_workflow_bundle.ps1 -Out temp_analysis/workflow_bundle.zip
```
2. Workflow starten:
```powershell
curl -F "bundle=@temp_analysis/workflow_bundle.zip" -F "options_json={\"gamma_sync\":true,\"gamma_attach_to_variants\":true}" http://localhost:8003/v1/workflow/run
```

Weitere Details:
- `docs/workflow/MAGAZIN_WORKFLOW_IMPLEMENTATION_PLAN.md`

