import json
from pathlib import Path

from packages.workflow import WorkflowConfig, WorkflowOrchestrator
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


def test_workflow_agents_step_creates_report(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = ProgressTracker(publish_to_bus=False)
    manifest_path, pptx_root = _write_min_manifest(tmp_path)

    layout_out = tmp_path / "layout_json"
    variants_out = tmp_path / "variants"
    resume_path = tmp_path / "state.json"

    cfg = WorkflowConfig(
        manifest_path=manifest_path,
        pptx_root=pptx_root,
        layout_out=layout_out,
        variants_out=variants_out,
        resume_path=resume_path,
        generate_variants=False,
        quality_check=False,
        render=False,
        agents_enabled=True,
        agent_steps=("SemanticEnricher", "LayoutDesigner", "QualityCritic"),
        agent_simulate=True,
        retry_max=0,
    )

    wf = WorkflowOrchestrator(cfg, tracker=tracker)
    wf.run()

    report_path = tmp_path / "temp_analysis" / "agents_report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert len(report.get("outputs") or []) == 1
    assert report["outputs"][0]["agents"]["LayoutDesigner"]["simulated"] is True
