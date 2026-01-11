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
MAX_QUOTES_PER_SLIDE = 1
DEFAULT_IMAGE_TAG = {
    "tag": "infographic",
    "fit": "contain",
    "anchor": [0.5, 0.5],
    "min_dpi": 240,
}


def safe_name(name):
    name = (name or "").strip()
    name = re.sub(r'[<>:"/\\\\|?*]', "_", name)
    return name or "pptx"


def load_json(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def dump_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(obj, handle, ensure_ascii=False, indent=2)


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


def ensure_tag_dict(path):
    if os.path.isfile(path):
        return load_json(path)
    return {"slides": {}}


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
        tags = ensure_tag_dict(tagfile)

        for s in slides:
            slide_no = int(s.get("slide", 0) or 0)
            if slide_no <= 0:
                continue

            slide_key = str(slide_no)
            slide_tags = tags["slides"].get(slide_key, {})
            text_tags = slide_tags.get("text_boxes", {})
            image_tags = slide_tags.get("image_boxes", {})

            # Pullquote candidate selection by area
            quote_candidates = []
            for i, tb in enumerate(s.get("text_boxes", []) or []):
                if str(i) in text_tags:
                    continue
                text = (tb.get("text") or "").strip()
                if not text:
                    continue
                rel_bbox = tb.get("rel_bbox", [0, 0, 1, 1])
                if is_pullquote_text(text):
                    quote_candidates.append((i, rel_bbox))

            quote_candidates.sort(key=lambda q: rel_area(q[1]), reverse=True)
            for i, _ in quote_candidates[:MAX_QUOTES_PER_SLIDE]:
                text_tags[str(i)] = "pullquote"

            # Sidebar notes
            for i, tb in enumerate(s.get("text_boxes", []) or []):
                if str(i) in text_tags:
                    continue
                rel_bbox = tb.get("rel_bbox", [0, 0, 1, 1])
                if is_sidebar_box(rel_bbox):
                    text_tags[str(i)] = "sidenote"

            # Images default to infographic (unless already tagged)
            for i, ib in enumerate(s.get("image_boxes", []) or []):
                if str(i) in image_tags:
                    continue
                image_tags[str(i)] = DEFAULT_IMAGE_TAG.copy()

            tags["slides"][slide_key] = {
                "text_boxes": text_tags,
                "image_boxes": image_tags,
            }

        dump_json(tagfile, tags)
        print("UPDATED", tagfile)


if __name__ == "__main__":
    main()
