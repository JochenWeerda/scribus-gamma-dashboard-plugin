from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from packages.layout_schema import validate_layout

from .json_converter import (
    PptxExtractConvertConfig,
    convert_extracted_pptx_json_to_layout_json,
    load_extracted_pptx_json,
    write_layout_json,
)
from .project_init import load_project_init, resolve_project_metadata
from .tag_reader import find_sidecar_file, SidecarTags, apply_sidecar_tags
from .element_detector import normalize_extracted_pptx


@dataclass(frozen=True)
class ManifestConvertResult:
    outputs: List[Path]
    valid_count: int
    invalid: List[Tuple[Path, List[str]]]


def _load_manifest(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def convert_manifest_to_layout_jsons(
    *,
    manifest_path: str | Path,
    pptx_root_dir: str | Path = "media_pool/pptx",
    out_dir: str | Path = "media_pool/layout_json",
    config: PptxExtractConvertConfig = PptxExtractConvertConfig(),
    include_ignored_text_boxes: Optional[bool] = None,
    project_init_path: Optional[str | Path] = None,
    use_sidecar: bool = False,
) -> ManifestConvertResult:
    """
    Batch-Conversion:
    `tools/extract_pptx_assets.py` -> `media_pool/pptx/manifest.json`
    -> für jedes manifest.files[i].json eine Layout-JSON Datei schreiben.
    """

    manifest_path = Path(manifest_path)
    pptx_root_dir = Path(pptx_root_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = _load_manifest(manifest_path)
    files: List[Dict[str, Any]] = manifest.get("files") or []

    project_init: Optional[Dict[str, Any]] = None
    if project_init_path:
        project_init = load_project_init(Path(project_init_path))

    cfg = config
    if include_ignored_text_boxes is not None and include_ignored_text_boxes != config.include_ignored_text_boxes:
        cfg = PptxExtractConvertConfig(
            width_px=config.width_px,
            height_px=config.height_px,
            dpi=config.dpi,
            include_ignored_text_boxes=include_ignored_text_boxes,
        )

    outputs: List[Path] = []
    invalid: List[Tuple[Path, List[str]]] = []
    valid_count = 0

    for entry in files:
        name = entry.get("name") or "pptx"
        rel_json = entry.get("json")
        if not rel_json:
            continue

        # manifest files may contain Windows-style backslashes even when consumed on Linux
        src = pptx_root_dir / Path(str(rel_json).replace("\\", "/"))
        extracted = load_extracted_pptx_json(src)
        if use_sidecar:
            sidecar_path = find_sidecar_file(pptx_root_dir, name)
            if sidecar_path:
                extracted = apply_sidecar_tags(extracted, SidecarTags.load(sidecar_path))
        extracted = normalize_extracted_pptx(extracted)
        layout = convert_extracted_pptx_json_to_layout_json(extracted, cfg)

        if project_init:
            md = resolve_project_metadata(project_init, pptx_name=name)
            layout.setdefault("source", {})
            layout["source"]["chapter"] = md.chapter
            layout["source"]["act"] = md.act
            layout["source"]["act_title"] = md.act_title

        out_name = f"{name}.layout.json"
        if project_init:
            md = resolve_project_metadata(project_init, pptx_name=name)
            if md.chapter is not None:
                out_name = f"chapter_{md.chapter:02d}_{name}.layout.json"
        out_path = out_dir / out_name
        write_layout_json(out_path, layout)
        outputs.append(out_path)

        ok, errors = validate_layout(layout)
        if ok:
            valid_count += 1
        else:
            invalid.append((out_path, errors))

    return ManifestConvertResult(outputs=outputs, valid_count=valid_count, invalid=invalid)
