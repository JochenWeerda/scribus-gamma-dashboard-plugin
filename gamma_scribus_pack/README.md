# Gamma -> Card-Crops -> Scribus (Setzerei Erweiterung)

## Ziel
Gamma-Exports sind oft "zerstueckelt" (viele Shapes). Statt hunderter Einzelobjekte erzeugen wir semantische Einheiten:
- Slide-PNG (Rendering-Wahrheit)
- PPTX (Text/Position-Wahrheit)
- Cluster & Crop (Card-Boxen erkennen, gruppieren, als PNG ausschneiden)
- Anchors: Text davor/dahinter + optional inside texts

Am Ende nutzt Scribus diese Crops als Infografiken im Magazinlayout.

---

## Projektstruktur (empfohlen)
Du brauchst einen Projektordner mit sprechendem Namen (z. B. `MagazinProjekt`).
Darin liegen zwei Eingangsordner und die erzeugten Outputs:

```
MagazinProjekt/
  gamma_exports/   # ZIPs pro Kapitel (Gamma Export)
  pptx/            # zugehoerige PPTX-Dateien
  output/          # erzeugte Slides, Crops, JSON
```

## Schnellstart (empfohlen, 1x Struktur uebernehmen)
Vorschlag fuer feste Ordnernamen. Wenn du das so uebernimmst, musst du nur noch
Zips und PPTX an die richtigen Orte kopieren:

```
MagazinProjekt/
  gamma_exports/   # hierhin: Gamma ZIPs pro Kapitel
  pptx/            # hierhin: zugehoerige PPTX-Dateien
  output/          # wird automatisch erzeugt
```

Beispiel (Windows):
```
C:\Projects\MagazinProjekt\
  gamma_exports\
  pptx\
  output\
```

PowerShell (Ordner anlegen):
```powershell
$root = "C:\Projects\MagazinProjekt"
New-Item -ItemType Directory -Force -Path $root | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $root "gamma_exports") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $root "pptx") | Out-Null
```

PowerShell (dein aktueller Pfad):
```powershell
$root = "C:\Users\Jochen\Documents\Die verbor´gene Uhr Gottes\MagazinProjekt"
New-Item -ItemType Directory -Force -Path $root | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $root "gamma_exports") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $root "pptx") | Out-Null
```

Mini-Checkliste:
1) Gamma ZIPs nach `gamma_exports` kopieren
2) PPTX-Dateien nach `pptx` kopieren
3) Pipeline starten (siehe Abschnitt "Pipeline Run")

Wenn du lieber deine bestehenden Ordner nutzt, kannst du sie direkt angeben:
- Gamma ZIPs: `C:\Users\Jochen\Documents\Die verbor´gene Uhr Gottes\PNGs`
- PPTX: `C:\Users\Jochen\Documents\Die verbor´gene Uhr Gottes\Powerpoints`

---

## Installation (Windows)
```bash
cd gamma_scribus_pack
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Getestet mit: Scribus 1.6.4 stable auf Windows 11.

## Install Routine (inkl. Abhaengigkeiten + Proof)
Auto-Installer (PowerShell):
```powershell
$root = "C:\Projects\MagazinProjekt"
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Library Proof (schneller Import-Check):
```powershell
.\.venv\Scripts\python.exe - << 'PY'
import cv2, numpy, PIL, pptx
print("OK: deps loaded")
PY
```

Oder als echte Scripts:
```powershell
.\install.ps1 -CreateProjectStructure -ProjectRoot "C:\Projects\MagazinProjekt"
.\proof_deps.ps1
```

Optional (Quellen direkt kopieren):
```powershell
.\install.ps1 -CreateProjectStructure -ProjectRoot "C:\Projects\MagazinProjekt" `
  -ZipSource "C:\Users\Jochen\Documents\Die verbor´gene Uhr Gottes\PNGs" `
  -PptxSource "C:\Users\Jochen\Documents\Die verbor´gene Uhr Gottes\Powerpoints"
```

## Gamma Export

In Gamma:

* Export: PPTX
* Export: PNGs (Slides) - idealerweise in derselben Export-ZIP oder im gleichen Ordner.

Hinweis: Wenn die PPTX nicht im ZIP liegt, lege sie in `MagazinProjekt/pptx/` ab
oder nutze `--pptx "C:\path\MagazinProjekt\pptx\Kapitel-1.pptx"`.

## Pipeline Run (standalone)

```bash
.\.venv\Scripts\python.exe tools\pipeline.py --gamma_export "C:\path\MagazinProjekt\gamma_exports\Kapitel-1.zip" --project "C:\path\MagazinProjekt" --max_clusters 3
```

Outputs:

* MagazinProjekt/output/slides/slide_0001.png ...
* MagazinProjekt/output/crops/slide_0001_cluster_01.png ...
* MagazinProjekt/output/hints_by_slide.json
* MagazinProjekt/output/debug_overlay/... (QC Overlay)

## Scribus Integration

1. Kopiere `scribus_extension/setzerei_gamma_bridge.py` in deinen Scribus Scripts-Ordner.
2. Setze ENV Variablen:

* ZC_GAMMA_EXPORT_DIR  = Gamma Export ZIP/Ordner
* ZC_PROJECT_DIR       = Projektordner (wo output/ landet)
* ZC_VENV_PY           = Pfad zur .venv python.exe

Beispiel (Windows PowerShell):

```powershell
$env:ZC_GAMMA_EXPORT_DIR="C:\path\MagazinProjekt\gamma_exports\Kapitel-1.zip"
$env:ZC_PROJECT_DIR="C:\path\MagazinProjekt"
$env:ZC_VENV_PY="C:\path\gamma_scribus_pack\.venv\Scripts\python.exe"
```

3. Scribus oeffnen, Template laden
4. Script ausfuehren: `setzerei_gamma_bridge.py`
5. Danach dein `setzerei_engine.py` ausfuehren (wie bisher).

## Qualitaet / QC

* Schau in `output/debug_overlay/`:

  * Gelb: Kandidaten
  * Gruen: Cluster-BBox (was geschnitten wird)
* Wenn zu viel/zu wenig:

  * tools/gamma_cards.py Parameter: min_rel_area, tol_* , max_clusters

## Warum Text nicht schwammig wird

* Wir croppen aus hochqualitativen Slide-PNGs.
* Fuer textlastige Karten kannst du optional in Scribus rekonstruktiv zeichnen (Shapes + Text) - als next step.
