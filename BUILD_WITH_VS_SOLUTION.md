# Scribus mit Visual Studio Solution bauen

## Status

✅ **Property-Sheet-Datei konfiguriert:**
- `C:\Development\scribus-1.7\win32\msvc2022\Scribus-build-props.props`

**Angepasste Pfade:**
- `SCRIBUS_LIB_ROOT`: `C:\Development\scribus-1.7.x-libs-msvc`
- `QT6_DIR` (x64/v143): `C:\Development\Qt\6.10.1\msvc2022_64`

## Voraussetzungen (erfüllt)

✅ Scribus-Libs-Kit gebaut (alle 25 Projekte, Release, x64)
✅ Qt 6.10.1 msvc2022_64 installiert
✅ Toolset-Kompatibilität: passt (v143)

## Build-Schritte

### 1. Visual Studio öffnen

Öffne die Solution-Datei:
```
C:\Development\scribus-1.7\win32\msvc2022\Scribus.sln
```

### 2. Konfiguration einstellen

- **Build → Configuration Manager...**
- **Active solution configuration:** `Release` (nicht Debug!)
- **Active solution platform:** `x64`
- **Close**

### 3. Build starten

- **Build → Build Solution** (F7)

**Hinweis:** Der Build kann einige Zeit dauern (Scribus ist ein großes Projekt).

### 4. Plugin bauen (falls gewünscht)

Das `gamma_dashboard` Plugin ist bereits in den Scribus-Source-Tree integriert und wird automatisch mitgebaut.

Falls nur das Plugin gebaut werden soll:
- **Solution Explorer → plugins → gamma_dashboard**
- **Rechtsklick → Build**

### 5. DLLs kopieren (nach Build)

Nach dem Build müssen die Dependency-DLLs kopiert werden:

1. **Öffne:** `C:\Development\scribus-1.7.x-libs-msvc\copy-dlls-to-build-dir.bat`
2. **Bearbeite:** Setze `SCRIBUS_BUILDS_DIR` auf:
   ```
   C:\Development\scribus-1.7\Scribus-builds
   ```
3. **Führe aus:** `copy-dlls-to-build-dir.bat`

### 6. Qt DLLs kopieren

Kopiere Qt-DLLs aus:
```
C:\Development\Qt\6.10.1\msvc2022_64\bin\*.dll
```

Nach:
```
C:\Development\scribus-1.7\Scribus-builds\scribus-Release-x64-v143\
```

## Build-Ausgabe

Die gebauten Dateien befinden sich in:
```
C:\Development\scribus-1.7\Scribus-builds\scribus-Release-x64-v143\
```

- `scribus.exe` - Hauptprogramm
- `plugins\` - Plugins (inkl. gamma_dashboard.dll)

## Troubleshooting

### "Property-Sheet nicht gefunden"

Stelle sicher, dass `scribus-lib-paths.props` im Libs-Kit-Verzeichnis existiert:
```
C:\Development\scribus-1.7.x-libs-msvc\scribus-lib-paths.props
```

### "Qt nicht gefunden"

Prüfe, ob Qt6_DIR korrekt gesetzt ist:
- Visual Studio: **Project → Properties → User Macros**
- Sollte sein: `C:\Development\Qt\6.10.1\msvc2022_64`

### "Bibliotheken nicht gefunden"

Die Property-Sheet importiert `scribus-lib-paths.props`, die alle Bibliothekspfade definiert. Falls Probleme auftreten, prüfe:
- `C:\Development\scribus-1.7.x-libs-msvc\scribus-lib-paths.props`
- Pfade in dieser Datei sollten relativ zu `SCRIBUS_LIB_ROOT` sein

