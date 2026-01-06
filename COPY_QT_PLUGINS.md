# Qt-Plugins kopieren

## Problem

Scribus zeigt Fehler:
- "This application failed to start because no Qt platform plugin could be initialized"

## Ursache

Die Qt-Platform-Plugins (z.B. `qwindows.dll`) fehlen im Build-Verzeichnis.

## Lösung

**Qt-Plugins aus vollständigem Scribus-Ordner kopieren:**

1. **Platforms-Ordner kopieren:**
   ```powershell
   $fullScribusDir = "C:\Program Files\Scribus 1.7.1(1)"
   $buildDir = "C:\Development\Scribus-builds\Scribus-Release-x64-v143"
   
   # Finde platforms-Ordner
   $platformsSource = Get-ChildItem $fullScribusDir -Directory -Filter "platforms" -Recurse | Select-Object -First 1
   
   # Erstelle Ziel-Ordner
   $platformsDest = Join-Path $buildDir "platforms"
   New-Item -ItemType Directory -Force -Path $platformsDest | Out-Null
   
   # Kopiere alle Platform-Plugins
   Copy-Item "$($platformsSource.FullName)\*" -Destination $platformsDest -Recurse -Force
   ```

2. **Qt6-DLLs kopieren:**
   ```powershell
   # Kopiere alle Qt6-DLLs
   Get-ChildItem $fullScribusDir -Filter "Qt6*.dll" -Recurse | ForEach-Object {
       Copy-Item $_.FullName -Destination $buildDir -Force
   }
   ```

## Benötigte Qt-Komponenten

### Qt-Platform-Plugins (im `platforms`-Ordner):
- `qwindows.dll` (Windows-Platform-Plugin, **KRITISCH**)
- `qminimal.dll` (optional)
- `qoffscreen.dll` (optional)

### Qt6-DLLs (im Hauptverzeichnis):
- `Qt6Core.dll`
- `Qt6Gui.dll`
- `Qt6Widgets.dll`
- `Qt6Network.dll`
- `Qt6PrintSupport.dll` (falls benötigt)
- `Qt6Svg.dll` (falls benötigt)
- `Qt6Xml.dll` (falls benötigt)

## Automatisches Script

Führe aus: `COPY_QT_PLUGINS.ps1`

```powershell
.\gamma_scribus_pack\plugin\cpp\COPY_QT_PLUGINS.ps1
```

## Verzeichnisstruktur nach dem Kopieren

```
C:\Development\Scribus-builds\Scribus-Release-x64-v143\
├── scribus.exe
├── Qt6Core.dll
├── Qt6Gui.dll
├── Qt6Widgets.dll
├── Qt6Network.dll
├── platforms\
│   └── qwindows.dll
└── plugins\
    └── gamma_dashboard.dll
```

## Nach dem Kopieren

1. **Scribus erneut starten:**
   ```powershell
   cd "C:\Development\Scribus-builds\Scribus-Release-x64-v143"
   .\scribus.exe
   ```

2. **Prüfe, ob weitere Qt-Plugins fehlen:**
   - Event Viewer prüfen
   - Oder Dependency Walker verwenden

## Alternative: Qt-Installation verwenden

Falls Qt-Plugins im Scribus-Ordner fehlen, können sie auch aus der Qt-Installation kopiert werden:

```powershell
$qtDir = "C:\Development\Qt\6.10.1\msvc2022_64"
$buildDir = "C:\Development\Scribus-builds\Scribus-Release-x64-v143"

# Kopiere platforms-Ordner
Copy-Item "$qtDir\plugins\platforms" -Destination $buildDir -Recurse -Force

# Kopiere Qt6-DLLs
Copy-Item "$qtDir\bin\Qt6*.dll" -Destination $buildDir -Force
```

## Troubleshooting

### "qwindows.dll nicht gefunden"
- Prüfe, ob `platforms\qwindows.dll` im Build-Verzeichnis existiert
- Prüfe, ob der `platforms`-Ordner im gleichen Verzeichnis wie `scribus.exe` liegt

### "Qt6Core.dll nicht gefunden"
- Prüfe, ob alle Qt6-DLLs im Build-Verzeichnis vorhanden sind
- Prüfe, ob die DLLs die richtige Architektur haben (x64)

### "Plugin kann nicht geladen werden"
- Prüfe, ob alle Dependency-DLLs vorhanden sind (siehe `COPY_DEPENDENCIES.md`)

