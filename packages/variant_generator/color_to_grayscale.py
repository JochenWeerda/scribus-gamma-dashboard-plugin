from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = (hex_color or "").strip()
    if not h:
        return 0, 0, 0
    if h.startswith("#"):
        h = h[1:]
    if len(h) != 6:
        return 0, 0, 0
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"#{r:02x}{g:02x}{b:02x}"


def _to_gray(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    r, g, b = rgb
    # sRGB luminance (approx)
    y = int(round(0.2126 * r + 0.7152 * g + 0.0722 * b))
    y = max(0, min(255, y))
    return (y, y, y)


def convert_layout_colors_to_grayscale(layout_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert hex colors on supported object fields to grayscale.
    This is a pragmatic MVP (no CMYK profiles, no images).
    """

    out = deepcopy(layout_json)
    for page in out.get("pages", []) or []:
        for obj in page.get("objects", []) or []:
            if obj.get("type") == "text":
                if isinstance(obj.get("color"), str) and obj["color"].startswith("#"):
                    obj["color"] = _rgb_to_hex(_to_gray(_hex_to_rgb(obj["color"])))
            if obj.get("type") == "rectangle":
                if isinstance(obj.get("fillColor"), str) and obj["fillColor"].startswith("#"):
                    obj["fillColor"] = _rgb_to_hex(_to_gray(_hex_to_rgb(obj["fillColor"])))
                if isinstance(obj.get("strokeColor"), str) and obj["strokeColor"].startswith("#"):
                    obj["strokeColor"] = _rgb_to_hex(_to_gray(_hex_to_rgb(obj["strokeColor"])))
    out.setdefault("variant", {})
    out["variant"]["colors"] = "grayscale"
    return out

