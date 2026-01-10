# -*- coding: utf-8 -*-
import os
import json
from typing import Dict, Any, List

def load_json(p: str):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(p: str, obj: Any):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def patch_pptx_slides(pptx_json_path: str, hints_by_slide_path: str, project_dir: str, min_existing: int = 1) -> Dict[str, Any]:
    pptx = load_json(pptx_json_path)
    hints_by_slide = load_json(hints_by_slide_path)

    for slide in pptx.get("slides", []):
        si = int(slide.get("slide", 0) or 0)
        # only patch if too few image_boxes
        img_boxes = slide.get("image_boxes", []) or []
        if len(img_boxes) >= min_existing:
            continue

        hints = hints_by_slide.get(str(si)) or hints_by_slide.get(si) or []
        for h in hints:
            if h.get("kind") != "infographic":
                continue
            slide.setdefault("image_boxes", []).append({
                "rel_bbox": h.get("rel_bbox"),
                "image": h.get("image"),  # relative to project_dir
            })

    return pptx

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx_json", required=True, help="Your pptx parsed JSON (slides[].image_boxes/text_boxes/texts)")
    ap.add_argument("--hints_by_slide", required=True, help="output/hints_by_slide.json from pipeline")
    ap.add_argument("--project", required=True, help="Project dir base")
    ap.add_argument("--out", required=True, help="Output patched JSON path")
    ap.add_argument("--min_existing", type=int, default=1)
    args = ap.parse_args()

    patched = patch_pptx_slides(args.pptx_json, args.hints_by_slide, args.project, min_existing=args.min_existing)
    save_json(args.out, patched)
    print("Wrote", args.out)

if __name__ == "__main__":
    main()
