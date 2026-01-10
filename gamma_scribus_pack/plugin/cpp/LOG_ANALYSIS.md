# Log-Analyse für Plugin-Laden

## Problem
Plugin wird nicht im Scribus-Menü angezeigt.

## Ursachen die bereits behoben wurden

✅ **Export-Funktionen korrekt hinzugefügt:**
- `gamma_dashboard_getPluginAPIVersion()`
- `gamma_dashboard_getPlugin()`
- `gamma_dashboard_freePlugin()`

✅ **DLL korrekt installiert:**
- `%APPDATA%\Scribus\plugins\gamma_dashboard.dll`
- `%LOCALAPPDATA%\Scribus\plugins\gamma_dashboard.dll`

✅ **plugin.json vorhanden**

## Mögliche verbleibende Probleme

### 1. Plugin wird nicht geladen
**Symptom:** Plugin erscheint nicht in `Extras > Plugins`

**Debugging:**
- Starte Scribus mit Logging:
  ```powershell
  cd "C:\Program Files\Scribus 1.7.1"
  .\scribus.exe 2>&1 | Tee-Object -FilePath "$env:TEMP\scribus_debug.log"
  ```
- Suche nach Fehlermeldungen:
  - `"API version mismatch when loading gamma_dashboard.dll"`
  - `"Unable to get ScPlugin when loading gamma_dashboard.dll"`
  - `"Invalid character in plugin name"`

### 2. Plugin wird geladen aber nicht aktiviert
**Symptom:** Plugin erscheint in `Extras > Plugins`, aber ist deaktiviert

**Lösung:** Checkbox aktivieren in `Extras > Plugins`

### 3. Plugin aktiviert, aber Menü erscheint nicht
**Symptom:** Plugin aktiviert, aber `Extras > Tools > Gamma Dashboard` fehlt

**Mögliche Ursachen:**
- `addToMainWindowMenu()` wird nicht aufgerufen
- `resolveMainWindow()` gibt `nullptr` zurück
- `ensureMenu()` findet "Extras > Tools" nicht

**Debugging:**
- Prüfe, ob `initPlugin()` aufgerufen wird (nur bei `ScPersistentPlugin`)
- Da wir `ScPlugin` verwenden, wird `initPlugin()` NICHT automatisch aufgerufen
- Lösung: Menü-Integration muss in `addToMainWindowMenu()` passieren

## Log-Datei prüfen

Die Log-Datei wird erstellt, wenn Scribus startet:
- Pfad: `%TEMP%\scribus_debug.log`
- Wird nur geschrieben, wenn Scribus mit Umleitung gestartet wurde

**Typische Fehlermeldungen:**
```
API version mismatch when loading gamma_dashboard.dll: Got 263, expected 263
```
(Wenn Versionen übereinstimmen, ist das OK)

```
Unable to get ScPlugin when loading gamma_dashboard.dll
```
(Plugin konnte nicht instanziiert werden)

```
Invalid character in plugin name for gamma_dashboard.dll; skipping
```
(Plugin-Name enthält ungültige Zeichen)

## Nächste Schritte

1. **Scribus vollständig schließen**
2. **Scribus mit Logging starten:**
   ```powershell
   cd "C:\Program Files\Scribus 1.7.1"
   .\scribus.exe 2>&1 | Tee-Object -FilePath "$env:TEMP\scribus_debug.log"
   ```
3. **Warte bis Scribus geladen ist**
4. **Prüfe `Extras > Plugins`**
5. **Scribus schließen**
6. **Log-Datei prüfen:**
   ```powershell
   Get-Content "$env:TEMP\scribus_debug.log" | Select-String -Pattern "gamma|plugin|error"
   ```

