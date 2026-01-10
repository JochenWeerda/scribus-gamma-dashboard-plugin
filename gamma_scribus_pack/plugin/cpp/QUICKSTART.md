# Quick Start - Gamma Dashboard Plugin

## Schnellstart (3 Schritte)

### Schritt 1: Voraussetzungen prüfen

Führe aus:
```powershell
cd "C:\Users\Jochen\Documents\Die verborgene Uhr Gottes\Gottes geheimer Zeitcode\gamma_scribus_pack\plugin\cpp"
.\setup_and_build.ps1
```

Das Script prüft automatisch:
- ✅ CMake (installiert automatisch falls fehlt)
- ⚠️ Qt5 (muss manuell installiert werden)
- ⚠️ Scribus-Quellcode (muss manuell heruntergeladen werden)

### Schritt 2: Fehlende Komponenten installieren

#### Qt5 installieren:
1. Gehe zu: https://www.qt.io/download
2. Wähle "Open Source" → "Download"
3. Installiere Qt 5.15.2 (oder höher) für **msvc2019_64** oder **msvc2022_64**
4. Merke dir den Installations-Pfad (z.B. `C:\Qt\5.15.2\msvc2019_64`)

#### Scribus-Quellcode herunterladen:
1. Gehe zu: https://www.scribus.net/downloads/source/
2. Lade die neueste Version herunter (1.7.x)
3. Extrahiere den Quellcode
4. Merke dir den Pfad (z.B. `C:\Scribus\scribus-1.7.x-svn`)

### Schritt 3: Build mit Pfaden

```powershell
.\setup_and_build.ps1 -QtPath "C:\Qt\5.15.2\msvc2019_64" -ScribusSourcePath "C:\Scribus\scribus-1.7.x-svn"
```

Oder falls Qt und Scribus bereits gefunden wurden:
```powershell
.\build_plugin.ps1
```

## Alternative: Manueller Build

Falls das automatische Script Probleme hat:

1. **Öffne Developer Command Prompt for VS**

2. **Wechsle ins Plugin-Verzeichnis:**
   ```cmd
   cd "C:\Users\Jochen\Documents\Die verborgene Uhr Gottes\Gottes geheimer Zeitcode\gamma_scribus_pack\plugin\cpp"
   ```

3. **Erstelle Build-Verzeichnis:**
   ```cmd
   mkdir build
   cd build
   ```

4. **Konfiguriere CMake:**
   ```cmd
   cmake .. -DSCRIBUS_INCLUDE_DIR="C:\Path\To\Scribus\scribus\plugins" -DCMAKE_PREFIX_PATH="C:\Qt\5.15.2\msvc2019_64" -DCMAKE_INSTALL_PREFIX="C:\Program Files\Scribus 1.7.1"
   ```

5. **Build:**
   ```cmd
   cmake --build . --config Release
   ```

6. **Installiere:**
   ```cmd
   cmake --install . --config Release
   ```

## Nach dem Build

1. **Kopiere DLL:**
   ```
   build\Release\gamma_dashboard.dll
   ```
   → `C:\Program Files\Scribus 1.7.1\lib\scribus\plugins\`

2. **Kopiere Python-Verzeichnis:**
   ```
   ..\gamma_dashboard\
   ```
   → `C:\Program Files\Scribus 1.7.1\plugins\gamma_dashboard\`

3. **Starte Scribus neu**

4. **Teste:**
   - Extras → Über die Plug-Ins → "Gamma Dashboard"
   - Extras → Gamma Dashboard

## Hilfe

Bei Problemen siehe:
- `README_BUILD.md` - Detaillierte Build-Anleitung
- `INSTALLATION_COMPLETE.md` - Vollständige Dokumentation

