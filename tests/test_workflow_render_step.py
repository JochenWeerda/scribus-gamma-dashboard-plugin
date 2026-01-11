import json
from pathlib import Path

from packages.workflow import WorkflowOrchestrator, WorkflowConfig
from packages.workflow.progress_tracker import ProgressTracker


def _write_min_manifest(tmp_path: Path) -> tuple[Path, Path]:
    pptx_root = tmp_path / "pptx"
    (pptx_root / "json").mkdir(parents=True, exist_ok=True)

    extracted = {
        "source": "x.pptx",
        "name": "sample",
        "slides": [
            {
                "slide": 1,
                "text_boxes": [{"text": "Hello", "rel_bbox": [0.1, 0.1, 0.9, 0.2], "role": "title", "ignore": False}],
                "image_boxes": [],
                "infoboxes": [],
            }
        ],
    }
    (pptx_root / "json" / "sample.json").write_text(json.dumps(extracted, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {"files": [{"name": "sample", "json": "json/sample.json"}]}
    manifest_path = pptx_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path, pptx_root


def test_workflow_render_step_creates_sla_and_placeholder_outputs(tmp_path: Path):
    tracker = ProgressTracker(publish_to_bus=False)
    manifest_path, pptx_root = _write_min_manifest(tmp_path)

    layout_out = tmp_path / "layout_json"
    variants_out = tmp_path / "variants"
    render_out = tmp_path / "render"
    resume_path = tmp_path / "state.json"

    cfg = WorkflowConfig(
        manifest_path=manifest_path,
        pptx_root=pptx_root,
        layout_out=layout_out,
        variants_out=variants_out,
        resume_path=resume_path,
        generate_variants=False,
        quality_check=False,
        render=True,
        render_out=render_out,
        render_pdf=True,
        render_png=True,
        retry_max=0,
    )

    wf = WorkflowOrchestrator(cfg, tracker=tracker)
    wf.run()

    assert (render_out / "sla").exists()
    assert any((render_out / "sla").glob("*.sla"))
    assert any((render_out / "pdf").glob("*.pdf"))
    assert any((render_out / "png").glob("*.png"))

