# Herder-Layout Implementation

## Übersicht
Implementierung des Herder G/GESCHICHTE Magazin-Layouts mit lua-pagemaker.

## Änderungen

### 1. Farben (main.tex)
- `HerderRed`: RGB(204,0,0) - Primär-Rot für Headlines, Zahlen, Logo
- `HerderGold`: RGB(255,153,0) - Orange/Gold für spezielle Headlines
- `HerderGray`: RGB(102,102,102) - Grau für Credits, Captions
- `HerderLightGray`: RGB(204,204,204) - Hellgrau für Rahmen

### 2. Typografie-Makros (main.tex)
- `\HerderHeadline[red|black]{Text}`: Große Headline (28pt), rot oder schwarz
- `\HerderDeck{Text}`: Deck-Text unter Headline (13pt)
- `\HerderNumber{Nummer}`: Große rote Zahl (36pt) für Artikel-Marker
- `\HerderDropCap{Buchstabe}`: Roter Drop Cap (48pt)
- `\HerderAuthor{Name}`: Autor-Credit (9pt, grau)
- `\HerderHeadlineGold{Text}`: Gold/Orange Headline für Features

### 3. Grid-Anpassungen (pages_print.lua)

#### Template: `story` (Standard-Artikel)
- **Spalten:** 35%, 30%, 20%, 15% (Sidebar rechts)
- **Colsep:** 0.20" (5mm) - kompakter als vorher

#### Template: `toc` (Mit Inhaltsverzeichnis)
- **Spalten:** 28% (TOC links), 35%, 30%, 7% (Mini-Sidebar rechts)
- **TOC-Sidebar:** Nicht im Textfluss (`flow=false`)
- **Slots:** `toc_header`, `toc_content`

#### Template: `guide` (wie bisher)
- **Spalten:** 35%, 30%, 20%, 15%
- **Slots:** Headline, Deck, Teaser, Pullquote, Factbox, Caption

### 4. Verwendung

#### Beispiel: Artikel mit Herder-Headline
```latex
\ifprintmode
  \ZCPlanSetPageSlot{101}{headline}{%
    \HerderNumber{18}\quad
    \HerderHeadline{Angriff aufs Weltreich}%
  }
  \ZCPlanSetPageSlot{101}{deck}{%
    \HerderDeck{Als Alexander in Persien einfällt, hält dessen Großkönig Dareios III. es noch nicht einmal für nötig, ihm persönlich entgegenzutreten.}%
  }
  \ZCPlanSetPageSlot{101}{author}{%
    \HerderAuthor{ALEXANDER BUDOW}%
  }
\fi

% Body-Text mit Drop Cap
\HerderDropCap{R}est des Textes beginnt hier...
```

#### Beispiel: TOC-Seite
```latex
\ifprintmode
  % TOC-Header
  \ZCPlanSetPageSlot{3}{toc_header}{%
    \sffamily\bfseries\color{HerderRed}INHALT\par
    \small\color{black}G/GESCHICHTE · Januar 1/2026%
  }
  % TOC-Content
  \ZCPlanSetPageSlot{3}{toc_content}{%
    \small
    \textbf{\color{HerderRed}AKTUELLES}\par
    \HerderNumber{6}\quad Artikel 1\par
    \HerderNumber{12}\quad Artikel 2\par
    ...
  }
\fi
```

## Nächste Schritte

1. **Header/Footer anpassen:**
   - "HERDER" Logo links oben (rot, sans-serif, bold)
   - Seitenzahlen "12 | 13" in Footer (rot)

2. **Template-Varianten erweitern:**
   - `herder_feature`: Feature-Seite mit großem Portrait
   - `herder_infographic`: Infografik-Seite mit Diagramm

3. **Textgröße anpassen:**
   - Body-Text: 10-11pt (statt 11pt) für feinere Abstufung
   - Zeilenabstand: 1.2-1.3x (bereits implementiert)

4. **Test-Kompilierung:**
   - Beispiel-Kapitel mit Herder-Makros testen
   - TOC-Template testen
   - Farben und Typografie prüfen

