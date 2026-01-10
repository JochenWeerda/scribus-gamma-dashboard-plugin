# Build-Anleitung für Visual Studio (ohne CMake-Befehle)

## Problem
Die DLL ist nur 10 KB groß, weil noch `test_step1.cpp` kompiliert wird statt der vollständigen Source-Dateien.

## Lösung: Visual Studio CMake-Cache neu generieren

### Schritt 1: CMakeLists.txt wurde angepasst
- `TEST_STEP=3` ist jetzt erzwungen (FORCE)
- Das vollständige Plugin wird immer kompiliert

### Schritt 2: In Visual Studio

1. **CMake-Cache neu generieren:**
   - Lösung: `Projekt > CMake-Cache für gamma_dashboard_plugin neu generieren`
   - ODER: Solution Explorer > Rechtsklick auf `gamma_dashboard_plugin` > `CMake-Cache neu generieren`
   
   Dies liest die aktualisierte CMakeLists.txt und generiert die .vcxproj neu.

2. **Build bereinigen:**
   - `Build > Projektmappe bereinigen`

3. **Neu kompilieren:**
   - `Build > Projektmappe erstellen` (oder Strg+Shift+B)
   - Configuration: **Release**
   - Platform: **x64**

### Schritt 3: Prüfen

Die neue DLL sollte jetzt **80-120 KB** groß sein (statt 10 KB).

Pfad: `build\Release\gamma_dashboard.dll`

### Schritt 4: Installieren

```powershell
.\install_latest_dll.ps1
```

(erfordert Admin-Rechte)

## Was wurde geändert?

**CMakeLists.txt:**
- `TEST_STEP` wird jetzt mit `FORCE` auf "3" gesetzt
- Visual Studio muss nur noch die Projektdateien neu generieren

## Warum Visual Studio?

Visual Studio hat integrierte CMake-Unterstützung und generiert automatisch die .vcxproj-Dateien. Du musst nur die CMake-Cache neu generieren lassen.


