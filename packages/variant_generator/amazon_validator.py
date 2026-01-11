from __future__ import annotations

from typing import Any, Dict, List, Tuple


def validate_kdp_layout(layout_json: Dict[str, Any], *, safety_margin_px: float = 0.0) -> tuple[bool, List[str]]:
    """
    MVP validator for KDP-like constraints:
    - all bboxes are within the page bounds (optionally with a safety margin)
    """

    doc = layout_json.get("document") or {}
    w = float(doc.get("width") or 0)
    h = float(doc.get("height") or 0)
    m = float(safety_margin_px)

    errors: List[str] = []
    for page in layout_json.get("pages", []) or []:
        for obj in page.get("objects", []) or []:
            bbox = obj.get("bbox") or {}
            if not {"x", "y", "w", "h"} <= set(bbox.keys()):
                continue
            x = float(bbox["x"])
            y = float(bbox["y"])
            bw = float(bbox["w"])
            bh = float(bbox["h"])
            if x < m or y < m or (x + bw) > (w - m) or (y + bh) > (h - m):
                errors.append(
                    f"Object {obj.get('id')} out of bounds: x={x},y={y},w={bw},h={bh} (doc {w}x{h}, margin {m})"
                )

    return (len(errors) == 0), errors

