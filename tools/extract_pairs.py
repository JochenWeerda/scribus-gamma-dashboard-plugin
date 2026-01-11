import json
import os
import re
from pathlib import Path

import fitz

PDF_DIR = os.environ.get(
    "ZC_PDF_DIR",
    r"C:\Users\Jochen\Documents\Die verbor´gene Uhr Gottes\PDFs DIN a4",
)
OUT_DIR = os.path.join("scribus", "data")
ASSET_DIR = os.path.join(OUT_DIR, "assets", "extracted")

START_PAGE_NUM = 4  # Scribus numbering start

# Acts define the processing order and which chapters belong to each act.
ACTS = [
    {"act": 1, "title": "DER URSPRUNG", "chapters": [0, 1, 2, 3], "hero": ""},
    {"act": 2, "title": "DAS DRAMA", "chapters": [4, 5, 6], "hero": ""},
    {"act": 3, "title": "DIE BESCHLEUNIGUNG", "chapters": [7, 8, 9, 10], "hero": ""},
    {"act": 4, "title": "DER SCHLEIER", "chapters": [11], "hero": ""},
    {"act": 5, "title": "DIE ANKUNFT", "chapters": [12, 13], "hero": ""},
]


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def list_pdfs(pdf_dir):
    items = []
    for name in os.listdir(pdf_dir):
        if name.lower().endswith(".pdf"):
            m = re.match(r"^(\d+)[\.-]", name)
            if m:
                items.append((int(m.group(1)), name))
    items.sort(key=lambda x: x[0])
    return items


def pdf_map(pdf_dir):
    mapping = {}
    for idx, name in list_pdfs(pdf_dir):
        mapping[idx] = os.path.join(pdf_dir, name)
    return mapping


def rel_bbox(page_rect, bbox):
    x0, y0, x1, y1 = bbox
    w = page_rect.width
    h = page_rect.height
    if w <= 0 or h <= 0:
        return [0.0, 0.0, 1.0, 1.0]
    return [
        max(0.0, min(1.0, x0 / w)),
        max(0.0, min(1.0, y0 / h)),
        max(0.0, min(1.0, x1 / w)),
        max(0.0, min(1.0, y1 / h)),
    ]


def extract_images(doc, page, chapter, page_index):
    items = []
    try:
        images = page.get_images(full=True)
    except Exception:
        images = []
    for img_info in images:
        xref = img_info[0]
        try:
            rects = page.get_image_rects(xref)
        except Exception:
            rects = []
        if not rects:
            continue
        try:
            img = doc.extract_image(xref)
        except Exception:
            continue
        ext = img.get("ext", "png")
        name = f"ch{chapter:02d}_p{page_index:03d}_img{xref}.{ext}"
        out_path = os.path.join(ASSET_DIR, name)
        with open(out_path, "wb") as handle:
            handle.write(img.get("image", b""))
        for rect in rects:
            items.append(
                {
                    "path": os.path.join("assets", "extracted", name),
                    "bbox": [rect.x0, rect.y0, rect.x1, rect.y1],
                }
            )
    return items


def largest_image(images):
    best = None
    best_area = 0.0
    for item in images:
        x0, y0, x1, y1 = item["bbox"]
        area = max(0.0, x1 - x0) * max(0.0, y1 - y0)
        if area > best_area:
            best_area = area
            best = item
    return best


def main():
    ensure_dir(OUT_DIR)
    ensure_dir(ASSET_DIR)

    pdfs = pdf_map(PDF_DIR)
    if not pdfs:
        raise SystemExit("No chapter PDFs found")

    manifest = []
    hints = []
    page_num = START_PAGE_NUM

    for act in ACTS:
        act_id = act["act"]
        act_title = act["title"]
        for ch in act["chapters"]:
            pdf_path = pdfs.get(ch)
            if not pdf_path:
                continue
            doc = fitz.open(pdf_path)
            pages = doc.page_count
            page_in_chapter = 1

            while page_in_chapter <= pages:
                for offset in (0, 1):
                    src_idx = page_in_chapter - 1 + offset
                    if src_idx >= pages:
                        continue
                    page = doc.load_page(src_idx)
                    text = page.get_text("text") or ""
                    images = extract_images(doc, page, ch, src_idx + 1)
                    hero = ""
                    if page_in_chapter == 1 and offset == 0 and images:
                        biggest = largest_image(images)
                        if biggest:
                            hero = biggest["path"]

                    data = {
                        "chapter": ch,
                        "act": act_id,
                        "act_name": act_title,
                        "page_in_chapter": src_idx + 1,
                        "headline": "" if src_idx > 0 else os.path.splitext(os.path.basename(pdf_path))[0],
                        "deck": "",
                        "body": text.strip(),
                        "caption": "",
                        "sidebar": "",
                        "quote": "",
                        "hero_image": hero,
                    }

                    out_name = "page_%04d.json" % page_num
                    out_path = os.path.join(OUT_DIR, out_name)
                    with open(out_path, "w", encoding="utf-8") as handle:
                        json.dump(data, handle, ensure_ascii=True, indent=2)

                    manifest.append(
                        {
                            "page": page_num,
                            "chapter": ch,
                            "act": act_id,
                            "act_name": act_title,
                            "source_pdf": pdf_path,
                            "page_in_chapter": src_idx + 1,
                            "data": out_path,
                        }
                    )

                    for img in images:
                        hints.append(
                            {
                                "chapter": ch,
                                "page_in_chapter": src_idx + 1,
                                "kind": "infographic",
                                "image": img["path"],
                                "caption": "",
                                "rel_bbox": rel_bbox(page.rect, img["bbox"]),
                            }
                        )

                    page_num += 1

                page_in_chapter += 2

            doc.close()

    with open(os.path.join(OUT_DIR, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=True, indent=2)

    with open(os.path.join(OUT_DIR, "layout_hints.json"), "w", encoding="utf-8") as handle:
        json.dump({"items": hints}, handle, ensure_ascii=True, indent=2)

    print("Wrote", len(manifest), "pages to", OUT_DIR)
    print("Wrote", len(hints), "hints to layout_hints.json")


if __name__ == "__main__":
    main()
