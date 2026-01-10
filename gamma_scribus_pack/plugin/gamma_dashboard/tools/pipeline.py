# -*- coding: utf-8 -*-
import os
import json
import re
from typing import Dict, Any, List, Optional

from ingest_gamma_export import unpack_if_zip, find_pptx, find_slide_pngs, normalize_slide_pngs
from pptx_text_extract import extract_text_boxes
from gamma_cards import run_on_slide
from anchor_map import find_anchors

def _ensure_dir(p: str) -> str:
    os.makedirs(p, exist_ok=True)
    return p

def _norm_name(name: str) -> str:
    name = name.lower()
    name = re.sub(r"\(\d+\)", "", name)
    name = name.replace("copy-of-", "")
    name = re.sub(r"[^a-z0-9]+", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def _find_project_pptx(project_dir: str, gamma_export: str) -> Optional[str]:
    pptx_dir = os.path.join(project_dir, "pptx")
    if not os.path.isdir(pptx_dir):
        return None
    candidates = [os.path.join(pptx_dir, f) for f in os.listdir(pptx_dir) if f.lower().endswith(".pptx")]
    if not candidates:
        return None
    zip_base = os.path.splitext(os.path.basename(gamma_export))[0]
    key = _norm_name(zip_base)
    if key:
        for c in candidates:
            if _norm_name(os.path.splitext(os.path.basename(c))[0]) == key:
                return c
    return candidates[0] if len(candidates) == 1 else None


def run_pipeline(
    gamma_export: str,
    project_dir: str,
    max_clusters_per_slide: int = 3,
    pptx_path: Optional[str] = None,
) -> Dict[str, Any]:
    project_dir = os.path.abspath(project_dir)
    out_dir = _ensure_dir(os.path.join(project_dir, "output"))
    slides_dir = _ensure_dir(os.path.join(out_dir, "slides"))
    crops_dir = _ensure_dir(os.path.join(out_dir, "crops"))
    overlay_dir = _ensure_dir(os.path.join(out_dir, "debug_overlay"))

    work_dir = _ensure_dir(os.path.join(out_dir, "_work"))
    root = unpack_if_zip(gamma_export, work_dir)

    pptx = pptx_path or find_pptx(root)
    if not pptx:
        pptx = _find_project_pptx(project_dir, gamma_export)
    if not pptx:
        raise RuntimeError("No PPTX found in Gamma export or project_dir/pptx.")

    slide_pngs = find_slide_pngs(root)
    if not slide_pngs:
        raise RuntimeError("No slide PNGs found in Gamma export. Export PNG from Gamma or add a renderer fallback.")
    normed_pngs = normalize_slide_pngs(slide_pngs, slides_dir)

    # extract text boxes
    pptx_data = extract_text_boxes(pptx)
    slide_text_map = {s["slide"]: s for s in pptx_data["slides"]}

    all_slide_clusters = []
    hints_by_slide = {}  # slide_index -> hints[]

    for i, png in enumerate(normed_pngs, start=1):
        res = run_on_slide(png_path=png, out_crops_dir=crops_dir, out_overlay_dir=overlay_dir, max_clusters=max_clusters_per_slide)
        slide_idx = i
        tb = (slide_text_map.get(slide_idx) or {}).get("text_boxes", [])
        hints = []
        for c in res["clusters"]:
            bb = c["rel_bbox"]
            anchors = find_anchors(bb, tb)
            hints.append({
                "kind": "infographic",
                "rel_bbox": bb,
                "image": os.path.relpath(c["crop"], project_dir).replace("\\", "/"),
                "fit": "contain",
                "anchor": (0.5, 0.5),
                "min_dpi": 240,
                "meta": {
                    "score": c.get("score", 0.0),
                    "anchors": anchors,
                    "slide": slide_idx,
                }
            })
        hints_by_slide[slide_idx] = hints
        all_slide_clusters.append(res)

    # write outputs
    with open(os.path.join(out_dir, "pptx_text_boxes.json"), "w", encoding="utf-8") as f:
        json.dump(pptx_data, f, ensure_ascii=False, indent=2)

    with open(os.path.join(out_dir, "slide_clusters.json"), "w", encoding="utf-8") as f:
        json.dump(all_slide_clusters, f, ensure_ascii=False, indent=2)

    with open(os.path.join(out_dir, "hints_by_slide.json"), "w", encoding="utf-8") as f:
        json.dump(hints_by_slide, f, ensure_ascii=False, indent=2)

    return {
        "project_dir": project_dir,
        "pptx": pptx,
        "slides": normed_pngs,
        "out_dir": out_dir,
        "hints_by_slide": os.path.join(out_dir, "hints_by_slide.json"),
    }

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--gamma_export", required=True, help="Gamma export zip or folder")
    ap.add_argument("--project", required=True, help="Project dir (creates output/)")
    ap.add_argument("--max_clusters", type=int, default=3)
    ap.add_argument("--pptx", default="", help="Optional PPTX path (if not inside Gamma export)")
    args = ap.parse_args()

    pptx_path = args.pptx.strip() or None
    res = run_pipeline(args.gamma_export, args.project, max_clusters_per_slide=args.max_clusters, pptx_path=pptx_path)
    print("OK:", res)

if __name__ == "__main__":
    main()
