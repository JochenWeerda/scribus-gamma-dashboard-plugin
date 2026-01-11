import argparse
import csv
import glob
import os
from dataclasses import dataclass

from PIL import Image


@dataclass
class Finding:
    path: str
    w: int
    h: int
    mode: str
    border_nonwhite_pct: float
    alpha_semitransparent_pct: float
    touches_border: bool
    suspicious: bool
    reason: str


def _nonwhite_bbox(im: Image.Image, thr: int = 245):
    """Return bbox of pixels that are not near-white; works on RGB."""
    rgb = im.convert("RGB")
    px = rgb.load()
    w, h = rgb.size
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


def _border_nonwhite_pct(im: Image.Image, border_px: int = 3, thr: int = 245) -> float:
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    total = 0
    nonwhite = 0

    def sample(x, y):
        nonlocal total, nonwhite
        r, g, b = px[x, y]
        total += 1
        if (r < thr) or (g < thr) or (b < thr):
            nonwhite += 1

    bp = min(border_px, w // 2, h // 2)
    for y in range(h):
        for x in range(w):
            if x < bp or x >= w - bp or y < bp or y >= h - bp:
                sample(x, y)

    return 0.0 if total == 0 else (nonwhite / total) * 100.0


def _alpha_semitransparent_pct(im: Image.Image) -> float:
    if "A" not in im.getbands():
        return 0.0
    a = im.getchannel("A")
    w, h = a.size
    px = a.load()
    total = w * h
    semi = 0
    for y in range(h):
        for x in range(w):
            v = px[x, y]
            if 0 < v < 255:
                semi += 1
    return (semi / total) * 100.0


def audit(paths: list[str]) -> list[Finding]:
    out: list[Finding] = []
    for p in paths:
        try:
            with Image.open(p) as im:
                w, h = im.size
                bbox = _nonwhite_bbox(im)
                touches = False
                if bbox is not None:
                    x0, y0, x1, y1 = bbox
                    touches = (x0 <= 1) or (y0 <= 1) or (x1 >= w - 1) or (y1 >= h - 1)

                border_pct = _border_nonwhite_pct(im)
                alpha_semi = _alpha_semitransparent_pct(im)

                # Heuristik: Separatoren sind sehr flach → nicht als "zu klein" werten.
                aspect = (w / h) if h else 999.0
                is_separator = (h <= 350 and w >= 900 and aspect >= 2.5)

                suspicious = False
                reason_parts = []

                if alpha_semi > 0.05:
                    suspicious = True
                    reason_parts.append(f"semi-alpha {alpha_semi:.2f}%")

                if touches and border_pct > 1.0:
                    suspicious = True
                    reason_parts.append(f"content-touches-border + border-nonwhite {border_pct:.2f}%")

                if (not is_separator) and max(w, h) < 1400:
                    suspicious = True
                    reason_parts.append(f"low-res {w}x{h}")

                out.append(
                    Finding(
                        path=p,
                        w=w,
                        h=h,
                        mode=im.mode,
                        border_nonwhite_pct=border_pct,
                        alpha_semitransparent_pct=alpha_semi,
                        touches_border=touches,
                        suspicious=suspicious,
                        reason="; ".join(reason_parts) if reason_parts else "",
                    )
                )
        except Exception as e:
            out.append(
                Finding(
                    path=p,
                    w=0,
                    h=0,
                    mode="ERR",
                    border_nonwhite_pct=0.0,
                    alpha_semitransparent_pct=0.0,
                    touches_border=False,
                    suspicious=True,
                    reason=f"open-failed: {e}",
                )
            )
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", default="00", help="z.B. 00")
    ap.add_argument("--kind", choices=["figures", "icons"], default="figures")
    ap.add_argument("--variant", default="print_bw", help="z.B. print_bw, color_navy")
    ap.add_argument("--out", default="asset_audit_report.csv")
    args = ap.parse_args()

    base = "assets/figures" if args.kind == "figures" else "assets/icons"
    glob_pat = os.path.join(base, f"ch{args.chapter}", args.variant, "*.png")
    paths = sorted(glob.glob(glob_pat))

    findings = audit(paths)
    suspicious = [f for f in findings if f.suspicious]
    suspicious.sort(key=lambda f: (f.alpha_semitransparent_pct, f.border_nonwhite_pct, -max(f.w, f.h)), reverse=True)

    with open(args.out, "w", newline="", encoding="utf-8") as fp:
        w = csv.writer(fp)
        w.writerow(
            [
                "path",
                "w",
                "h",
                "mode",
                "border_nonwhite_pct",
                "alpha_semitransparent_pct",
                "touches_border",
                "suspicious",
                "reason",
            ]
        )
        for f in findings:
            w.writerow(
                [
                    f.path,
                    f.w,
                    f.h,
                    f.mode,
                    f"{f.border_nonwhite_pct:.3f}",
                    f"{f.alpha_semitransparent_pct:.3f}",
                    str(f.touches_border),
                    str(f.suspicious),
                    f.reason,
                ]
            )

    print(f"Audited: {len(findings)} files")
    print(f"Suspicious: {len(suspicious)} files")
    for f in suspicious[:20]:
        print(f"- {f.path} :: {f.w}x{f.h} :: {f.reason}")


if __name__ == "__main__":
    main()


