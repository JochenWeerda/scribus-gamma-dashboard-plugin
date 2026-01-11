from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Tuple


def _doc_px_for(format_name: str, dpi: int) -> tuple[int, int]:
    fmt = (format_name or "").strip().lower()
    if fmt in {"a4"}:
        # 210x297mm
        w_in = 210.0 / 25.4
        h_in = 297.0 / 25.4
    elif fmt in {"8x11.5", "8x11_5", "8x11,5"}:
        w_in = 8.0
        h_in = 11.5
    else:
        raise ValueError(f"Unsupported format: {format_name}")
    return int(round(w_in * dpi)), int(round(h_in * dpi))


def convert_layout_format(layout_json: Dict[str, Any], *, target_format: str) -> Dict[str, Any]:
    """
    Convert document size and scale all bboxes. MVP assumes a single uniform coordinate system in px.
    """

    out = deepcopy(layout_json)
    doc = out.get("document") or {}
    src_w = float(doc.get("width") or 1)
    src_h = float(doc.get("height") or 1)
    dpi = int(doc.get("dpi") or 300)

    dst_w, dst_h = _doc_px_for(target_format, dpi)
    sx = float(dst_w) / src_w if src_w else 1.0
    sy = float(dst_h) / src_h if src_h else 1.0

    out.setdefault("document", {})
    out["document"]["width"] = dst_w
    out["document"]["height"] = dst_h
    out["document"]["dpi"] = dpi

    for page in out.get("pages", []) or []:
        for obj in page.get("objects", []) or []:
            bbox = obj.get("bbox") or {}
            if {"x", "y", "w", "h"} <= set(bbox.keys()):
                bbox["x"] = float(bbox["x"]) * sx
                bbox["y"] = float(bbox["y"]) * sy
                bbox["w"] = max(1.0, float(bbox["w"]) * sx)
                bbox["h"] = max(1.0, float(bbox["h"]) * sy)
                obj["bbox"] = bbox

    out.setdefault("variant", {})
    out["variant"]["format"] = target_format
    return out

