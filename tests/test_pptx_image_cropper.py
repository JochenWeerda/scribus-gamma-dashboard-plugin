from pathlib import Path

from PIL import Image, ImageDraw

from packages.pptx_parser.image_cropper import CropConfig, crop_from_rel_bbox


def test_crop_from_rel_bbox_refine_expands_to_content(tmp_path: Path):
    # Create a white canvas with a black rectangle that slightly exceeds the base bbox.
    img = Image.new("RGBA", (1000, 1000), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    # actual content box: x=120..520, y=200..450
    draw.rectangle((120, 200, 520, 450), fill=(0, 0, 0, 255))
    png = tmp_path / "slide_001.png"
    img.save(png)

    # Base bbox is too tight (misses some left/top)
    rel_bbox = [0.13, 0.22, 0.50, 0.44]  # ~130..500, 220..440
    out = tmp_path / "crop.png"

    bbox_px = crop_from_rel_bbox(
        png,
        rel_bbox,
        out,
        config=CropConfig(pad_px=0, refine=True, refine_margin_px=50, bg_threshold=250),
    )

    # Expect refined bbox to cover the real rectangle bounds (roughly).
    l, u, r, d = bbox_px
    assert l <= 120
    assert u <= 200
    assert r >= 520
    assert d >= 450
    assert out.exists()

