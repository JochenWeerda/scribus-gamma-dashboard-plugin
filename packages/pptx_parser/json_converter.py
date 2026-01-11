from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class PptxExtractConvertConfig:
    width_px: int = 2480
    height_px: int = 3508
    dpi: int = 300
    include_ignored_text_boxes: bool = False
    ignored_text_boxes_as_overlay: bool = True

    # Layer defaults (can be overridden by style presets)
    layer_bg: str = "Background"
    layer_text: str = "Text"
    layer_images: str = "Images"
    layer_images_bg: str = "Images_BG"
    layer_wrap: str = "Wrap"
    layer_overlay: str = "Overlay"

    # Typography defaults (MVP; can be driven by project config later)
    font_family_body: str = "Arial"
    font_family_title: str = "Arial"
    font_family_quote: str = "Arial"

    font_size_body: int = 12
    font_size_title: int = 20
    font_size_h2: int = 14
    font_size_quote: int = 10

    # Scribus paragraph style names (optional metadata)
    pstyle_title: str = "Title_Gold"
    pstyle_h2: str = "H2_Black"
    pstyle_body: str = "Body_Garamond"
    pstyle_sidebar: str = "Sidebar"
    pstyle_quote: str = "Body_Garamond"
    pstyle_caption: str = "Body_Garamond"

    # Colors (hex; derived from design decisions)
    title_color: str = "#C9A227"  # gold approximation
    body_color: str = "#000000"
    quote_color: str = "#333333"

    # Infobox styling (derived from design decisions)
    infobox_bg_color: str = "#333333"
    infobox_bg_opacity: float = 1.0
    infobox_text_color: str = "#FFFFFF"
    infobox_pad_mm: float = 2.5

    # Sidebar styling (derived from design decisions)
    sidebar_bg_color: str = "#333333"
    sidebar_bg_opacity: float = 1.0
    sidebar_text_color: str = "#FFFFFF"
    sidebar_pad_mm: float = 2.5
    sidebar_add_background: bool = True


def mm_to_px(mm: float, dpi: int) -> float:
    return (mm / 25.4) * float(dpi)


