import argparse
import os
import re
from dataclasses import dataclass

import fitz  # PyMuPDF
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


VARIANTS = ["print_bw", "grey", "color_navy", "color_magenta", "color_gold"]


def _parse_vecfig_index(filename: str) -> int | None:
    m = re.search(r"_vecfig_(\d{3})\.png$", filename)
    if not m:
        return None
    return int(m.group(1))


def _nonwhite_bbox_rgb(im: Image.Image, thr: int = 245):
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if (r < thr) or (g < thr) or (b < thr):
                if x < minx:
                    minx = x
                if y < miny:
                    miny = y
                if x > maxx:
                    maxx = x
                if y > maxy:
                    maxy = y
    if maxx < 0:
        return None
    return (minx, miny, maxx + 1, maxy + 1)


def _crop_to_content(im: Image.Image, pad: int = 12) -> Image.Image:
    bbox = _nonwhite_bbox_rgb(im)
    if bbox is None:
        return im
    x0, y0, x1, y1 = bbox
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(im.width, x1 + pad)
    y1 = min(im.height, y1 + pad)
    return im.crop((x0, y0, x1, y1))


def _mk_variants(base_rgb: Image.Image):
    # Grundlage: Graustufen mit gutem Kontrast
    gray = ImageOps.grayscale(base_rgb)
    gray = ImageOps.autocontrast(gray, cutoff=0.2)

    # print_bw: sehr hoher Kontrast + leichtes Schärfen (ohne harte Thresholds)
    bw = gray
    bw = ImageEnhance.Contrast(bw).enhance(1.7)
    bw = bw.filter(ImageFilter.UnsharpMask(radius=2, percent=160, threshold=3))
    bw_rgb = bw.convert("RGB")

    # grey: moderater Kontrast
    g = ImageEnhance.Contrast(gray).enhance(1.15).convert("RGB")

    # monochrome Tints (für Digital-Farbvarianten)
    navy = ImageOps.colorize(gray, black=(0, 32, 96), white=(255, 255, 255))
    magenta = ImageOps.colorize(gray, black=(200, 0, 100), white=(255, 255, 255))
    gold = ImageOps.colorize(gray, black=(210, 160, 0), white=(255, 255, 255))

    return {
        "print_bw": bw_rgb,
        "grey": g,
        "color_navy": navy,
        "color_magenta": magenta,
        "color_gold": gold,
    }


def _render_page(pdf: fitz.Document, page_index: int, dpi: int) -> Image.Image:
    page = pdf.load_page(page_index)
    scale = dpi / 72.0
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, alpha=False)  # alpha aus → keine Fransen durch Transparenz
    mode = "RGB"
    img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
    return img


def regenerate_chapter(ch: int, chapters_dir: str, figures_dir: str, dpi: int, overwrite: bool):
    chs = f"{ch:02d}"
    pdf_path = os.path.join(chapters_dir, f"chapter{chs}.pdf")
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(pdf_path)

    # Welche Indizes existieren bereits? (wir regenerieren exakt diese, damit Kapitel-Struktur stabil bleibt)
    existing = set()
    probe_dir = os.path.join(figures_dir, f"ch{chs}", "print_bw")
    if os.path.isdir(probe_dir):
        for fn in os.listdir(probe_dir):
            idx = _parse_vecfig_index(fn)
            if idx is not None:
                existing.add(idx)
    if not existing:
        # Fallback: generiere 0..(pages-1)
        doc = fitz.open(pdf_path)
        existing = set(range(doc.page_count))
        doc.close()

    doc = fitz.open(pdf_path)
    try:
        max_page = doc.page_count - 1
        indices = sorted(existing)
        print(f"[ch{chs}] PDF pages={doc.page_count}, regenerate {len(indices)} figures @ {dpi}dpi")

        for idx in indices:
            page_i = min(idx, max_page)
            base = _render_page(doc, page_i, dpi=dpi)
            base = _crop_to_content(base)
            variants = _mk_variants(base)

            out_name = f"ch{chs}_vecfig_{idx:03d}.png"
            for variant, im in variants.items():
                out_dir = os.path.join(figures_dir, f"ch{chs}", variant)
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, out_name)
                if (not overwrite) and os.path.exists(out_path):
                    continue
                im.save(out_path, format="PNG", optimize=True)

            print(f"  - regenerated {out_name} (page {page_i+1}/{doc.page_count})")
    finally:
        doc.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int, default=0)
    ap.add_argument("--chapters-dir", default="assets/chapters")
    ap.add_argument("--figures-dir", default="assets/figures")
    ap.add_argument("--dpi", type=int, default=450)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    regenerate_chapter(
        ch=args.chapter,
        chapters_dir=args.chapters_dir,
        figures_dir=args.figures_dir,
        dpi=args.dpi,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()


