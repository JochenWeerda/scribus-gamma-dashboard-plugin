# Gesamtstatus: Magazin-Workflow (Implementierung)

Stand: Der Magazin-Workflow ist als Backend/Worker-Pipeline lauffähig und kann Bundles aus PPTX-Extraktion verarbeiten.

## Ergebnis (heute)
- Workflow kann per API gestartet werden (`/v1/workflow/run`) und erzeugt ein Workflow-Report-ZIP als Artefakt.
- Gamma-Export-ZIPs können optional eingebunden werden, um reale PNG-Crops („optische Wahrheit“) zu erzeugen.
- Varianten können optional automatisch mit Crop-Artefakten verlinkt werden (`imageUrl=/v1/artifacts/<id>`).

## Was ist „100%“ im Sinne der Pipeline?
- Stabiler Bundle-Standard (Windows → Linux): erfüllt (Bundle-Builder + Manifest-Normalisierung)
- Wiederanlauf/Idempotenz: Schrittzustand wird persistiert (`workflow_state.json`), Steps sind hash-basiert resumable
- Flags für teure Schritte: Gamma-Crops/Attach nur bei gesetzten Flags
- Artefakt-Output: Report + optionale Teil-Artefakte (Layouts/Variants/Quality)

## Nächste sinnvolle Ausbaupunkte
- PPTX-Element-Detektion:
  - robustes Figure-Cluster (Infografiken als „1 Bild“ statt 100 Shapes)
  - Quote/Caption/Sidebar heuristischer + optional per Sidecar-Tags overridable
- Quality-Checks:
  - stärkere Parametrisierung über `docs/workflow/MAGAZIN_WORKFLOW_DESIGN_DECISIONS.md`
  - klare „fail vs warn“ Policy pro Check (Amazon/Preflight)

