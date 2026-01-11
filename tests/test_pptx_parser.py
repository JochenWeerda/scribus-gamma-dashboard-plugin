import json
from pathlib import Path

from packages.layout_schema import validate_layout
from packages.pptx_parser.json_converter import (
    PptxExtractConvertConfig,
    convert_extracted_pptx_json_to_layout_json,
)


def test_convert_extracted_pptx_json_to_layout_json_schema_valid():
    sample = json.loads(Path("tests/fixtures/sample_pptx_extract.json").read_text(encoding="utf-8"))

    layout = convert_extracted_pptx_json_to_layout_json(
        sample,
        PptxExtractConvertConfig(
            width_px=1000,
            height_px=2000,
            dpi=300,
            include_ignored_text_boxes=False,
            ignored_text_boxes_as_overlay=False,
        ),
    )

    ok, errors = validate_layout(layout)
    assert ok, errors

    page = layout["pages"][0]
    assert page["pageNumber"] == 1
    # Ignored box should not be included
    assert any(o["type"] == "text" and o["content"] == "Hello Title" for o in page["objects"])
    assert not any(o["type"] == "text" and o.get("content") == "Ignored quote" for o in page["objects"])
    assert any(o["type"] == "image" for o in page["objects"])
    assert any(o["type"] == "rectangle" and o.get("fillColor") for o in page["objects"])

    # Sidebar should create a background rectangle and a text object with role metadata
    assert any(o["type"] == "rectangle" and o.get("role") == "sidebar_bg" for o in page["objects"])
    assert any(o["type"] == "text" and o.get("role") == "sidebar" for o in page["objects"])
