# Scribus Gamma Dashboard Plugin

Native C++/Qt Plugin für Scribus (Gamma Dashboard) plus zugehöriges Backend (Docker: API-Gateway, Sidecar, Worker).

## Struktur
- Plugin (C++/Qt): `gamma_scribus_pack/plugin/cpp/`
- Backend (Docker + Services): `docker/`, `apps/`, `packages/`
- Workflow-Dokumente: `docs/workflow/`
- RAG/Figma Strategie: `strategy/RAG_FIGMA_LAYOUT_STRATEGY.md`

## Quick Start (Backend)
```powershell
cd docker
docker compose up -d --build
```
- API Gateway Health: `http://localhost:8003/health`

## Workflow Quick Start
```powershell
pwsh tools/build_workflow_bundle.ps1 -Out temp_analysis/workflow_bundle.zip
curl -F "bundle=@temp_analysis/workflow_bundle.zip" -F "options_json={\"gamma_sync\":true,\"gamma_attach_to_variants\":true}" http://localhost:8003/v1/workflow/run
```

## Plugin Build (Windows / VS2022)
Siehe: `gamma_scribus_pack/plugin/cpp/SCRIBUS_PLUGIN_COOKBOOK.md`

