# PPTX Parser (Stage-1)

Dieses Paket konvertiert das bereits extrahierte PPTX-JSON (Output von `tools/extract_pptx_assets.py`)
in schema-valide Layout-JSONs (`packages/layout_schema/layout-mvp.schema.json`).

## Quickstart

1) PPTX extrahieren (Stage-0):

```powershell
python tools\extract_pptx_assets.py
```

2) Alles aus `media_pool/pptx/manifest.json` nach `media_pool/layout_json/` konvertieren:

```powershell
python -m packages.pptx_parser convert-manifest `
  --manifest media_pool\pptx\manifest.json `
  --pptx-root media_pool\pptx `
  --out-dir media_pool\layout_json `
  --style magazin `
  --use-sidecar `
  --project-init .cursor\project_init.json.template `
  --report temp_analysis\pptx_manifest_convert_report.json `
  --width 2480 --height 3508 --dpi 300
```

3) Einzeldatei konvertieren:

```powershell
python -m packages.pptx_parser convert-one `
  --in media_pool\pptx\json\Gottes-erste-Uhr-die-Schopfung.json `
  --out temp_analysis\layout_from_pptx_sample.json `
  --style magazin `
  --use-sidecar `
  --width 2480 --height 3508 --dpi 300
```

## Hinweis

- Der Converter nutzt primär `text_boxes` und `image_boxes` inkl. `rel_bbox` (0..1) und mappt diese auf px-Koordinaten.
- Output wird standardisiert um `role`/`pStyle` Metadaten pro Objekt (z.B. `title`, `h2`, `quote`, `sidebar`, `infobox`).
- Mit `--style magazin` nutzt der Converter die Design-Decision Layer-Namen (z.B. `Hintergrund`, `Images`, `Text`, `Wrap`, `CaptionOverlay`).
- Sidebar: optionaler Hintergrund-Rechteckrahmen (`role=sidebar_bg`) + Padding.
- Offene Erweiterungen stehen in `TODO_MAGAZIN_WORKFLOW.md`.
