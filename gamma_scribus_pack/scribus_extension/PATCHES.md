# PATCHES – Setzerei Engine (minimal)

## Ziel
Wenn Gamma-PPTX zu wenig `image_boxes` liefert, sollen automatisch Card-Crops aus `output/hints_by_slide.json` als Infografiken verwendet werden.

## Minimal-Patch in `build_entries_from_pptx()`

1) Lade einmal am Anfang (optional) `output/hints_by_slide.json`:
- Pfad: `${PROJECT_DIR}/output/hints_by_slide.json` oder relativ zu PPTX_DIR/../output/

2) Pro Slide:
- Wenn `slide.get("image_boxes",[])` leer oder sehr klein:
  - Hänge `image_boxes` an aus hints_by_slide[slide_idx]
  - Map: hint["image"] -> ib["image"], hint["rel_bbox"] -> ib["rel_bbox"]

3) Optional:
- Setze `forced=True` und `tag_meta.region` = "body"/"sidebar" je nach Breite.

Dadurch nutzt dein vorhandener Codepfad (merge_image_boxes, heuristics, packer, run_image_jobs) automatisch die neuen Crops.
