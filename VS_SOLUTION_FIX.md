# Visual Studio Solution - Bibliotheksfehler beheben

## Problem

Beim Bauen mit Visual Studio Solution treten Linker-Fehler auf:
- `Datei "icudt.lib" kann nicht geöffnet werden`
- `Datei "libxml2.lib" kann nicht geöffnet werden`

## Ursache

Die Property-Sheet-Variablen (`ICU_LIB_DIR`, `LIBXML2_LIB_DIR`) werden möglicherweise nicht korrekt aufgelöst, obwohl:
- ✅ Die Bibliotheken existieren: `C:\Development\scribus-1.7.x-libs-msvc\icu-76.1\lib\x64-v143\icudt.lib`
- ✅ Die Property-Sheet wird importiert: `Scribus-build-props.props` → `scribus-lib-paths.props`
- ✅ Die Projekte verwenden die Variablen: `$(ICU_LIB_DIR)`, `$(LIBXML2_LIB_DIR)`

## Lösungen

### Lösung 1: Visual Studio neu starten (Property-Sheet-Cache)

Nach Änderungen an Property-Sheets muss Visual Studio manchmal neu gestartet werden:

1. **Visual Studio schließen**
2. **Visual Studio neu starten**
3. **Scribus.sln öffnen**
4. **Build → Clean Solution**
5. **Build → Build Solution**

### Lösung 2: Property-Sheet manuell prüfen (Visual Studio)

1. **Projekt öffnen:** `scribus-main → Scribus.vcxproj`
2. **Rechtsklick → Properties**
3. **Configuration Properties → VC++ Directories**
4. **Library Directories:** Sollte `$(ICU_LIB_DIR)` enthalten
5. **Prüfe, ob Variable aufgelöst wird:** Falls leer → Property-Sheet wird nicht geladen

### Lösung 3: Property-Sheet-Import verifizieren

Die Property-Sheet wird in `Scribus.vcxproj` importiert:

```xml
<ImportGroup Condition="'$(Configuration)|$(Platform)'=='Release|x64'" Label="PropertySheets">
  <Import Project="..\Scribus-build-props.props" />
</ImportGroup>
```

**Prüfen:**
1. **Solution Explorer → scribus-main → Scribus.vcxproj**
2. **Rechtsklick → Unload Project**
3. **Rechtsklick → Edit Scribus.vcxproj**
4. **Suche nach:** `Scribus-build-props.props`
5. **Prüfe Pfad:** Sollte `..\Scribus-build-props.props` sein (relativ zu Projekt-Verzeichnis)

### Lösung 4: Bibliothekspfade manuell setzen (Notfall)

Falls Property-Sheets nicht funktionieren, können Pfade manuell gesetzt werden:

1. **Project → Properties → Configuration Properties → Linker → General**
2. **Additional Library Directories:**
   - `C:\Development\scribus-1.7.x-libs-msvc\icu-76.1\lib\x64-v143`
   - `C:\Development\scribus-1.7.x-libs-msvc\libxml2-2.15.1\lib\x64-v143`
3. **Apply → OK**

**⚠️ Warnung:** Diese Lösung ist nur für Debugging gedacht. Property-Sheets sollten verwendet werden.

### Lösung 5: Property-Sheet-Debugging

Prüfe, ob MSBuild die Variablen sieht:

1. **Developer Command Prompt für VS 2022 öffnen**
2. **Wechsle zu:** `C:\Development\scribus-1.7\win32\msvc2022\scribus-main`
3. **Führe aus:**
   ```cmd
   msbuild Scribus.vcxproj /p:Configuration=Release /p:Platform=x64 /t:Clean /v:diagnostic 2>&1 | findstr /i "ICU_LIB_DIR"
   ```

Falls `ICU_LIB_DIR` nicht in der Ausgabe erscheint → Property-Sheet wird nicht geladen.

## Empfohlener Workflow

1. ✅ **Visual Studio schließen**
2. ✅ **Visual Studio als Administrator starten** (für bessere Berechtigungen)
3. ✅ **Scribus.sln öffnen**
4. ✅ **Configuration: Release, Platform: x64**
5. ✅ **Build → Clean Solution**
6. ✅ **Build → Build Solution**

Falls Fehler weiterhin auftreten:
- Prüfe **Output Window** (View → Output) für detaillierte Fehlermeldungen
- Prüfe, ob alle Property-Sheets korrekt importiert werden
- Prüfe, ob `SCRIBUS_LIB_ROOT` korrekt gesetzt ist: `C:\Development\scribus-1.7.x-libs-msvc`

## Weitere Fehler

### "Die Variable 'AffEntry::c' ist nicht initialisiert"

Dies ist ein Compiler-Fehler (Code-Analyse), kein Linker-Fehler. Dies kann ignoriert werden, falls der Build trotzdem durchläuft, oder durch Initialisierung der Variable behoben werden (nicht kritisch für Build).

