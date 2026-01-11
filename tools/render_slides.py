# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Literal, Optional

Backend = Literal["auto", "powerpoint", "libreoffice"]


def _which(exe: str) -> Optional[str]:
    return shutil.which(exe)


def _normalize_png_names(out_dir: Path) -> list[str]:
    pngs = sorted(out_dir.glob("*.png")) + sorted(out_dir.glob("*.PNG"))
    if not pngs:
        return []
    normalized = []
    for idx, src in enumerate(pngs, start=1):
        dst = out_dir / f"slide_{idx:04d}.png"
        if src.resolve() != dst.resolve():
            try:
                if dst.exists():
                    dst.unlink()
                src.replace(dst)
            except Exception:
                dst = src
        normalized.append(str(dst))
    return normalized


def render_pptx_to_pngs(
    pptx_path: str,
    out_dir: str,
    backend: Backend = "auto",
    dpi: int = 300,
) -> list[str]:
    """
    Render PPTX slides to PNGs in out_dir.
    Uses PowerPoint COM on Windows if available, otherwise LibreOffice headless.
    Returns list of created PNG paths (sorted, normalized to slide_0001.png).
    """
    pptx = Path(pptx_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    if backend == "auto":
        if os.name == "nt":
            try:
                import win32com.client  # type: ignore

                backend = "powerpoint"
            except Exception:
                backend = "libreoffice"
        else:
            backend = "libreoffice"

    if backend == "powerpoint":
        if os.name != "nt":
            raise RuntimeError("PowerPoint backend only works on Windows.")
        try:
            import pythoncom  # type: ignore
            import win32com.client  # type: ignore
        except Exception as exc:
            raise RuntimeError("pywin32 missing. Install: pip install pywin32") from exc

        # PowerPoint Export uses pixel size. Approximate DPI via scale factor.
        scale = max(1.0, dpi / 96.0)
        width_px = int(1920 * scale)
        height_px = int(1080 * scale)

        pythoncom.CoInitialize()
        app = win32com.client.Dispatch("PowerPoint.Application")
        app.Visible = 1
        pres = app.Presentations.Open(str(pptx), WithWindow=False)
        pres.Export(str(out), "PNG", width_px, height_px)
        pres.Close()
        app.Quit()

        return _normalize_png_names(out)

    if backend == "libreoffice":
        soffice = _which("soffice") or _which("libreoffice")
        if not soffice:
            raise RuntimeError("LibreOffice not found. Install or add soffice to PATH.")
        cmd = [
            soffice,
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            "--convert-to",
            "png",
            "--outdir",
            str(out),
            str(pptx),
        ]
        subprocess.check_call(cmd)

        pngs = _normalize_png_names(out)
        if not pngs:
            raise RuntimeError("LibreOffice conversion produced no PNGs.")
        return pngs

    raise ValueError(f"Unknown backend: {backend}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx", required=True, help="Path to PPTX")
    ap.add_argument("--out", required=True, help="Output folder for slide PNGs")
    ap.add_argument("--backend", default="auto", choices=["auto", "powerpoint", "libreoffice"])
    ap.add_argument("--dpi", type=int, default=300)
    args = ap.parse_args()

    pngs = render_pptx_to_pngs(args.pptx, args.out, backend=args.backend, dpi=args.dpi)
    print("\n".join(pngs))
