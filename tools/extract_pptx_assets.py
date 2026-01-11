# -*- coding: utf-8 -*-
import json
import os
import re
import time
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

PPT_DIR = os.environ.get("ZC_PPT_DIR", "")

if not PPT_DIR or not os.path.isdir(PPT_DIR):
    docs_dir = Path.home() / "Documents"
    try:
        for cand in docs_dir.iterdir():
            if cand.name.startswith("Die verbor"):
                ppt = cand / "Powerpoints"
                if ppt.is_dir():
                    PPT_DIR = str(ppt)
                    break
    except Exception:
        pass
OUT_DIR = os.path.join("media_pool", "pptx")
IMG_DIR = os.path.join(OUT_DIR, "images")
JSON_DIR = os.path.join(OUT_DIR, "json")
MANIFEST_PATH = os.path.join(OUT_DIR, "manifest.json")
LOG_PATH = os.path.join(OUT_DIR, "extract.log")
LOG_RESET = True

PPTX_ONLY = []
ENV_ONLY = os.environ.get("ZC_PPTX_ONLY", "").strip()
if ENV_ONLY:
    PPTX_ONLY = [p.strip() for p in ENV_ONLY.split(",") if p.strip()]
try:
    PPTX_LIMIT = int(os.environ.get("ZC_PPTX_LIMIT", "0") or 0)
except ValueError:
    PPTX_LIMIT = 0

SLIDE_DIR = "ppt/slides"
RELS_DIR = "ppt/slides/_rels"
MEDIA_DIR = "ppt/media"
PRESENTATION_XML = "ppt/presentation.xml"

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

QUOTE_CHARS = ['"', "\u201c", "\u201d", "\u201e", "\u00bb", "\u00ab", "\u2019", "\u2018"]

# =========================================================
# PPTX Infografik-Parsing Heuristics
# =========================================================
INFO_MIN_REL_AREA = 0.02
INFO_MIN_REL_W = 0.08
INFO_MIN_REL_H = 0.05
INFO_MAX_REL_AREA_FOR_BG_SKIP = 0.92
INFO_MIN_ASPECT = 0.15
INFO_MAX_ASPECT = 6.50
INFO_MERGE_ENABLED = True
INFO_IOU_MERGE_TH = 0.25
INFO_GAP_MERGE_TH = 0.03
INFO_MAX_MERGED_PER_SLIDE = 4

# Background/Frame suppress
INFO_BG_SUPPRESS_ENABLED = True
INFO_BG_EDGE_EPS = 0.015
INFO_BG_MIN_REL_H = 0.82
INFO_BG_MIN_REL_W = 0.45
INFO_BG_MIN_TOUCH_EDGES = 2
INFO_BG_CONTAIN_ENABLED = True
INFO_BG_CONTAIN_EPS = 0.006
INFO_BG_CONTAIN_MIN_AREA = 0.50
INFO_BG_CONTAIN_MIN_COUNT = 1
INFO_BG_CONTAIN_SUM_AREA_FRAC = 0.12

# Text vs image overlap
TEXT_IMAGE_OVERLAP_TH = 0.20

# Infobox (text-card) heuristics
INFOBOX_MIN_REL_AREA = 0.04
INFOBOX_MIN_REL_W = 0.12
INFOBOX_MIN_REL_H = 0.06
INFOBOX_MIN_TEXT_CHARS = 8
INFOBOX_MAX_TEXT_CHARS = 320
INFOBOX_MAX_LINES = 10


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def _now_ts():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def init_logging():
    if LOG_RESET:
        try:
            ensure_dir(OUT_DIR)
            with open(LOG_PATH, "w", encoding="utf-8") as handle:
                handle.write("")
        except Exception:
            pass
    log("extract_log_init")


def log(msg):
    line = "[%s] %s" % (_now_ts(), msg)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except Exception:
        pass


def list_pptx(ppt_dir):
    allowed = {p.lower() for p in PPTX_ONLY} if PPTX_ONLY else None
    files = sorted(
        [
            os.path.join(ppt_dir, name)
            for name in os.listdir(ppt_dir)
            if name.lower().endswith(".pptx")
            and (not allowed or os.path.splitext(name)[0].lower() in allowed)
        ]
    )
    if PPTX_LIMIT and PPTX_LIMIT > 0:
        return files[:PPTX_LIMIT]
    return files


