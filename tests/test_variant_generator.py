import json
from pathlib import Path

from packages.variant_generator import (
    apply_bleed,
    convert_layout_colors_to_grayscale,
    convert_layout_format,
)


def _sample_layout():
    return {
        "version": "1.0.0",
        "document": {"width": 1000, "height": 2000, "dpi": 300},
        "pages": [
            {
                "pageNumber": 1,
                "objects": [
                    {
                        "id": "t1",
                        "type": "text",
                        "bbox": {"x": 10, "y": 20, "w": 100, "h": 30},
                        "layer": "Text",
                        "content": "Hello",
                        "color": "#ff0000",
                    },
                    {
                        "id": "r1",
                        "type": "rectangle",
                        "bbox": {"x": 50, "y": 60, "w": 200, "h": 100},
                        "layer": "Wrap",
                        "fillColor": "#00ff00",
                        "strokeColor": "#0000ff",
                        "strokeWidth": 1,
                    },
                ],
            }
        ],
    }


def test_grayscale_conversion_changes_hex_colors():
    layout = _sample_layout()
    gray = convert_layout_colors_to_grayscale(layout)
    objs = gray["pages"][0]["objects"]
    assert objs[0]["color"].startswith("#")
    assert objs[0]["color"] != "#ff0000"
    assert objs[1]["fillColor"] != "#00ff00"
    assert gray["variant"]["colors"] == "grayscale"


def test_format_conversion_scales_bbox_and_doc():
    layout = _sample_layout()
    converted = convert_layout_format(layout, target_format="A4")
    assert converted["document"]["width"] != 1000
    assert converted["document"]["height"] != 2000
    bbox = converted["pages"][0]["objects"][0]["bbox"]
    assert bbox["x"] != 10
    assert converted["variant"]["format"] == "A4"


def test_bleed_expands_doc_and_shifts_objects():
    layout = _sample_layout()
    b = apply_bleed(layout, bleed_mm=3.0)
    assert b["document"]["width"] > layout["document"]["width"]
    assert b["pages"][0]["objects"][0]["bbox"]["x"] > layout["pages"][0]["objects"][0]["bbox"]["x"]

