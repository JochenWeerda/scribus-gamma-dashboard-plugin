# Gamma Dashboard Plugin - Build-Anleitung

## Voraussetzungen

1. **Visual Studio 2019/2022** mit C++-Entwicklungstools
   - Community Edition reicht aus: https://visualstudio.microsoft.com/

2. **CMake** (Version 3.15+)
   - Download: https://cmake.org/download/
   - Installiere mit "Add CMake to PATH"

3. **Qt5** (Version 5.12+)
   - Muss zu Scribus passen (normalerweise 5.15.x)
   - Download: https://www.qt.io/download
   - Oder: https://www.qt.io/download-open-source

4. **Scribus-Quellcode** (für Header-Dateien)
   - Download: https://www.scribus.net/downloads/source/
   - Extrahiere und merke dir den Pfad

## Build-Schritte

### 1. Vorbereitung

```powershell
cd "C:\Users\Jochen\Documents\Die verborgene Uhr Gottes\Gottes geheimer Zeitcode\gamma_scribus_pack\plugin\cpp"
```

### 2. Build starten

```powershell
.\build_plugin.ps1 -ScribusSourcePath "F:\Scribus for Windows\scribus-1.7.x-svn" -QtPath "C:\Qt\5.15.2\msvc2019_64"
```

**Oder automatisch:**

```powershell
.\build_plugin.ps1
```

(Das Script sucht automatisch nach Qt und Scribus-Headern)

### 3. Installation

Nach erfolgreichem Build:

1. Kopiere `build\Release\gamma_dashboard.dll` (oder `build\gamma_dashboard.dll`) nach:
   ```
   C:\Program Files\Scribus 1.7.1\lib\scribus\plugins\
   ```

2. Kopiere auch das Python-Script-Verzeichnis:
   ```
   C:\Program Files\Scribus 1.7.1\plugins\gamma_dashboard\
   ```

3. Starte Scribus neu

## Troubleshooting

### CMake nicht gefunden
- Installiere CMake und stelle sicher, dass es im PATH ist
- Oder gib den vollständigen Pfad an: `& "C:\Program Files\CMake\bin\cmake.exe" ...`

### Qt nicht gefunden
- Installiere Qt5 für deinen Visual Studio Compiler (msvc2019_64 oder msvc2022_64)
- Oder gib den Qt-Pfad explizit an: `-QtPath "C:\Qt\5.15.2\msvc2019_64"`

### Scribus-Header nicht gefunden
- Lade den Scribus-Quellcode herunter
- Extrahiere ihn
- Gib den Pfad an: `-ScribusSourcePath "C:\Path\To\Scribus\Source"`

### Kompilierungsfehler
- Stelle sicher, dass Visual Studio C++-Tools installiert sind
- Prüfe, ob Qt-Version zu Scribus passt
- Prüfe, ob Scribus-Header-Version zu deiner Scribus-Installation passt

## Manueller Build mit Visual Studio

1. Öffne "Developer Command Prompt for VS"
2. Wechsle ins Plugin-Verzeichnis
3. Führe CMake aus:
   ```bash
   mkdir build
   cd build
   cmake .. -DSCRIBUS_INCLUDE_DIR="..." -DCMAKE_PREFIX_PATH="..."
   cmake --build . --config Release
   ```

