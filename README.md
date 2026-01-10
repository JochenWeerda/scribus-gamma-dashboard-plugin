# Gamma Dashboard Plugin for Scribus - AI-Powered Publishing Pipeline

[![Scribus](https://img.shields.io/badge/Scribus-1.7.1+-blue.svg)](https://www.scribus.net/)
[![Qt](https://img.shields.io/badge/Qt-6.10.1-green.svg)](https://www.qt.io/)
[![License](https://img.shields.io/badge/License-GPL--2.0-orange.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![AI-Powered](https://img.shields.io/badge/AI-Powered-purple.svg)](https://github.com/JochenWeerda/scribus-gamma-dashboard-plugin)

**A revolutionary AI-powered native C++ plugin for Scribus** that provides an intelligent dockable dashboard panel for monitoring and controlling automated publishing pipelines with real-time AI-assisted layout validation, asset quality analysis, and intelligent workflow automation.

---

**Ein revolution├ñres KI-gest├╝tztes natives C++-Plugin f├╝r Scribus**, das ein intelligentes dockbares Dashboard-Panel zur ├£berwachung und Steuerung automatisierter Publishing-Pipelines mit Echtzeit-KI-gest├╝tzter Layout-Validierung, Asset-Qualit├ñtsanalyse und intelligenter Workflow-Automatisierung bereitstellt.

---

## Table of Contents / Inhaltsverzeichnis

- [English](#english) | [Deutsch](#deutsch)

---

# English

## ­ƒÄ» Overview

The **Gamma Dashboard Plugin** integrates seamlessly into Scribus 1.7.1+ and provides a **revolutionary AI-powered publishing pipeline** with:

- **­ƒñû AI-Powered Real-time Pipeline Monitoring** - Intelligent tracking and optimization of automated publishing workflows
- **­ƒºá AI-Assisted Layout Audit** - Advanced Z-order validation, overlap detection, and AI-driven asset quality analysis
- **­ƒôè Intelligent Asset Validator** - AI-enhanced progress tracking for asset validation and automated text fit analysis
- **Ôÿü´©Å Cloud Synchronization** - Seamless sync to AI-enhanced cloud storage with intelligent conflict resolution
- **ÔÜí Batch Rendering** - Headless PDF rendering with AI-optimized quality presets
- **­ƒÄ» Smart Manual Override** - AI-assisted layer management and intelligent document manipulation tools

## Ô£¿ Features

### Current Implementation

- Ô£à Native C++/Qt plugin (no Python dependencies)
- Ô£à Dockable panel integrated into Scribus UI
- Ô£à Mock mode for testing and demonstration
- Ô£à Real-time status updates with visual indicators
- Ô£à Progress tracking for multiple workflows
- Ô£à Log viewer with auto-scroll functionality
- Ô£à Dark theme UI matching modern design standards

### Backend Status

- Ô£à **Backend API server** - Docker-based backend with API endpoints
- Ô£à **API endpoints implemented** - Status, Pipeline, Assets, Layout audit
- ­ƒöä **Plugin-to-Backend integration** - Currently mock mode, backend connection pending
- ­ƒöä **Authentication** - API key management for backend connection

### Planned Features

- ­ƒöä Connect plugin to existing backend API
- ­ƒöä Cloud synchronization (backend ready)
- ­ƒöä Batch PDF rendering (backend ready)
- ­ƒöä Layer management tools (Scribus API integration)
- ­ƒöä Advanced layout auditing (backend ready, integration pending)

## ­ƒôï Requirements

### Build Requirements

- **Windows 10/11** (x64)
- **Visual Studio 2022** (v143 toolset) or Build Tools
- **Qt 6.10.1** (msvc2022_64)
- **Scribus 1.7.1+** source code
- **Scribus Libs Kit** (from SourceForge)

### Runtime Requirements

- **Scribus 1.7.1+** installed
- **Windows 10/11** (x64)

## ­ƒÜÇ Building

### Prerequisites

1. **Install Qt 6.10.1:**
   - Download from [Qt Official](https://www.qt.io/)
   - Install Qt 6.10.1 for MSVC 2022 64-bit
   - Install Qt 5 Compatibility Module

2. **Download Scribus Source:**
   ```bash
   git clone https://github.com/scribusproject/scribus.git
   cd scribus
   git checkout 1.7.1  # or master for latest
   ```

3. **Download Scribus Libs Kit:**
   - Download from [Scribus SourceForge](https://sourceforge.net/projects/scribus/files/)
   - Extract to `C:\Development\scribus-1.7.x-libs-msvc`
   - Build the libraries (Release, x64)

### Build Instructions

#### Option 1: Visual Studio Solution (Recommended)

1. **Open Visual Studio Solution:**
   ```
   C:\Development\scribus-1.7\win32\msvc2022\Scribus.sln
   ```

2. **Configure Property Sheets:**
   - Edit `Scribus-build-props.props`
   - Set `SCRIBUS_LIB_ROOT` to your Libs Kit path
   - Set `QT6_DIR` to your Qt 6.10.1 installation

3. **Build:**
   - Select Configuration: **Release**
   - Select Platform: **x64**
   - Build Solution (F7)

4. **Output:**
   - Plugin DLL: `C:\Development\Scribus-builds\Scribus-Release-x64-v143\plugins\gamma_dashboard.dll`

## ­ƒôª Installation

### Automatic Installation (PowerShell)

```powershell
# Requires Administrator privileges
.\COPY_TO_INSTALLED.ps1
```

### Manual Installation

1. **Copy Plugin DLL:**
   ```
   Copy: gamma_dashboard.dll
   To: C:\Program Files\Scribus 1.7.1\plugins\
   ```

2. **Copy Dependencies:**
   - Qt6 DLLs (Qt6Core.dll, Qt6Gui.dll, Qt6Widgets.dll, Qt6Network.dll)
   - Qt Platform Plugin (platforms\qwindows.dll)
   - Other dependencies from Scribus installation

3. **Restart Scribus**

## ­ƒÄ« Usage

1. **Start Scribus**

2. **Open Plugin:**
   - Menu: **Extras ÔåÆ Gamma Dashboard**
   - Or use keyboard shortcut: **Ctrl+Shift+G**

3. **Dock Panel:**
   - The dashboard appears as a dockable panel (default: right side)
   - Can be docked to left, right, or floating

4. **Monitor Pipeline:**
   - View real-time status and progress
   - Check AI-powered layout audit results
   - Monitor asset validation progress

## ­ƒô© Screenshots

### Current Implementation / Aktueller Stand

![Current Status](screenshots/gamma_dashboard_current.png)

**Current Status / Aktueller Stand:**
The Gamma Dashboard Plugin running in Scribus 1.7.2.svn, showing:
- Ô£à **Connected Status** - Green indicator showing "Connected (42 ms)"
- Ô£à **Pipeline Control** - Pipeline dropdown with Start/Stop buttons and 75% progress
- Ô£à **Layout Audit** - Z-Order Guard and No Overlaps validated, with warning for 2 low-res images
- Ô£à **Asset Validator** - Asset progress at 97%, Text Fit at 13%
- Ô£à **Log Viewer** - Real-time mock status updates with auto-scroll enabled
- Ô£à **Dark Theme UI** - Modern interface matching Scribus aesthetics

**Aktueller Stand:**
Das Gamma Dashboard Plugin l├ñuft in Scribus 1.7.2.svn und zeigt:
- Ô£à **Verbindungsstatus** - Gr├╝ner Indikator zeigt "Connected (42 ms)"
- Ô£à **Pipeline-Steuerung** - Pipeline-Dropdown mit Start/Stop-Buttons und 75% Fortschritt
- Ô£à **Layout-├£berpr├╝fung** - Z-Order Guard und No Overlaps validiert, Warnung f├╝r 2 niedrigaufl├Âsende Bilder
- Ô£à **Asset-Validator** - Asset-Fortschritt bei 97%, Text Fit bei 13%
- Ô£à **Log-Viewer** - Echtzeit-Mock-Status-Updates mit aktiviertem Auto-Scroll
- Ô£à **Dark Theme UI** - Moderne Oberfl├ñche passend zur Scribus-├ästhetik

---

### Design Vision with AI Integration / Designentwurf mit KI-Integration

![AI Integration Design](screenshots/mcp_ai_dashboard_design.png)

**Design Vision with AI Integration / Designentwurf mit KI-Integration:**
Future vision showing advanced AI-powered features:
- ­ƒñû **AI-Powered Font Analysis** - Intelligent font checking and optimization (e.g., "Checking fonts...")
- ­ƒºá **Smart Layout Analysis** - Advanced AI-driven layout validation with intelligent warnings
- ­ƒôè **Intelligent Asset Validation** - AI-enhanced text fit analysis reaching 98% optimization
- Ôÿü´©Å **Cloud Integration** - Seamless AI-enhanced cloud synchronization ready
- ÔÜí **Batch Processing** - AI-optimized batch rendering capabilities for PDF export
- ­ƒÄ» **Context-Aware Assistance** - AI-powered manual override with intelligent layer management suggestions

**Designentwurf mit KI-Integration:**
Zukunfts-Vision mit erweiterten KI-gest├╝tzten Features:
- ­ƒñû **KI-gest├╝tzte Font-Analyse** - Intelligente Schriftpr├╝fung und Optimierung (z.B. "Checking fonts...")
- ­ƒºá **Intelligente Layout-Analyse** - Erweiterte KI-gest├╝tzte Layout-Validierung mit intelligenten Warnungen
- ­ƒôè **Intelligenter Asset-Validator** - KI-gest├╝tzte Textfit-Analyse erreicht 98% Optimierung
- Ôÿü´©Å **Cloud-Integration** - Nahtlose KI-gest├╝tzte Cloud-Synchronisation bereit
- ÔÜí **Batch-Verarbeitung** - KI-optimierte Batch-Rendering-F├ñhigkeiten f├╝r PDF-Export
- ­ƒÄ» **Kontextbewusste Unterst├╝tzung** - KI-gest├╝tzte manuelle ├£berschreibung mit intelligenten Layer-Management-Vorschl├ñgen

---

## ­ƒÅù´©Å Architecture

### Plugin Structure

```
gamma_dashboard/
Ôö£ÔöÇÔöÇ gamma_dashboard_plugin.h/cpp    # Main plugin class (ScActionPlugin)
Ôö£ÔöÇÔöÇ gamma_dashboard_dock.h/cpp      # Dock widget UI (QWidget)
Ôö£ÔöÇÔöÇ gamma_dashboard_exports.cpp     # C-ABI export functions
ÔööÔöÇÔöÇ CMakeLists.txt                  # Build configuration
```

### Key Components

- **GammaDashboardPlugin** - Main plugin class inheriting from `ScActionPlugin`
- **GammaDashboardDock** - UI widget inheriting from `QWidget`
- **Export Functions** - C-ABI exports required by Scribus plugin system

## ­ƒöº Configuration

### Environment Variables

- `GAMMA_BASE_URL` - AI API endpoint URL (default: `http://localhost:8000`)
- `GAMMA_API_KEY` - API authentication key

### Mock Mode

The plugin runs in mock mode by default for testing. To enable real AI API:

1. Set environment variables
2. Modify plugin source to disable mock mode
3. Rebuild plugin

## ­ƒôØ Development

### Code Style

- Follow Scribus coding conventions
- Use Qt-style naming (camelCase for methods, m_ prefix for members)
- Use `tr()` for all user-visible strings
- Comment complex logic

## ­ƒôä License

This plugin is licensed under the **GPL v2** (or later), matching Scribus's license.

## ­ƒæñ Author

**Jochen Weerda**
- Email: jochen.weerda@gmail.com
- GitHub: [@JochenWeerda](https://github.com/JochenWeerda)

## ­ƒÖÅ Acknowledgments

- **Scribus Development Team** - For the excellent plugin API and documentation
- **Qt Project** - For the powerful Qt framework
- **MCP Dashboard Plugin** - Inspiration for the dock widget pattern

---

# Deutsch

## ­ƒÄ» ├£bersicht

Das **Gamma Dashboard Plugin** integriert sich nahtlos in Scribus 1.7.1+ und bietet eine **revolution├ñre KI-gest├╝tzte Publishing-Pipeline** mit:

- **­ƒñû KI-gest├╝tztes Echtzeit-Pipeline-Monitoring** - Intelligente Verfolgung und Optimierung automatisierter Publishing-Workflows
- **­ƒºá KI-gest├╝tzte Layout-├£berpr├╝fung** - Erweiterte Z-Order-Validierung, Overlap-Erkennung und KI-gest├╝tzte Asset-Qualit├ñtsanalyse
- **­ƒôè Intelligenter Asset-Validator** - KI-gest├╝tztes Fortschritts-Tracking f├╝r Asset-Validierung und automatisierte Textfit-Analyse
- **Ôÿü´©Å Cloud-Synchronisation** - Nahtlose Synchronisation mit KI-gest├╝tztem Cloud-Speicher und intelligenter Konfliktl├Âsung
- **ÔÜí Batch-Rendering** - Headless PDF-Rendering mit KI-optimierten Qualit├ñtsvoreinstellungen
- **­ƒÄ» Intelligente manuelle ├£berschreibung** - KI-gest├╝tztes Layer-Management und intelligente Dokumentmanipulation

## Ô£¿ Features

### Aktuelle Implementierung

- Ô£à Natives C++/Qt-Plugin (keine Python-Abh├ñngigkeiten)
- Ô£à Dockbares Panel in Scribus UI integriert
- Ô£à Mock-Modus f├╝r Tests und Demonstrationen
- Ô£à Echtzeit-Status-Updates mit visuellen Indikatoren
- Ô£à Fortschritts-Tracking f├╝r mehrere Workflows
- Ô£à Log-Viewer mit Auto-Scroll-Funktionalit├ñt
- Ô£à Dark-Theme UI im modernen Design-Standard

### Backend-Status

- Ô£à **Backend-API-Server** - Docker-basiertes Backend mit API-Endpunkten
- Ô£à **API-Endpunkte implementiert** - Status, Pipeline, Assets, Layout-Audit
- ­ƒöä **Plugin-zu-Backend-Integration** - Aktuell Mock-Modus, Backend-Verbindung ausstehend
- ­ƒöä **Authentifizierung** - API-Key-Management f├╝r Backend-Verbindung

### Geplante Features

- ­ƒöä Plugin mit vorhandenem Backend-API verbinden
- ­ƒöä Cloud-Synchronisation (Backend bereit)
- ­ƒöä Batch PDF-Rendering (Backend bereit)
- ­ƒöä Layer-Management-Tools (Scribus API-Integration)
- ­ƒöä Erweiterte Layout-├£berpr├╝fung (Backend bereit, Integration ausstehend)

## ­ƒôï Anforderungen

### Build-Anforderungen

- **Windows 10/11** (x64)
- **Visual Studio 2022** (v143 Toolset) oder Build Tools
- **Qt 6.10.1** (msvc2022_64)
- **Scribus 1.7.1+** Quellcode
- **Scribus Libs Kit** (von SourceForge)

### Laufzeit-Anforderungen

- **Scribus 1.7.1+** installiert
- **Windows 10/11** (x64)

## ­ƒÜÇ Build

### Voraussetzungen

1. **Qt 6.10.1 installieren:**
   - Download von [Qt Official](https://www.qt.io/)
   - Qt 6.10.1 f├╝r MSVC 2022 64-bit installieren
   - Qt 5 Kompatibilit├ñtsmodul installieren

2. **Scribus Quellcode herunterladen:**
   ```bash
   git clone https://github.com/scribusproject/scribus.git
   cd scribus
   git checkout 1.7.1  # oder master f├╝r neueste Version
   ```

3. **Scribus Libs Kit herunterladen:**
   - Download von [Scribus SourceForge](https://sourceforge.net/projects/scribus/files/)
   - Extrahiere nach `C:\Development\scribus-1.7.x-libs-msvc`
   - Bibliotheken bauen (Release, x64)

### Build-Anleitung

#### Option 1: Visual Studio Solution (Empfohlen)

1. **Visual Studio Solution ├Âffnen:**
   ```
   C:\Development\scribus-1.7\win32\msvc2022\Scribus.sln
   ```

2. **Property Sheets konfigurieren:**
   - Bearbeite `Scribus-build-props.props`
   - Setze `SCRIBUS_LIB_ROOT` auf deinen Libs Kit-Pfad
   - Setze `QT6_DIR` auf deine Qt 6.10.1 Installation

3. **Build:**
   - Konfiguration w├ñhlen: **Release**
   - Plattform w├ñhlen: **x64**
   - Solution bauen (F7)

4. **Output:**
   - Plugin DLL: `C:\Development\Scribus-builds\Scribus-Release-x64-v143\plugins\gamma_dashboard.dll`

## ­ƒôª Installation

### Automatische Installation (PowerShell)

```powershell
# Ben├Âtigt Administrator-Rechte
.\COPY_TO_INSTALLED.ps1
```

### Manuelle Installation

1. **Plugin DLL kopieren:**
   ```
   Kopiere: gamma_dashboard.dll
   Nach: C:\Program Files\Scribus 1.7.1\plugins\
   ```

2. **Abh├ñngigkeiten kopieren:**
   - Qt6 DLLs (Qt6Core.dll, Qt6Gui.dll, Qt6Widgets.dll, Qt6Network.dll)
   - Qt Platform Plugin (platforms\qwindows.dll)
   - Andere Abh├ñngigkeiten von der Scribus-Installation

3. **Scribus neu starten**

## ­ƒÄ« Verwendung

1. **Scribus starten**

2. **Plugin ├Âffnen:**
   - Men├╝: **Extras ÔåÆ Gamma Dashboard**
   - Oder Tastenkombination: **Strg+Umschalt+G**

3. **Panel docken:**
   - Das Dashboard erscheint als dockbares Panel (Standard: rechts)
   - Kann links, rechts oder schwebend gedockt werden

4. **Pipeline ├╝berwachen:**
   - Echtzeit-Status und Fortschritt anzeigen
   - KI-gest├╝tzte Layout-├£berpr├╝fungsergebnisse pr├╝fen
   - Asset-Validierungsfortschritt ├╝berwachen

## ­ƒÅù´©Å Architektur

### Plugin-Struktur

```
gamma_dashboard/
Ôö£ÔöÇÔöÇ gamma_dashboard_plugin.h/cpp    # Haupt-Plugin-Klasse (ScActionPlugin)
Ôö£ÔöÇÔöÇ gamma_dashboard_dock.h/cpp      # Dock-Widget UI (QWidget)
Ôö£ÔöÇÔöÇ gamma_dashboard_exports.cpp     # C-ABI Export-Funktionen
ÔööÔöÇÔöÇ CMakeLists.txt                  # Build-Konfiguration
```

### Wichtige Komponenten

- **GammaDashboardPlugin** - Haupt-Plugin-Klasse, erbt von `ScActionPlugin`
- **GammaDashboardDock** - UI-Widget, erbt von `QWidget`
- **Export-Funktionen** - C-ABI Exports, die vom Scribus Plugin-System ben├Âtigt werden

## ­ƒöº Konfiguration

### Umgebungsvariablen

- `GAMMA_BASE_URL` - KI-API-Endpunkt-URL (Standard: `http://localhost:8000`)
- `GAMMA_API_KEY` - API-Authentifizierungsschl├╝ssel

### Mock-Modus

Das Plugin l├ñuft standardm├ñ├ƒig im Mock-Modus f├╝r Tests. Um die echte KI-API zu aktivieren:

1. Umgebungsvariablen setzen
2. Plugin-Quellcode ├ñndern, um Mock-Modus zu deaktivieren
3. Plugin neu bauen

## ­ƒôØ Entwicklung

### Code-Stil

- Folge Scribus Coding-Konventionen
- Verwende Qt-Stil-Namensgebung (camelCase f├╝r Methoden, m_-Pr├ñfix f├╝r Member)
- Verwende `tr()` f├╝r alle benutzer-sichtbaren Strings
- Kommentiere komplexe Logik

## ­ƒôä Lizenz

Dieses Plugin ist unter der **GPL v2** (oder h├Âher) lizenziert, passend zur Scribus-Lizenz.

## ­ƒæñ Autor

**Jochen Weerda**
- E-Mail: jochen.weerda@gmail.com
- GitHub: [@JochenWeerda](https://github.com/JochenWeerda)

## ­ƒÖÅ Danksagungen

- **Scribus Entwicklerteam** - F├╝r die hervorragende Plugin-API und Dokumentation
- **Qt-Projekt** - F├╝r das leistungsstarke Qt-Framework
- **MCP Dashboard Plugin** - Inspiration f├╝r das Dock-Widget-Pattern

---

## ­ƒôÜ Resources / Ressourcen

- [Scribus Documentation](https://wiki.scribus.net/) | [Scribus Dokumentation](https://wiki.scribus.net/)
- [Scribus Plugin API](https://wiki.scribus.net/canvas/Plugin_API) | [Scribus Plugin API](https://wiki.scribus.net/canvas/Plugin_API)
- [Qt Documentation](https://doc.qt.io/) | [Qt Dokumentation](https://doc.qt.io/)
- [Scribus Forums](https://forums.scribus.net/) | [Scribus Foren](https://forums.scribus.net/)

## ­ƒôè Status

**Current Version / Aktuelle Version:** 1.0.0 (Alpha)  
**Status:** ­ƒÜº Early Development - UI Complete, Features in Progress / Fr├╝he Entwicklung - UI vollst├ñndig, Features in Arbeit  
**Scribus Compatibility / Scribus-Kompatibilit├ñt:** 1.7.1+  
**Platform / Plattform:** Windows x64

**Note / Hinweis:** This is an early alpha release. The UI is fully functional with mock data. Real API integration and backend features are planned for future releases.  
Dies ist eine fr├╝he Alpha-Version. Die UI funktioniert vollst├ñndig mit Mock-Daten. Echte API-Integration und Backend-Features sind f├╝r zuk├╝nftige Releases geplant.  

---

**Note / Hinweis:** This is an independent plugin and is not officially endorsed by the Scribus project.  
Dies ist ein unabh├ñngiges Plugin und wird nicht offiziell vom Scribus-Projekt unterst├╝tzt.
