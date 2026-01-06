# Einfache Lösung: Build-Fehler beheben

## Problem

- Visual Studio findet `icudt.lib` nicht
- "VC++ Directories" gibt es nicht auf Solution-Ebene

## Lösung: Release-Build verwenden

**Die Property-Sheet-Datei `scribus-lib-paths.props` definiert bereits alle Bibliothekspfade!**

### Schritte:

1. **Schließe das Dialogfeld "Eigenschaftenseiten"** (Abbrechen oder OK)

2. **Build → Configuration Manager...**
   - **Active solution configuration:** `Release` (nicht Debug!)
   - **Active solution platform:** `x64`
   - **Close**

3. **Build → Build Solution** (F7)

Die Property-Sheet sollte automatisch die Bibliothekspfade setzen. Falls es immer noch nicht funktioniert, müssen die Projekte die Property-Sheet importieren (dann können wir das einzeln beheben).

