# Nach Scribus-Neuinstallation

## Schritt-für-Schritt Test-Prozess

### 1. Nach Neuinstallation prüfen

**Prüfe ob Scribus startet:**
```powershell
cd "C:\Program Files\Scribus 1.7.1"
.\scribus.exe
```

✅ **Wenn Scribus startet:** Weiter zu Schritt 2
❌ **Wenn Scribus abstürzt:** Problem liegt nicht beim Plugin → weitere Diagnose nötig

---

### 2. Plugin installieren

**Als Administrator:**

```powershell
cd "C:\Users\Jochen\Documents\Die verborgene Uhr Gottes\Gottes geheimer Zeitcode\gamma_scribus_pack\plugin\cpp"
.\INSTALL_SYSTEM_PLUGIN.ps1
```

**Oder manuell:**
```powershell
Copy-Item "C:\Users\Jochen\Documents\Die verborgene Uhr Gottes\Gottes geheimer Zeitcode\gamma_scribus_pack\plugin\cpp\build\Release\gamma_dashboard.dll" -Destination "C:\Program Files\Scribus 1.7.1\plugins\gamma_dashboard.dll" -Force
```

---

### 3. Plugin testen

**Scribus starten:**
```powershell
.\scribus.exe
```

**Prüfe:**
1. Startet Scribus ohne Absturz? ✅
2. Gehe zu: `Extras > Einstellungen > Plug-Ins`
3. Suche nach: "Gamma Dashboard"
4. Plugin sollte in der Liste erscheinen
5. Falls deaktiviert: Aktivieren
6. Gehe zu: `Extras > Tools`
7. "Gamma Dashboard" sollte im Menü erscheinen

---

### 4. Falls Probleme

**Plugin temporär deaktivieren:**
```powershell
cd "C:\Users\Jochen\Documents\Die verborgene Uhr Gottes\Gottes geheimer Zeitcode\gamma_scribus_pack\plugin\cpp"
.\TEST_DISABLE_PLUGIN.ps1
```

**Log-Datei prüfen:**
```powershell
Get-Content "$env:TEMP\scribus_debug.log" | Select-String -Pattern "gamma|plugin|error" -Context 2,2
```

---

## Plugin-Status

✅ **Plugin ist vollständig implementiert:**
- Export-Funktionen: ✅
- initPlugin(): ✅
- addToMainWindowMenu(): ✅
- Menü-Integration: ✅
- DLL korrekt gebaut: ✅

**Version:** 79.5 KB (neueste mit allen Fixes)

