# Qt Maintenance Tool - Schritt-für-Schritt Anleitung

## Aktueller Status (basierend auf Screenshot)

✅ **Qt 6.10.1** ist erweitert
✅ **MSVC 2022 64-bit** ist bereits markiert (checkbox aktiviert)

## Nächste Schritte

### Schritt 1: "Additional Libraries" erweitern

1. **Suche nach "Additional Libraries"** in der Liste unter "MSVC 2022 64-bit"
2. **Klicke auf das "+" Symbol** oder doppelklicke auf "Additional Libraries"
3. Die Liste der zusätzlichen Bibliotheken wird angezeigt

### Schritt 2: "Qt 5 Compatibility Module" aktivieren

1. **In der erweiterten "Additional Libraries"-Liste:**
   - Suche nach: **"Qt 5 Compatibility Module"**
   - ODER: **"Qt5Compat"**
   - ODER: **"Qt5 Compatibility"**

2. **Aktiviere das Häkchen:**
   - Klicke auf die Checkbox neben "Qt 5 Compatibility Module"
   - Ein grünes Häkchen sollte erscheinen

### Schritt 3: Installation starten

1. **Prüfe "Erforderlicher Festplattenplatz":**
   - Sollte jetzt einen Wert > 0 Bytes anzeigen
   - Zeigt an, wie viel Speicherplatz benötigt wird

2. **"Weiter"-Button aktivieren:**
   - Der Button sollte jetzt aktiv (nicht mehr grau) sein

3. **Klicke auf "Weiter >":**
   - Die Installation beginnt
   - Ein Fortschrittsbalken wird angezeigt

4. **Warte auf Installation:**
   - Kann einige Minuten dauern (abhängig von Download-Geschwindigkeit)

### Schritt 4: Installation abschließen

1. **Nach erfolgreicher Installation:**
   - "Abschließen"-Button erscheint
   - Klicke darauf

2. **Qt Maintenance Tool schließen**

## Alternative: Suche-Funktion verwenden

Falls "Additional Libraries" nicht gefunden werden kann:

1. **Nutze die "Suchen"-Funktion** (oben rechts)
2. **Suche nach:** "Qt 5 Compatibility" oder "Qt5Compat"
3. **Aktiviere das gefundene Element**

## Überprüfung nach Installation

Nach der Installation prüfe, ob Qt6Core5Compat installiert wurde:

**PowerShell:**
```powershell
Test-Path "C:\Development\Qt\6.10.1\msvc2022_64\lib\Qt6Core5Compat.lib"
```

**Sollte `True` zurückgeben.**

## Falls "Qt 5 Compatibility Module" nicht erscheint

Mögliche Gründe:
- Das Modul ist bereits installiert (überprüfe die Bibliotheken)
- Die Qt-Version unterstützt es nicht (selten)
- Ein Update des Maintenance Tools ist erforderlich

**Lösung:** Prüfe die Bibliotheken direkt:
```powershell
Get-ChildItem "C:\Development\Qt\6.10.1\msvc2022_64\lib\Qt6Core5Compat*"
```

