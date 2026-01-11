# Hints/Tags Schema (Scribus Engine)

This document defines the fields accepted by the Scribus layout engine in
`scribus/35_setzerei_engine.py` for PPTX sidecar tags and layout hints.

## Sidecar Tags

Sidecar tag files live under `media_pool/pptx/tags/` and follow this format:

```json
{
  "slides": {
    "3": {
      "text_boxes": {
        "5": "pullquote",
        "7": {"tag": "hero_caption", "position": "bottom"}
      },
      "image_boxes": {
        "1": "infographic",
        "2": {
          "tag": "infographic",
          "fit": "contain",
          "anchor": [0.5, 0.5],
          "min_dpi": 240,
          "bg_color": "MagGold"
        }
      }
    }
  }
}
```

### Text box tags

- `pullquote` / `quote`: becomes a quote card.
- `sidenote` / `sidebar`: goes into sidebar text.
- `hero_caption`: renders as overlay on the hero image.
- `caption`: goes into the caption field.
- `skip` / `body_skip`: ignored.

Optional fields for `hero_caption`:

- `position`: `"bottom"` (default), `"bottom-left"`, `"bottom-right"`, `"top"`.

### Image box tags

- `infographic`, `photo`, `herophoto`, `photostack`: rendered as infographic cards.
- `skip` / `body_skip`: ignored.

Optional fields for image rendering:

- `fit`: `"contain"` (default), `"cover"`, `"stretch"`.
- `anchor`: `[ax, ay]` with values `0..1` (default `[0.5, 0.5]`).
- `min_dpi`: minimum effective DPI before fallback (default `240`).
- `bg_color`: named Scribus color used when DPI is too low.

## Layout Hints (layout_hints.json)

Hints can also be supplied per page:

```json
{
  "items": [
    {
      "chapter": 3,
      "page_in_chapter": 2,
      "kind": "infographic",
      "image": "images/foo.png",
      "rel_bbox": [0.67, 0.35, 0.98, 0.55],
      "fit": "contain",
      "anchor": [0.5, 0.5],
      "min_dpi": 240,
      "bg_color": "MagGold"
    },
    {
      "chapter": 3,
      "page_in_chapter": 2,
      "kind": "hero_caption",
      "text": "Overlay text",
      "overlay": true,
      "position": "bottom"
    }
  ]
}
```

### rel_bbox

- `[x0, y0, x1, y1]` in normalized 0..1 page coordinates.
- The engine uses this to pick region and desired vertical placement.
