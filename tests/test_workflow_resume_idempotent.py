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


def test_workflow_is_idempotent_and_skips_completed_steps(tmp_path: Path):
    events = []
    tracker = ProgressTracker(on_event=lambda e: events.append(e), publish_to_bus=False)

    manifest_path, pptx_root = _write_min_manifest(tmp_path)
    layout_out = tmp_path / "layout_json"
    variants_out = tmp_path / "layout_json_variants"
    resume_path = tmp_path / "state.json"

    cfg = WorkflowConfig(
        manifest_path=manifest_path,
        pptx_root=pptx_root,
        layout_out=layout_out,
        variants_out=variants_out,
        project_init=None,
        resume_path=resume_path,
        generate_variants=True,
        force=False,
        retry_max=0,
    )

    wf = WorkflowOrchestrator(cfg, tracker=tracker)
    wf.run()

    state1 = json.loads(resume_path.read_text(encoding="utf-8"))
    assert state1["steps"]["convert_manifest"]["status"] == "completed"
    assert state1["steps"]["generate_variants"]["status"] == "completed"
    assert any(layout_out.glob("*.layout.json"))
    assert any(variants_out.glob("*.layout.*.layout.json"))

    events.clear()
    wf2 = WorkflowOrchestrator(cfg, tracker=tracker)
    wf2.run()

    skipped = [e for e in events if e.get("event") == "step.skipped"]
    skipped_ids = {e.get("step_id") for e in skipped}
    assert "convert_manifest" in skipped_ids
    assert "generate_variants" in skipped_ids

