"""
Smoke: PPTX extract JSON -> Layout JSON -> SLA XML -> optional API-Gateway job.

This is intentionally lightweight and should run without Docker if you skip --api-url.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.layout_schema import validate_layout  # noqa: E402
from packages.pptx_parser.json_converter import PptxExtractConvertConfig  # noqa: E402
from packages.pptx_parser.manifest_converter import convert_manifest_to_layout_jsons  # noqa: E402
from packages.sla_compiler import compile_layout_to_sla  # noqa: E402


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _post_job(api_url: str, layout_json: Dict[str, Any], *, timeout_s: int = 30) -> str:
    try:
        import requests
    except Exception as e:
        raise RuntimeError("requests is required for --api-url. Install with: pip install requests") from e

    resp = requests.post(
        f"{api_url.rstrip('/')}/v1/jobs",
        json={"layout_json": layout_json, "priority": 0, "metadata": {"source": "pptx_smoke"}},
        timeout=timeout_s,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"POST /v1/jobs failed: {resp.status_code} {resp.text}")
    data = resp.json()
    return data.get("id") or data.get("job_id") or ""


def _poll_job(api_url: str, job_id: str, *, timeout_s: int = 60) -> Dict[str, Any]:
    import requests

    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        resp = requests.get(f"{api_url.rstrip('/')}/v1/jobs/{job_id}", timeout=15)
        resp.raise_for_status()
        last = resp.json()
        status = (last.get("status") or "").lower()
        if status in {"completed", "failed"}:
            return last
        time.sleep(2)
    return last or {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test for PPTX->Layout->SLA pipeline")
    parser.add_argument("--manifest", default="media_pool/pptx/manifest.json")
    parser.add_argument("--pptx-root", default="media_pool/pptx")
    parser.add_argument("--out-dir", default="media_pool/layout_json")
    parser.add_argument("--project-init", default="", help="Optional .cursor/project_init.json.template")
    parser.add_argument("--width", type=int, default=2480)
    parser.add_argument("--height", type=int, default=3508)
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--include-ignored", action="store_true")
    parser.add_argument("--sla-out", default="temp_analysis/smoke_output.sla")
    parser.add_argument("--api-url", default="", help="Optional, e.g. http://localhost:8003")
    parser.add_argument("--poll", action="store_true", help="Poll job status when --api-url is set")
    args = parser.parse_args()

    cfg = PptxExtractConvertConfig(
        width_px=args.width,
        height_px=args.height,
        dpi=args.dpi,
        include_ignored_text_boxes=args.include_ignored,
    )
    result = convert_manifest_to_layout_jsons(
        manifest_path=Path(args.manifest),
        pptx_root_dir=Path(args.pptx_root),
        out_dir=Path(args.out_dir),
        config=cfg,
        project_init_path=(Path(args.project_init) if args.project_init else None),
    )
    if not result.outputs:
        print("No outputs produced")
        return 1
    if result.invalid:
        print(f"{len(result.invalid)} output(s) are schema-invalid; aborting")
        return 2

    first = result.outputs[0]
    layout = _load_json(first)
    ok, errors = validate_layout(layout)
    if not ok:
        print("Schema invalid:", errors[:20])
        return 2

    sla_bytes = compile_layout_to_sla(layout)
    sla_out = Path(args.sla_out)
    sla_out.parent.mkdir(parents=True, exist_ok=True)
    sla_out.write_bytes(sla_bytes)
    print(f"Wrote SLA: {sla_out} ({len(sla_bytes)} bytes) from {first}")

    if args.api_url:
        job_id = _post_job(args.api_url, layout)
        if not job_id:
            print("Job created but no id returned")
            return 3
        print(f"Created job: {job_id}")
        if args.poll:
            final = _poll_job(args.api_url, job_id)
            print("Job status:", final.get("status"))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