def load_extracted_pptx_json(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8"))


def write_layout_json(path: str | Path, layout_json: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(layout_json, ensure_ascii=False, indent=2), encoding="utf-8")


def _bbox_from_rel(rel_bbox: List[float], config: PptxExtractConvertConfig) -> Dict[str, float]:
    x1, y1, x2, y2 = rel_bbox
    x = max(0.0, min(float(config.width_px), x1 * config.width_px))
    y = max(0.0, min(float(config.height_px), y1 * config.height_px))
    w = max(1.0, min(float(config.width_px) - x, (x2 - x1) * config.width_px))
    h = max(1.0, min(float(config.height_px) - y, (y2 - y1) * config.height_px))
    return {"x": x, "y": y, "w": w, "h": h}


def _role_to_layer(role: Optional[str]) -> str:
    # Scribus-Layer-Konzept: Hintergrund / Images / Text / Overlay.
    # Für den MVP halten wir es simpel und nutzen "Text" und "Images".
    if not role:
        return "Text"
    r = role.lower()
    if "image" in r:
        return "Images"
    if r in {"overlay", "captionoverlay"}:
        return "Overlay"
    if r in {"wrap"}:
        return "Wrap"
    if r in {"background", "hintergrund"}:
        return "Background"
    # title/body/infobox/quote -> Text (quote kann optional Overlay sein)
    return "Text"


def _role_to_layer_cfg(role: Optional[str], config: PptxExtractConvertConfig) -> str:
    if not role:
        return config.layer_text

    r = role.lower()
    if r in {"background", "hintergrund"}:
        return config.layer_bg
    if "image" in r:
        return config.layer_images
    if r in {"images_bg", "image_bg"}:
        return config.layer_images_bg
    if r in {"overlay", "captionoverlay", "caption", "infobox"}:
        return config.layer_overlay
    if r in {"wrap"}:
        return config.layer_wrap

    return config.layer_text


def _role_to_zorder(layer: str, role: Optional[str]) -> int:
    # Align with packages/sla_compiler/compiler.py:get_layer_zorder() mapping.
    if layer in {"Background", "Hintergrund"}:
        return 0
    if layer in {"Images_BG"}:
        return 10
    if layer == "Images":
        return 20
    if layer == "Text":
        if role and role.lower() in {"title", "h1", "headline"}:
            return 35
        return 30
    if layer in {"Overlay", "CaptionOverlay"}:
        return 40
    if layer == "Wrap":
        return 50
    return 30


def _layer_to_zorder_cfg(layer: str, role: Optional[str], config: PptxExtractConvertConfig) -> int:
    if layer == config.layer_bg:
        return 0
    if layer == config.layer_images_bg:
        return 10
    if layer == config.layer_images:
        return 20
    if layer == config.layer_text:
        r = (role or "").lower()
        if r in {"title", "h1", "headline"}:
            return 35
        if r in {"h2"}:
            return 34
        if r in {"quote"}:
            return 32
        return 30
    if layer == config.layer_overlay:
        return 40
    if layer == config.layer_wrap:
        return 50
    return 30


def _text_style_for_role(role: Optional[str], config: PptxExtractConvertConfig) -> Dict[str, Any]:
    r = (role or "").lower()
    if r in {"title", "h1", "headline"}:
        return {
            "fontFamily": config.font_family_title,
            "fontSize": config.font_size_title,
            "fontWeight": "bold",
            "color": config.title_color,
            "align": "left",
            "pStyle": config.pstyle_title,
        }
    if r in {"h2"}:
        return {
            "fontFamily": config.font_family_body,
            "fontSize": config.font_size_h2,
            "fontWeight": "bold",
            "color": config.body_color,
            "align": "left",
            "pStyle": config.pstyle_h2,
        }
    if r in {"quote"}:
        return {
            "fontFamily": config.font_family_quote,
            "fontSize": config.font_size_quote,
            "fontWeight": "normal",
            "color": config.quote_color,
            "align": "left",
            "pStyle": config.pstyle_quote,
        }
    if r in {"sidebar"}:
        return {
            "fontFamily": config.font_family_body,
            "fontSize": config.font_size_body,
            "fontWeight": "normal",
            "color": config.sidebar_text_color,
            "align": "left",
            "pStyle": config.pstyle_sidebar,
        }
    return {
        "fontFamily": config.font_family_body,
        "fontSize": config.font_size_body,
        "fontWeight": "normal",
        "color": config.body_color,
        "align": "left",
        "pStyle": config.pstyle_body,
    }


def convert_extracted_pptx_json_to_layout_json(
    extracted: Dict[str, Any],
    config: PptxExtractConvertConfig = PptxExtractConvertConfig(),
    *,
    page_number_offset: int = 0,
) -> Dict[str, Any]:
    """
    Konvertiert das Output-Format von `tools/extract_pptx_assets.py` (intermediate JSON)
    in das MVP Layout-JSON Schema (`packages/layout_schema/layout-mvp.schema.json`).
    """

    slides: List[Dict[str, Any]] = extracted.get("slides", []) or []
    pages: List[Dict[str, Any]] = []

    for slide in slides:
        slide_no = int(slide.get("slide", 0) or 0)
        page_number = max(1, slide_no + page_number_offset) if slide_no else (len(pages) + 1 + page_number_offset)

        objects: List[Dict[str, Any]] = []
        obj_index = 0

        # Infoboxes (background rectangle + text)
        for ibox in (slide.get("infoboxes") or []):
            rel_bbox = ibox.get("rel_bbox")
            if not rel_bbox or len(rel_bbox) != 4:
                continue

            box = _bbox_from_rel(rel_bbox, config)
            layer = config.layer_overlay
            pad_px = mm_to_px(config.infobox_pad_mm, config.dpi)
            inner = {
                "x": box["x"] + pad_px,
                "y": box["y"] + pad_px,
                "w": max(1.0, box["w"] - 2 * pad_px),
                "h": max(1.0, box["h"] - 2 * pad_px),
            }

            objects.append(
                {
                    "id": f"s{page_number:03d}_ibox_bg_{obj_index}",
                    "type": "rectangle",
                    "bbox": box,
                    "layer": layer,
                    "zOrder": 39,
                    "role": "infobox_bg",
                    "fillColor": config.infobox_bg_color,
                    "fillOpacity": float(config.infobox_bg_opacity),
                    "strokeWidth": 0,
                    "strokeOpacity": 0.0,
                }
            )
            obj_index += 1

            objects.append(
                {
                    "id": f"s{page_number:03d}_ibox_text_{obj_index}",
                    "type": "text",
                    "bbox": inner,
                    "layer": layer,
                    "zOrder": 40,
                    "role": "infobox",
                    "content": ibox.get("text") or "",
                    "fontFamily": config.font_family_body,
                    "fontSize": config.font_size_body,
                    "fontWeight": "normal",
                    "color": config.infobox_text_color,
                    "align": "left",
                    "pStyle": config.pstyle_sidebar,
                    "columns": 1,
                    "columnGap": 0,
                }
            )
            obj_index += 1

        # Text boxes
        for tb in (slide.get("text_boxes") or []):
            role = tb.get("role")
            ignored = tb.get("ignore") is True
            if ignored and not config.include_ignored_text_boxes:
                if not config.ignored_text_boxes_as_overlay:
                    continue
                # keep ignored boxes, but place them in Overlay by default
                role = "overlay"

            rel_bbox = tb.get("rel_bbox")
            if not rel_bbox or len(rel_bbox) != 4:
                continue

            content = tb.get("text") or ""
            layer = _role_to_layer_cfg(role, config)
            style = _text_style_for_role(tb.get("role"), config)

            bbox = _bbox_from_rel(rel_bbox, config)
            role_norm = (tb.get("role") or role or "").strip() or None

            if (role_norm or "").lower() == "sidebar" and config.sidebar_add_background:
                bg_layer = config.layer_wrap
                objects.append(
                    {
                        "id": f"s{page_number:03d}_sidebar_bg_{obj_index}",
                        "type": "rectangle",
                        "bbox": bbox,
                        "layer": bg_layer,
                        "zOrder": _layer_to_zorder_cfg(bg_layer, "sidebar_bg", config),
                        "role": "sidebar_bg",
                        "fillColor": config.sidebar_bg_color,
                        "fillOpacity": float(config.sidebar_bg_opacity),
                        "strokeWidth": 0,
                        "strokeOpacity": 0.0,
                    }
                )
                obj_index += 1

                pad_px = mm_to_px(config.sidebar_pad_mm, config.dpi)
                bbox = {
                    "x": bbox["x"] + pad_px,
                    "y": bbox["y"] + pad_px,
                    "w": max(1.0, bbox["w"] - 2 * pad_px),
                    "h": max(1.0, bbox["h"] - 2 * pad_px),
                }

            objects.append(
                {
                    "id": f"s{page_number:03d}_text_{obj_index}",
                    "type": "text",
                    "bbox": bbox,
                    "layer": layer,
                    "zOrder": _layer_to_zorder_cfg(layer, tb.get("role"), config),
                    "role": role_norm,
                    "content": content,
                    **style,
                    "columns": 1,
                    "columnGap": 0,
                }
            )
            obj_index += 1

        # Image boxes
        for i, ib in enumerate((slide.get("image_boxes") or [])):
            rel_bbox = ib.get("rel_bbox")
            if not rel_bbox or len(rel_bbox) != 4:
                continue

            image_path = ib.get("image") or ""
            objects.append(
                {
                    "id": f"s{page_number:03d}_img_{obj_index}",
                    "type": "image",
                    "bbox": _bbox_from_rel(rel_bbox, config),
                    "layer": config.layer_images,
                    "zOrder": _layer_to_zorder_cfg(config.layer_images, None, config),
                    "role": "image",
                    "sourceSlide": slide_no or page_number,
                    "sourceIndex": i,
                    "sourceKind": "image_box",
                    "imageUrl": image_path,
                    "scaleToFrame": True,
                    "maintainAspectRatio": True,
                }
            )
            obj_index += 1

        pages.append({"pageNumber": page_number, "objects": objects})

    return {
        "version": "1.0.0",
        "document": {"width": config.width_px, "height": config.height_px, "dpi": config.dpi},
        "pages": pages or [{"pageNumber": 1, "objects": []}],
        "meta": {
            "grid": {
                "cols": 6,
                "gutter_mm": 5.0,
                "body_cols": 4,
                "side_cols": 2,
                "baseline_mm": 4.0,
            },
            "layers": {
                "background": config.layer_bg,
                "images_bg": config.layer_images_bg,
                "images": config.layer_images,
                "text": config.layer_text,
                "wrap": config.layer_wrap,
                "overlay": config.layer_overlay,
            },
        },
        "source": {
            "kind": "pptx_extract_json",
            "name": extracted.get("name"),
            "path": extracted.get("source"),
        },
    }
