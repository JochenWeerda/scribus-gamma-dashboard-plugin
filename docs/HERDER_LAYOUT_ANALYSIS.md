# Herder G/GESCHICHTE Layout-Analyse

## Übersicht
Analyse der Layout-Strukturen des Herder-Magazins basierend auf Screenshots der Leseprobe (Seiten 1-23).

---

## 1. Grid-System & Spaltenanordnung

### Basis-Grid
- **Format:** 8.5" x 11" (US Letter), Hochformat
- **Asymmetrisches Grid:** Feste Sidebar links + flexibles Haupt-Grid rechts

### Spaltenverteilung (typisch)

#### Variante A: Mit Inhaltsverzeichnis (Seite 3)
- **Links:** Feste Sidebar (ca. 25-30% der Seitenbreite)
  - "INHALT" (Inhaltsverzeichnis)
  - Nicht im Textfluss (`flow=false`)
  - Roter Header "INHALT", schwarzer Text
- **Rechts:** 3-4 Textspalten für Hauptinhalt
  - Spalten 1-2: Haupttext (ca. 35-40% je Spalte)
  - Spalte 3: Schmaler (ca. 20-25%) für Pullquotes/Factboxes
  - Spalte 4 (optional): Sehr schmal (ca. 10-15%) für Sidebar-Elemente

#### Variante B: Doppelseite ohne TOC (Seiten 12-13, 20-21)
- **Links:** 2-3 Textspalten (ca. 50% der Doppelseite)
- **Rechts:** 2-3 Textspalten + große Bildfläche
- **Gutter:** Ca. 0.25-0.30" zwischen den Seiten

#### Variante C: Feature-Seite (Seite 22-23)
- **Links:** 3 Textspalten (gleichmäßig verteilt)
- **Rechts:** Dominantes Bild (Portrait) + schmale Textspalte daneben

### Spaltenabstände
- **Colsep:** Ca. 0.18-0.25" (4.5-6mm) zwischen Textspalten
- **Gutter (Binding):** Ca. 0.25-0.30" für Doppelseiten

---

## 2. Typografie & Textgrößen

