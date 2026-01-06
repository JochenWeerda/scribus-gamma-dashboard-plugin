# Gebaute Scribus-Dateien nach installierte Version kopieren

## Übersicht

Dieses Script kopiert die neu gebauten Scribus-Dateien und das Plugin nach `C:\Program Files\Scribus 1.7.1(1)` (die aktuell installierte Version).

## Was wird kopiert?

1. **scribus.exe** → Hauptverzeichnis
2. **gamma_dashboard.dll** → `plugins\` Ordner
3. **Weitere Dateien** (optional):
   - scribus.pdb
   - scribusapi.dll
   - scribusapi.lib

## Voraussetzungen

- **Administrator-Rechte** erforderlich (für `C:\Program Files\...`)
- Build-Verzeichnis vorhanden: `C:\Development\Scribus-builds\Scribus-Release-x64-v143`
- Installationsverzeichnis vorhanden: `C:\Program Files\Scribus 1.7.1(1)`

## Verwendung

### Option 1: PowerShell als Administrator

1. **PowerShell als Administrator starten:**
   - Rechtsklick auf PowerShell → "Als Administrator ausführen"

2. **Script ausführen:**
   ```powershell
   cd "C:\Users\Jochen\Documents\Die verborgene Uhr Gottes\Gottes geheimer Zeitcode\.cursor"
   .\gamma_scribus_pack\plugin\cpp\COPY_TO_INSTALLED.ps1
   ```

### Option 2: Automatisch mit Administrator-Rechten

```powershell
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"gamma_scribus_pack\plugin\cpp\COPY_TO_INSTALLED.ps1`"" -Verb RunAs -Wait
```

## Parameter

Das Script akzeptiert optionale Parameter:

```powershell
.\COPY_TO_INSTALLED.ps1 -BuildDir "C:\Development\Scribus-builds\Scribus-Release-x64-v143" -InstallDir "C:\Program Files\Scribus 1.7.1(1)"
```

## Was passiert?

1. **Prüfung:** Administrator-Rechte, Verzeichnisse vorhanden
2. **Kopieren:** scribus.exe nach Installationsverzeichnis
3. **Kopieren:** Plugin nach `plugins\` Ordner
4. **Kopieren:** Optionale Dateien (falls vorhanden)
5. **Prüfung:** Finale Verifikation, ob alles erfolgreich kopiert wurde

## Nach dem Kopieren

1. **Scribus starten:**
   ```powershell
   cd "C:\Program Files\Scribus 1.7.1(1)"
   .\scribus.exe
   ```

2. **Plugin testen:**
   - Menü → Extras → Gamma Dashboard
   - Dock-Widget sollte rechts erscheinen

## Troubleshooting

### "Zugriff verweigert"
- **Lösung:** PowerShell als Administrator starten

### "Datei wird verwendet"
- **Lösung:** Scribus schließen, dann erneut kopieren

### "Verzeichnis nicht gefunden"
- **Lösung:** Prüfe, ob Build-Verzeichnis und Installationsverzeichnis existieren
- Passe Parameter an, falls Pfade anders sind

### "Plugin erscheint nicht im Menü"
- **Lösung:** 
  1. Prüfe, ob `gamma_dashboard.dll` in `plugins\` Ordner liegt
  2. Prüfe Scribus-Log auf Plugin-Ladefehler
  3. Prüfe, ob Plugin-DLL die richtige Architektur hat (x64)

## Dateistruktur nach dem Kopieren

```
C:\Program Files\Scribus 1.7.1(1)\
├── scribus.exe                 (neu gebaut)
├── scribus.pdb                 (optional)
├── scribusapi.dll              (optional)
├── scribusapi.lib              (optional)
└── plugins\
    └── gamma_dashboard.dll     (Plugin)
```

## Backup-Empfehlung

**Vor dem Kopieren:** Erstelle ein Backup der originalen `scribus.exe`:

```powershell
$installDir = "C:\Program Files\Scribus 1.7.1(1)"
Copy-Item "$installDir\scribus.exe" "$installDir\scribus.exe.backup" -Force
```

**Wiederherstellung:**

```powershell
$installDir = "C:\Program Files\Scribus 1.7.1(1)"
Copy-Item "$installDir\scribus.exe.backup" "$installDir\scribus.exe" -Force
```

