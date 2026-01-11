# Nächste Schritte: Layout-System

## ✅ Was bereits erledigt ist

1. **PDF-Text-Extraktion**: Alle 14 PDFs wurden eingelesen und Text extrahiert
2. **Layout-Dateien**: Für jedes Kapitel wurde eine `chapter*_layout.tex` erstellt mit:
   - Text aus dem PDF
   - Dummy-Bildflächen (tcolorbox) mit Asset-ID, Titel, Beschreibung und Prompt
   - PagePlan-Slots für Print-Mode
3. **PagePlan-System**: Vollständiges Mapping für alle 145 Seiten:
   - `tex/pageplan_full.tex` – LaTeX-Code für Template-Zuordnung
   - `docs/PAGEPLAN_OVERVIEW.md` – Übersicht aller Seiten
4. **Integration**: Layout-Dateien sind in `main.tex` eingebunden

## 🔧 Nächste Schritte

### 1. Test-Kompilierung

```powershell
# Kompiliere Print-Version (mit Layout)
.\compile_pdfs.ps1
```

**Erwartetes Ergebnis:**
- PDF mit ~145 Seiten
- Dummy-Bildflächen (graue Boxen) mit Asset-Beschreibungen
- Text aus PDFs um die Bild-Frames verteilt
- PagePlan-Templates (bleed/guide/story) pro Seite

**Zu prüfen:**
- ✅ Sind alle Kapitel enthalten?
- ✅ Werden Dummy-Bilder angezeigt?
- ✅ Passt der Text ins Layout?
- ✅ Gibt es LaTeX-Fehler?

### 2. Text-Formatierung verbessern

Die aktuelle Text-Extraktion hat noch Probleme:
- Zu viele Zeilenumbrüche
- Sonderzeichen nicht korrekt escaped
- Absätze nicht optimal erkannt

**Script:** `tools/improve_text_extraction.py`
```powershell
python tools\improve_text_extraction.py
```

**Was es macht:**
- Entfernt unnötige Zeilenumbrüche
- Verbessert Absatzerkennung
- Bereinigt Sonderzeichen für LaTeX

### 3. Dummy-Bilder durch echte Bilder ersetzen

Sobald Bilder in gamma.app/napkin.ai erstellt wurden:

**Script:** `tools/replace_dummy_images.py`
```powershell
python tools\replace_dummy_images.py
```

**Was es macht:**
- Liest `assets/manifest_assets.csv`
- Prüft, ob Bild-Dateien existieren
- Ersetzt Dummy-Boxen automatisch durch `\includegraphics` oder `\heroimg`

**Voraussetzung:**
- Bilder müssen in den Pfaden aus `manifest_assets.csv` (Spalte `output_path_print`) liegen
- Beispiel: `assets/images/hires/ch00_sunrise.png`

### 4. Text anpassen (manuell)

Nach der Kompilierung siehst du, wo Text gekürzt oder verlängert werden muss:

**In `tex/chapters/chapter*_layout.tex`:**
- Text kürzen, wenn er zu lang ist
- Text verlängern, wenn zu viel Weißraum
- Absätze umbrechen für besseren Flow

**Tipps:**
- Pro Doppelseite: ~800-1000 Wörter
- Bilder brauchen Platz: Text entsprechend kürzen
- Pullquotes/Factboxes: Text extrahieren und in Slots setzen

### 5. PagePlan anpassen

Falls bestimmte Seiten andere Templates brauchen:

**In `tex/pageplan_full.tex` oder `tools/create_full_pageplan.py`:**
- Template-Zuordnung ändern (bleed/guide/story)
- Neue Templates in `tex/pages_print.lua` definieren

## 📋 Workflow

### Erste Kompilierung
```powershell
# 1. Kompiliere Print-Version
.\compile_pdfs.ps1

# 2. Öffne PDF und prüfe Layout
# 3. Notiere: Wo muss Text gekürzt/verlängert werden?
# 4. Notiere: Welche Bilder fehlen noch?
```

### Text verbessern
```powershell
# 1. Verbessere Text-Extraktion
python tools\improve_text_extraction.py

# 2. Manuell in chapter*_layout.tex anpassen
# 3. Erneut kompilieren
.\compile_pdfs.ps1
```

### Bilder einfügen
```powershell
# 1. Erstelle Bilder in gamma.app/napkin.ai
# 2. Speichere in assets/images/hires/ oder assets/figures/
# 3. Ersetze Dummy-Bilder automatisch
python tools\replace_dummy_images.py

# 4. Oder manuell in chapter*_layout.tex ersetzen:
#    \ZCPlanSetPageSlot{3}{hero}{\heroimg{ch00_sunrise.png}}
```

## 🎯 Ziel

**Finales Layout:**
- Alle 145 Seiten mit Text + Bildern
- Magazin-Style (4-Spalten-Grid)
- Dummy-Bilder durch echte Bilder ersetzt
- Text optimal verteilt (keine Überläufe, keine Lücken)

## 📝 Notizen

- **Seitenzahl**: Aktuell 145 Seiten (kann sich durch Text-Anpassungen ändern)
- **Bilder**: ~60 Assets (Hero + Detail + Texture + Infografiken)
- **Templates**: bleed (28), guide (30), story (87)

