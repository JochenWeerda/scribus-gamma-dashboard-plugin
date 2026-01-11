from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


def _mm_to_px(mm: float, dpi: int) -> float:
    return (mm / 25.4) * float(dpi)


def apply_bleed(layout_json: Dict[str, Any], *, bleed_mm: float = 3.0) -> Dict[str, Any]:
    """
    Add bleed by expanding the document size and shifting objects by bleed amount.
    MVP applies the same bleed on all sides.
    """

    out = deepcopy(layout_json)
    doc = out.get("document") or {}
    dpi = int(doc.get("dpi") or 300)
    bleed_px = _mm_to_px(float(bleed_mm), dpi)

    out.setdefault("document", {})
    out["document"]["width"] = float(doc.get("width") or 0) + 2 * bleed_px
    out["document"]["height"] = float(doc.get("height") or 0) + 2 * bleed_px
    out["document"]["dpi"] = dpi

    for page in out.get("pages", []) or []:
        for obj in page.get("objects", []) or []:
            bbox = obj.get("bbox") or {}
            if {"x", "y", "w", "h"} <= set(bbox.keys()):
                bbox["x"] = float(bbox["x"]) + bleed_px
                bbox["y"] = float(bbox["y"]) + bleed_px
                obj["bbox"] = bbox

    out.setdefault("variant", {})
    out["variant"]["bleed_mm"] = float(bleed_mm)
    return out

