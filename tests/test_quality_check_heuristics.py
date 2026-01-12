import json
from pathlib import Path

from packages.workflow.step_executor import StepExecutor
from packages.workflow.progress_tracker import ProgressTracker


def _layout_with_overflow():
    # Small bbox + big text + large font => should trigger overflow warning
    return {
        "version": "1.0.0",
        "document": {"width": 1000, "height": 2000, "dpi": 300},
        "pages": [
            {
                "pageNumber": 1,
                "objects": [
                    {
                        "id": "t1",
                        "type": "text",
                        "bbox": {"x": 10, "y": 20, "w": 120, "h": 30},
                        "layer": "TEXT",
                        "content": "This is a long line of text that will not fit.",
                        "fontFamily": "Inter",
                        "fontSize": 28,
                    }
                ],
            }
        ],
    }


def test_quality_check_includes_heuristics_when_enabled(tmp_path: Path):
    layout_path = tmp_path / "layout.json"
    layout_path.write_text(json.dumps(_layout_with_overflow(), ensure_ascii=False, indent=2), encoding="utf-8")

    project_init = tmp_path / "project_init.json"
    project_init.write_text(
        json.dumps(
            {
                "quality": {
                    "heuristics": {
                        "overflow_warn_ratio": 0.8,
                        "objects_per_page_warn": 10,
                    }
                }
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    exec = StepExecutor(tracker=ProgressTracker(publish_to_bus=False))
    rep = exec.quality_check(layout_paths=[layout_path], out_dir=tmp_path / "qc", checks=["heuristics"], project_init=project_init)

    assert rep["errors"] == []
    assert len(rep["outputs"]) == 1
    assert "heuristics" in rep["outputs"][0]
    h = rep["outputs"][0]["heuristics"]
    assert h["passed"] is True
    assert h["summary"]["warnCount"] >= 1

