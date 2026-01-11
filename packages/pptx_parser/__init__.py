"""PPTX parsing utilities (PPTX -> intermediate JSON -> Layout JSON)."""

from .json_converter import (
    PptxExtractConvertConfig,
    convert_extracted_pptx_json_to_layout_json,
    load_extracted_pptx_json,
    write_layout_json,
)

