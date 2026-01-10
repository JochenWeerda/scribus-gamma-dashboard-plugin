# -*- coding: utf-8 -*-
import os
import json
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional

import cv2
import numpy as np

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _imread(path: str) -> Optional[np.ndarray]:
    try:
        path.encode("ascii")
        ascii_ok = True
    except Exception:
        ascii_ok = False
    if ascii_ok:
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is not None:
            return img
    try:
        data = np.fromfile(path, dtype=np.uint8)
        if data.size:
            return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        return None
    return None


def _imwrite(path: str, img: np.ndarray) -> bool:
    try:
        path.encode("ascii")
        ascii_ok = True
    except Exception:
        ascii_ok = False
    if ascii_ok:
        return bool(cv2.imwrite(path, img))
    try:
        ext = os.path.splitext(path)[1] or ".png"
        ok, buf = cv2.imencode(ext, img)
        if not ok:
            return False
        buf.tofile(path)
        return True
    except Exception:
        return False
@dataclass
class Box:
    x0: int
    y0: int
    x1: int
    y1: int
    score: float = 0.0

    @property
    def w(self): return max(0, self.x1 - self.x0)
    @property
    def h(self): return max(0, self.y1 - self.y0)
    @property
    def area(self): return self.w * self.h

    def to_norm(self, W: int, H: int) -> List[float]:
        return [clamp01(self.x0 / W), clamp01(self.y0 / H), clamp01(self.x1 / W), clamp01(self.y1 / H)]

def _rectangularity(cnt) -> float:
    x, y, w, h = cv2.boundingRect(cnt)
    if w <= 0 or h <= 0:
        return 0.0
    a = cv2.contourArea(cnt)
    return float(a) / float(w * h)

def _border_contrast_score(img_bgr: np.ndarray, box: Box) -> float:
    """
    Gamma-cards often have visible border/gradient transitions.
    We measure contrast between a thin outer ring and inner ring.
    """
    H, W = img_bgr.shape[:2]
    x0, y0, x1, y1 = box.x0, box.y0, box.x1, box.y1
    if box.w < 20 or box.h < 20:
        return 0.0

    pad = max(2, int(min(box.w, box.h) * 0.02))
    x0i, y0i = max(0, x0 + pad), max(0, y0 + pad)
    x1i, y1i = min(W, x1 - pad), min(H, y1 - pad)
    if x1i <= x0i or y1i <= y0i:
        return 0.0

    outer = img_bgr[max(0,y0-pad):min(H,y1+pad), max(0,x0-pad):min(W,x1+pad)]
    inner = img_bgr[y0i:y1i, x0i:x1i]
    if outer.size == 0 or inner.size == 0:
        return 0.0

    # Use LAB for perceptual difference
    outer_lab = cv2.cvtColor(outer, cv2.COLOR_BGR2LAB)
    inner_lab = cv2.cvtColor(inner, cv2.COLOR_BGR2LAB)

    o = np.mean(outer_lab.reshape(-1,3), axis=0)
    i = np.mean(inner_lab.reshape(-1,3), axis=0)
    d = float(np.linalg.norm(o - i))
    # normalize to ~0..1 range
    return min(1.0, d / 40.0)

