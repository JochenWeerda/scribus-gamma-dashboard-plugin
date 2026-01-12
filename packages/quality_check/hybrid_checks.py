from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class HeuristicConfig:
    # Text overflow heuristic
    avg_char_width_em: float = 0.6  # ~0.5-0.6 is typical for Latin fonts
    line_height_em: float = 1.2
    overflow_warn_ratio: float = 1.0  # >1 means text likely doesn't fit
    overflow_info_ratio: float = 0.9  # >0.9 means tight fit

    # Page density heuristic
    objects_per_page_warn: int = 80


def _as_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return float(default)


def _as_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return int(default)


def _iter_pages(layout_json: Dict[str, Any]):
    for page in layout_json.get("pages", []) or []:
        if isinstance(page, dict):
            yield page


def _iter_objects(page: Dict[str, Any]):
    for obj in page.get("objects", []) or []:
        if isinstance(obj, dict):
            yield obj


def estimate_text_overflow_ratio(
    *,
    text: str,
    bbox_w: float,
    bbox_h: float,
    font_size: float,
    cfg: HeuristicConfig,
) -> Optional[float]:
    """
    Estimate overflow risk as (needed_height / available_height).
    Returns None if not enough inputs.
    """

    if not text or bbox_w <= 0 or bbox_h <= 0 or font_size <= 0:
        return None

    # chars per line (rough)
    char_w = max(0.1, cfg.avg_char_width_em * font_size)
    cpl = max(1.0, bbox_w / char_w)

    # count "visual" characters (ignore excessive whitespace)
    compact = " ".join(text.split())
    n = len(compact)
    if n <= 0:
        return None

    # line count (simple)
    lines = max(1.0, (n / cpl))
    line_h = max(0.1, cfg.line_height_em * font_size)
    needed_h = lines * line_h

    return needed_h / bbox_h


def run_heuristic_checks(
    layout_json: Dict[str, Any],
    *,
    config: Optional[HeuristicConfig] = None,
) -> Dict[str, Any]:
    """
    Warn-only checks:
    - text_overflow_risk: estimates if text likely doesn't fit its bbox
    - page_density: objects-per-page beyond threshold

    Output is designed to be stable/deterministic given identical inputs.
    """

    cfg = config or HeuristicConfig()

    warnings: List[Dict[str, Any]] = []
    infos: List[Dict[str, Any]] = []

    pages_summary: List[Dict[str, Any]] = []
    for page in _iter_pages(layout_json):
        pn = _as_int(page.get("pageNumber"), 0)
        objs = list(_iter_objects(page))
        pages_summary.append({"pageNumber": pn, "objectCount": len(objs)})

        if len(objs) >= cfg.objects_per_page_warn:
            warnings.append(
                {
                    "id": "page.density",
                    "page": pn,
                    "message": f"High object count on page {pn}: {len(objs)} objects",
                    "objectCount": len(objs),
                }
            )

        for obj in objs:
            if str(obj.get("type") or "") != "text":
                continue
            text = str(obj.get("content") or "")
            bbox = obj.get("bbox") or {}
            ratio = estimate_text_overflow_ratio(
                text=text,
                bbox_w=_as_float(bbox.get("w"), 0.0),
                bbox_h=_as_float(bbox.get("h"), 0.0),
                font_size=_as_float(obj.get("fontSize"), 0.0),
                cfg=cfg,
            )
            if ratio is None:
                continue

            entry = {
                "id": "text.overflow_risk",
                "page": pn,
                "objectId": obj.get("id"),
                "ratio": round(float(ratio), 4),
                "message": "Estimated text overflow risk (needed_height / bbox_height)",
            }
            if ratio > cfg.overflow_warn_ratio:
                warnings.append(entry)
            elif ratio > cfg.overflow_info_ratio:
                infos.append(entry)

    return {
        "passed": True,  # warn-only module
        "warnings": warnings,
        "infos": infos,
        "summary": {
            "pages": pages_summary,
            "warnCount": len(warnings),
            "infoCount": len(infos),
            "config": {
                "avg_char_width_em": cfg.avg_char_width_em,
                "line_height_em": cfg.line_height_em,
                "overflow_warn_ratio": cfg.overflow_warn_ratio,
                "overflow_info_ratio": cfg.overflow_info_ratio,
                "objects_per_page_warn": cfg.objects_per_page_warn,
            },
        },
    }

