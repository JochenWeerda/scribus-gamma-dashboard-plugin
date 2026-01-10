# Plugin-Laden Debugging

## Problem
Plugin wird nicht von Scribus erkannt/geladen.

## Ursache gefunden
Scribus sucht nach spezifischen Export-Funktionen:
- `{pluginName}_getPluginAPIVersion()` 
- `{pluginName}_getPlugin()`
- `{pluginName}_freePlugin()`

**Plugin-Name wird aus Dateiname extrahiert:**
- `gamma_dashboard.dll` → `gamma_dashboard`
- Gesucht wird: `gamma_dashboard_getPluginAPIVersion()`

## Lösung implementiert
✅ Korrekte Export-Funktionen hinzugefügt:
- `gamma_dashboard_getPluginAPIVersion()` → gibt `PLUGIN_API_VERSION` zurück
- `gamma_dashboard_getPlugin()` → erstellt Plugin-Instanz
- `gamma_dashboard_freePlugin()` → löscht Plugin-Instanz

## Logs prüfen

### 1. Scribus starten mit Debug-Output
```powershell
# In PowerShell oder CMD
cd "C:\Program Files\Scribus 1.7.1"
.\scribus.exe 2>&1 | Tee-Object -FilePath "$env:TEMP\scribus_debug.log"
```

### 2. Plugin-Loading-Fehler
Scribus gibt `qDebug()` Meldungen aus bei:
- API-Version-Mismatch
- Fehlende Export-Funktionen
- Plugin-Load-Fehler

### 3. Typische Fehlermeldungen
```
"API version mismatch when loading gamma_dashboard.dll: Got X, expected Y"
"Unable to get ScPlugin when loading gamma_dashboard.dll"
```

### 4. Plugin wird nicht gefunden
- Prüfe: `Extras > Plugins`
- Falls Plugin nicht erscheint: DLL wird nicht geladen
- Falls Plugin erscheint aber deaktiviert: `enableOnStartup = false`

## Nächste Schritte

1. **Scribus neu starten** (vollständig schließen!)
2. **Prüfen**: `Extras > Plugins` → "Gamma Dashboard" sollte erscheinen
3. **Aktivieren**: Falls deaktiviert, Checkbox setzen
4. **Prüfen**: `Extras > Tools > Gamma Dashboard` sollte erscheinen

## Export-Funktionen prüfen

Mit `dumpbin` (Visual Studio):
```powershell
dumpbin /EXPORTS "gamma_dashboard.dll" | Select-String "gamma_dashboard"
```

Sollte zeigen:
- `gamma_dashboard_getPluginAPIVersion`
- `gamma_dashboard_getPlugin`
- `gamma_dashboard_freePlugin`

