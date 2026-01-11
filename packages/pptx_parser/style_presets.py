from __future__ import annotations

from dataclasses import replace
from typing import Dict

from .json_converter import PptxExtractConvertConfig


def list_style_presets() -> list[str]:
    return ["magazin"]


def apply_style_preset(config: PptxExtractConvertConfig, preset: str) -> PptxExtractConvertConfig:
    """
    Apply a named style preset derived from the magazine design decisions.
    """

    preset = (preset or "").strip().lower()
    if not preset:
        return config

    if preset == "magazin":
        return replace(
            config,
            # Derived from MAGAZIN_WORKFLOW_DESIGN_DECISIONS.md (Body_Garamond etc.)
            font_family_body="Garamond",
            font_family_title="Garamond",
            font_family_quote="Garamond",
            font_size_body=12,
            font_size_title=24,
            font_size_h2=14,
            font_size_quote=10,
            # Layer names (match design decisions / Scribus project conventions)
            layer_bg="Hintergrund",
            layer_text="Text",
            layer_images="Images",
            layer_images_bg="Images_BG",
            layer_wrap="Wrap",
            layer_overlay="CaptionOverlay",
            # Paragraph style names (metadata)
            pstyle_title="Title_Gold",
            pstyle_h2="H2_Black",
            pstyle_body="Body_Garamond",
            pstyle_sidebar="Sidebar",
            pstyle_quote="Body_Garamond",
            pstyle_caption="Body_Garamond",
            # Colors
            title_color="#C9A227",
            body_color="#000000",
            quote_color="#333333",
            infobox_bg_color="#333333",
            infobox_text_color="#FFFFFF",
            infobox_pad_mm=2.5,
            sidebar_bg_color="#333333",
            sidebar_text_color="#FFFFFF",
            sidebar_pad_mm=2.5,
            sidebar_add_background=True,
        )

    raise ValueError(f"Unknown style preset: {preset}. Available: {', '.join(list_style_presets())}")
