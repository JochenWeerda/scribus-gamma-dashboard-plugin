# -*- coding: utf-8 -*-
import os
import re
import zipfile
import shutil
from typing import Dict, List, Tuple, Optional

IMG_EXTS = (".png", ".jpg", ".jpeg", ".webp")

def _ensure_dir(p: str) -> str:
    os.makedirs(p, exist_ok=True)
    return p

def is_zip(path: str) -> bool:
    return path.lower().endswith(".zip") and os.path.isfile(path)

def unpack_if_zip(gamma_export: str, work_dir: str) -> str:
    """
    Returns a directory containing the exported files.
    If gamma_export is a zip -> extracts into work_dir/_gamma_unpacked
    If gamma_export is a dir -> returns it
    """
    if os.path.isdir(gamma_export):
        return gamma_export
    if is_zip(gamma_export):
        out = _ensure_dir(os.path.join(work_dir, "_gamma_unpacked"))
        with zipfile.ZipFile(gamma_export, "r") as zf:
            zf.extractall(out)
        return out
    raise FileNotFoundError(f"gamma_export not found: {gamma_export}")

def find_pptx(root: str) -> Optional[str]:
    for base, _dirs, files in os.walk(root):
        for fn in files:
            if fn.lower().endswith(".pptx"):
                return os.path.join(base, fn)
    return None

def find_slide_pngs(root: str) -> List[str]:
    """
    Gamma exports often include slide PNGs. We look for pngs with 'slide' in name,
    but also accept any pngs if nothing else found.
    """
    pngs = []
    loose = []
    for base, _dirs, files in os.walk(root):
        for fn in files:
            if fn.lower().endswith(".png"):
                p = os.path.join(base, fn)
                if re.search(r"slide|seite|page", fn.lower()):
                    pngs.append(p)
                else:
                    loose.append(p)
    return sorted(pngs) if pngs else sorted(loose)

def normalize_slide_pngs(slide_pngs: List[str], out_dir: str) -> List[str]:
    """
    Copies slide images to out_dir as slide_0001.png ... in sorted order.
    """
    _ensure_dir(out_dir)
    normed = []
    for i, src in enumerate(slide_pngs, start=1):
        dst = os.path.join(out_dir, f"slide_{i:04d}.png")
        if os.path.abspath(src) != os.path.abspath(dst):
            shutil.copy2(src, dst)
        normed.append(dst)
    return normed
