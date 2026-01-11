# Scribus Plugin Development Cookbook

Ein umfassendes Handbuch für die Entwicklung, das Builden, Testen und Installieren von Scribus-Plugins.

## 📋 Inhaltsverzeichnis

1. [Schnellstart](#schnellstart)
2. [Plugin-Architektur](#plugin-architektur)
3. [Build-Prozess](#build-prozess)
4. [Installation](#installation)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)
7. [Häufige Probleme](#häufige-probleme)

---

## 🚀 Schnellstart

### Plugin schnell neu bauen und installieren

**Empfohlen: Automatisiertes Script (mit Clean)**
```powershell
cd 'gamma_scribus_pack\plugin\cpp'
.\rebuild_and_install.ps1
```
*Hinweis: Das Script synchronisiert zuerst die Quellen aus `src/` in den Scribus Source Tree (siehe `UPDATE_SCRIBUS_SOURCE.ps1`).*
*Führt automatisch Clean, Build, Scribus beenden und Installation durch*

**MSBuild BinLog (Standard: an)**
- BinLog liegt unter `gamma_scribus_pack/plugin/cpp/artifacts/` (für MSBuild Structured Log Viewer)
- Automatisch öffnen: `.\rebuild_and_install.ps1 -OpenBinLog`
- Deaktivieren: `.\rebuild_and_install.ps1 -BinLog:$false`

**Manuell:**
```powershell
# 0. Clean (wichtig für sauberen Build!)
cd C:\Development\scribus-1.7\win32\msvc2022
msbuild Scribus.sln /t:gamma_dashboard:Clean /p:Configuration=Release /p:Platform=x64 /v:minimal

# 1. Plugin bauen
msbuild Scribus.sln /t:gamma_dashboard /p:Configuration=Release /p:Platform=x64 /m:1 /v:minimal

# 2. Scribus schließen (wichtig!)

# 3. Plugin installieren (als Administrator)
Copy-Item 'C:\Development\Scribus-builds\Scribus-Release-x64-v143\plugins\gamma_dashboard.dll' -Destination 'C:\Program Files\Scribus 1.7.1(1)\plugins\gamma_dashboard.dll' -Force

# 4. Scribus neu starten
```

---

## 🏗️ Plugin-Architektur

### Basis-Struktur

Ein Scribus-Plugin benötigt:

1. **Export-Funktionen** (in `gamma_dashboard_exports.cpp`):
   ```cpp
   extern "C" PLUGIN_API int gamma_dashboard_getPluginAPIVersion()
   extern "C" PLUGIN_API ScPlugin* gamma_dashboard_getPlugin()
   extern "C" PLUGIN_API void gamma_dashboard_freePlugin(ScPlugin* plugin)
   ```

2. **Plugin-Klasse** (von `ScPlugin` oder `ScActionPlugin` ableiten):
   ```cpp
   class GammaDashboardPlugin : public ScActionPlugin
   {
       Q_OBJECT
       // ...
   };
   ```

3. **Menü-Integration** (via `addToMainWindowMenu()`):
   ```cpp
   void addToMainWindowMenu(ScribusMainWindow* mw) override
   ```

### Datei-Struktur

```
gamma_dashboard/
├── gamma_dashboard_plugin.h          # Plugin-Hauptklasse
├── gamma_dashboard_plugin.cpp        # Plugin-Implementierung
├── gamma_dashboard_dock.h            # Dock-Widget Header
├── gamma_dashboard_dock.cpp          # Dock-Widget Implementierung
├── gamma_dashboard_exports.cpp       # C-ABI Export-Funktionen
├── gamma_api_client.h                # API-Client (optional)
├── gamma_api_client.cpp
├── gamma_api_settings_dialog.h       # Settings-Dialog (optional)
└── gamma_api_settings_dialog.cpp
```

---

## 🔨 Build-Prozess

### Voraussetzungen

- **Visual Studio 2022** (Build Tools oder Community)
- **Qt 6.10.1** (msvc2022_64) - muss mit Scribus-Version übereinstimmen
- **Scribus Source Tree** (`C:\Development\scribus-1.7`)
- **Scribus Libs Kit** (`C:\Development\scribus-1.7.x-libs-msvc`)

### Debug-Build: Fehlende `*_d.lib` (z.B. `cairo2d.lib`)

Wenn du im **Debug**-Build Fehler wie `LNK1104: Datei "cairo2d.lib" kann nicht geöffnet werden` bekommst, fehlen meistens Debug-Libs im `...\\lib\\x64-v143\\` Ordner.

Fix (einmalig):
```powershell
cd 'gamma_scribus_pack\plugin\cpp'
.\scripts\fix_libs_debug_v143.ps1
```

### Build-Schritte

#### Option 1: Visual Studio Solution (Empfohlen)

```powershell
# 1. Öffne Developer Command Prompt for VS 2022
# Oder lade Environment:
call "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

# 2. Navigiere zum Solution-Verzeichnis
cd C:\Development\scribus-1.7\win32\msvc2022

# 3. Clean (wichtig für sauberen Build!)
msbuild Scribus.sln /t:gamma_dashboard:Clean /p:Configuration=Release /p:Platform=x64 /v:minimal

# 4. Baue nur das Plugin-Projekt
msbuild Scribus.sln /t:gamma_dashboard /p:Configuration=Release /p:Platform=x64 /m:1 /v:minimal

# 5. Prüfe Output
# DLL sollte sein: C:\Development\Scribus-builds\Scribus-Release-x64-v143\plugins\gamma_dashboard.dll
```

**WICHTIG:** Führe immer ein Clean durch, bevor du baust, um sicherzustellen, dass alte Objektdateien nicht wiederverwendet werden!

#### Option 2: CMake (Alternative)

```powershell
# Konfigurieren
cmake -B build -S . `
  -DQt6_DIR="C:\Development\Qt\6.10.1\msvc2022_64" `
  -DCMAKE_INCLUDE_PATH="C:\Development\scribus-1.7.x-libs-msvc" `
  -DCMAKE_LIBRARY_PATH="C:\Development\scribus-1.7.x-libs-msvc"

# Bauen
cmake --build build --config Release
```

### Projekt-Datei aktualisieren

Wenn neue Dateien hinzugefügt werden, **`gamma_dashboard.vcxproj`** aktualisieren:

```xml
<ItemGroup>
  <ClCompile Include="..\..\..\scribus\plugins\gamma_dashboard\gamma_dashboard_plugin.cpp" />
  <ClCompile Include="..\..\..\scribus\plugins\gamma_dashboard\gamma_dashboard_dock.cpp" />
  <ClCompile Include="..\..\..\scribus\plugins\gamma_dashboard\gamma_dashboard_exports.cpp" />
  <ClCompile Include="..\..\..\scribus\plugins\gamma_dashboard\gamma_api_client.cpp" />
  <!-- Neue Dateien hier hinzufügen -->
</ItemGroup>
<ItemGroup>
  <moc Include="..\..\..\scribus\plugins\gamma_dashboard\gamma_dashboard_plugin.h" />
  <!-- Q_OBJECT Klassen hier hinzufügen -->
</ItemGroup>
```

---

## 📦 Installation

### Manuelle Installation

```powershell
# WICHTIG: Scribus muss geschlossen sein!

# 1. Als Administrator in PowerShell
Copy-Item `
  'C:\Development\Scribus-builds\Scribus-Release-x64-v143\plugins\gamma_dashboard.dll' `
  -Destination 'C:\Program Files\Scribus 1.7.1(1)\plugins\gamma_dashboard.dll' `
  -Force

# 2. Prüfe Installation
Get-Item 'C:\Program Files\Scribus 1.7.1(1)\plugins\gamma_dashboard.dll'
```

### Automatisiertes Installations-Script

```powershell
# NOTE: Prefer running the real script from this repo:
#   cd 'gamma_scribus_pack\plugin\cpp'
#   .\install_plugin.ps1
# install_plugin.ps1
$sourceDll = "C:\Development\Scribus-builds\Scribus-Release-x64-v143\plugins\gamma_dashboard.dll"
$targetDll = "C:\Program Files\Scribus 1.7.1(1)\plugins\gamma_dashboard.dll"

# Prüfe ob Scribus läuft
$scribusProcesses = Get-Process -Name "scribus" -ErrorAction SilentlyContinue
if ($scribusProcesses) {
    Write-Host "FEHLER: Scribus läuft noch! Bitte schließen." -ForegroundColor Red
    exit 1
}

# Installiere
Copy-Item $sourceDll -Destination $targetDll -Force
Write-Host "Plugin installiert!" -ForegroundColor Green
```

### Installations-Verzeichnis

Scribus 1.7.1 lädt Plugins nur aus:
- `C:\Program Files\Scribus 1.7.1(1)\plugins\` (System-weit)
- **NICHT** aus `AppData\Roaming\Scribus\plugins\` (veraltet)

---

## 🔍 Troubleshooting

### Plugin wird nicht geladen

**Symptome:**
- Plugin erscheint nicht in "Extras > Einstellungen > Plug-Ins"
- Kein Menü-Eintrag sichtbar

**Lösungsschritte:**

1. **Prüfe DLL-Installation:**
   ```powershell
   Get-Item 'C:\Program Files\Scribus 1.7.1(1)\plugins\gamma_dashboard.dll'
   # Sollte existieren und ~143 KB groß sein
   ```

2. **Prüfe Export-Funktionen:**
   ```powershell
   # Mit dumpbin (falls verfügbar)
   dumpbin /EXPORTS "C:\Program Files\Scribus 1.7.1(1)\plugins\gamma_dashboard.dll"
   # Sollte enthalten: gamma_dashboard_getPluginAPIVersion, gamma_dashboard_getPlugin, gamma_dashboard_freePlugin
   ```

3. **Prüfe Debug-Log:**
   - In Scribus: `Hilfe > Debug-Fenster`
   - Oder starte Scribus von Kommandozeile: `scribus.exe 2>&1 | Tee-Object debug.log`
   - Suche nach Fehlern mit "gamma", "plugin", "error"

4. **Prüfe Abhängigkeiten:**
   - Qt6-DLLs müssen im Scribus-Verzeichnis vorhanden sein
   - Runtime-Library muss übereinstimmen (`/MD` MultiThreadedDLL)

### Plugin wird geladen, aber Menü fehlt

**Symptome:**
- Plugin erscheint in "Extras > Einstellungen > Plug-Ins"
- Aber kein Menü-Eintrag unter "Extras"

**Ursache:**
- `addToMainWindowMenu()` wird nicht aufgerufen
- Menü-Erstellung schlägt fehl (z.B. "Tools" Untermenü existiert nicht)

**Lösung:**
- Menü direkt unter "Extras" hinzufügen, nicht unter "Extras" → "Tools"
- Fallback-Mechanismus implementieren

### Plugin-Crash beim Laden

**Symptome:**
- Scribus startet nicht
- "EXCEPTION_ACCESS_VIOLATION" Fehler

**Häufige Ursachen:**

1. **Runtime-Library Mismatch:**
   - Scribus verwendet `/MD` (MultiThreadedDLL)
   - Plugin muss auch `/MD` verwenden
   - **Fix:** `CMAKE_MSVC_RUNTIME_LIBRARY="MultiThreadedDLL"` in CMakeLists.txt

2. **Qt-Version Mismatch:**
   - Scribus verwendet Qt 6.10.1
   - Plugin muss mit gleicher Qt-Version gebaut werden
   - **Fix:** Qt 6.10.1 installieren und verwenden

3. **Fehlende Abhängigkeiten:**
   - Qt6-DLLs fehlen im Scribus-Verzeichnis
   - **Fix:** DLLs kopieren oder statisch linken

### Build-Fehler

#### Linker-Fehler: Unresolved Symbols

**Problem:**
```
error LNK2019: unresolved external symbol
```

**Lösung:**
- Für Test-Builds: `/FORCE:UNRESOLVED` verwenden (nur zum Testen!)
- Für Production: Alle Abhängigkeiten korrekt linken

#### MOC-Fehler: Q_OBJECT nicht gefunden

**Problem:**
```
error: undefined reference to `vtable for GammaDashboardPlugin`
```

**Lösung:**
- `CMAKE_AUTOMOC ON` in CMakeLists.txt
- Oder MOC-Dateien manuell zu `gamma_dashboard.vcxproj` hinzufügen

#### Fehlende Header

**Problem:**
```
error C1083: Cannot open include file: 'pluginapi.h'
```

**Lösung:**
- Include-Pfade in `gamma_dashboard.vcxproj` prüfen
- `SCRIBUS_INCLUDE_DIR` muss auf `C:\Development\scribus-1.7\scribus` zeigen

#### Debug-Build (MSVC) schlägt mit LNK2038 / fehlenden *_d.lib fehl

Wenn du den **Scribus-Debug** Build gegen das **Libs-Kit** baust, fehlen oft echte Debug-Libs (oder sie sind Release gebaut). Dann bekommst du typischerweise:
- `LNK2038 _ITERATOR_DEBUG_LEVEL / RuntimeLibrary`
- `LNK1104 ...*_d.lib kann nicht geöffnet werden`

**Empfehlung: FastDebug aktivieren (Debug-Konfiguration, aber Release-CRT + Release-Dependencies):**

```powershell
# einmalig (persistiert): 
setx SCRIBUS_FASTDEBUG 1

# oder nur für die aktuelle Session:
$env:SCRIBUS_FASTDEBUG = 1
```

Dann in Visual Studio **einmal** `Clean`/`Rebuild` (oder `msbuild ... /t:Clean;Build`) damit alle internen Libs neu erzeugt werden.

---

## ✅ Best Practices

### 1. Plugin-Lebenszyklus

```cpp
// Constructor: Minimale Initialisierung
GammaDashboardPlugin::GammaDashboardPlugin()
    : ScPlugin()
{
    // Nur Member-Variablen initialisieren
    // Keine komplexe Objekterstellung hier
}

// addToMainWindowMenu: UI-Initialisierung
void GammaDashboardPlugin::addToMainWindowMenu(ScribusMainWindow* mw)
{
    // Menü-Einträge erstellen
    // Dock-Widget wird lazy erstellt (in toggleDashboard())
}

// cleanupPlugin: Saubere Bereinigung
bool GammaDashboardPlugin::cleanupPlugin()
{
    // Timers stoppen
    // Netzwerk-Verbindungen trennen
    // Dock-Widget sofort löschen (nicht deleteLater!)
    if (m_dock) {
        delete m_dock;  // Nicht deleteLater()!
        m_dock = nullptr;
    }
    return true;
}
```

### 2. Menü-Integration

```cpp
// Robuste Menü-Erstellung mit Fallback
QMenu* menu = ensureMenu(bar, QStringList() << "Extras");
if (!menu) {
    // Fallback 1: Versuche "Extras" -> "Tools"
    menu = ensureMenu(bar, QStringList() << "Extras" << "Tools");
}
if (!menu) {
    // Fallback 2: Erstelle eigenes Menü
    menu = bar->addMenu(tr("Gamma Dashboard"));
}
```

### 3. Dock-Widget Management

```cpp
// Dock-Widget lazy erstellen
void toggleDashboard()
{
    if (!m_dock) {
        m_dock = new GammaDashboardDock(mainWindow);
        mainWindow->addDockWidget(Qt::RightDockWidgetArea, m_dock);
        // Signale verbinden
    }
    m_dock->setVisible(!m_dock->isVisible());
}

// QPointer verwenden für automatische Null-Checks
QPointer<GammaDashboardDock> m_dock = nullptr;
```

### 4. Settings Management

```cpp
// QSettings für persistente Konfiguration
void loadSettings()
{
    QSettings settings;
    settings.beginGroup("GammaDashboard");
    m_baseUrl = settings.value("baseUrl", "http://localhost:8003").toString();
    
    // Environment variable has priority
    QString envUrl = qEnvironmentVariable("GAMMA_BASE_URL");
    if (!envUrl.isEmpty())
        m_baseUrl = envUrl;
    m_apiKey = settings.value("apiKey", "").toString();
    settings.endGroup();
}

// Environment-Variablen haben Vorrang
QString envUrl = qEnvironmentVariable("GAMMA_BASE_URL");
if (!envUrl.isEmpty())
    m_baseUrl = envUrl;
```

### 5. Error Handling

```cpp
// Try-Catch in Export-Funktionen
extern "C" PLUGIN_API ScPlugin* gamma_dashboard_getPlugin()
{
    try {
        return new GammaDashboardPlugin();
    } catch (...) {
        // Bei Fehlern nullptr zurückgeben
        return nullptr;
    }
}

// QPointer für Null-Checks
if (!m_dock) return;  // Sicherheits-Check vor UI-Updates
```

---

## 🐛 Häufige Probleme

### Problem 1: "DLL wird von einem anderen Prozess verwendet"

**Ursache:** Scribus läuft noch

**Lösung:**
```powershell
# Prüfe ob Scribus läuft
Get-Process -Name "scribus" -ErrorAction SilentlyContinue

# Beende alle Scribus-Prozesse
Get-Process -Name "scribus" | Stop-Process -Force

# Warte kurz
Start-Sleep -Seconds 2

# Dann installieren
```

### Problem 2: "Plugin wird geladen, aber nicht angezeigt"

**Ursache:** `addToMainWindowMenu()` wird nicht aufgerufen oder Menü-Erstellung schlägt fehl

**Lösung:**
- Debug-Log prüfen
- Menü direkt unter "Extras" hinzufügen (nicht Untermenü)
- Fallback-Mechanismus implementieren

### Problem 3: "Plugin crash beim Start"

**Ursache:** Runtime-Library oder Qt-Version Mismatch

**Lösung:**
- Runtime-Library prüfen: `/MD` muss überall verwendet werden
- Qt-Version prüfen: Muss mit Scribus-Version übereinstimmen (6.10.1)

### Problem 4: "Export-Funktionen nicht gefunden"

**Ursache:** Falscher Funktionsname oder fehlender `extern "C"`

**Lösung:**
```cpp
// Korrekt:
extern "C" PLUGIN_API int gamma_dashboard_getPluginAPIVersion()

// Pattern: <pluginname>_getPluginAPIVersion
// Pattern: <pluginname>_getPlugin
// Pattern: <pluginname>_freePlugin
```

### Problem 5: "MOC-Dateien werden nicht generiert"

**Ursache:** `CMAKE_AUTOMOC` nicht aktiviert oder MOC-Dateien fehlen im Projekt

**Lösung:**
- CMake: `set(CMAKE_AUTOMOC ON)`
- VS Solution: MOC-Dateien zu `gamma_dashboard.vcxproj` hinzufügen

### Problem 6: "Alte Version wird gebaut trotz Änderungen"

**Ursache:** Kein Clean durchgeführt - alte Objektdateien werden wiederverwendet

**Symptome:**
- Code wurde geändert, aber Plugin-Verhalten ändert sich nicht
- Objektdateien haben unterschiedliche Zeitstempel (alte + neue gemischt)

**Lösung:**
```powershell
# Clean durchführen VOR dem Build
msbuild Scribus.sln /t:gamma_dashboard:Clean /p:Configuration=Release /p:Platform=x64 /v:minimal

# Dann bauen
msbuild Scribus.sln /t:gamma_dashboard /p:Configuration=Release /p:Platform=x64 /m:1 /v:minimal
```

**Oder:** Verwende `rebuild_and_install.ps1` - führt automatisch Clean durch!

---

## 🔄 Workflow: Änderung → Test

### Automatisiertes Script (Empfohlen)

```powershell
cd 'gamma_scribus_pack\plugin\cpp'
.\rebuild_and_install.ps1
```

**Das Script macht automatisch:**
1. ✅ Clean Build-Verzeichnis (löscht alte Objektdateien)
2. ✅ Clean Project (MSBuild Clean)
3. ✅ Plugin neu bauen
4. ✅ Scribus automatisch beenden
5. ✅ Backup der alten Version erstellen
6. ✅ Neue Version installieren

### Manueller Workflow

### 1. Code ändern

```cpp
// In gamma_dashboard_plugin.cpp ändern
// ...
```

**WICHTIG:** Kopiere Änderungen in Scribus Source Tree:
```powershell
# Automatisch mit Script:
.\UPDATE_SCRIBUS_SOURCE.ps1

# Oder manuell:
Copy-Item 'gamma_scribus_pack\plugin\cpp\src\gamma_*.cpp' -Destination 'C:\Development\scribus-1.7\scribus\plugins\gamma_dashboard\' -Force
Copy-Item 'gamma_scribus_pack\plugin\cpp\src\gamma_*.h' -Destination 'C:\Development\scribus-1.7\scribus\plugins\gamma_dashboard\' -Force
Copy-Item 'gamma_scribus_pack\plugin\cpp\src\CMakeLists.txt' -Destination 'C:\Development\scribus-1.7\scribus\plugins\gamma_dashboard\CMakeLists.txt' -Force
```

### 2. Clean & Build

```powershell
cd C:\Development\scribus-1.7\win32\msvc2022

# Clean (WICHTIG - verhindert Wiederverwendung alter Objektdateien!)
msbuild Scribus.sln /t:gamma_dashboard:Clean /p:Configuration=Release /p:Platform=x64 /v:minimal

# Build
msbuild Scribus.sln /t:gamma_dashboard /p:Configuration=Release /p:Platform=x64 /m:1 /v:minimal
```

### 3. Scribus schließen

```powershell
Get-Process -Name "scribus" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
```

### 4. Plugin installieren

```powershell
Copy-Item 'C:\Development\Scribus-builds\Scribus-Release-x64-v143\plugins\gamma_dashboard.dll' -Destination 'C:\Program Files\Scribus 1.7.1(1)\plugins\gamma_dashboard.dll' -Force
```

### 5. Scribus starten und testen

```powershell
Start-Process "C:\Program Files\Scribus 1.7.1(1)\scribus.exe"
```

---

## 📝 Checkliste: Neues Feature hinzufügen

- [ ] Code in Workspace-Verzeichnis ändern (`gamma_scribus_pack/plugin/cpp/`)
- [ ] Änderungen in Scribus Source Tree kopieren (`C:\Development\scribus-1.7\scribus\plugins\gamma_dashboard\`)
  - **Script:** `.\UPDATE_SCRIBUS_SOURCE.ps1`
- [ ] Projekt-Datei aktualisieren (falls neue Dateien: `gamma_dashboard.vcxproj`)
- [ ] **Clean durchführen** (wichtig!)
  - `msbuild ... /t:gamma_dashboard:Clean ...`
- [ ] Plugin neu bauen
- [ ] Scribus schließen
- [ ] Plugin installieren (als Administrator)
- [ ] Scribus starten und testen
- [ ] Debug-Log prüfen (falls Probleme)

**Oder einfach:** `.\rebuild_and_install.ps1` (macht alles automatisch!)

---

## 📚 Weitere Ressourcen

- **Scribus Plugin API:** `C:\Development\scribus-1.7\scribus\scplugin.h`
- **Plugin Examples:** `C:\Development\scribus-1.7\scribus\plugins\`
- **Qt Documentation:** https://doc.qt.io/qt-6/

---

**Letzte Aktualisierung:** 2026-01-06  
**Scribus Version:** 1.7.1  
**Qt Version:** 6.10.1  
**Visual Studio:** 2022 (v143)

