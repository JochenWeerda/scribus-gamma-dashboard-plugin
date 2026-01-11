from __future__ import annotations

import argparse
import json
from pathlib import Path

from packages.layout_schema import validate_layout

from .json_converter import (
    PptxExtractConvertConfig,
    convert_extracted_pptx_json_to_layout_json,
    load_extracted_pptx_json,
    write_layout_json,
)
from .manifest_converter import convert_manifest_to_layout_jsons
from .style_presets import apply_style_preset, list_style_presets
from .tag_reader import SidecarTags, apply_sidecar_tags, find_sidecar_file
from .element_detector import normalize_extracted_pptx
from .image_cropper import CropConfig, crop_from_rel_bbox, find_gamma_png


def _cmd_convert_one(args: argparse.Namespace) -> int:
    cfg = PptxExtractConvertConfig(
        width_px=args.width,
        height_px=args.height,
        dpi=args.dpi,
        include_ignored_text_boxes=args.include_ignored,
    )
    cfg = apply_style_preset(cfg, args.style)
    extracted = load_extracted_pptx_json(Path(args.input_path))
    if args.use_sidecar:
        name = extracted.get("name") or Path(args.input_path).stem
        pptx_root = Path(args.pptx_root)
        sidecar_path = find_sidecar_file(pptx_root, str(name))
        if sidecar_path:
            extracted = apply_sidecar_tags(extracted, SidecarTags.load(sidecar_path))
    extracted = normalize_extracted_pptx(extracted)
    layout_json = convert_extracted_pptx_json_to_layout_json(extracted, cfg)

    ok, errors = validate_layout(layout_json)
    if not ok:
        raise SystemExit("Schema validation failed:\n" + "\n".join(errors[:50]))

    write_layout_json(Path(args.output_path), layout_json)
    return 0


def _cmd_convert_manifest(args: argparse.Namespace) -> int:
    cfg = PptxExtractConvertConfig(
        width_px=args.width,
        height_px=args.height,
        dpi=args.dpi,
        include_ignored_text_boxes=args.include_ignored,
    )
    cfg = apply_style_preset(cfg, args.style)
    result = convert_manifest_to_layout_jsons(
        manifest_path=Path(args.manifest),
        pptx_root_dir=Path(args.pptx_root),
        out_dir=Path(args.out_dir),
        config=cfg,
        project_init_path=(Path(args.project_init) if args.project_init else None),
        use_sidecar=bool(args.use_sidecar),
    )

    report = {
        "manifest": str(Path(args.manifest)),
        "pptx_root": str(Path(args.pptx_root)),
        "out_dir": str(Path(args.out_dir)),
        "outputs": [str(p) for p in result.outputs],
        "valid": result.valid_count,
        "invalid": [{"path": str(p), "errors": errs} for (p, errs) in result.invalid],
    }

    if args.report:
        Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if result.invalid:
        print(f"[WARN] {len(result.invalid)} file(s) failed schema validation")
        return 2
    return 0


def _cmd_crop(args: argparse.Namespace) -> int:
    if args.png:
        png_path = Path(args.png)
    else:
        found = find_gamma_png(
            args.png_root,
            pptx_stem=args.pptx_name,
            slide_index=int(args.slide),
        )
        if not found:
            raise SystemExit("PNG not found. Provide --png or ensure naming under --png-root.")
        png_path = found

    rel_bbox = [float(x) for x in args.bbox.split(",")]
    if len(rel_bbox) != 4:
        raise SystemExit("--bbox must be 'x1,y1,x2,y2' (4 floats)")

    cfg = CropConfig(
        pad_px=int(args.pad_px),
        refine=bool(args.refine),
        refine_margin_px=int(args.refine_margin_px),
        bg_threshold=int(args.bg_threshold),
    )
    bbox_px = crop_from_rel_bbox(png_path, rel_bbox, Path(args.out), config=cfg)
    print(json.dumps({"png": str(png_path), "out": str(Path(args.out)), "bbox_px": bbox_px}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pptx_parser", description="PPTX parsing helpers.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    one = sub.add_parser("convert-one", help="Convert one extracted PPTX JSON to Layout JSON")
    one.add_argument("--in", dest="input_path", required=True)
    one.add_argument("--out", dest="output_path", required=True)
    one.add_argument("--width", type=int, default=2480)
    one.add_argument("--height", type=int, default=3508)
    one.add_argument("--dpi", type=int, default=300)
    one.add_argument("--include-ignored", action="store_true")
    one.add_argument("--style", default="", help=f"Optional style preset: {', '.join(list_style_presets())}")
    one.add_argument("--use-sidecar", action="store_true", help="Apply sidecar tags (opt-in)")
    one.add_argument("--pptx-root", default="media_pool/pptx", help="Where to search for sidecar files")
    one.set_defaults(func=_cmd_convert_one)

    man = sub.add_parser("convert-manifest", help="Convert all files listed in a manifest.json")
    man.add_argument("--manifest", default="media_pool/pptx/manifest.json")
    man.add_argument("--pptx-root", default="media_pool/pptx")
    man.add_argument("--out-dir", default="media_pool/layout_json")
    man.add_argument("--report", default="", help="Optional path to write a JSON report")
    man.add_argument(
        "--project-init",
        default="",
        help="Optional project_init.json path to enrich outputs with chapter/act metadata (e.g. .cursor/project_init.json.template)",
    )
    man.add_argument("--width", type=int, default=2480)
    man.add_argument("--height", type=int, default=3508)
    man.add_argument("--dpi", type=int, default=300)
    man.add_argument("--include-ignored", action="store_true")
    man.add_argument("--style", default="", help=f"Optional style preset: {', '.join(list_style_presets())}")
    man.add_argument("--use-sidecar", action="store_true", help="Apply sidecar tags (opt-in)")
    man.set_defaults(func=_cmd_convert_manifest)

    crop = sub.add_parser("crop", help="Crop a Gamma export PNG using a PPTX rel_bbox (0..1)")
    crop.add_argument("--png", default="", help="Explicit PNG path (optional)")
    crop.add_argument("--png-root", default=str(Path.home() / "Documents" / "Die verborgene Uhr Gottes" / "PNGs"))
    crop.add_argument("--pptx-name", default="", help="PPTX stem/name for PNG lookup (optional)")
    crop.add_argument("--slide", type=int, default=1, help="Slide index for PNG lookup (1-based)")
    crop.add_argument("--bbox", required=True, help="rel bbox: x1,y1,x2,y2 (0..1)")
    crop.add_argument("--out", required=True, help="Output crop PNG path")
    crop.add_argument("--pad-px", type=int, default=0)
    crop.add_argument("--refine", action="store_true", help="Refine boundaries using pixel analysis")
    crop.add_argument("--refine-margin-px", type=int, default=30)
    crop.add_argument("--bg-threshold", type=int, default=245)
    crop.set_defaults(func=_cmd_crop)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
