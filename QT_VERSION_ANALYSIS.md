# Qt-Version Analyse: Scribus 1.7.1(1)

## Installierte Scribus-Version

- **Pfad:** `C:\Program Files\Scribus 1.7.1(1)`
- **Qt Version:** 6.10.1 (nachgewiesen durch Qt6Core.dll)
- **Qt DLLs vorhanden:** Qt6Core.dll, Qt6Gui.dll, Qt6Widgets.dll, etc.

## Empfehlung

### Um Fehler vorzubeugen:

1. **Verwende Qt 6.10.1 für den Build**
   - Nicht Qt 6.5.3 (die installierte Scribus verwendet 6.10.1)
   - Installiere Qt 6.10.1 über Qt Online Installer falls nötig

2. **Toolset muss übereinstimmen**
   - Prüfe, welches MSVC-Toolset die installierte Scribus verwendet
   - Verwende dasselbe Toolset für den Build (msvc2019_64 oder msvc2022_64)

3. **Wenn Qt 6.10.1 fehlt:**
   - Qt Online Installer: https://www.qt.io/download-qt-installer
   - Installiere: Qt 6.10.1 → MSVC 2022 64-bit (empfohlen)
   - ODER: MSVC 2019 64-bit (falls installierte Scribus dieses verwendet)

## Nächste Schritte

1. Prüfe, ob Qt 6.10.1 installiert ist: `C:\Qt\6.10.1`
2. Falls nicht: Qt 6.10.1 installieren
3. CMake mit Qt6_DIR konfigurieren
4. Toolset-Kompatibilität sicherstellen

