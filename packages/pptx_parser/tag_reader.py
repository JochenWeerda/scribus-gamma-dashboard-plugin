from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


@dataclass(frozen=True)
class SidecarTags:
    """
    Minimal structure:
    {
      "slides": {
        "1": { "text_boxes": { "0": {"role": "sidebar"} } }
      }
    }
    """

    data: Dict[str, Any]

    @staticmethod
    def load(path: Path) -> "SidecarTags":
        if path.suffix.lower() in {".yaml", ".yml"}:
            if yaml is None:
                raise RuntimeError("PyYAML not installed but YAML sidecar file was provided")
            return SidecarTags(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
        return SidecarTags(json.loads(path.read_text(encoding="utf-8")))


def find_sidecar_file(pptx_root: Path, pptx_name: str) -> Optional[Path]:
    candidates = [
        pptx_root / "sidecar" / f"{pptx_name}.json",
        pptx_root / "sidecar" / f"{pptx_name}.sidecar.json",
        pptx_root / "sidecar" / f"{pptx_name}.yaml",
        pptx_root / "sidecar" / f"{pptx_name}.yml",
        pptx_root / f"{pptx_name}.sidecar.json",
        pptx_root / f"{pptx_name}.sidecar.yaml",
        pptx_root / f"{pptx_name}.sidecar.yml",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def apply_sidecar_tags(extracted: Dict[str, Any], tags: SidecarTags) -> Dict[str, Any]:
    """
    Apply role/ignore overrides to Stage-0 extractor output.
    Unknown tags are ignored.
    """

    out = json.loads(json.dumps(extracted))
    slide_map = (tags.data.get("slides") or {}) if isinstance(tags.data, dict) else {}

    for slide in out.get("slides", []) or []:
        slide_no = str(slide.get("slide") or "")
        s_cfg = slide_map.get(slide_no) or {}
        tb_cfg = ((s_cfg.get("text_boxes") or {}) if isinstance(s_cfg, dict) else {}) if s_cfg else {}

        tbs = slide.get("text_boxes") or []
        for idx, tb in enumerate(tbs):
            override = tb_cfg.get(str(idx)) or tb_cfg.get(idx)
            if not isinstance(override, dict):
                continue
            if "role" in override:
                tb["role"] = override["role"]
            if "ignore" in override:
                tb["ignore"] = bool(override["ignore"])

    return out
