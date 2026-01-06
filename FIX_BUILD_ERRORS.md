# Build-Fehler beheben: Scribus-Libs-Kit

## Problem-Analyse

**Hauptproblem:** Visual Studio sucht nach Debug-Bibliotheken (`libxml2_d.lib`), die nicht vorhanden sind.

**Gefundene Bibliotheken:**
- ✅ ICU: Vorhanden in `icu-76.1\lib\x64-v142` und `x64-v143` (beide: Debug und Release)
- ✅ libxml2: **Nur Release-Version** in `libxml2-2.15.1\lib\x64-v143\libxml2.lib`
- ❌ libxml2_d.lib: **FEHLT** (keine Debug-Version vorhanden)

## Lösung: Release-Build verwenden

**WICHTIG:** "VC++ Directories" gibt es **nur auf PROJEKT-Ebene**, nicht auf Solution-Ebene!

**Aber:** Es gibt bereits eine Property-Sheet-Datei `scribus-lib-paths.props`, die alle Bibliothekspfade definiert (inklusive ICU und libxml2). Diese sollte automatisch funktionieren!

### Einfache Lösung:

1. **Schließe das Dialogfeld "Eigenschaftenseiten"** (Abbrechen oder OK)
2. **Build → Configuration Manager...**
3. **Active solution configuration:** `Release` (nicht Debug!)
4. **Active solution platform:** `x64`
5. Klicke **Close**
6. **Build → Build Solution** (F7)

### Alternative: Pro-Project konfigurieren (falls Solution-Properties nicht funktioniert)

1. **Rechtsklick auf Projekt → Properties**
2. **Configuration:** Release, **Platform:** x64
3. **Configuration Properties → Linker → General → Additional Library Directories**
4. Füge hinzu:
   ```
   C:\Development\scribus-1.7.x-libs-msvc\icu-76.1\lib\x64-v143
   C:\Development\scribus-1.7.x-libs-msvc\libxml2-2.15.1\lib\x64-v143
   ```
5. Klicke **Apply** → **OK**

## Warnungen (nicht kritisch)

Wenn du Warnungen siehst wie:
- "Einem vorzeichenlosen Typ wurde ein unärer Minus-Operator zugewiesen"
- "nicht referenzierter Parameter"
- "Unreferenzierte lokale Variable"

**Das ist NORMAL und kein Problem!**
- ✅ Diese sind **Warnungen**, keine Fehler
- ✅ Sie blockieren den Build **nicht**
- ✅ Typisch bei externen Bibliotheken (ICU, libxml2, etc.)
- ✅ Können ignoriert werden

**Prüfe:** Wenn der Build mit "Build succeeded" endet, ist alles OK!

Falls Warnungen als Fehler behandelt werden:
1. **Project Properties → C/C++ → General**
2. **Treat Warnings As Errors:** No (/WX-)

## Empfehlung

**Verwende Release-Build** - das ist die einfachste und empfohlene Lösung für Scribus-Libs-Kit.

