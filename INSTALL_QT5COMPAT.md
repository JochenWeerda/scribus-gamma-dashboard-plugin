# Qt6Core5Compat installieren

## Status

❌ **Qt6Core5Compat ist NICHT installiert** in keiner der verfügbaren Qt-Installationen:
- C:\Development\Qt\6.10.1\msvc2022_64
- C:\Qt\6.6.0\msvc2022_64 (falls vorhanden)
- C:\Qt\6.5.3\msvc2022_64 (falls vorhanden)

## Problem

Scribus benötigt Qt6Core5Compat für Qt5-Kompatibilitäts-APIs (z.B. `QRegExp`), aber das Modul ist nicht installiert.

**Fehler:**
- `Qt6Core5Compat.lib` kann nicht geöffnet werden
- `qregexp.h` kann nicht geöffnet werden

## Lösung: Qt Maintenance Tool verwenden

### Schritt 1: Qt Maintenance Tool öffnen

**Option A: Über Windows Start-Menü**
- Windows Start-Menü → "Qt Maintenance Tool"
- ODER: Suche nach "Qt Maintenance Tool"

**Option B: Direkter Pfad**
```
C:\Development\Qt\MaintenanceTool.exe
```
ODER
```
C:\Qt\MaintenanceTool.exe
```

**Option C: PowerShell**
```powershell
Start-Process "C:\Development\Qt\MaintenanceTool.exe"
```

### Schritt 2: Qt 5 Compatibility Module installieren

1. **Im Qt Maintenance Tool:**
   - Klicke auf **"Add or remove components"** (Komponenten hinzufügen oder entfernen)

2. **Qt-Version finden:**
   - Expand: **Qt 6.10.1** (oder deine installierte Version)
   - Expand: **MSVC 2022 64-bit** (oder passende Architektur)

3. **Qt 5 Compatibility Module aktivieren:**
   - Suche nach: **Qt 5 Compatibility Module**
   - ✅ **Aktiviere den Haken** bei `Qt 5 Compatibility Module`
   - (Optional: `Qt 5 Compatibility Module for WebEngine` - nicht notwendig)

4. **Installation starten:**
   - Klicke auf **"Next"** oder **"Update"**
   - Warte auf Installation (kann einige Minuten dauern)

5. **Fertig:**
   - Installation abgeschlossen
   - Qt Maintenance Tool kann geschlossen werden

### Schritt 3: Überprüfung

**Prüfe, ob Qt6Core5Compat installiert ist:**

**PowerShell:**
```powershell
Test-Path "C:\Development\Qt\6.10.1\msvc2022_64\lib\Qt6Core5Compat.lib"
# Sollte True zurückgeben
```

**ODER prüfe alle Dateien:**
```powershell
Get-ChildItem "C:\Development\Qt\6.10.1\msvc2022_64\lib\Qt6Core5Compat*"
```

**Erwartete Ausgabe:**
- `Qt6Core5Compat.lib` (Release)
- `Qt6Core5Compatd.lib` (Debug)

### Schritt 4: Build erneut starten

Nach der Installation:

1. **Build erneut starten:**
   ```powershell
   cd C:\Development\scribus-1.7\win32\msvc2022
   msbuild Scribus.sln /p:Configuration=Release /p:Platform=x64 /t:Build
   ```

2. **ODER in Visual Studio:**
   - Build → Rebuild Solution

## Alternative: Qt6Core5Compat manuell installieren (nicht empfohlen)

Falls Qt Maintenance Tool nicht verfügbar ist, kann Qt6Core5Compat manuell installiert werden, aber das ist komplex und nicht empfohlen. Besser: Qt Maintenance Tool verwenden.

## Hinweis: Header-Anpassung (bereits dokumentiert)

Nach der Installation von Qt6Core5Compat muss noch der Header angepasst werden:
- **Datei:** `C:\Development\scribus-1.7\win32\msvc2022\scribus-rtf\scribus-rtf-pch.h`
- **Zeile 69:** `#include <qregexp.h>` → `#include <QtCore5Compat/QRegExp>`

Siehe: `BUILD_ERRORS_QT.md` für Details.

