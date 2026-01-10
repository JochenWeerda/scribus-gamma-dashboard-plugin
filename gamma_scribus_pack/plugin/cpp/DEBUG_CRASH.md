# Debug: Crash Analysis

## Problem
Scribus stürzt mit `EXCEPTION_ACCESS_VIOLATION` ab, sobald das Plugin geladen wird.

## Mögliche Ursachen

### 1. Q_OBJECT / MOC Problem
- MOC-Dateien möglicherweise nicht korrekt generiert
- Q_OBJECT Makro-Probleme
- Meta-Object-Symbole fehlen

### 2. Constructor Problem
- Der Constructor versucht auf etwas zuzugreifen, was noch nicht verfügbar ist
- Environment-Variablen-Abfrage verursacht Problem

### 3. DLL Dependency Problem
- Qt-Version-Mismatch (aber Scribus verwendet Qt6, Plugin auch Qt6)
- Runtime-Library-Mismatch
- Fehlende DLL-Dependencies

### 4. Unresolved Symbols Problem
- `/FORCE:UNRESOLVED` erlaubt unaufgelöste Symbole
- Zur Laufzeit können diese fehlen → Crash

## Nächste Schritte

1. **Test: Plugin temporär entfernen**
   - Wenn Scribus ohne Plugin startet → Problem definitiv beim Plugin
   - Wenn Scribus auch ohne Plugin abstürzt → Problem woanders

2. **Minimale Test-Version erstellen**
   - Nur Export-Funktionen
   - Keine Q_OBJECT
   - Keine Initialisierung

3. **MOC-Dateien prüfen**
   - Prüfen ob MOC korrekt ausgeführt wurde
   - Prüfen ob meta_*.cpp Dateien vorhanden sind

4. **Vergleich mit MCP Dashboard**
   - Warum funktioniert MCP Dashboard?
   - Was ist anders?

