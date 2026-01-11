import json
import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

from packages.workflow.step_executor import StepExecutor
from packages.workflow.progress_tracker import ProgressTracker


def _make_png_bytes() -> bytes:
    img = Image.new("RGBA", (400, 300), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle((50, 60, 200, 150), fill=(0, 0, 0, 255))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_gamma_sync_creates_crops_from_zip(tmp_path: Path):
    extracted_root = tmp_path / "extracted"
    (extracted_root / "json").mkdir(parents=True)
    gamma_dir = tmp_path / "gamma"
    gamma_dir.mkdir()
    out_dir = tmp_path / "crops"

    extracted = {
        "name": "sample",
        "slides": [
            {
                "slide": 10,
                "infoboxes": [{"rel_bbox": [0.1, 0.1, 0.5, 0.5], "text": "x"}],
                "image_boxes": [],
                "text_boxes": [],
            }
        ],
    }
    (extracted_root / "json" / "sample.json").write_text(json.dumps(extracted, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {"files": [{"name": "sample", "json": "json/sample.json"}]}
    manifest_path = extracted_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # Gamma zip with slide "10_..." PNG
    zip_path = gamma_dir / "sample.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("10_Test.png", _make_png_bytes())

    exec = StepExecutor(tracker=ProgressTracker(publish_to_bus=False))
    rep = exec.gamma_sync(
        extracted_manifest_path=manifest_path,
        extracted_root=extracted_root,
        gamma_png_dir=gamma_dir,
        out_dir=out_dir,
        crop_pad_px=0,
        crop_refine=False,
    )

    assert rep["errors"] == []
    assert len(rep["outputs"]) == 1
    out_path = Path(rep["outputs"][0]["out"])
    assert out_path.exists()