### Headlines
- **Font:** Sans-serif (Helvetica/Arial-ähnlich), bold
- **Farbe:** Rot (#C00 oder ähnlich) oder Schwarz
- **Größe:** 
  - Haupt-Headline: 24-36pt (sehr groß, mehrzeilig)
  - Sub-Headline: 14-18pt
  - Deck/Teaser: 11-13pt
- **Position:** Oben links oder überlagert auf Hero-Bildern

### Body Text
- **Font:** Serif (Times/Georgia-ähnlich), regular
- **Größe:** 10-11pt (Standard)
- **Zeilenabstand:** 1.2-1.3x (leicht geöffnet)
- **Ausrichtung:** Blocksatz (justified)
- **Spaltenbreite:** 50-70 Zeichen pro Zeile (optimal für Lesbarkeit)

### Drop Caps
- **Font:** Serif, sehr groß
- **Größe:** 3-4 Zeilen hoch
- **Farbe:** Rot
- **Verwendung:** Erster Buchstabe des Hauptartikels

### Zahlen/Akzente
- **Große rote Zahlen:** 24-48pt, bold, sans-serif
  - Verwendet für Artikel-Nummern, Kapitel-Marker
  - Position: Links neben Headlines oder als visueller Anker

### Autor-Credits
- **Font:** Sans-serif, light/regular
- **Größe:** 9-10pt
- **Farbe:** Grau (#666)
- **Format:** "VON [NAME]" oder "I VON [NAME] I"

---

## 3. Bildplatzierung & Hero-Elemente

### Full-Bleed Hero-Bilder
- **Cover (Seite 1):** Full-bleed auf allen Seiten (top, left, right, bottom)
- **Doppelseiten-Hero (Seiten 12-13):** Spannt beide Seiten, Text überlagert
- **Höhe:** 50-70% der Seitenhöhe

### Feature-Bilder
- **Größe:** 1-2 Spalten breit, 2-4 Spalten hoch
- **Rahmen:** Dünner weißer Rand (0.5-1pt) oder kein Rand
- **Beschriftungen:** Kleine Textboxen überlagert (z.B. "PORTRÄT", "SERIE ERFINDUNGEN")

### Infografiken/Diagramme
- **Stil:** Technische Zeichnungen, Cutaway-Diagramme
- **Beschriftungen:** Weiße Textboxen mit schwarzem Text, präzise positioniert
- **Farben:** Muted (Grau, Braun, Blau, Gelb)

---

## 4. Box-Elemente & Slots

### Pullquotes
- **Position:** Rechte Spalte (schmal, 1-2 Spalten breit)
- **Font:** Serif, italic oder regular, 11-13pt
- **Rahmen:** Optional (dünne Linie oben/unten oder kein Rahmen)
- **Höhe:** 1.5-2.5" (flexibel)

### Factboxes
- **Position:** Rechte Spalte oder unter Pullquotes
- **Stil:** Weißer Hintergrund, schwarzer Text, optional roter Akzent
- **Höhe:** 1.0-1.5"

### Captions/Bildunterschriften
- **Position:** Unter Bildern oder in separater Spalte
- **Font:** Sans-serif, 8-9pt, light
- **Farbe:** Grau oder Schwarz

### Teaser/Deck
- **Position:** Direkt unter Headline
- **Font:** Sans-serif, 11-13pt, regular
- **Länge:** 2-4 Zeilen

---

## 5. Header & Footer

### Header (jede Seite)
- **Links:** "HERDER" Logo, rot, sans-serif, bold, 12-14pt
- **Rechts:** Share/Print-Icons (rot, klein)
- **Höhe:** Ca. 0.5-0.6" (12-15mm)

### Footer
- **Links:** Navigation-Icons (Zoom, Inhaltsverzeichnis)
- **Mitte:** Seitenzahlen "12 | 13" (rot, sans-serif, 10-11pt)
- **Rechts:** Zoom-Slider, Vollbild-Icon
- **Höhe:** Ca. 0.4-0.5" (10-12mm)

### Running Headers (optional)
- **Links:** Magazin-Titel (z.B. "G/GESCHICHTE")
- **Rechts:** Kapitel-Titel oder Artikel-Titel
- **Font:** Sans-serif, 9-10pt, light

---

## 6. Farbpalette

### Primärfarben
- **Rot:** #C00 oder #D00 (für Akzente, Headlines, Zahlen, Logo)
- **Schwarz:** #000 (für Body-Text, Headlines)
- **Weiß:** #FFF (Hintergrund)

### Sekundärfarben
- **Orange/Gold:** #F60 oder #C90 (für spezielle Headlines, z.B. "Der König des Geldes")
- **Grau:** #666 (für Credits, Captions, Footer-Text)
- **Hellgrau:** #CCC (für Rahmen, Trennlinien)

---

## 7. Layout-Varianten (Templates)

### Template 1: Inhaltsverzeichnis-Seite
- Feste Sidebar links (TOC)
- 3-4 Textspalten rechts
- Feature-Boxen mit Bildern
- Große rote Zahlen als Marker

### Template 2: Doppelseiten-Artikel
- Links: Headline + Deck + 2-3 Textspalten
- Rechts: Hero-Bild (full-bleed oder groß) + Textspalten
- Drop Cap auf erster Spalte rechts
- Text fließt um Bild herum

### Template 3: Feature-Seite (Portrait)
- Links: 3 Textspalten
- Rechts: Großes Portrait (full-height) + schmale Textspalte
- Headline überlagert oder links oben

### Template 4: Infografik-Seite
- Großes Diagramm/Bild (2-3 Spalten breit)
- Textspalten daneben oder darunter
- Beschriftungen als Overlays

---

## 8. Abstände & Ränder

### Seitenränder
- **Top:** 0.8-0.9" (20-23mm)
- **Bottom:** 0.9-1.0" (23-25mm)
- **Außen:** 0.65-0.75" (16-19mm)
- **Innen (Gutter):** 0.90-1.15" (23-29mm, inkl. Binding-Offset)

### Absatzabstände
- **Zwischen Absätzen:** 0.5-0.75x Baselineskip (ca. 6-8pt)
- **Vor Überschriften:** 1.0-1.5x Baselineskip (ca. 12-15pt)
- **Nach Überschriften:** 0.5-0.75x Baselineskip

### Box-Abstände
- **Um Pullquotes/Factboxes:** 0.25-0.35" (6-9mm) Abstand zum Text
- **Um Bilder:** 0.15-0.25" (4-6mm)

---

## 9. Empfehlungen für lua-pagemaker-Implementierung

### Grid-Anpassungen
1. **Asymmetrisches Grid:** 
   - Sidebar links: 25-30% (wenn TOC vorhanden)
   - Hauptspalten rechts: 3 Spalten (35%, 30%, 20%) + optional 15% Sidebar
2. **Flexible Spaltenbreiten:** Abhängig vom Template
3. **Colsep:** 0.18-0.25" (4.5-6mm)

### Typografie-Makros
- `\HerderHeadline{...}`: Große rote/schwarze Headline
- `\HerderDeck{...}`: Deck-Text unter Headline
- `\HerderDropCap{...}`: Roter Drop Cap
- `\HerderNumber{...}`: Große rote Zahl (Artikel-Marker)

### Template-System
- `herder_toc`: Mit Inhaltsverzeichnis-Sidebar
- `herder_article`: Standard-Artikel (Doppelseite)
- `herder_feature`: Feature mit großem Bild
- `herder_infographic`: Infografik-Seite

### Farben definieren
```latex
\definecolor{HerderRed}{RGB}{204,0,0}
\definecolor{HerderGold}{RGB}{255,153,0}
\definecolor{HerderGray}{RGB}{102,102,102}
```

---

## 10. Vergleich mit aktuellem Layout

### Aktuelles Layout (zeitcode)
- **Grid:** 4 Spalten (38%, 33%, 19%, 10%)
- **Sidebar:** Rechts, 10% (zu schmal für TOC)
- **Colsep:** 0.25" (gut)

### Anpassungen für Herder-Style
1. **Sidebar links:** 25-30% für TOC (optional)
2. **Hauptspalten:** 3 Spalten (35%, 30%, 20%) statt 4
3. **Textgröße:** 10-11pt statt 11pt (feinere Abstufung)
4. **Headlines:** Größer, roter Akzent
5. **Drop Caps:** Implementieren
6. **Große rote Zahlen:** Als visuelle Marker

---

## 11. Nächste Schritte

1. **Grid anpassen:** Asymmetrisches Grid mit optionaler TOC-Sidebar
2. **Typografie-Makros:** Herder-spezifische Headline/Deck/DropCap-Makros
3. **Template-Varianten:** 4-5 Templates für verschiedene Seiten-Typen
4. **Farben:** Herder-Farbpalette definieren
5. **Header/Footer:** Herder-Style Header/Footer implementieren
6. **Test-Kompilierung:** Mit Beispiel-Inhalten testen

