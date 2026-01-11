from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional


def _norm_role(role: Optional[str]) -> Optional[str]:
    if role is None:
        return None
    r = str(role).strip().lower()
    if not r:
        return None

    aliases = {
        "headline": "title",
        "h1": "title",
        "titel": "title",
        "heading": "title",
        "subheadline": "h2",
        "subtitle": "h2",
        "untertitel": "h2",
        "subheading": "h2",
        "bodytext": "body",
        "text": "body",
        "paragraph": "body",
        "citation": "quote",
        "blockquote": "quote",
        "side": "sidebar",
        "aside": "sidebar",
        "infobox_bg": "infobox",
        "captionoverlay": "overlay",
        "overlay": "overlay",
    }

    return aliases.get(r, r)


def _ensure_bbox(box: Dict[str, Any]) -> Dict[str, Any]:
    # Extractor uses rel_bbox [x1,y1,x2,y2]; we keep it as-is and only ensure shape.
    rel = box.get("rel_bbox")
    if isinstance(rel, list) and len(rel) == 4:
        return box
    # If bbox is missing, drop by returning an empty dict marker.
    return {}


def normalize_extracted_pptx(extracted: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize the Stage-0 extractor output to a stable shape:
    - ensures `slides[*].text_boxes|image_boxes|infoboxes` exist
    - canonicalizes `role` values
    - ensures boolean `ignore` is present
    """

    out = deepcopy(extracted)
    slides = out.get("slides") or []
    if not isinstance(slides, list):
        slides = []
        out["slides"] = slides

    for slide in slides:
        if not isinstance(slide, dict):
            continue

        slide.setdefault("text_boxes", [])
        slide.setdefault("image_boxes", [])
        slide.setdefault("infoboxes", [])

        normalized_tbs: List[Dict[str, Any]] = []
        for tb in slide.get("text_boxes") or []:
            if not isinstance(tb, dict):
                continue
            tb = deepcopy(tb)
            tb["role"] = _norm_role(tb.get("role"))
            tb["ignore"] = bool(tb.get("ignore") is True)
            if not _ensure_bbox(tb):
                continue
            normalized_tbs.append(tb)
        slide["text_boxes"] = normalized_tbs

        normalized_ibox: List[Dict[str, Any]] = []
        for ib in slide.get("infoboxes") or []:
            if not isinstance(ib, dict):
                continue
            ib = deepcopy(ib)
            ib["role"] = _norm_role(ib.get("role") or "infobox") or "infobox"
            ib["ignore"] = bool(ib.get("ignore") is True)
            if not _ensure_bbox(ib):
                continue
            normalized_ibox.append(ib)
        slide["infoboxes"] = normalized_ibox

        normalized_imgs: List[Dict[str, Any]] = []
        for im in slide.get("image_boxes") or []:
            if not isinstance(im, dict):
                continue
            im = deepcopy(im)
            im["role"] = _norm_role(im.get("role") or "image") or "image"
            if not _ensure_bbox(im):
                continue
            normalized_imgs.append(im)
        slide["image_boxes"] = normalized_imgs

    return out


def detect_elements_from_extracted_slide(slide: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compatibility adapter. Prefer using `normalize_extracted_pptx()` + the raw lists.
    """

    return {
        "text_boxes": slide.get("text_boxes") or [],
        "image_boxes": slide.get("image_boxes") or [],
        "infoboxes": slide.get("infoboxes") or [],
        "quote_candidates": slide.get("quote_candidates") or [],
    }

