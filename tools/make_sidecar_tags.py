import json
import os
import re


PPTX_DIR = os.environ.get(
    "ZC_PPTX_DIR",
    os.path.abspath(os.path.join(os.getcwd(), "media_pool", "pptx")),
)
TAGS_DIR = os.path.join(PPTX_DIR, "tags")
MANIFEST = os.path.join(PPTX_DIR, "manifest.json")

QUOTE_CHARS = ['"', "“", "”", "„", "»", "«"]


def safe_name(name):
    name = (name or "").strip()
    name = re.sub(r'[<>:"/\\\\|?*]', "_", name)
    return name or "pptx"


def looks_like_bullets(text):
    t = (text or "").strip()
    if not t:
        return False
    if "\n" in t and any(line.strip().startswith(("•", "-", "–", "·")) for line in t.splitlines() if line.strip()):
        return True
    if t.count("\n") >= 4:
        return True
    return False


def is_pullquote_text(text):
    t = (text or "").strip()
    if not t:
        return False
    if any(ch in t for ch in QUOTE_CHARS):
        if 30 <= len(t) <= 260 and not looks_like_bullets(t):
            return True
    return False


def is_sidebar_box(rel_bbox):
    x0, y0, x1, y1 = rel_bbox
    w = max(0.0, x1 - x0)
    return (x0 >= 0.66) or (x0 >= 0.55 and w <= 0.40)


def rel_area(rel_bbox):
    x0, y0, x1, y1 = rel_bbox
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def load_json(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def dump_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(obj, handle, ensure_ascii=False, indent=2)


def main():
    if not os.path.isfile(MANIFEST):
        raise SystemExit("manifest.json nicht gefunden: %s" % MANIFEST)

    manifest = load_json(MANIFEST)
    files = manifest.get("files", [])
    if not files:
        raise SystemExit("manifest.json hat keine 'files'")

    os.makedirs(TAGS_DIR, exist_ok=True)

    for f in files:
        name = f.get("name")
        rel_json = f.get("json")
        if not name or not rel_json:
            continue

        json_path = os.path.join(PPTX_DIR, rel_json)
        if not os.path.isfile(json_path):
            print("SKIP missing json:", json_path)
            continue

        data = load_json(json_path)
        slides = sorted(data.get("slides", []), key=lambda s: int(s.get("slide", 0) or 0))

        tagfile = os.path.join(TAGS_DIR, "%s_tags.json" % safe_name(name))
        indexfile = os.path.join(TAGS_DIR, "%s_index.json" % safe_name(name))

        if not os.path.isfile(tagfile):
            dump_json(tagfile, {"slides": {}})
            print("CREATED", tagfile)

        idx_out = {"pptx": name, "hint_schema": "v1", "slides": {}}

        for s in slides:
            slide_no = int(s.get("slide", 0) or 0)
            if slide_no <= 0:
                continue

            tbs = s.get("text_boxes", []) or []
            ibs = s.get("image_boxes", []) or []

            slide_entry = {"text_boxes": [], "image_boxes": []}

            for i, tb in enumerate(tbs):
                text = (tb.get("text") or "").strip()
                rel_bbox = tb.get("rel_bbox", [0, 0, 1, 1])
                guess = []
                if is_sidebar_box(rel_bbox):
                    guess.append("sidenote?")
                if is_pullquote_text(text):
                    guess.append("pullquote?")
                slide_entry["text_boxes"].append(
                    {
                        "i": i,
                        "rel_bbox": rel_bbox,
                        "area": round(rel_area(rel_bbox), 4),
                        "len": len(text),
                        "guess": guess,
                        "position_hint": "bottom",
                        "text": text[:120].replace("\n", " ⏎ "),
                    }
                )

            for i, ib in enumerate(ibs):
                rel_bbox = ib.get("rel_bbox", [0, 0, 1, 1])
                slide_entry["image_boxes"].append(
                    {
                        "i": i,
                        "rel_bbox": rel_bbox,
                        "area": round(rel_area(rel_bbox), 4),
                        "image": ib.get("image", ""),
                        "fit_hint": "contain",
                        "anchor_hint": [0.5, 0.5],
                        "min_dpi_hint": 240,
                    }
                )

            idx_out["slides"][str(slide_no)] = slide_entry

        dump_json(indexfile, idx_out)
        print("WROTE", indexfile)


if __name__ == "__main__":
    main()
