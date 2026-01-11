import json
from pathlib import Path

from packages.pptx_parser.manifest_converter import convert_manifest_to_layout_jsons
from packages.pptx_parser.json_converter import PptxExtractConvertConfig
from packages.pptx_parser.style_presets import apply_style_preset


def test_sidecar_only_applied_when_flag_set(tmp_path: Path):
    pptx_root = tmp_path / "pptx"
    (pptx_root / "json").mkdir(parents=True)
    (pptx_root / "sidecar").mkdir(parents=True)

    extracted = {
        "source": "x.pptx",
        "name": "sample",
        "slides": [
            {
                "slide": 1,
                "text_boxes": [
                    {"text": "Sidebar via sidecar", "rel_bbox": [0.7, 0.4, 0.95, 0.58], "role": "body", "ignore": False}
                ],
                "image_boxes": [],
                "infoboxes": [],
            }
        ],
    }
    (pptx_root / "json" / "sample.json").write_text(json.dumps(extracted, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest = {"files": [{"name": "sample", "json": "json/sample.json"}]}
    (pptx_root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    sidecar = {"slides": {"1": {"text_boxes": {"0": {"role": "sidebar"}}}}}
    (pptx_root / "sidecar" / "sample.json").write_text(json.dumps(sidecar, ensure_ascii=False, indent=2), encoding="utf-8")

    cfg = apply_style_preset(PptxExtractConvertConfig(width_px=1000, height_px=2000, dpi=300), "magazin")

    out_dir_a = tmp_path / "out_a"
    res_a = convert_manifest_to_layout_jsons(
        manifest_path=pptx_root / "manifest.json",
        pptx_root_dir=pptx_root,
        out_dir=out_dir_a,
        config=cfg,
        use_sidecar=False,
    )
    layout_a = json.loads(res_a.outputs[0].read_text(encoding="utf-8"))
    roles_a = {o.get("role") for o in layout_a["pages"][0]["objects"] if o.get("type") == "text"}
    assert "sidebar" not in roles_a

    out_dir_b = tmp_path / "out_b"
    res_b = convert_manifest_to_layout_jsons(
        manifest_path=pptx_root / "manifest.json",
        pptx_root_dir=pptx_root,
        out_dir=out_dir_b,
        config=cfg,
        use_sidecar=True,
    )
    layout_b = json.loads(res_b.outputs[0].read_text(encoding="utf-8"))
    roles_b = {o.get("role") for o in layout_b["pages"][0]["objects"] if o.get("type") == "text"}
    assert "sidebar" in roles_b
    assert any(o.get("role") == "sidebar_bg" for o in layout_b["pages"][0]["objects"])

