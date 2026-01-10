# Crash Fix - Plugin Initialisierung

## Problem
Scribus stürzt mit `EXCEPTION_ACCESS_VIOLATION` ab, wenn das Plugin geladen wird.

## Ursache
1. **initPlugin() wird nicht aufgerufen:** Für direkte `ScPlugin`-Subklassen wird `initPlugin()` NICHT aufgerufen (nur für `ScPersistentPlugin`).
2. **Menü-Integration am falschen Ort:** Die Menü-Integration erfolgte in `initPlugin()`, wird aber nicht aufgerufen.

## Lösung
- Menü-Integration von `initPlugin()` nach `addToMainWindowMenu()` verschoben
- `initPlugin()` bleibt für zukünftige Migration zu `ScPersistentPlugin` vorhanden, aber minimal

## Änderungen

### gamma_dashboard_plugin.cpp

**Vorher:**
- Menü-Integration in `initPlugin()` (wird nie aufgerufen)
- `addToMainWindowMenu()` leer

**Nachher:**
- `initPlugin()` minimal (nur Initialisierung von Netzwerk/Timer)
- `addToMainWindowMenu()` enthält komplette Menü-Integration

## Status
✅ Code angepasst
✅ Neu kompiliert
⏳ Installation im System-Verzeichnis erforderlich (Admin-Rechte)

## Nächste Schritte
1. Plugin ins System-Verzeichnis kopieren (als Administrator)
2. Scribus neu starten
3. Prüfen ob Plugin geladen wird ohne Absturz

