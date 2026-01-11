from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Optional, Set


Severity = Literal["fail", "warn", "info"]


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    severity: Severity
    passed: bool
    message: str


def _iter_objects(layout_json: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    for page in layout_json.get("pages", []) or []:
        for obj in page.get("objects", []) or []:
            if isinstance(obj, dict):
                yield obj


def _mm_to_px(mm: float, dpi: float) -> float:
    return (float(mm) / 25.4) * float(dpi)


def evaluate_quality_gate(
    layout_json: Dict[str, Any],
    *,
    project_init: Optional[Dict[str, Any]] = None,
) -> List[CheckResult]:
    """
    Pragmatic "production gate" for layout JSON.

    - fail: blocks production export
    - warn: export allowed but flagged
    - info: diagnostics only

    This complements schema/preflight checks with project-specific constraints.
    """

    project_init = project_init or {}
    results: List[CheckResult] = []

    doc = layout_json.get("document") or {}
    w = float(doc.get("width") or 0)
    h = float(doc.get("height") or 0)
    dpi = float(doc.get("dpi") or 0)

    # Document sanity (FAIL)
    if w <= 0 or h <= 0:
        results.append(CheckResult("document.dimensions", "fail", False, "Document width/height must be > 0"))
    else:
        results.append(CheckResult("document.dimensions", "info", True, f"Document size OK: {w}x{h}px"))

    if dpi <= 0:
        results.append(CheckResult("document.dpi", "fail", False, "Document dpi must be > 0"))
    else:
        results.append(CheckResult("document.dpi", "info", True, f"DPI OK: {dpi}"))

    # Page numbering (WARN)
    page_numbers: List[int] = []
    for p in layout_json.get("pages", []) or []:
        try:
            page_numbers.append(int(p.get("pageNumber") or 0))
        except Exception:
            page_numbers.append(0)
    if (0 in set(page_numbers)) or (len(set(page_numbers)) != len(page_numbers)):
        results.append(CheckResult("pages.numbering", "warn", False, f"Invalid/duplicate pageNumber(s): {page_numbers}"))
    else:
        results.append(CheckResult("pages.numbering", "info", True, f"Pages: {len(page_numbers)}"))

    # Object IDs unique (WARN)
    ids = [str(o.get("id") or "") for o in _iter_objects(layout_json)]
    ids_nonempty = [x for x in ids if x.strip()]
    if len(ids_nonempty) != len(ids):
        results.append(CheckResult("objects.unique_ids", "warn", False, "Empty object id(s) detected"))
    elif len(ids_nonempty) != len(set(ids_nonempty)):
        results.append(CheckResult("objects.unique_ids", "warn", False, "Duplicate object id(s) detected"))
    else:
        results.append(CheckResult("objects.unique_ids", "info", True, f"Objects: {len(ids_nonempty)}"))

    # Known layers (WARN) if defined
    allowed_layers: Optional[Set[str]] = None
    layers_cfg = (project_init.get("layout") or {}).get("layers")
    if isinstance(layers_cfg, (list, tuple)) and layers_cfg:
        allowed_layers = {str(x) for x in layers_cfg if str(x).strip()}
    if allowed_layers:
        bad = set()
        for obj in _iter_objects(layout_json):
            layer = str(obj.get("layer") or "").strip()
            if layer and layer not in allowed_layers:
                bad.add(layer)
        if bad:
            results.append(CheckResult("layout.layers", "warn", False, f"Unknown layer(s) used: {sorted(bad)}"))
        else:
            results.append(CheckResult("layout.layers", "info", True, "All layers match project_init"))

    # Fonts declared (WARN) if typography.fonts provided
    fonts_cfg = (project_init.get("typography") or {}).get("fonts")
    declared_fonts: Optional[Set[str]] = None
    if isinstance(fonts_cfg, (list, tuple)) and fonts_cfg:
        declared_fonts = {str(f.get("family") or "") for f in fonts_cfg if isinstance(f, dict) and f.get("family")}
        declared_fonts = {f for f in declared_fonts if f.strip()}
    if declared_fonts:
        unknown = set()
        for obj in _iter_objects(layout_json):
            if str(obj.get("type") or "") != "text":
                continue
            ff = str(obj.get("fontFamily") or "").strip()
            if ff and ff not in declared_fonts:
                unknown.add(ff)
        if unknown:
            results.append(CheckResult("typography.fonts", "warn", False, f"Undeclared font(s): {sorted(unknown)}"))
        else:
            results.append(CheckResult("typography.fonts", "info", True, "All fonts declared in project_init"))

    # Images must have imageUrl (FAIL)
    missing_images = 0
    for obj in _iter_objects(layout_json):
        if str(obj.get("type") or "") != "image":
            continue
        if not str(obj.get("imageUrl") or "").strip():
            missing_images += 1
    if missing_images:
        results.append(CheckResult("images.urls", "fail", False, f"{missing_images} image object(s) missing imageUrl"))
    else:
        results.append(CheckResult("images.urls", "info", True, "All image objects have imageUrl"))

    # Bleed requirement for color variant (FAIL if variant name indicates color)
    variant = layout_json.get("variant") or {}
    variant_name = str(variant.get("name") or variant.get("variant") or "")
    bleed_mm = float(variant.get("bleed_mm") or 0.0)
    require_bleed_mm = float((project_init.get("print") or {}).get("bleed_mm") or 3.0)
    if variant_name.lower() in {"color", "colour"}:
        if bleed_mm + 1e-6 < require_bleed_mm:
            results.append(CheckResult("print.bleed", "fail", False, f"Color variant requires bleed_mm >= {require_bleed_mm}"))
        else:
            results.append(CheckResult("print.bleed", "info", True, f"Bleed OK: {bleed_mm}mm"))

    # Amazon safety margin (FAIL when amazon.enabled and margin > 0)
    amazon_cfg = project_init.get("amazon") or {}
    is_amazon = str(amazon_cfg.get("enabled") or "").lower() in {"1", "true", "yes"}
    if is_amazon and w > 0 and h > 0 and dpi > 0:
        safety_mm = float(amazon_cfg.get("safety_margin_mm") or 0.0)
        m = _mm_to_px(safety_mm, dpi)
        if m > 0:
            bad = 0
            for obj in _iter_objects(layout_json):
                bbox = obj.get("bbox") or {}
                if not {"x", "y", "w", "h"} <= set(bbox.keys()):
                    continue
                x = float(bbox["x"])
                y = float(bbox["y"])
                bw = float(bbox["w"])
                bh = float(bbox["h"])
                if x < m or y < m or (x + bw) > (w - m) or (y + bh) > (h - m):
                    bad += 1
            if bad:
                results.append(CheckResult("amazon.safe_area", "fail", False, f"{bad} object(s) violate safety margin ({safety_mm}mm)"))
            else:
                results.append(CheckResult("amazon.safe_area", "info", True, f"All objects within safety margin ({safety_mm}mm)"))

    # Local file existence (WARN) - only for absolute paths
    missing_local: List[str] = []
    for obj in _iter_objects(layout_json):
        if str(obj.get("type") or "") != "image":
            continue
        url = str(obj.get("imageUrl") or "")
        if not url:
            continue
        if url.startswith(("http://", "https://", "/v1/artifacts/")):
            continue
        p = Path(url)
        if p.is_absolute() and not p.exists():
            missing_local.append(url)
    if missing_local:
        results.append(CheckResult("images.local_files", "warn", False, f"Missing local image file(s): {missing_local[:10]}"))

    return results


def summarize_quality_gate(results: List[CheckResult]) -> Dict[str, Any]:
    fails = [r for r in results if r.severity == "fail" and not r.passed]
    warns = [r for r in results if r.severity == "warn" and not r.passed]
    return {
        "passed": len(fails) == 0,
        "fail_count": len(fails),
        "warn_count": len(warns),
        "results": [{"id": r.check_id, "severity": r.severity, "passed": r.passed, "message": r.message} for r in results],
    }

