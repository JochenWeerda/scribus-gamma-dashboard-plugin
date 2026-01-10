# Fix: gamma_dashboard.dll kann nicht geladen werden

## Problem
Scribus zeigt Warnung: "Es ist ein Problem beim Laden von 1 von 59 Plugins aufgetreten" für `gamma_dashboard.dll`

## Mögliche Ursachen

### 1. Qt-Versionsmismatch
**Symptom:** DLL wurde mit anderer Qt-Version kompiliert als Scribus verwendet

**Prüfen:**
```powershell
# Qt-Version in Scribus prüfen
Get-Item "C:\Program Files\Scribus 1.7.1(1)\Qt6Core.dll" | Select-Object VersionInfo

# Qt-Version beim Kompilieren prüfen
# In CMakeCache.txt nach Qt6_VERSION suchen
```

**Lösung:** Plugin mit exakt derselben Qt-Version kompilieren wie Scribus verwendet.

### 2. MSVC Runtime Library Mismatch
**Symptom:** `/MD` vs `/MT` Problem

**Prüfen:** DLL sollte mit `/MD` (MultiThreadedDLL) kompiliert sein.

**Lösung:** 
- CMakeLists.txt prüfen: `CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreadedDLL"`
- MSVC Runtime muss im System vorhanden sein (Visual C++ Redistributable)

### 3. Fehlende Dependencies
**Symptom:** DLL benötigt andere DLLs, die nicht gefunden werden

**Prüfen mit Dependency Walker oder:**
```powershell
# DLL-Dependencies prüfen
dumpbin /DEPENDENTS build\Release\gamma_dashboard.dll
```

**Lösung:** Fehlende DLLs nach Scribus-Verzeichnis kopieren oder in PATH aufnehmen.

### 4. DLL im falschen Verzeichnis
**Symptom:** Scribus findet DLL nicht oder lädt falsche Version

**Prüfen:**
```powershell
# Welche DLL wird geladen?
Get-Item "C:\Program Files\Scribus 1.7.1(1)\plugins\gamma_dashboard.dll"
Get-Item "$env:APPDATA\Scribus\plugins\gamma_dashboard.dll"
```

**Lösung:** Korrekte DLL installieren.

## Sofort-Fix

### Schritt 1: Alte DLL entfernen
```powershell
# Alle gamma_dashboard.dll finden
Get-ChildItem "C:\Program Files*" -Recurse -Filter "gamma_dashboard.dll" -ErrorAction SilentlyContinue

# Alte DLLs löschen oder umbenennen
Remove-Item "C:\Program Files\Scribus 1.7.1(1)\plugins\gamma_dashboard.dll" -Force
```

### Schritt 2: Neu kompilieren mit korrekter Qt-Version
```powershell
cd "c:\Users\Jochen\Documents\Die verborgene Uhr Gottes\Gottes geheimer Zeitcode\gamma_scribus_pack\plugin\cpp"

# Qt-Version prüfen die Scribus verwendet
$qtVersion = (Get-Item "C:\Program Files\Scribus 1.7.1(1)\Qt6Core.dll").VersionInfo.ProductVersion
Write-Host "Scribus verwendet Qt: $qtVersion"

# CMake neu konfigurieren mit dieser Qt-Version
# Dann neu kompilieren
```

### Schritt 3: DLL-Dependencies kopieren (falls nötig)
Wenn die DLL Qt-DLLs nicht findet, müssen sie im gleichen Verzeichnis sein oder im PATH.

## Debug-Tipps

1. **Event Viewer prüfen:**
   - Windows Event Viewer öffnen
   - Windows Logs > Application
   - Nach "gamma_dashboard" suchen

2. **Scribus Log-Datei prüfen:**
   - Scribus Log-Verzeichnis finden
   - Nach Fehlermeldungen suchen

3. **DLL mit Dependency Walker analysieren:**
   - Dependency Walker herunterladen
   - DLL öffnen
   - Fehlende Dependencies rot markiert

## Häufigste Lösung

**In 90% der Fälle:** DLL wurde mit falscher Qt-Version kompiliert.

**Fix:**
1. Qt-Version identifizieren, die Scribus verwendet
2. Plugin mit dieser exakten Qt-Version neu kompilieren
3. DLL installieren


