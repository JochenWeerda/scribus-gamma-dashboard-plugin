# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional, Tuple

def bbox_area(bb):
    x0,y0,x1,y1 = bb
    return max(0.0, x1-x0) * max(0.0, y1-y0)

def x_overlap(a, b) -> float:
    ax0,_,ax1,_ = a
    bx0,_,bx1,_ = b
    inter = max(0.0, min(ax1,bx1) - max(ax0,bx0))
    denom = max(1e-6, min(ax1-ax0, bx1-bx0))
    return inter / denom

def inside(inner, outer) -> bool:
    x0,y0,x1,y1 = inner
    ox0,oy0,ox1,oy1 = outer
    return x0>=ox0 and y0>=oy0 and x1<=ox1 and y1<=oy1

def find_anchors(cluster_bb, text_boxes, min_x_ov=0.35):
    """
    preceding: closest textbox above cluster with good x overlap
    following: closest textbox below cluster with good x overlap
    inside_texts: all textboxes inside cluster
    """
    cx0,cy0,cx1,cy1 = cluster_bb

    inside_t = [tb for tb in text_boxes if inside(tb["rel_bbox"], cluster_bb)]
    inside_t.sort(key=lambda t: (t["rel_bbox"][1], t["rel_bbox"][0]))

    above = []
    below = []
    for tb in text_boxes:
        bb = tb["rel_bbox"]
        ov = x_overlap(cluster_bb, bb)
        if ov < min_x_ov:
            continue
        if bb[3] <= cy0:  # below top of cluster
            dist = cy0 - bb[3]
            above.append((dist, tb))
        elif bb[1] >= cy1:
            dist = bb[1] - cy1
            below.append((dist, tb))

    above.sort(key=lambda x: x[0])
    below.sort(key=lambda x: x[0])

    preceding = above[0][1]["text"] if above else ""
    following = below[0][1]["text"] if below else ""
    return {
        "preceding_text": preceding,
        "following_text": following,
        "inside_texts": [t["text"] for t in inside_t],
    }