def detect_card_candidates(png_path: str,
                          min_rel_area: float = 0.03,
                          max_rel_area: float = 0.95,
                          min_aspect: float = 0.15,
                          max_aspect: float = 6.5) -> Tuple[np.ndarray, List[Box]]:
    img = _imread(png_path)
    if img is None:
        raise FileNotFoundError(png_path)
    H, W = img.shape[:2]

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # slight blur helps for gradients
    gray = cv2.GaussianBlur(gray, (5,5), 0)

    edges = cv2.Canny(gray, 40, 120)
    # close gaps
    k = max(3, int(min(W, H) * 0.004) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
    edges2 = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
    edges2 = cv2.dilate(edges2, kernel, iterations=1)

    contours, _ = cv2.findContours(edges2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes: List[Box] = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w <= 0 or h <= 0:
            continue
        rel_area = (w*h) / float(W*H)
        if rel_area < min_rel_area or rel_area > max_rel_area:
            continue
        aspect = h / float(w)
        if aspect < min_aspect or aspect > max_aspect:
            continue

        recty = _rectangularity(cnt)
        if recty < 0.45:
            continue

        b = Box(x, y, x+w, y+h, score=0.0)
        bc = _border_contrast_score(img, b)
        # score: rectangularity + border contrast + area bonus
        b.score = 0.55*recty + 0.35*bc + 0.10*min(1.0, rel_area/0.20)
        boxes.append(b)

    # NMS-like prune: remove boxes heavily contained by bigger better boxes
    boxes.sort(key=lambda b: (b.score, b.area), reverse=True)
    kept: List[Box] = []
    for b in boxes:
        drop = False
        for kbox in kept:
            # containment test
            if b.x0 >= kbox.x0 and b.y0 >= kbox.y0 and b.x1 <= kbox.x1 and b.y1 <= kbox.y1:
                if kbox.area >= b.area * 1.1:
                    drop = True
                    break
        if not drop:
            kept.append(b)

    return img, kept

class UnionFind:
    def __init__(self, n: int):
        self.p = list(range(n))
        self.r = [0]*n
    def find(self, a: int) -> int:
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a
    def union(self, a: int, b: int):
        ra, rb = self.find(a), self.find(b)
        if ra == rb: return
        if self.r[ra] < self.r[rb]:
            self.p[ra] = rb
        elif self.r[ra] > self.r[rb]:
            self.p[rb] = ra
        else:
            self.p[rb] = ra
            self.r[ra] += 1

def _gap(a0, a1, b0, b1) -> int:
    # gap between intervals [a0,a1] and [b0,b1]
    if a1 < b0: return b0 - a1
    if b1 < a0: return a0 - b1
    return 0

def cluster_boxes(boxes: List[Box], W: int, H: int,
                 tol_y: float = 0.02, tol_h: float = 0.06,
                 tol_x: float = 0.02, tol_w: float = 0.06,
                 tol_gap: float = 0.03) -> List[List[Box]]:
    """
    Merge boxes that likely belong together (Gamma grids / stacked cards).
    """
    if not boxes:
        return []
    n = len(boxes)
    uf = UnionFind(n)

    ty = int(tol_y * H)
    th = int(tol_h * H)
    tx = int(tol_x * W)
    tw = int(tol_w * W)
    tg = int(tol_gap * max(W, H))

    for i in range(n):
        for j in range(i+1, n):
            a, b = boxes[i], boxes[j]

            # row merge: similar y0 and height and small x gap
            row_ok = abs(a.y0 - b.y0) <= ty and abs(a.h - b.h) <= th
            if row_ok:
                gx = _gap(a.x0, a.x1, b.x0, b.x1)
                if gx <= tg:
                    uf.union(i, j)
                    continue

            # column merge: similar x0 and width and small y gap
            col_ok = abs(a.x0 - b.x0) <= tx and abs(a.w - b.w) <= tw
            if col_ok:
                gy = _gap(a.y0, a.y1, b.y0, b.y1)
                if gy <= tg:
                    uf.union(i, j)
                    continue

            # “attached” merge: heavy overlap in one axis + tiny gap in other
            ox = max(0, min(a.x1, b.x1) - max(a.x0, b.x0))
            oy = max(0, min(a.y1, b.y1) - max(a.y0, b.y0))
            if ox > 0.6*min(a.w, b.w) and _gap(a.y0, a.y1, b.y0, b.y1) <= tg:
                uf.union(i, j)
                continue
            if oy > 0.6*min(a.h, b.h) and _gap(a.x0, a.x1, b.x0, b.x1) <= tg:
                uf.union(i, j)
                continue

    clusters: Dict[int, List[Box]] = {}
    for i in range(n):
        r = uf.find(i)
        clusters.setdefault(r, []).append(boxes[i])

    # merge cluster bbox (represented as 1 Box)
    merged: List[Tuple[Box, List[Box]]] = []
    for _, items in clusters.items():
        x0 = min(b.x0 for b in items); y0 = min(b.y0 for b in items)
        x1 = max(b.x1 for b in items); y1 = max(b.y1 for b in items)
        score = float(np.mean([b.score for b in items]))
        merged.append((Box(x0,y0,x1,y1,score=score), items))

    # Sort by area+score, keep top 3 by default (param in pipeline)
    merged.sort(key=lambda t: (t[0].area, t[0].score), reverse=True)
    return [m[1] for m in merged]  # return original boxes per cluster

def merge_cluster_bbox(cluster: List[Box]) -> Box:
    x0 = min(b.x0 for b in cluster); y0 = min(b.y0 for b in cluster)
    x1 = max(b.x1 for b in cluster); y1 = max(b.y1 for b in cluster)
    score = float(np.mean([b.score for b in cluster]))
    return Box(x0,y0,x1,y1,score=score)

def export_debug_overlay(img: np.ndarray, candidates: List[Box], clusters: List[List[Box]], out_path: str):
    vis = img.copy()
    for b in candidates:
        cv2.rectangle(vis, (b.x0,b.y0), (b.x1,b.y1), (0,255,255), 2)
    for cl in clusters:
        mb = merge_cluster_bbox(cl)
        cv2.rectangle(vis, (mb.x0,mb.y0), (mb.x1,mb.y1), (0,255,0), 3)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    _imwrite(out_path, vis)

def crop_png(img_path: str, box: Box, out_path: str, pad_px: int = 10):
    img = _imread(img_path)
    if img is None:
        raise FileNotFoundError(img_path)
    H, W = img.shape[:2]
    x0 = max(0, box.x0 - pad_px)
    y0 = max(0, box.y0 - pad_px)
    x1 = min(W, box.x1 + pad_px)
    y1 = min(H, box.y1 + pad_px)
    crop = img[y0:y1, x0:x1]
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    _imwrite(out_path, crop)

def run_on_slide(png_path: str,
                 out_crops_dir: str,
                 out_overlay_dir: str,
                 max_clusters: int = 3) -> Dict[str, Any]:
    img, candidates = detect_card_candidates(png_path)
    H, W = img.shape[:2]
    clusters = cluster_boxes(candidates, W, H)

    # Convert clusters to merged boxes and keep top N
    merged = [merge_cluster_bbox(cl) for cl in clusters]
    merged.sort(key=lambda b: (b.area, b.score), reverse=True)
    merged = merged[:max_clusters]

    slide_id = os.path.splitext(os.path.basename(png_path))[0]
    overlay_path = os.path.join(out_overlay_dir, f"{slide_id}_overlay.png")
    export_debug_overlay(img, candidates, clusters, overlay_path)

    items = []
    for i, mb in enumerate(merged, start=1):
        crop_name = f"{slide_id}_cluster_{i:02d}.png"
        crop_path = os.path.join(out_crops_dir, crop_name)
        crop_png(png_path, mb, crop_path, pad_px=max(8, int(0.008*max(W,H))))
        items.append({
            "cluster_index": i,
            "rel_bbox": mb.to_norm(W, H),
            "score": mb.score,
            "crop": crop_path,
        })

    return {
        "slide_png": png_path,
        "slide_id": slide_id,
        "overlay": overlay_path,
        "clusters": items,
        "candidates": len(candidates),
    }

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--slide_png", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--max_clusters", type=int, default=3)
    args = ap.parse_args()

    crops_dir = os.path.join(args.out_dir, "crops")
    ov_dir = os.path.join(args.out_dir, "debug_overlay")
    res = run_on_slide(args.slide_png, crops_dir, ov_dir, max_clusters=args.max_clusters)
    out = os.path.join(args.out_dir, f"{res['slide_id']}_clusters.json")
    os.makedirs(args.out_dir, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("Wrote", out)

if __name__ == "__main__":
    main()
