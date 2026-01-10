# Installation des Gamma Dashboard Plugins

## Voraussetzungen

1. **CMake 4.2.1** (bereits heruntergeladen: `C:\Users\Jochen\Downloads\cmake-4.2.1.zip`)
2. **Qt5** (noch zu installieren)
3. **Scribus-Quellcode** (wahrscheinlich vorhanden: `F:\Scribus for Windows\scribus-1.7.x-svn`)
4. **Visual Studio** mit C++-Tools

## Installationsschritte

### 1. CMake extrahieren

Die ZIP-Datei ist bereits heruntergeladen. Extrahiere sie bitte nach `C:\Development\cmake-4.2.1`:

```powershell
Expand-Archive -Path "C:\Users\Jochen\Downloads\cmake-4.2.1.zip" -DestinationPath "C:\Development" -Force
```

Dann sollte CMake hier verfügbar sein: `C:\Development\cmake-4.2.1\bin\cmake.exe`

**Alternativ:** Installiere CMake über den Installer von https://cmake.org/download/

### 2. Qt5 installieren

Qt5 muss für Windows mit Visual Studio installiert werden:

1. Gehe zu: https://www.qt.io/download
2. Installiere **Qt 5.15.2** (Open Source Version)
3. Wähle während der Installation:
   - **MSVC 2019 64-bit** oder **MSVC 2022 64-bit**
   - Standard-Pfad: `C:\Qt\5.15.2\msvc2019_64`

**Wichtig:** Notiere dir den Qt-Installationspfad für den nächsten Schritt.

### 3. Scribus-Quellcode prüfen

Stelle sicher, dass der Scribus-Quellcode vorhanden ist:
- Erwarteter Pfad: `F:\Scribus for Windows\scribus-1.7.x-svn`
- Erforderliche Header: `Scribus\scribus\plugins\scplugin.h`

Falls nicht vorhanden:
```powershell
git clone https://github.com/scribusproject/scribus.git "F:\Scribus for Windows\scribus-1.7.x-svn"
```

### 4. Plugin kompilieren

Nachdem alle Voraussetzungen erfüllt sind, führe aus:

```powershell
cd "C:\Users\Jochen\Documents\Die verborgene Uhr Gottes\Gottes geheimer Zeitcode\gamma_scribus_pack\plugin\cpp"
.\quick_build.ps1 -CmakePath "C:\Development\cmake-4.2.1" -ScribusSourcePath "F:\Scribus for Windows\scribus-1.7.x-svn" -QtPath "C:\Qt\5.15.2\msvc2019_64"
```

### 5. Plugin installieren

Nach erfolgreicher Kompilierung:

1. Kopiere die erstellte DLL (`build\Release\gamma_dashboard.dll` oder ähnlich) nach:
   - `C:\Program Files\Scribus 1.7.1\lib\scribus\plugins\` (oder dein Scribus-Installationsverzeichnis)
2. Kopiere die Python-Dateien nach:
   - `C:\Users\Jochen\AppData\Roaming\Scribus\scripts\plugin\` (erstelle das Verzeichnis falls nicht vorhanden)
3. Starte Scribus neu

Das Plugin sollte dann unter **Extras → Gamma Dashboard** erscheinen.

## Troubleshooting

### CMake nicht gefunden
- Stelle sicher, dass CMake extrahiert wurde
- Prüfe, ob `cmake.exe` in `C:\Development\cmake-4.2.1\bin\` existiert
- Alternativ: Füge CMake zum System-PATH hinzu

### Qt5 nicht gefunden
- Prüfe, ob Qt installiert ist: `C:\Qt\5.15.2\msvc2019_64\bin\qmake.exe`
- Gib den korrekten Qt-Pfad im Build-Script an

### Scribus-Header nicht gefunden
- Prüfe, ob der Scribus-Quellcode-Pfad korrekt ist
- Suche nach `scplugin.h` im Scribus-Quellcode-Verzeichnis

### Kompilierungsfehler
- Stelle sicher, dass Visual Studio mit C++-Tools installiert ist
- Öffne eine "Developer Command Prompt" für Visual Studio
- Führe das Build-Script dort aus

## Nächste Schritte

Nach erfolgreicher Installation:
1. Teste das Plugin in Scribus
2. Prüfe die Logs bei Problemen: `C:\Users\Jochen\AppData\Roaming\Scribus\`
3. Siehe `README.md` für Plugin-Funktionen

