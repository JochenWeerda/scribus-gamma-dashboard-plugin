import json
from pathlib import Path

from packages.workflow.step_executor import StepExecutor
from packages.workflow.progress_tracker import ProgressTracker


def _sample_layout():
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
                        "bbox": {"x": 10, "y": 20, "w": 100, "h": 30},
                        "layer": "Text",
                        "content": "Hello",
                        "color": "#ff0000",
                    }
                ],
            }
        ],
    }


def test_quality_check_writes_report(tmp_path: Path):
    layout_path = tmp_path / "layout.json"
    layout_path.write_text(json.dumps(_sample_layout(), ensure_ascii=False, indent=2), encoding="utf-8")

    exec = StepExecutor(tracker=ProgressTracker(publish_to_bus=False))
    rep = exec.quality_check(layout_paths=[layout_path], out_dir=tmp_path / "qc")

    assert rep["errors"] == []
    assert len(rep["outputs"]) == 1
    assert "quality_gate" in rep["outputs"][0]
    report_path = Path(rep["report_path"])
    assert report_path.exists()
