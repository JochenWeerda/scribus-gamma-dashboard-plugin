from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from packages.layout_schema import validate_layout


def validate_layout_semantics(
    layout_json: Dict[str, Any],
    *,
    checks: Optional[List[str]] = None,
) -> tuple[bool, List[str]]:
    """
    Adds basic semantic checks on top of schema validation:
    - bboxes within document bounds
    - non-empty ids
    - basic document/page sanity
    - optional object-type sanity (text/image)
    """

    ok, errors = validate_layout(layout_json)
    if not ok:
        return ok, errors

    doc = layout_json.get("document") or {}
    w = float(doc.get("width") or 0)
    h = float(doc.get("height") or 0)
    dpi = float(doc.get("dpi") or 0)

    sem_errors: List[str] = []
    checks = checks or ["document", "pages", "bbox", "text", "image", "layers"]

    if "document" in checks:
        if w <= 0 or h <= 0:
            sem_errors.append("Document width/height must be > 0")
        if dpi <= 0:
            sem_errors.append("Document dpi must be > 0")

    allowed_layers: Optional[Set[str]] = None
    if "layers" in checks:
        layers = (layout_json.get("meta") or {}).get("layers") or {}
        if isinstance(layers, dict) and layers:
            allowed_layers = {str(v) for v in layers.values() if v}

    if "pages" in checks:
        seen_pages: Set[int] = set()
        for page in layout_json.get("pages", []) or []:
            try:
                pn = int(page.get("pageNumber") or 0)
            except Exception:
                pn = 0
            if pn <= 0:
                sem_errors.append("Page has invalid pageNumber")
            if pn in seen_pages:
                sem_errors.append(f"Duplicate pageNumber: {pn}")
            seen_pages.add(pn)

    for page in layout_json.get("pages", []) or []:
        for obj in page.get("objects", []) or []:
            if not (obj.get("id") or "").strip():
                sem_errors.append("Object has empty id")
                continue

            bbox = obj.get("bbox") or {}
            if not {"x", "y", "w", "h"} <= set(bbox.keys()):
                continue
            x = float(bbox["x"])
            y = float(bbox["y"])
            bw = float(bbox["w"])
            bh = float(bbox["h"])

            if "bbox" in checks:
                if x < 0 or y < 0 or bw < 1 or bh < 1:
                    sem_errors.append(f"Invalid bbox for {obj.get('id')}")
                if (x + bw) > w + 1e-6 or (y + bh) > h + 1e-6:
                    sem_errors.append(f"Object {obj.get('id')} out of bounds")

            if allowed_layers is not None:
                layer = str(obj.get("layer") or "")
                if layer and layer not in allowed_layers:
                    sem_errors.append(f"Object {obj.get('id')} uses unknown layer '{layer}'")

            obj_type = str(obj.get("type") or "")
            if obj_type == "text" and "text" in checks:
                if not (obj.get("content") or "").strip():
                    sem_errors.append(f"Text object {obj.get('id')} has empty content")
                try:
                    if float(obj.get("fontSize") or 0) <= 0:
                        sem_errors.append(f"Text object {obj.get('id')} has invalid fontSize")
                except Exception:
                    sem_errors.append(f"Text object {obj.get('id')} has invalid fontSize")
                if not (obj.get("fontFamily") or "").strip():
                    sem_errors.append(f"Text object {obj.get('id')} missing fontFamily")

            if obj_type == "image" and "image" in checks:
                if not (obj.get("imageUrl") or "").strip():
                    sem_errors.append(f"Image object {obj.get('id')} missing imageUrl")

    return (len(sem_errors) == 0), sem_errors
