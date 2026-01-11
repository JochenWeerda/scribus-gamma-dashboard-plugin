from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Tuple

from PIL import Image, ImageChops
from io import BytesIO
import zipfile


@dataclass(frozen=True)
class CropConfig:
    pad_px: int = 0
    refine: bool = False
    refine_margin_px: int = 30
    bg_threshold: int = 245  # 0..255, higher = treat "almost white" as background


def rel_bbox_to_px(rel_bbox: Iterable[float], *, width: int, height: int) -> tuple[int, int, int, int]:
    """
    Convert rel bbox (x1,y1,x2,y2 in 0..1) to pixel bbox (left, upper, right, lower).
    """
    x1, y1, x2, y2 = [float(v) for v in rel_bbox]
    left = int(round(max(0.0, min(1.0, x1)) * width))
    upper = int(round(max(0.0, min(1.0, y1)) * height))
    right = int(round(max(0.0, min(1.0, x2)) * width))
    lower = int(round(max(0.0, min(1.0, y2)) * height))
    if right <= left:
        right = min(width, left + 1)
    if lower <= upper:
        lower = min(height, upper + 1)
    return left, upper, right, lower


def _clamp_bbox(b: tuple[int, int, int, int], *, width: int, height: int) -> tuple[int, int, int, int]:
    l, u, r, d = b
    l = max(0, min(width, int(l)))
    r = max(0, min(width, int(r)))
    u = max(0, min(height, int(u)))
    d = max(0, min(height, int(d)))
    if r <= l:
        r = min(width, l + 1)
    if d <= u:
        d = min(height, u + 1)
    return l, u, r, d


def _pad_bbox(b: tuple[int, int, int, int], pad: int) -> tuple[int, int, int, int]:
    l, u, r, d = b
    return l - pad, u - pad, r + pad, d + pad


def refine_bbox_with_image(
    image: Image.Image,
    bbox_px: tuple[int, int, int, int],
    *,
    margin_px: int = 30,
    bg_threshold: int = 245,
) -> tuple[int, int, int, int]:
    """
    Expand bbox to include non-background pixels in a search area around the bbox.

    Background is approximated as "nearly white" (all RGB channels >= bg_threshold).
    This works well for Gamma PNG exports where the canvas is white and objects are darker.
    """

    width, height = image.size
    base = _clamp_bbox(bbox_px, width=width, height=height)
    search = _clamp_bbox(_pad_bbox(base, int(margin_px)), width=width, height=height)
    l, u, r, d = search
    region = image.crop((l, u, r, d)).convert("RGBA")

    # Build a "foreground" mask: pixels that are not near-white and not fully transparent.
    # Create alpha mask
    alpha = region.getchannel("A")
    rgb = region.convert("RGB")
    # near-white mask
    # Convert RGB to a mask by thresholding each channel, then combine.
    r_ch, g_ch, b_ch = rgb.split()
    r_mask = r_ch.point(lambda v: 255 if v >= bg_threshold else 0)
    g_mask = g_ch.point(lambda v: 255 if v >= bg_threshold else 0)
    b_mask = b_ch.point(lambda v: 255 if v >= bg_threshold else 0)
    # We treat masks as 0/255 in mode "L" and use multiply as AND.
    white_mask = ImageChops.multiply(ImageChops.multiply(r_mask, g_mask), b_mask)
    # Not-white = invert
    not_white = ImageChops.invert(white_mask)
    # Not-transparent: alpha > 0
    not_transparent = alpha.point(lambda v: 255 if v > 0 else 0)
    fg_mask = ImageChops.multiply(not_white, not_transparent)

    bbox = fg_mask.getbbox()
    if bbox is None:
        return base

    bb_l, bb_u, bb_r, bb_d = bbox
    refined = (l + bb_l, u + bb_u, l + bb_r, u + bb_d)
    return _clamp_bbox(refined, width=width, height=height)


def crop_from_rel_bbox(
    png_path: str | Path,
    rel_bbox: Iterable[float],
    out_path: str | Path,
    *,
    config: CropConfig = CropConfig(),
) -> tuple[int, int, int, int]:
    """
    Crop from a Gamma-export PNG based on a PPTX rel_bbox (0..1 coordinates).
    Returns the final pixel bbox used.
    """

    png_path = Path(png_path)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    image = Image.open(png_path)
    base = rel_bbox_to_px(rel_bbox, width=image.size[0], height=image.size[1])
    padded = _clamp_bbox(_pad_bbox(base, int(config.pad_px)), width=image.size[0], height=image.size[1])

    final_bbox = padded
    if config.refine:
        final_bbox = refine_bbox_with_image(
            image,
            padded,
            margin_px=int(config.refine_margin_px),
            bg_threshold=int(config.bg_threshold),
        )

    cropped = image.crop(final_bbox)
    cropped.save(out_path)
    return final_bbox


def crop_from_image(
    image: Image.Image,
    rel_bbox: Iterable[float],
    out_path: str | Path,
    *,
    config: CropConfig = CropConfig(),
) -> tuple[int, int, int, int]:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    base = rel_bbox_to_px(rel_bbox, width=image.size[0], height=image.size[1])
    padded = _clamp_bbox(_pad_bbox(base, int(config.pad_px)), width=image.size[0], height=image.size[1])
    final_bbox = padded
    if config.refine:
        final_bbox = refine_bbox_with_image(
            image,
            padded,
            margin_px=int(config.refine_margin_px),
            bg_threshold=int(config.bg_threshold),
        )
    image.crop(final_bbox).save(out_path)
    return final_bbox


def find_gamma_png(
    png_root: str | Path,
    *,
    pptx_stem: str,
    slide_index: int,
) -> Optional[Path]:
    """
    Try to locate the corresponding Gamma export PNG by common naming patterns.
    """

    root = Path(png_root)
    s = int(slide_index)
    candidates = [
        root / f"{pptx_stem}_s{s:03d}.png",
        root / f"{pptx_stem}_slide_{s:03d}.png",
        root / f"{pptx_stem}_slide{s:03d}.png",
        root / f"slide_{s:03d}.png",
        root / f"slide{s:03d}.png",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def find_gamma_png_in_zip(zip_path: str | Path, *, slide_index: int) -> Optional[str]:
    """
    Find a PNG member name inside a ZIP by common naming conventions.
    Many Gamma exports name slides like `10_Title.png` (1-based).
    """

    zip_path = Path(zip_path)
    s = int(slide_index)
    prefixes = [f"{s:02d}_", f"{s:03d}_", f"slide_{s:03d}", f"slide{s:03d}", f"{s}_"]
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = [n for n in zf.namelist() if n.lower().endswith(".png")]
            for pref in prefixes:
                for n in names:
                    base = Path(n).name
                    if base.startswith(pref):
                        return n
            # fallback: first png
            return names[0] if names else None
    except Exception:
        return None


def load_png_from_zip(zip_path: str | Path, member_name: str) -> Image.Image:
    zip_path = Path(zip_path)
    with zipfile.ZipFile(zip_path, "r") as zf:
        data = zf.read(member_name)
    return Image.open(BytesIO(data)).convert("RGBA")
