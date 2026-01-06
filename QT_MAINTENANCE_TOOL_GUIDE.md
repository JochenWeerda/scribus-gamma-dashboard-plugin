# Qt Maintenance Tool - Qt 5 Compatibility Module installieren

## Screenshot-Analyse

Ich sehe im Qt Maintenance Tool:
- ✅ Qt 6.10.1 ist installiert
- ✅ MSVC 2022 64-bit ist aktiviert (Checkbox angekreuzt)
- ⚠️ "Qt 5 Compatibility Module" muss noch aktiviert werden

## Schritt-für-Schritt Anleitung

### Schritt 1: MSVC 2022 64-bit erweitern

1. **Klicke auf "MSVC 2022 64-bit"** (oder das Minus-Symbol daneben)
   - Dies erweitert die Unterkomponenten
   - Du solltest jetzt eine Liste von Unterkomponenten sehen

### Schritt 2: Qt 5 Compatibility Module finden

Die Unterkomponenten von "MSVC 2022 64-bit" sollten enthalten:
- Qt Core
- Qt GUI
- Qt Widgets
- Qt Network
- **Qt 5 Compatibility Module** ← Das ist was wir brauchen!
- Weitere Komponenten...

**ODER** prüfe unter:
- **"Additional Libraries" (Zusätzliche Bibliotheken)**
  - Klicke auf "Additional Libraries" um es zu erweitern
  - Suche nach "Qt 5 Compatibility Module"

### Schritt 3: Qt 5 Compatibility Module aktivieren

1. **Finde "Qt 5 Compatibility Module"** in der Liste
2. **Aktiviere das Häkchen** (Checkbox setzen)
3. Die Checkbox sollte grün werden (angekreuzt)

### Schritt 4: Installation starten

1. **Prüfe "Erforderlicher Festplattenplatz"** - sollte jetzt > 0 Bytes sein
2. **Klicke auf "Weiter >"** (Next) Button
3. **Folge den weiteren Schritten:**
   - Lizenzabkommen akzeptieren (falls nötig)
   - Zusammenfassung prüfen
   - Installation starten
4. **Warte auf die Installation** (kann einige Minuten dauern)

### Schritt 5: Installation abschließen

1. Wenn die Installation abgeschlossen ist, erscheint "Abschließen" (Finish)
2. **Klicke auf "Abschließen"**
3. **Qt Maintenance Tool schließen**

## Nach der Installation

**Überprüfung:**
```powershell
Test-Path "C:\Development\Qt\6.10.1\msvc2022_64\lib\Qt6Core5Compat.lib"
```

**Erwartete Ausgabe:** `True`

**Dann:**
- Sage mir Bescheid, dann starte ich den Build erneut!

## Falls Qt 5 Compatibility Module nicht sichtbar ist

**Mögliche Ursachen:**
1. Die Komponente ist unter einem anderen Namen
2. Die Komponente muss über "Additional Libraries" installiert werden
3. Die Qt-Version unterstützt Qt5Compat nicht (unwahrscheinlich bei Qt 6.10.1)

**Lösung:**
- Prüfe alle erweiterten Unterkomponenten von "MSVC 2022 64-bit"
- Prüfe "Additional Libraries"
- Falls nicht gefunden: Qt Maintenance Tool neu starten oder Qt-Installation aktualisieren

