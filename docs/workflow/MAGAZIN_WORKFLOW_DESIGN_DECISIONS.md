# Magazin-Workflow: Designentscheidungen

Dieses Dokument bündelt die Design-/Layout-Entscheidungen für den Magazin-Workflow (Scribus + Gamma-Assets + Backend).
Ziel ist, dass Parser/Generator/Validator **deterministisch** arbeiten (gleiches Input → gleiches Output) und dass die RAG-DB
stabil bleibt.

## Zielbild
- Input: PPTX (Kapitel), optional Gamma-PNG-Exports (visuelle Wahrheit), optional PDFs (Referenz/Regression)
- Output: Layout-JSON (interne Repräsentation), Scribus-SLA, Varianten (Farbe + Graustufe), Quality-Reports

## Format & Druck
- Standard: DIN A4 `210×297mm`
- Bleed (Farbe): `3mm`
- Alternative (Amazon Paperback): `8×11.5"` (`203.2×292.1mm`)
- Margins (empfohlen, Paperback):
  - innen `25mm`, außen `20mm`, oben `20mm`, unten `23mm`
- Content-Start: ab Seite 4, Start auf rechter Seite.

## Grid / Layout
- 6-Spalten-Grid als Baseline (variabel per Template/Projekt).
- Objekte werden als „Boxes“ in Layout-JSON modelliert:
  - `text_box`, `image_box`, `infobox`, `quote_box`, `hero`, `background`, `figure_cluster`
- Priorität: Hero/Background zuerst, dann Text-Fluss, dann Infobox/Quotes, dann Deko/Ornamente.

## Typografie (konzeptionell)
- Styles sind **namentlich stabil** (kein dynamisches Renaming pro Run).
- Mindestens: `Body`, `H1`, `H2`, `Caption`, `Quote`, `Infobox`.
- Zahlen/Zeilen: konsistent (keine „Auto“-Schwankungen durch unterschiedliche Fonts).

## Farben & Akte
- 5 Akt-Farben (CMYK) – definieren Akzentfarben (Infobox/Quote/Divider).
- Variante „Graustufe“: Farbakzente werden sauber nach Graustufe überführt (siehe `packages/variant_generator/`).

## Layer-Konzept (Scribus)
- Layer-Namen sind stabil und werden als Ziel für SLA-Generator/Validator genutzt:
  - `BACKGROUND`, `IMAGES`, `TEXT`, `INFOBOX`, `QUOTES`, `OVERLAY` (minimaler Satz; erweiterbar)

## Heuristiken (PPTX → Layout)
- Text:
  - Erkennung über `pptx` Text-Runs, Font-Größe, Absatz-Stil, Bounding-Box
  - Headlines typischerweise größer, weniger Zeilen, „oben“ positioniert.
- Infobox:
  - Cluster aus Shapes + kurzer Text, oft mit Hintergrund-Shape
  - Im Workflow darf Infobox optional als **Gamma-Crop** gerendert werden (optische Wahrheit).
- Quote:
  - Erkennung über Anführungszeichen/Marker + typografische Merkmale (z.B. Italic/Spacing).
- „Infografik/Cluster“:
  - Viele kleine Shapes dicht beieinander → als `figure_cluster` behandeln
  - Optional als einzelnes hochauflösendes Bild via Gamma-Crop statt Import von 100+ Shapes.

## Gamma-Exports (optische Wahrheit)
- Gamma-PNG-Exports dienen als Referenz, um Ränder/Schlagschatten nicht abzuschneiden.
- Koordinaten-Mapping: PPTX-Units (72 DPI/points) → PNG-Pixel (z.B. 300/600 DPI).
- Crop-Regel: nur bestimmte Typen (Default: `infobox`) cropen; weitere Typen nur per Flag.

## RAG / Embeddings (Stabilität)
- Text-Embedding ist **hart** auf `paraphrase-multilingual-mpnet-base-v2` gesetzt (siehe `packages/rag_service/embeddings.py`).
- Grund: Ein Modellwechsel würde bestehende Chroma-Collections semantisch/dimensional inkonsistent machen.

## Output-Standards (JSON)
- Alle Pfade in Bundles/Manifests werden als **POSIX** (Forward-Slash) gespeichert, damit Linux-Container sicher arbeiten.
- Varianten-JSON kann (optional) `imageUrl` auf Artefakte zeigen, z.B. `/v1/artifacts/<id>`.

