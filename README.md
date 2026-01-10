# Scribus Gamma Dashboard Plugin

Native C++/Qt Plugin für Scribus (Gamma Dashboard) plus ein zugehöriges, selbst entwickeltes Backend (Docker: API‑Gateway, Sidecar, Worker).

## Inhalt

- Plugin (C++/Qt): `gamma_scribus_pack/plugin/cpp/`
- Plugin (Python‑Teil): `gamma_scribus_pack/plugin/gamma_dashboard/`
- Backend (Docker + Services): `docker/`, `apps/`, `packages/`, `mvp/`
- Strategie (RAG für Figma/Layout): `strategy/RAG_FIGMA_LAYOUT_STRATEGY.md`

## Quick Start (Backend)

```powershell
cd docker
docker compose up -d --build
```

- API Gateway Health: `http://localhost:8003/health`
- Sidecar Health: `http://localhost:8004/health`

## Plugin Build (Windows / VS2022)

Siehe: `gamma_scribus_pack/plugin/cpp/SCRIBUS_PLUGIN_COOKBOOK.md`

