# Variant Generator (MVP)

Dieses Paket transformiert Layout-JSONs in verschiedene Publishing-Varianten.

- `color_to_grayscale.py`: Hex-Farben → Graustufen (MVP, ohne CMYK Profile / Bilder)
- `format_converter.py`: A4 ↔ 8x11.5 (skalierte BBoxes + Doc-Size)
- `bleed_manager.py`: Bleed hinzufügen (Doc vergrößern + Shift)
- `amazon_validator.py`: Minimaler Bounds-Check (MVP)

