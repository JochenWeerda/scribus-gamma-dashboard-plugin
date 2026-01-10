# Plugin Implementation Checklist

## ✅ Konformität mit Scribus Plugin-Dokumentation

Basierend auf der offiziellen Scribus Plugin-Dokumentation:

### 1. Export-Funktionen (ERFORDERLICH)
✅ **Erfüllt:**
- `gamma_dashboard_getPluginAPIVersion()` → gibt `PLUGIN_API_VERSION` zurück
- `gamma_dashboard_getPlugin()` → erstellt Plugin-Instanz
- `gamma_dashboard_freePlugin()` → löscht Plugin-Instanz

**Code:**
```cpp
extern "C" PLUGIN_API int gamma_dashboard_getPluginAPIVersion()
{
    return PLUGIN_API_VERSION;
}

extern "C" PLUGIN_API ScPlugin* gamma_dashboard_getPlugin()
{
    return new GammaDashboardPlugin();
}

extern "C" PLUGIN_API void gamma_dashboard_freePlugin(ScPlugin* plugin)
{
    delete plugin;
}
```

### 2. Plugin-Basisklasse
✅ **Erfüllt:**
- Vererbt von `ScPlugin` (korrekt für allgemeine Plugins)
- Implementiert `initPlugin()` (pure virtual in ScPlugin-Subklassen)
- Implementiert `cleanupPlugin()`
- Implementiert `fullTrName()` (pure virtual)
- Implementiert `addToMainWindowMenu()` (pure virtual)

### 3. initPlugin() Implementierung
✅ **Erfüllt:**
- Initialisiert Network Manager und Timer
- Erstellt Menü-Einträge in `Extras > Tools`
- Gibt `true` bei Erfolg zurück, `false` bei Fehler

**Wichtig:** `initPlugin()` wird von `PluginManager::enablePlugin()` aufgerufen (siehe pluginmanager.cpp Zeile 256).

### 4. Menü-Integration
✅ **Erfüllt:**
- Menü-Eintrag in `Extras > Tools`
- `QAction` mit `toggleDashboard()` Signal/Slot-Verbindung
- Checkable Action für Toggle-Verhalten

### 5. Plugin-Metadaten
✅ **Erfüllt:**
- `getAboutData()` implementiert mit:
  - Author: jochen.weerda@gmail.com
  - Version: 1.0.0
  - Description: Vollständige Beschreibung
  - License: Proprietary
  - Release Date: 2025-01-27

### 6. Includes
✅ **Erfüllt:**
- `pluginapi.h` → für `PLUGIN_API` Macro
- `scplugin.h` → für `ScPlugin` Basisklasse und `PLUGIN_API_VERSION`

### 7. Compilation
✅ **Erfüllt:**
- CMake-Konfiguration vorhanden
- `/FORCE:UNRESOLVED` für Runtime-Symbol-Resolution
- DLL wird als `gamma_dashboard.dll` erstellt
- Export-Funktionen werden korrekt exportiert

## Vergleich mit MCP Dashboard Plugin

Das MCP Dashboard Plugin verwendet das gleiche Pattern:
- ✅ Export-Funktionen: `mcp_ai_dashboard_*`
- ✅ `initPlugin()` Implementierung
- ✅ Menü-Integration in `Extras > Tools`
- ✅ `ScPlugin` als Basisklasse

**Unterschied:** MCP Dashboard hat zusätzlich `scribus_plugin()` (optional, für Legacy-Support).

## Installation

✅ **Installiert in:**
- `%APPDATA%\Scribus\plugins\gamma_dashboard.dll`
- `%LOCALAPPDATA%\Scribus\plugins\gamma_dashboard.dll`

✅ **plugin.json vorhanden:**
```json
{
  "Name": "Gamma Dashboard",
  "Version": "1.0.0",
  "Description": "Gamma → Scribus Pipeline Dashboard with dockable panel.",
  "Author": "jochen.weerda@gmail.com",
  "License": "Proprietary",
  "Type": "UI"
}
```

## Plugin-Loading-Prozess (laut Dokumentation)

1. Scribus lädt DLL via `PluginManager::loadPlugin()`
2. Resolved Export-Funktion `gamma_dashboard_getPluginAPIVersion()`
3. Prüft API-Version (muss `PLUGIN_API_VERSION` (0x00000107) entsprechen)
4. Ruft `gamma_dashboard_getPlugin()` auf → erstellt Plugin-Instanz
5. Ruft `plugin->initPlugin()` auf → initialisiert Menü, etc.
6. Plugin erscheint in `Extras > Plugins` Liste
7. Wenn aktiviert: `Extras > Tools > Gamma Dashboard` wird angezeigt

## Mögliche Probleme

### Plugin erscheint nicht in `Extras > Plugins`
**Ursachen:**
- DLL nicht in Plugin-Verzeichnis
- Export-Funktionen fehlen oder haben falschen Namen
- API-Version-Mismatch
- DLL kann nicht geladen werden (Dependencies fehlen)

**Lösung:** Prüfe Log-Ausgaben von Scribus:
```powershell
.\scribus.exe 2>&1 | Tee-Object -FilePath "$env:TEMP\scribus_debug.log"
```

### Plugin erscheint, aber Menü fehlt
**Ursachen:**
- `initPlugin()` gibt `false` zurück
- `resolveMainWindow()` gibt `nullptr` zurück
- `ensureMenu()` findet Menü nicht

**Lösung:** Prüfe `initPlugin()` Implementierung und MainWindow-Resolution.

## Status

✅ **Plugin ist vollständig implementiert und sollte funktionieren!**

Alle Anforderungen der Scribus Plugin-Dokumentation sind erfüllt. Das Plugin sollte von Scribus erkannt und geladen werden können.

