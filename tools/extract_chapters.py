import json
import os
import re
from pathlib import Path

import fitz

PDF_DIR = os.environ.get("ZC_PDF_DIR", r"C:\Users\Jochen\Documents\Die verbor?gene Uhr Gottes\PDFs DIN a4")
ASSET_BASE = os.path.join(PDF_DIR, "zeitcode_overleaf_assets_FULL_refresh", "images")
HERO_DIR = os.path.join(ASSET_BASE, "heroes", "hires")
OUT_DIR = os.path.join("scribus", "data")

START_PAGE_NUM = 4  # Scribus page numbering start for chapter 0
PAGES_PER_CHAPTER = 10

# Act mapping (adjusted to current chapter set)
ACTS = [
    ("I", "Der Ursprung", {0, 1, 2, 3}),
    ("II", "Das Drama der Geschichte", {4, 5, 6, 7}),
    ("III", "Die Beschleunigung", {8, 9, 10}),
    ("IV", "Der Uebergang", {11}),
    ("V", "Das Finale", {12, 13}),
]


def list_pdfs(pdf_dir):
    items = []
    for name in os.listdir(pdf_dir):
        if name.lower().endswith(".pdf"):
            m = re.match(r"^(\d+)-", name)
            if m:
                items.append((int(m.group(1)), name))
    items.sort(key=lambda x: x[0])
    return items


def pick_hero_image(ch_idx):
    if not os.path.isdir(HERO_DIR):
        return ""
    prefix = "ch%02d" % ch_idx
    for name in os.listdir(HERO_DIR):
        lower = name.lower()
        if lower.startswith(prefix) and lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".svg")):
            return os.path.join(HERO_DIR, name)
    return ""


def act_for_chapter(ch_idx):
    for act_id, act_name, chapters in ACTS:
        if ch_idx in chapters:
            return act_id, act_name
    return "", ""


def first_lines(text, max_lines=3):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return lines[:max_lines]


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def main():
    ensure_dir(OUT_DIR)
    pdfs = list_pdfs(PDF_DIR)
    if not pdfs:
        raise SystemExit("No chapter PDFs found")

    manifest = []
    page_num = START_PAGE_NUM

    for ch_idx, name in pdfs:
        pdf_path = os.path.join(PDF_DIR, name)
        doc = fitz.open(pdf_path)
        hero_path = pick_hero_image(ch_idx)
        title = os.path.splitext(name)[0]
        act_id, act_name = act_for_chapter(ch_idx)

        for i in range(PAGES_PER_CHAPTER):
            text = ""
            if i < doc.page_count:
                text = doc.load_page(i).get_text("text")
            lines = first_lines(text)
            headline = title if i == 0 else ""
            deck = " ".join(lines[:2]) if i == 0 else ""

            data = {
                "chapter": ch_idx,
                "act": act_id,
                "act_name": act_name,
                "page_in_chapter": i + 1,
                "headline": headline,
                "deck": deck,
                "body": text.strip(),
                "caption": "",
                "sidebar": "",
                "quote": "",
                "hero_image_url": hero_path if i == 0 else "",
            }

            out_name = "page_%04d.json" % page_num
            out_path = os.path.join(OUT_DIR, out_name)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=True, indent=2)

            manifest.append({
                "page": page_num,
                "chapter": ch_idx,
                "act": act_id,
                "act_name": act_name,
                "source_pdf": pdf_path,
                "page_in_chapter": i + 1,
                "data": out_path,
            })
            page_num += 1

        doc.close()

    with open(os.path.join(OUT_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=True, indent=2)

    print("Wrote", len(manifest), "pages to", OUT_DIR)


if __name__ == "__main__":
    main()
