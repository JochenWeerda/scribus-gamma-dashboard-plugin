#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_manifest(zf: zipfile.ZipFile, manifest: Dict[str, Any]) -> None:
    # Normalize Windows separators so Linux containers can resolve paths
    for f in manifest.get("files") or []:
        if isinstance(f, dict) and isinstance(f.get("json"), str):
            f["json"] = f["json"].replace("\\", "/")
    zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))


def build_bundle(
    *,
    extracted_root: Path,
    out_zip: Path,
    pptx_names: Optional[List[str]] = None,
    gamma_zip_dir: Optional[Path] = None,
    project_init: Optional[Path] = None,
) -> Path:
    extracted_root = extracted_root.resolve()
    manifest_path = extracted_root / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"manifest.json not found: {manifest_path}")

    manifest = _load_json(manifest_path)
    files = manifest.get("files") or []
    if pptx_names:
        wanted = set(pptx_names)
        files = [f for f in files if (f.get("name") in wanted)]
        manifest["files"] = files

    out_zip.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        _write_manifest(zf, manifest)

        # Add extracted json files under json/
        for f in files:
            rel = f.get("json")
            if not rel:
                continue
            src = extracted_root / Path(str(rel).replace("\\", "/"))
            if not src.exists():
                # fallback: locate by basename
                hits = list(extracted_root.rglob(Path(str(rel)).name))
                if hits:
                    src = hits[0]
            if not src.exists():
                raise SystemExit(f"extracted json missing: {src}")
            zf.write(src, arcname=f"json/{src.name}")

        # Add optional gamma zips under gamma/
        if gamma_zip_dir:
            gamma_zip_dir = gamma_zip_dir.resolve()
            for f in files:
                name = f.get("name")
                if not name:
                    continue
                cand = gamma_zip_dir / f"{name}.zip"
                if cand.exists():
                    zf.write(cand, arcname=f"gamma/{name}.zip")

        # Optional project_init.json
        if project_init and project_init.exists():
            zf.write(project_init, arcname="project_init.json")

    return out_zip


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a workflow bundle ZIP for /v1/workflow/run")
    ap.add_argument(
        "--extracted-root",
        type=Path,
        default=Path("media_pool/pptx"),
        help="Folder containing manifest.json + json/*.json (pptx extractor outputs)",
    )
    ap.add_argument("--out", type=Path, required=True, help="Output zip path")
    ap.add_argument(
        "--pptx",
        action="append",
        dest="pptx_names",
        help="Restrict bundle to a single PPTX name (repeatable). If omitted, includes all.",
    )
    ap.add_argument(
        "--gamma-zip-dir",
        type=Path,
        default=None,
        help="Directory containing Gamma export ZIPs named <pptx_name>.zip",
    )
    ap.add_argument(
        "--project-init",
        type=Path,
        default=None,
        help="Optional project_init.json (variants decisions)",
    )

    args = ap.parse_args()
    out = build_bundle(
        extracted_root=args.extracted_root,
        out_zip=args.out,
        pptx_names=args.pptx_names,
        gamma_zip_dir=args.gamma_zip_dir,
        project_init=args.project_init,
    )
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

