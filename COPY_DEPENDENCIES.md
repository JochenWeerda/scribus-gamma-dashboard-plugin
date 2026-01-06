# Dependency-DLLs kopieren

## Problem

Scribus zeigt Fehler beim Start:
- `cairo2.dll nicht gefunden`
- `harfbuzz.dll nicht gefunden`

## Ursache

Die Dependency-DLLs aus dem Scribus-Libs-Kit fehlen im Build-Verzeichnis.

## Lösung

**Vollständiger Scribus-Ordner verwenden:**
- `C:\Program Files\Scribus 1.7.1(1)` (vollständig, alle DLLs vorhanden)
- NICHT: `C:\Program Files\Scribus 1.7.1` (unvollständig)

**DLLs kopieren:**
1. Alle DLLs aus `C:\Program Files\Scribus 1.7.1(1)\` → Build-Verzeichnis
2. DLLs aus Unterordnern (`lib`, `bin`, `plugins`) → Build-Verzeichnis

## Script zum Kopieren

```powershell
$fullScribusDir = "C:\Program Files\Scribus 1.7.1(1)"
$buildDir = "C:\Development\Scribus-builds\Scribus-Release-x64-v143"

# Kopiere alle DLLs aus Hauptverzeichnis
Get-ChildItem $fullScribusDir -Filter "*.dll" -File | ForEach-Object {
    Copy-Item $_.FullName -Destination $buildDir -Force
}

# Kopiere aus Unterordnern
Get-ChildItem $fullScribusDir -Directory | ForEach-Object {
    $subDlls = Get-ChildItem $_.FullName -Filter "*.dll" -File -ErrorAction SilentlyContinue
    if ($subDlls) {
        $targetDir = if ($_.Name -eq "plugins") { Join-Path $buildDir "plugins" } else { $buildDir }
        foreach ($dll in $subDlls) {
            Copy-Item $dll.FullName -Destination $targetDir -Force -ErrorAction SilentlyContinue
        }
    }
}
```

## Alternative: Scribus-Libs-Kit verwenden

Falls DLLs im vollständigen Scribus-Ordner fehlen:

```powershell
$libsKit = "C:\Development\scribus-1.7.x-libs-msvc"
$buildDir = "C:\Development\Scribus-builds\Scribus-Release-x64-v143"

# Kopiere alle DLLs aus Libs-Kit
Get-ChildItem $libsKit -Filter "*.dll" -Recurse -File | ForEach-Object {
    Copy-Item $_.FullName -Destination $buildDir -Force
}
```

## Benötigte DLLs (Minimum)

- `cairo2.dll`
- `harfbuzz.dll`
- `icuuc76.dll`, `icuin76.dll`, `icudt76.dll`
- `libxml2.dll`
- `freetype.dll`
- Qt6-DLLs (aus Qt-Installation)

## Nach dem Kopieren

1. **Scribus erneut starten:**
   ```powershell
   cd "C:\Development\Scribus-builds\Scribus-Release-x64-v143"
   .\scribus.exe
   ```

2. **Prüfe, ob weitere DLLs fehlen:**
   - Event Viewer prüfen
   - Oder Dependency Walker verwenden

## Automatisches Script

Führe aus: `COPY_ALL_DLLS.ps1` (siehe unten)

