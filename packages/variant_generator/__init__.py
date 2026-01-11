"""Variant Generator (MVP).

Transforms Layout JSON into different publishing variants:
- color -> grayscale (simple RGB/hex based)
- A4 <-> 8x11.5 conversions (scale bboxes)
- bleed on/off (expand page and shift)
"""

from .color_to_grayscale import convert_layout_colors_to_grayscale
from .format_converter import convert_layout_format
from .bleed_manager import apply_bleed
from .amazon_validator import validate_kdp_layout

__all__ = [
    "convert_layout_colors_to_grayscale",
    "convert_layout_format",
    "apply_bleed",
    "validate_kdp_layout",
]

