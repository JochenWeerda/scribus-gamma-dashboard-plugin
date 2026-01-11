# GitHub Publishing Plan (scribus-gamma-dashboard-plugin)

Ziel: GitHub enthält **nur** den selbst entwickelten Code (Plugin + Backend) und kuratierte Dokumentation – keine Assets, keine Secrets.

## Was gehört ins Repo?
- Plugin (C++/Qt): `gamma_scribus_pack/plugin/cpp/`
- Backend (Docker + Services): `docker/`, `apps/`, `packages/`
- Kuratierte Docs: `README.md`, `INSTALLATION.md`, `PROJECT_STRUCTURE.md`, `docs/`
- Tools/Skripte: `tools/` (z.B. Bundle-Builder)

## Was gehört NICHT ins Repo?
- Secrets: `.env`, Tokens, Credentials
- Große/binary Artefakte: `*.pptx`, `*.pdf`, `*.png`, `*.sla`, `*.zip`
- Lokale Workspaces: `.cursor/`, `media_pool/`, `assets/`, `screenshots/`, `temp_analysis/`

## Release-/Tagging Vorschlag
- Tags: `v0.1.0-alpha`, `v0.2.0-alpha`, …
- Release Assets:
  - Plugin DLL (Windows) als Release-Anhang
  - Optional: vorkonfigurierte `docker-compose.override.example.yml`

## Minimal-Check vor Push
- `rg -n \"figd_|FIGMA_ACCESS_TOKEN|MINIO_SECRET|PASSWORD\" -S .` (keine Secrets im Repo)
- `pytest -q` (wenn Tests vorhanden/konfiguriert)
- `docker compose build` (optional)

