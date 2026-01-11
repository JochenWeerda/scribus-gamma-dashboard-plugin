from pathlib import Path

from packages.workflow.step_executor import StepExecutor
from packages.workflow.progress_tracker import ProgressTracker


def test_attach_gamma_crops_to_layout_rewrites_image_url():
    exec = StepExecutor(tracker=ProgressTracker(publish_to_bus=False))

    layout = {
        "version": "1.0.0",
        "document": {"width": 1000, "height": 2000, "dpi": 300},
        "pages": [
            {
                "pageNumber": 1,
                "objects": [
                    {
                        "id": "img1",
                        "type": "image",
                        "bbox": {"x": 10, "y": 20, "w": 200, "h": 100},
                        "layer": "Images",
                        "imageUrl": "old.png",
                        "sourceSlide": 10,
                        "sourceIndex": 0,
                        "sourceKind": "image_box",
                    }
                ],
            }
        ],
        "source": {"kind": "pptx_extract_json", "name": "sample"},
    }

    gamma_report = {
        "outputs": [
            {
                "pptx": "sample",
                "slide": 10,
                "box_index": 0,
                "kind": "image_box",
                "out": str(Path("crops") / "sample.png"),
            }
        ],
        "errors": [],
    }

    out = exec.attach_gamma_crops_to_layout(
        layout_json=layout,
        gamma_report=gamma_report,
        pptx_name="sample",
        kinds=["image_box"],
    )

    obj = out["pages"][0]["objects"][0]
    assert obj["imageUrl"].endswith("crops\\sample.png") or obj["imageUrl"].endswith("crops/sample.png")
    assert obj["gammaCrop"] is True
    assert out["variant"]["gamma_crops_attached"] is True

