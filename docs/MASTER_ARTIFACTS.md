# Master: Artefakte, Workflow, Wissen

Dieses Dokument bündelt die wichtigsten Artefakte/Entry-Points im Repo, damit Build/Workflow/Debugging reproduzierbar sind.

## Wichtigste Dokumente
- Plugin Build/Debug Cookbook: `gamma_scribus_pack/plugin/cpp/SCRIBUS_PLUGIN_COOKBOOK.md`
- Workflow Design-Decisions: `docs/workflow/MAGAZIN_WORKFLOW_DESIGN_DECISIONS.md`
- Workflow Implementierungsplan (Ist-Stand): `docs/workflow/MAGAZIN_WORKFLOW_IMPLEMENTATION_PLAN.md`
- Workflow Kurzstatus: `docs/workflow/WORKFLOW_SUMMARY.md`
- GitHub Publishing Plan: `docs/workflow/GITHUB_PUBLISHING_PLAN.md`
- Dokumenten-Triage: `docs/DOCS_TRIAGE.md`

## Backend / Workflow Entry Points
- Docker Compose: `docker/docker-compose.yml`
- API Gateway: `apps/api-gateway/main.py`
- Workflow API Router: `apps/api-gateway/workflow.py`
- Artefakt Download: `apps/api-gateway/main.py` (`GET /v1/artifacts/{artifact_id}`)
- Worker: `apps/worker-scribus/worker.py` (`process_workflow_job`)
- Workflow Orchestrator: `packages/workflow/orchestrator.py`
- Gamma Crop Step: `packages/workflow/step_executor.py` (`gamma_sync`)

## Bundle-Builder (Windows → Linux sicher)
- CLI: `tools/build_workflow_bundle.py`
- PowerShell Wrapper: `tools/build_workflow_bundle.ps1`

Warum: PowerShell `Compress-Archive` kann ZIPs erzeugen, die in Linux-Containern bei Pfaden (Backslashes) Probleme machen.

## Flags (nur wenn gesetzt)
Die Pipeline ist so gebaut, dass „teure“ Schritte nur bei gesetzten Flags laufen:
- `gamma_sync`: erzeugt echte PNG-Crops aus Gamma-Export-ZIPs
- `gamma_crop_kinds`: Auswahl der Crop-Typen (Default: `["infobox"]`)
- `gamma_attach_to_variants`: hängt Crop-Artefakte als `imageUrl` in Varianten-JSON ein (setzt `gamma_sync=true` voraus)

## RAG: Stabilität
- Embedding Model ist hart auf `paraphrase-multilingual-mpnet-base-v2` gesetzt (`packages/rag_service/embeddings.py`), um Chroma-DB konsistent zu halten.