def slide_name(idx):
    return "slide%d.xml" % idx


def rels_name(idx):
    return "slide%d.xml.rels" % idx


def parse_rels(xml_bytes):
    rels = {}
    try:
        root = ET.fromstring(xml_bytes)
    except Exception:
        return rels
    for rel in root.findall(".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
        r_id = rel.attrib.get("Id")
        target = rel.attrib.get("Target")
        r_type = rel.attrib.get("Type", "")
        if r_id and target and "image" in r_type:
            rels[r_id] = target
    return rels


def parse_slide_text(xml_bytes):
    try:
        root = ET.fromstring(xml_bytes)
    except Exception:
        return []
    paragraphs = []
    for p in root.findall(".//a:p", NS):
        runs = []
        for t in p.findall(".//a:t", NS):
            if t.text:
                runs.append(t.text)
        if runs:
            text = "".join(runs).strip()
            if text:
                paragraphs.append(text)
    return paragraphs


def parse_slide_images(xml_bytes):
    try:
        root = ET.fromstring(xml_bytes)
    except Exception:
        return []
    r_ids = []
    for blip in root.findall(".//a:blip", NS):
        r_id = blip.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
        if r_id:
            r_ids.append(r_id)
    return r_ids


def safe_filename(name):
    base = re.sub(r"[^a-zA-Z0-9._-]+", "_", name)
    return base.strip("_") or "asset"


def is_quote_candidate(text):
    t = (text or "").strip()
    if not t:
        return False
    if any(ch in t for ch in QUOTE_CHARS):
        return True
    if t.startswith((">", "\u00bb")):
        return True
    if 40 <= len(t) <= 220 and t.count(".") <= 3 and not looks_like_bullets(t):
        return True
    return False


def looks_like_bullets(text):
    t = (text or "").strip()
    if not t:
        return False
    bullets = ("\u2022", "\u00b7", "- ", "\u2013 ")
    lines = [line.strip() for line in t.splitlines() if line.strip()]
    bullet_lines = [line for line in lines if line.startswith(bullets)]
    return len(bullet_lines) >= 2


def looks_like_infobox_text(text, rel_bbox):
    t = (text or "").strip()
    if not t:
        return False
    x0, y0, x1, y1 = rel_bbox
    w = max(0.0, x1 - x0)
    h = max(0.0, y1 - y0)
    area = w * h
    if area < INFOBOX_MIN_REL_AREA:
        return False
    if w < INFOBOX_MIN_REL_W or h < INFOBOX_MIN_REL_H:
        return False
    if len(t) < INFOBOX_MIN_TEXT_CHARS or len(t) > INFOBOX_MAX_TEXT_CHARS:
        return False
    if t.count("\n") > INFOBOX_MAX_LINES:
        return False
    if looks_like_bullets(t):
        return False
    if is_quote_candidate(t):
        return False
    return True


def write_image(blob, out_dir, base_name):
    ensure_dir(out_dir)
    name = safe_filename(base_name)
    path = os.path.join(out_dir, name)
    if os.path.exists(path):
        root, ext = os.path.splitext(name)
        counter = 1
        while True:
            candidate = os.path.join(out_dir, "%s_%d%s" % (root, counter, ext))
            if not os.path.exists(candidate):
                path = candidate
                break
            counter += 1
    with open(path, "wb") as handle:
        handle.write(blob)
    return path


def slide_size_from_presentation(zf):
    if PRESENTATION_XML not in zf.namelist():
        return None
    try:
        root = ET.fromstring(zf.read(PRESENTATION_XML))
    except Exception:
        return None
    sld_sz = root.find(".//p:sldSz", NS)
    if sld_sz is None:
        return None
    try:
        cx = int(sld_sz.attrib.get("cx", "0"))
        cy = int(sld_sz.attrib.get("cy", "0"))
    except Exception:
        return None
    if cx <= 0 or cy <= 0:
        return None
    return cx, cy


def rel_bbox_from_emu(x, y, w, h, size):
    if not size:
        return [0.0, 0.0, 1.0, 1.0]
    max_x, max_y = size
    if max_x <= 0 or max_y <= 0:
        return [0.0, 0.0, 1.0, 1.0]
    return [
        max(0.0, min(1.0, x / max_x)),
        max(0.0, min(1.0, y / max_y)),
        max(0.0, min(1.0, (x + w) / max_x)),
        max(0.0, min(1.0, (y + h) / max_y)),
    ]


def clamp_bbox(rel_bbox):
    x0, y0, x1, y1 = rel_bbox
    return [
        max(0.0, min(1.0, x0)),
        max(0.0, min(1.0, y0)),
        max(0.0, min(1.0, x1)),
        max(0.0, min(1.0, y1)),
    ]


def bbox_area(rel_bbox):
    x0, y0, x1, y1 = rel_bbox
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def bbox_iou(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0 = max(ax0, bx0)
    iy0 = max(ay0, by0)
    ix1 = min(ax1, bx1)
    iy1 = min(ay1, by1)
    iw = max(0.0, ix1 - ix0)
    ih = max(0.0, iy1 - iy0)
    inter = iw * ih
    if inter <= 0.0:
        return 0.0
    union = bbox_area(a) + bbox_area(b) - inter
    if union <= 0.0:
        return 0.0
    return inter / union


def bbox_gap(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(0.0, max(ax0, bx0) - min(ax1, bx1))
    dy = max(0.0, max(ay0, by0) - min(ay1, by1))
    return max(dx, dy)


def merge_bbox(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return [min(ax0, bx0), min(ay0, by0), max(ax1, bx1), max(ay1, by1)]


def bbox_touches_edges(rel_bbox, eps=INFO_BG_EDGE_EPS):
    x0, y0, x1, y1 = rel_bbox
    touches = 0
    if x0 <= eps:
        touches += 1
    if y0 <= eps:
        touches += 1
    if (1.0 - x1) <= eps:
        touches += 1
    if (1.0 - y1) <= eps:
        touches += 1
    return touches


def bbox_contains(a, b, eps=INFO_BG_CONTAIN_EPS):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return (bx0 >= ax0 - eps) and (by0 >= ay0 - eps) and (bx1 <= ax1 + eps) and (by1 <= ay1 + eps)


def looks_like_real_infographic(rel_bbox):
    x0, y0, x1, y1 = rel_bbox
    w = max(0.0, x1 - x0)
    h = max(0.0, y1 - y0)
    area = w * h
    if area < INFO_MIN_REL_AREA:
        return False
    if w < INFO_MIN_REL_W or h < INFO_MIN_REL_H:
        return False
    if area > INFO_MAX_REL_AREA_FOR_BG_SKIP:
        return False
    aspect = h / w if w > 0 else 0.0
    if aspect < INFO_MIN_ASPECT or aspect > INFO_MAX_ASPECT:
        return False
    return True


def looks_like_background_fill(rel_bbox):
    x0, y0, x1, y1 = rel_bbox
    w = max(0.0, x1 - x0)
    h = max(0.0, y1 - y0)
    if h >= INFO_BG_MIN_REL_H and w >= INFO_BG_MIN_REL_W:
        if bbox_touches_edges(rel_bbox) >= INFO_BG_MIN_TOUCH_EDGES:
            return True
    return False


def looks_like_background_container(candidate_bbox, all_boxes_rel_bboxes):
    if not INFO_BG_CONTAIN_ENABLED:
        return False
    area = bbox_area(candidate_bbox)
    if area < INFO_BG_CONTAIN_MIN_AREA:
        return False
    count = 0
    sum_area = 0.0
    for bb in all_boxes_rel_bboxes:
        if bb == candidate_bbox:
            continue
        if bbox_contains(candidate_bbox, bb):
            count += 1
            sum_area += bbox_area(bb)
    if count >= INFO_BG_CONTAIN_MIN_COUNT and sum_area >= area * INFO_BG_CONTAIN_SUM_AREA_FRAC:
        return True
    return False


def merge_image_boxes(boxes):
    if not boxes or not INFO_MERGE_ENABLED:
        out = []
        for b in boxes or []:
            rb = b.get("rel_bbox")
            if rb and looks_like_real_infographic(rb):
                out.append(b)
        return out

    clusters = []
    for box in boxes:
        b = box["rel_bbox"]
        placed = False
        for cl in clusters:
            if bbox_iou(b, cl["bbox"]) >= INFO_IOU_MERGE_TH or bbox_gap(b, cl["bbox"]) <= INFO_GAP_MERGE_TH:
                cl["items"].append(box)
                cl["bbox"] = merge_bbox(cl["bbox"], b)
                placed = True
                break
        if not placed:
            clusters.append({"bbox": b, "items": [box]})

    merged = True
    while merged and len(clusters) > 1:
        merged = False
        out = []
        used = [False] * len(clusters)
        for i in range(len(clusters)):
            if used[i]:
                continue
            base = clusters[i]
            for j in range(i + 1, len(clusters)):
                if used[j]:
                    continue
                other = clusters[j]
                if bbox_iou(base["bbox"], other["bbox"]) >= INFO_IOU_MERGE_TH or bbox_gap(
                    base["bbox"], other["bbox"]
                ) <= INFO_GAP_MERGE_TH:
                    base["bbox"] = merge_bbox(base["bbox"], other["bbox"])
                    base["items"].extend(other["items"])
                    used[j] = True
                    merged = True
            used[i] = True
            out.append(base)
        clusters = out

    merged_boxes = []
    for cl in clusters:
        rep = max(cl["items"], key=lambda it: bbox_area(it["rel_bbox"]))
        rep = dict(rep)
        rep["rel_bbox"] = cl["bbox"]
        if not looks_like_real_infographic(rep["rel_bbox"]):
            continue
        merged_boxes.append(rep)

    return merged_boxes


def overlaps_image_mask(text_bbox, image_masks):
    if not image_masks:
        return False
    for ib in image_masks:
        if bbox_iou(text_bbox, ib) >= TEXT_IMAGE_OVERLAP_TH:
            return True
    return False


def parse_text_boxes(xml_bytes, slide_size):
    try:
        root = ET.fromstring(xml_bytes)
    except Exception:
        return []
    boxes = []
    for sp in root.findall(".//p:sp", NS):
        tx_body = sp.find(".//p:txBody", NS)
        if tx_body is None:
            continue
        texts = []
        for t in tx_body.findall(".//a:t", NS):
            if t.text:
                texts.append(t.text)
        text = "".join(texts).strip()
        if not text:
            continue
        xfrm = sp.find(".//p:spPr/a:xfrm", NS)
        if xfrm is None:
            xfrm = sp.find(".//a:xfrm", NS)
        x = y = w = h = 0
        if xfrm is not None:
            off = xfrm.find("a:off", NS)
            ext = xfrm.find("a:ext", NS)
            if off is not None:
                x = int(off.attrib.get("x", "0") or 0)
                y = int(off.attrib.get("y", "0") or 0)
            if ext is not None:
                w = int(ext.attrib.get("cx", "0") or 0)
                h = int(ext.attrib.get("cy", "0") or 0)
        boxes.append(
            {
                "text": text,
                "bbox_emu": [x, y, x + w, y + h],
                "rel_bbox": rel_bbox_from_emu(x, y, w, h, slide_size),
            }
        )
    return boxes


def parse_image_boxes(xml_bytes, rels, slide_size):
    try:
        root = ET.fromstring(xml_bytes)
    except Exception:
        return []
    boxes = []
    for pic in root.findall(".//p:pic", NS):
        blip = pic.find(".//a:blip", NS)
        r_id = None
        if blip is not None:
            r_id = blip.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
        if not r_id:
            continue
        target = rels.get(r_id)
        if not target:
            continue
        xfrm = pic.find(".//p:spPr/a:xfrm", NS)
        if xfrm is None:
            xfrm = pic.find(".//a:xfrm", NS)
        x = y = w = h = 0
        if xfrm is not None:
            off = xfrm.find("a:off", NS)
            ext = xfrm.find("a:ext", NS)
            if off is not None:
                x = int(off.attrib.get("x", "0") or 0)
                y = int(off.attrib.get("y", "0") or 0)
            if ext is not None:
                w = int(ext.attrib.get("cx", "0") or 0)
                h = int(ext.attrib.get("cy", "0") or 0)
        boxes.append(
            {
                "r_id": r_id,
                "target": target,
                "bbox_emu": [x, y, x + w, y + h],
                "rel_bbox": rel_bbox_from_emu(x, y, w, h, slide_size),
            }
        )
    return boxes


def extract_from_pptx(path):
    base = os.path.splitext(os.path.basename(path))[0]
    slides = []
    images = []
    texts = []
    quotes = []
    t0 = time.perf_counter()
    log("pptx_start %s" % base)
    try:
        with zipfile.ZipFile(path, "r") as zf:
            slide_size = slide_size_from_presentation(zf)
            extracted_media = {}
            slide_files = sorted(
                [name for name in zf.namelist() if name.startswith(SLIDE_DIR + "/slide") and name.endswith(".xml")]
            )
            for slide_file in slide_files:
                slide_t0 = time.perf_counter()
                idx_str = os.path.splitext(os.path.basename(slide_file))[0].replace("slide", "")
                try:
                    idx = int(idx_str)
                except Exception:
                    continue
                rels_file = "%s/%s" % (RELS_DIR, rels_name(idx))
                rels = {}
                try:
                    if rels_file in zf.namelist():
                        rels = parse_rels(zf.read(rels_file))
                except KeyError:
                    rels = {}

                try:
                    xml_bytes = zf.read(slide_file)
                except KeyError:
                    continue

                image_boxes_all = parse_image_boxes(xml_bytes, rels, slide_size)
                all_rel_bboxes = [clamp_bbox(b.get("rel_bbox", [0.0, 0.0, 1.0, 1.0])) for b in image_boxes_all]

                raw_images = []
                skip_small = 0
                skip_bg_fill = 0
                skip_bg_cont = 0

                for entry in image_boxes_all:
                    rel_bbox = clamp_bbox(entry.get("rel_bbox", [0.0, 0.0, 1.0, 1.0]))
                    entry["rel_bbox"] = rel_bbox

                    if not looks_like_real_infographic(rel_bbox):
                        skip_small += 1
                        continue

                    if INFO_BG_SUPPRESS_ENABLED:
                        if looks_like_background_fill(rel_bbox):
                            skip_bg_fill += 1
                            continue
                        if looks_like_background_container(rel_bbox, all_rel_bboxes):
                            skip_bg_cont += 1
                            continue

                    raw_images.append(entry)

                candidates = merge_image_boxes(raw_images)
                candidates.sort(key=lambda b: bbox_area(b["rel_bbox"]), reverse=True)

                if INFO_MAX_MERGED_PER_SLIDE:
                    kept = candidates[: INFO_MAX_MERGED_PER_SLIDE]
                else:
                    kept = candidates

                slide_images = []
                image_masks = []
                for entry in kept:
                    target = entry.get("target")
                    if not target:
                        continue
                    target_path = target.replace("..", "").lstrip("/")
                    media_path = os.path.normpath(os.path.join(SLIDE_DIR, target_path)).replace("\\", "/")
                    if media_path not in zf.namelist():
                        media_path = os.path.normpath(os.path.join("ppt", target_path)).replace("\\", "/")
                    if media_path not in zf.namelist():
                        continue

                    if media_path not in extracted_media:
                        blob = zf.read(media_path)
                        out_name = "%s_s%03d_%s" % (base, idx, os.path.basename(media_path))
                        out_path = write_image(blob, IMG_DIR, out_name)
                        extracted_media[media_path] = os.path.relpath(out_path, OUT_DIR)

                    rel_out = extracted_media[media_path]
                    entry["image"] = rel_out
                    slide_images.append(rel_out)
                    images.append(rel_out)
                    image_masks.append(entry.get("rel_bbox"))

                text_boxes_all = parse_text_boxes(xml_bytes, slide_size)
                text_boxes_out = []
                ignored_overlap = 0
                ignored_infobox = 0
                ignored_quote = 0
                for tb in text_boxes_all:
                    rel_bbox = clamp_bbox(tb.get("rel_bbox", [0.0, 0.0, 1.0, 1.0]))
                    tb["rel_bbox"] = rel_bbox

                    role = "body"
                    ignore = False
                    if overlaps_image_mask(rel_bbox, image_masks):
                        role = "image_overlap"
                        ignore = True
                        ignored_overlap += 1
                    elif looks_like_infobox_text(tb.get("text", ""), rel_bbox):
                        role = "infobox"
                        ignore = True
                        ignored_infobox += 1
                    elif is_quote_candidate(tb.get("text", "")):
                        role = "quote"
                        ignore = True
                        ignored_quote += 1

                    tb["role"] = role
                    tb["ignore"] = ignore
                    text_boxes_out.append(tb)

                text_blocks = [
                    b["text"]
                    for b in text_boxes_out
                    if (not b.get("ignore")) and b.get("text") and b.get("role") == "body"
                ]
                quote_blocks = [
                    b["text"] for b in text_boxes_out if b.get("role") == "quote" and b.get("text")
                ]
                infoboxes = [b for b in text_boxes_out if b.get("role") == "infobox"]

                slides.append(
                    {
                        "slide": idx,
                        "texts": text_blocks,
                        "quote_candidates": quote_blocks,
                        "infoboxes": infoboxes,
                        "infobox_count": len(infoboxes),
                        "quote_count": len(quote_blocks),
                        "images": slide_images,
                        "text_boxes": text_boxes_out,
                        "image_boxes": kept,
                        "image_masks": image_masks,
                        "text_boxes_total": len(text_boxes_all),
                        "text_boxes_kept": len(text_blocks),
                        "text_boxes_overlap": ignored_overlap,
                        "text_boxes_infobox": ignored_infobox,
                        "text_boxes_quote": ignored_quote,
                        "image_boxes_total": len(image_boxes_all),
                        "image_boxes_kept": len(kept),
                        "skip_small": skip_small,
                        "skip_bg_fill": skip_bg_fill,
                        "skip_bg_cont": skip_bg_cont,
                        "slide_seconds": round(time.perf_counter() - slide_t0, 3),
                    }
                )

                texts.extend(text_blocks)
                quotes.extend(quote_blocks)

                log(
                    "slide %s: t=%.3fs img_total=%d kept=%d skip_small=%d skip_bg_fill=%d skip_bg_cont=%d text_boxes=%d text_kept=%d overlap=%d infobox=%d quote=%d"
                    % (
                        idx,
                        time.perf_counter() - slide_t0,
                        len(image_boxes_all),
                        len(kept),
                        skip_small,
                        skip_bg_fill,
                        skip_bg_cont,
                        len(text_boxes_all),
                        len(text_blocks),
                        ignored_overlap,
                        len(infoboxes),
                        len(quote_blocks),
                    )
                )
    except zipfile.BadZipFile:
        log("bad_zip %s" % path)
        return None
    except Exception as exc:
        log("extract_error %s %s" % (path, exc))
        return None

    char_count = sum(len(t) for t in texts)
    quote_char_count = sum(len(t) for t in quotes)
    dt = time.perf_counter() - t0
    log("pptx_done %s seconds=%.2f slides=%d images=%d" % (base, dt, len(slides), len(images)))

    return {
        "source": path,
        "name": base,
        "slides": slides,
        "images": images,
        "texts": texts,
        "quotes": quotes,
        "char_count": char_count,
        "quote_char_count": quote_char_count,
    }


def main():
    ensure_dir(OUT_DIR)
    ensure_dir(IMG_DIR)
    ensure_dir(JSON_DIR)
    init_logging()

    pptx_files = list_pptx(PPT_DIR)
    if not pptx_files:
        log("no_pptx_files %s" % PPT_DIR)
        raise SystemExit("No PPTX files found in %s" % PPT_DIR)

    if PPTX_ONLY:
        log("pptx_only %s" % ", ".join(PPTX_ONLY))
    if PPTX_LIMIT:
        log("pptx_limit %d" % PPTX_LIMIT)
    log("pptx_files %d" % len(pptx_files))

    manifest = {"source_dir": PPT_DIR, "files": []}

    for pptx in pptx_files:
        log("pptx_file %s" % os.path.basename(pptx))
        data = extract_from_pptx(pptx)
        if not data:
            continue
        out_path = os.path.join(JSON_DIR, "%s.json" % data["name"])
        with open(out_path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
        manifest["files"].append(
            {
                "name": data["name"],
                "source": data["source"],
                "json": os.path.relpath(out_path, OUT_DIR),
                "slides": len(data["slides"]),
                "images": len(data["images"]),
                "quotes": len(data["quotes"]),
                "char_count": data["char_count"],
                "quote_char_count": data["quote_char_count"],
            }
        )

    with open(MANIFEST_PATH, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)

    log("manifest_written %s files=%d" % (MANIFEST_PATH, len(manifest["files"])))
    print("Extracted %d PPTX files" % len(manifest["files"]))
    print("Manifest:", MANIFEST_PATH)


if __name__ == "__main__":
    main()
