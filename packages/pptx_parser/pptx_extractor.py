from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ExtractResult:
    manifest_path: Path
    out_dir: Path


def extract_with_stage0_tool(
    *,
    ppt_dir: Path,
    out_dir: Path = Path("media_pool/pptx"),
    limit: int = 0,
    only: Optional[list[str]] = None,
) -> ExtractResult:
    """
    Wrapper around the existing Stage-0 extractor `tools/extract_pptx_assets.py`.
    Keeps behavior consistent while providing the `packages.pptx_parser.pptx_extractor` entrypoint
    expected by the design docs.
    """

    env = os.environ.copy()
    env["ZC_PPT_DIR"] = str(ppt_dir)
    if limit:
        env["ZC_PPTX_LIMIT"] = str(int(limit))
    if only:
        env["ZC_PPTX_ONLY"] = ",".join(only)

    script = Path("tools") / "extract_pptx_assets.py"
    cmd = [sys.executable, str(script)]
    subprocess.check_call(cmd, env=env)
    return ExtractResult(manifest_path=out_dir / "manifest.json", out_dir=out_dir)
