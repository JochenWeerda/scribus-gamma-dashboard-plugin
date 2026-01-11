# Dokumenten-Triage (Keep / RAG / Archive / Remove)

Ziel: Repo bleibt schlank (GitHub), gleichzeitig bleibt Wissen auffindbar (RAG) und historische Notizen gehen nicht verloren (Archive – lokal).

## Keep (im Repo)
- `README.md`
- `LICENSE`
- `INSTALLATION.md`
- `PROJECT_STRUCTURE.md`
- `gamma_scribus_pack/plugin/cpp/SCRIBUS_PLUGIN_COOKBOOK.md`
- `docs/workflow/*`
- `strategy/*`

## RAG (empfohlen zu indexieren)
- `docs/workflow/MAGAZIN_WORKFLOW_DESIGN_DECISIONS.md`
- `docs/workflow/MAGAZIN_WORKFLOW_IMPLEMENTATION_PLAN.md`
- `docs/workflow/WORKFLOW_SUMMARY.md`
- `strategy/RAG_FIGMA_LAYOUT_STRATEGY.md`
- `gamma_scribus_pack/plugin/cpp/SCRIBUS_PLUGIN_COOKBOOK.md` (Build/Debug-Wissen)
- optional: ausgewählte Architektur-Dossiers in `docs/` (Bus/Performance)

## Archive (lokal, nicht in GitHub)
- Root-Notizen/Status/Changelogs: z.B. `CHANGELOG_*.md`, `BUILD_*.md`, `*STATUS*.md`
- Temporäre Analysen: `temp_analysis/`
- Exportierte Medien & Templates: `*.sla`, `*.pdf`, `*.pptx`, `*.png`, …

Hinweis: `docs/archive/` ist absichtlich per `.gitignore` ausgeschlossen.

## Remove (bzw. nicht versionieren)
- Logs, Dumps, BinLogs, Debug-Outputs
- venvs, caches, Container-Volumes

## Helfer-Skript
- `tools/triage_docs.ps1` kann Root-„Notiz“-MDs in `docs/archive/root_md/` verschieben (opt-in).

