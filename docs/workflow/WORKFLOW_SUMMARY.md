# Magazin-Workflow: Kurzstatus

## Implementiert
- Workflow-API: `POST /v1/workflow/run` (Bundle ZIP + Optionen)
- Worker-Ausführung (RQ): Queue `workflow`, Artefakte werden hochgeladen und sind downloadbar über `/v1/artifacts/{id}`
- Gamma-Crop Pipeline (optional): `gamma_sync` erzeugt echte PNG-Crops aus Gamma-Export-ZIPs
- Varianten-Anreicherung (optional): `gamma_attach_to_variants` setzt `imageUrl` auf Crop-Artefakte
- Bundle-Builder: `tools/build_workflow_bundle.py` / `tools/build_workflow_bundle.ps1`

## Bekannte Grenzen (Roadmap)
- PPTX-Element-Detektion/Clustering ist derzeit pragmatisch (weiter verfeinern: figure_cluster, quotes, captions).
- Quality-Checks sind modular, aber noch nicht vollständig mit allen Design-Decisions parametrisiert.

## Einstiegspunkte
- Workflow-API: `apps/api-gateway/workflow.py`
- Worker: `apps/worker-scribus/worker.py` (`process_workflow_job`)
- Orchestrator: `packages/workflow/orchestrator.py`
- Gamma-Crops: `packages/workflow/step_executor.py` (`gamma_sync`)

