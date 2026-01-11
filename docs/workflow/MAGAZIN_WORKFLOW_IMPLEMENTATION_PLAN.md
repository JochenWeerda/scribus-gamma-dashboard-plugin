# Magazin-Workflow: Implementierungsplan (Ist-Stand)

Dieses Dokument beschreibt den Workflow als **laufende Implementierung** (Backend + Worker), inkl. Flags/Optionen.

## Quick Start
1. Docker starten: `cd docker; docker compose up -d --build`
2. Bundle bauen (Windows-sicher, Linux-kompatibel):
   - `pwsh tools/build_workflow_bundle.ps1 -Out temp_analysis/workflow_bundle.zip`
3. Workflow starten:
   - `curl -F \"bundle=@temp_analysis/workflow_bundle.zip\" -F \"options_json={\\\"gamma_sync\\\":true,\\\"gamma_attach_to_variants\\\":true}\" http://localhost:8003/v1/workflow/run`

## Backend API
- `POST /v1/workflow/run` (multipart)
  - `bundle`: ZIP (manifest.json + json/* + optional gamma/* + optional project_init.json)
  - `options_json`: Workflow-Optionen (JSON; optional)
- `GET /v1/artifacts/{artifact_id}`: Download von Artefakten
- `GET /health`: Health Check

## Worker / Queues / BUS
- RQ Queues: `compile`, `export`, `workflow` (Worker hört auf alle drei).
- Event-Bus Events (worker-seitig, aktuell):
  - `workflow.job.created`, `workflow.job.completed`, `workflow.job.failed`

## Bundle-Spezifikation
ZIP-Layout:
- `manifest.json`:
  - `files[]`: `{ name: <pptx_name>, json: <path/to/file.json> }`
- `json/<file>.json`: extrahierte PPTX-Struktur
- optional: `gamma/<pptx_name>.zip`: Gamma-Exports pro PPTX (für Crops)
- optional: `project_init.json`: Projekt-/Varianten-Entscheidungen

Wichtig:
- Pfade in `manifest.json` müssen **Forward-Slashes** nutzen.
- Bundles sollten mit `tools/build_workflow_bundle.py` erstellt werden (kein `Compress-Archive`).

## Workflow-Konfiguration (Options)
Options werden über `options_json` an den Job-`metadata` gehängt und im Worker in `WorkflowConfig` gemappt.

Empfohlene Defaults:
- `gamma_sync=false` (nur aktivieren wenn Gamma-Exports vorhanden sind)
- `gamma_crop_kinds=["infobox"]` (konservativ; Erweiterung nur bei Bedarf)
- `gamma_attach_to_variants=false` (nur sinnvoll, wenn Variants genutzt werden)
- `render=false` (Render ist teuer; bewusst opt-in)

Render-Flags:
- `render=true|false`
- `render_on_variants=true|false`
- `render_pdf=true|false`
- `render_png=true|false`

## Steps (Pipeline)
Der Orchestrator führt Schritte sequentiell aus und schreibt einen Resume-State (`workflow_state.json`).

Typischer Ablauf:
1. **pptx_parse**: liest `json/*.json` aus dem Bundle und normalisiert Inhalte/Pfade.
2. **gamma_sync** *(optional)*:
   - erzeugt echte Crop-PNGs aus Gamma-Exports und schreibt Report in den State
   - nur aktiv, wenn `gamma_sync=true`
3. **variants** *(optional/teilweise)*:
   - erzeugt Varianten-JSON; optional werden `imageUrl`/`gammaCropArtifactId` gesetzt, wenn `gamma_attach_to_variants=true`
4. **quality_check** *(optional/teilweise)*:
   - erzeugt Quality-JSON (z.B. Amazon-Checks), wenn aktiviert
5. **report**:
   - bundelt Outputs und lädt ein ZIP als `ArtifactType.WORKFLOW_REPORT` hoch

## „Nur wenn Flag gesetzt ist“
Die „teuren“ oder potenziell invasive Schritte sind strikt Flag-gesteuert:
- Gamma-Crops: nur bei `gamma_sync=true`
- Attach zu Varianten: nur bei `gamma_attach_to_variants=true` (und nur wenn `gamma_sync=true`)
