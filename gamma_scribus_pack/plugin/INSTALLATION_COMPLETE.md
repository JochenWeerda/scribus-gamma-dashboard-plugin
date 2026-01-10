# Gamma Dashboard Plugin - Vollständige Installation

## Status

✅ **C++-Plugin-Code erstellt**
- `cpp/gamma_dashboard_plugin.h` - Plugin-Header
- `cpp/gamma_dashboard_plugin.cpp` - Plugin-Implementation
- `cpp/CMakeLists.txt` - Build-Konfiguration
- `cpp/build_plugin.ps1` - Build-Script

✅ **Python-Script-Teil erstellt**
- `gamma_dashboard/gamma_dashboard_plugin.py` - Haupt-Script
- `gamma_dashboard/qt_loader.py` - QT-Binding Loader
- `gamma_dashboard/qt_dashboard_widget.py` - Dashboard-UI
- `gamma_dashboard/tools/` - Pipeline-Tools

## Nächste Schritte zum Build

### 1. Voraussetzungen installieren

#### CMake
```powershell
# Download von https://cmake.org/download/
# Installiere mit "Add CMake to PATH"
```

#### Qt5
```powershell
# Download von https://www.qt.io/download
# Installiere Qt5 für Visual Studio (z.B. msvc2019_64)
# Merke dir den Installations-Pfad (z.B. C:\Qt\5.15.2\msvc2019_64)
```

#### Scribus-Quellcode
```powershell
# Download von https://www.scribus.net/downloads/source/
# Extrahiere den Quellcode
# Merke dir den Pfad (z.B. C:\Scribus\scribus-1.7.x-svn)
```

### 2. Build starten

```powershell
cd "C:\Users\Jochen\Documents\Die verborgene Uhr Gottes\Gottes geheimer Zeitcode\gamma_scribus_pack\plugin\cpp"

.\build_plugin.ps1 -ScribusSourcePath "C:\Path\To\Scribus\Source" -QtPath "C:\Qt\5.15.2\msvc2019_64"
```

**Oder automatisch (Script sucht selbst):**
```powershell
.\build_plugin.ps1
```

### 3. Installation

Nach erfolgreichem Build:

1. **Kopiere die DLL:**
   ```
   build\Release\gamma_dashboard.dll
   ```
   nach:
   ```
   C:\Program Files\Scribus 1.7.1\lib\scribus\plugins\
   ```

2. **Kopiere Python-Verzeichnis:**
   ```
   gamma_dashboard\
   ```
   nach:
   ```
   C:\Program Files\Scribus 1.7.1\plugins\gamma_dashboard\
   ```

3. **Starte Scribus neu**

4. **Teste Plugin:**
   - Extras → Über die Plug-Ins
   - Suche nach "Gamma Dashboard"
   - Extras → Gamma Dashboard

## Wie es funktioniert

1. **C++-Plugin** wird von Scribus automatisch geladen (echtes Plugin)
2. **Plugin erscheint** im "Extras"-Menü und im Plugin-Dialog
3. **Beim Aufruf** startet das C++-Plugin das Python-Script in einem **separaten Prozess**
4. **Python-Script** zeigt das QT-Dashboard an (läuft nicht blockierend!)
5. **Scribus bleibt** währenddessen vollständig nutzbar

## Troubleshooting

### "CMake nicht gefunden"
- Installiere CMake und stelle sicher, dass es im PATH ist
- Oder gib den vollständigen Pfad im Script an

### "Qt nicht gefunden"
- Installiere Qt5 für deinen Visual Studio Compiler
- Oder gib den Qt-Pfad explizit an: `-QtPath "C:\Qt\5.15.2\msvc2019_64"`

### "Scribus-Header nicht gefunden"
- Lade den Scribus-Quellcode herunter
- Gib den Pfad an: `-ScribusSourcePath "C:\Path\To\Scribus\Source"`

### "Kompilierungsfehler"
- Prüfe, ob Visual Studio C++-Tools installiert sind
- Prüfe, ob Qt-Version zu Scribus passt
- Prüfe, ob Scribus-Header-Version zu deiner Installation passt

## Dateistruktur

```
gamma_scribus_pack/plugin/
├── cpp/                              # C++-Plugin (wird kompiliert)
│   ├── gamma_dashboard_plugin.h      # Header
│   ├── gamma_dashboard_plugin.cpp    # Implementation
│   ├── CMakeLists.txt                # CMake-Konfiguration
│   ├── build_plugin.ps1              # Build-Script
│   └── README_BUILD.md               # Build-Anleitung
│
└── gamma_dashboard/                  # Python-Teil (wird vom C++-Plugin aufgerufen)
    ├── gamma_dashboard_plugin.py     # Haupt-Script
    ├── qt_loader.py                  # QT-Loader
    ├── qt_dashboard_widget.py        # Dashboard-UI
    ├── tools/                        # Pipeline-Tools
    │   ├── pipeline.py
    │   ├── gamma_cards.py
    │   └── ...
    └── config.json                   # Konfiguration (wird erstellt)
```

## Wichtig

- Das C++-Plugin muss **kompiliert** werden (kann nicht direkt als Python-Script laufen)
- Das Plugin erscheint **automatisch** im Menü (keine manuelle Registrierung nötig)
- Das Python-Script läuft in einem **separaten Prozess** (blockiert Scribus nicht)

