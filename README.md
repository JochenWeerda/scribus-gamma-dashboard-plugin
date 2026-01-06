# Gamma Dashboard Plugin for Scribus - AI-Powered Publishing Pipeline

[![Scribus](https://img.shields.io/badge/Scribus-1.7.1+-blue.svg)](https://www.scribus.net/)
[![Qt](https://img.shields.io/badge/Qt-6.10.1-green.svg)](https://www.qt.io/)
[![License](https://img.shields.io/badge/License-GPL--2.0-orange.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![AI-Powered](https://img.shields.io/badge/AI-Powered-purple.svg)](https://github.com/JochenWeerda/scribus-gamma-dashboard-plugin)

**A revolutionary AI-powered native C++ plugin for Scribus** that provides an intelligent dockable dashboard panel for monitoring and controlling automated publishing pipelines with real-time AI-assisted layout validation, asset quality analysis, and intelligent workflow automation.

---

**Ein revolutionäres KI-gestütztes natives C++-Plugin für Scribus**, das ein intelligentes dockbares Dashboard-Panel zur Überwachung und Steuerung automatisierter Publishing-Pipelines mit Echtzeit-KI-gestützter Layout-Validierung, Asset-Qualitätsanalyse und intelligenter Workflow-Automatisierung bereitstellt.

---

## Table of Contents / Inhaltsverzeichnis

- [English](#english) | [Deutsch](#deutsch)

---

# English

## 🎯 Overview

The **Gamma Dashboard Plugin** integrates seamlessly into Scribus 1.7.1+ and provides a **revolutionary AI-powered publishing pipeline** with:

- **🤖 AI-Powered Real-time Pipeline Monitoring** - Intelligent tracking and optimization of automated publishing workflows
- **🧠 AI-Assisted Layout Audit** - Advanced Z-order validation, overlap detection, and AI-driven asset quality analysis
- **📊 Intelligent Asset Validator** - AI-enhanced progress tracking for asset validation and automated text fit analysis
- **☁️ Cloud Synchronization** - Seamless sync to AI-enhanced cloud storage with intelligent conflict resolution
- **⚡ Batch Rendering** - Headless PDF rendering with AI-optimized quality presets
- **🎯 Smart Manual Override** - AI-assisted layer management and intelligent document manipulation tools

## ✨ Features

### Current Implementation

- ✅ Native C++/Qt plugin (no Python dependencies)
- ✅ Dockable panel integrated into Scribus UI
- ✅ Mock mode for testing and demonstration
- ✅ Real-time status updates with visual indicators
- ✅ Progress tracking for multiple workflows
- ✅ Log viewer with auto-scroll functionality
- ✅ Dark theme UI matching modern design standards

### Planned Features

- 🔄 Real AI API integration (currently mock mode)
- 🔄 Cloud synchronization endpoints with AI optimization
- 🔄 Batch PDF rendering with AI quality presets
- 🔄 Layer management tools with AI assistance
- 🔄 Advanced AI-powered layout auditing

## 📋 Requirements

### Build Requirements

- **Windows 10/11** (x64)
- **Visual Studio 2022** (v143 toolset) or Build Tools
- **Qt 6.10.1** (msvc2022_64)
- **Scribus 1.7.1+** source code
- **Scribus Libs Kit** (from SourceForge)

### Runtime Requirements

- **Scribus 1.7.1+** installed
- **Windows 10/11** (x64)

## 🚀 Building

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

## 📦 Installation

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

## 🎮 Usage

1. **Start Scribus**

2. **Open Plugin:**
   - Menu: **Extras → Gamma Dashboard**
   - Or use keyboard shortcut: **Ctrl+Shift+G**

3. **Dock Panel:**
   - The dashboard appears as a dockable panel (default: right side)
   - Can be docked to left, right, or floating

4. **Monitor Pipeline:**
   - View real-time status and progress
   - Check AI-powered layout audit results
   - Monitor asset validation progress

## 🏗️ Architecture

### Plugin Structure

```
gamma_dashboard/
├── gamma_dashboard_plugin.h/cpp    # Main plugin class (ScActionPlugin)
├── gamma_dashboard_dock.h/cpp      # Dock widget UI (QWidget)
├── gamma_dashboard_exports.cpp     # C-ABI export functions
└── CMakeLists.txt                  # Build configuration
```

### Key Components

- **GammaDashboardPlugin** - Main plugin class inheriting from `ScActionPlugin`
- **GammaDashboardDock** - UI widget inheriting from `QWidget`
- **Export Functions** - C-ABI exports required by Scribus plugin system

## 🔧 Configuration

### Environment Variables

- `GAMMA_BASE_URL` - AI API endpoint URL (default: `http://localhost:8000`)
- `GAMMA_API_KEY` - API authentication key

### Mock Mode

The plugin runs in mock mode by default for testing. To enable real AI API:

1. Set environment variables
2. Modify plugin source to disable mock mode
3. Rebuild plugin

## 📝 Development

### Code Style

- Follow Scribus coding conventions
- Use Qt-style naming (camelCase for methods, m_ prefix for members)
- Use `tr()` for all user-visible strings
- Comment complex logic

## 📄 License

This plugin is licensed under the **GPL v2** (or later), matching Scribus's license.

## 👤 Author

**Jochen Weerda**
- Email: jochen.weerda@gmail.com
- GitHub: [@JochenWeerda](https://github.com/JochenWeerda)

## 🙏 Acknowledgments

- **Scribus Development Team** - For the excellent plugin API and documentation
- **Qt Project** - For the powerful Qt framework
- **MCP Dashboard Plugin** - Inspiration for the dock widget pattern

---

# Deutsch

## 🎯 Übersicht

Das **Gamma Dashboard Plugin** integriert sich nahtlos in Scribus 1.7.1+ und bietet eine **revolutionäre KI-gestützte Publishing-Pipeline** mit:

- **🤖 KI-gestütztes Echtzeit-Pipeline-Monitoring** - Intelligente Verfolgung und Optimierung automatisierter Publishing-Workflows
- **🧠 KI-gestützte Layout-Überprüfung** - Erweiterte Z-Order-Validierung, Overlap-Erkennung und KI-gestützte Asset-Qualitätsanalyse
- **📊 Intelligenter Asset-Validator** - KI-gestütztes Fortschritts-Tracking für Asset-Validierung und automatisierte Textfit-Analyse
- **☁️ Cloud-Synchronisation** - Nahtlose Synchronisation mit KI-gestütztem Cloud-Speicher und intelligenter Konfliktlösung
- **⚡ Batch-Rendering** - Headless PDF-Rendering mit KI-optimierten Qualitätsvoreinstellungen
- **🎯 Intelligente manuelle Überschreibung** - KI-gestütztes Layer-Management und intelligente Dokumentmanipulation

## ✨ Features

### Aktuelle Implementierung

- ✅ Natives C++/Qt-Plugin (keine Python-Abhängigkeiten)
- ✅ Dockbares Panel in Scribus UI integriert
- ✅ Mock-Modus für Tests und Demonstrationen
- ✅ Echtzeit-Status-Updates mit visuellen Indikatoren
- ✅ Fortschritts-Tracking für mehrere Workflows
- ✅ Log-Viewer mit Auto-Scroll-Funktionalität
- ✅ Dark-Theme UI im modernen Design-Standard

### Geplante Features

- 🔄 Echte KI-API-Integration (aktuell Mock-Modus)
- 🔄 Cloud-Synchronisations-Endpunkte mit KI-Optimierung
- 🔄 Batch PDF-Rendering mit KI-Qualitätsvoreinstellungen
- 🔄 Layer-Management-Tools mit KI-Unterstützung
- 🔄 Erweiterte KI-gestützte Layout-Überprüfung

## 📋 Anforderungen

### Build-Anforderungen

- **Windows 10/11** (x64)
- **Visual Studio 2022** (v143 Toolset) oder Build Tools
- **Qt 6.10.1** (msvc2022_64)
- **Scribus 1.7.1+** Quellcode
- **Scribus Libs Kit** (von SourceForge)

### Laufzeit-Anforderungen

- **Scribus 1.7.1+** installiert
- **Windows 10/11** (x64)

## 🚀 Build

### Voraussetzungen

1. **Qt 6.10.1 installieren:**
   - Download von [Qt Official](https://www.qt.io/)
   - Qt 6.10.1 für MSVC 2022 64-bit installieren
   - Qt 5 Kompatibilitätsmodul installieren

2. **Scribus Quellcode herunterladen:**
   ```bash
   git clone https://github.com/scribusproject/scribus.git
   cd scribus
   git checkout 1.7.1  # oder master für neueste Version
   ```

3. **Scribus Libs Kit herunterladen:**
   - Download von [Scribus SourceForge](https://sourceforge.net/projects/scribus/files/)
   - Extrahiere nach `C:\Development\scribus-1.7.x-libs-msvc`
   - Bibliotheken bauen (Release, x64)

### Build-Anleitung

#### Option 1: Visual Studio Solution (Empfohlen)

1. **Visual Studio Solution öffnen:**
   ```
   C:\Development\scribus-1.7\win32\msvc2022\Scribus.sln
   ```

2. **Property Sheets konfigurieren:**
   - Bearbeite `Scribus-build-props.props`
   - Setze `SCRIBUS_LIB_ROOT` auf deinen Libs Kit-Pfad
   - Setze `QT6_DIR` auf deine Qt 6.10.1 Installation

3. **Build:**
   - Konfiguration wählen: **Release**
   - Plattform wählen: **x64**
   - Solution bauen (F7)

4. **Output:**
   - Plugin DLL: `C:\Development\Scribus-builds\Scribus-Release-x64-v143\plugins\gamma_dashboard.dll`

## 📦 Installation

### Automatische Installation (PowerShell)

```powershell
# Benötigt Administrator-Rechte
.\COPY_TO_INSTALLED.ps1
```

### Manuelle Installation

1. **Plugin DLL kopieren:**
   ```
   Kopiere: gamma_dashboard.dll
   Nach: C:\Program Files\Scribus 1.7.1\plugins\
   ```

2. **Abhängigkeiten kopieren:**
   - Qt6 DLLs (Qt6Core.dll, Qt6Gui.dll, Qt6Widgets.dll, Qt6Network.dll)
   - Qt Platform Plugin (platforms\qwindows.dll)
   - Andere Abhängigkeiten von der Scribus-Installation

3. **Scribus neu starten**

## 🎮 Verwendung

1. **Scribus starten**

2. **Plugin öffnen:**
   - Menü: **Extras → Gamma Dashboard**
   - Oder Tastenkombination: **Strg+Umschalt+G**

3. **Panel docken:**
   - Das Dashboard erscheint als dockbares Panel (Standard: rechts)
   - Kann links, rechts oder schwebend gedockt werden

4. **Pipeline überwachen:**
   - Echtzeit-Status und Fortschritt anzeigen
   - KI-gestützte Layout-Überprüfungsergebnisse prüfen
   - Asset-Validierungsfortschritt überwachen

## 🏗️ Architektur

### Plugin-Struktur

```
gamma_dashboard/
├── gamma_dashboard_plugin.h/cpp    # Haupt-Plugin-Klasse (ScActionPlugin)
├── gamma_dashboard_dock.h/cpp      # Dock-Widget UI (QWidget)
├── gamma_dashboard_exports.cpp     # C-ABI Export-Funktionen
└── CMakeLists.txt                  # Build-Konfiguration
```

### Wichtige Komponenten

- **GammaDashboardPlugin** - Haupt-Plugin-Klasse, erbt von `ScActionPlugin`
- **GammaDashboardDock** - UI-Widget, erbt von `QWidget`
- **Export-Funktionen** - C-ABI Exports, die vom Scribus Plugin-System benötigt werden

## 🔧 Konfiguration

### Umgebungsvariablen

- `GAMMA_BASE_URL` - KI-API-Endpunkt-URL (Standard: `http://localhost:8000`)
- `GAMMA_API_KEY` - API-Authentifizierungsschlüssel

### Mock-Modus

Das Plugin läuft standardmäßig im Mock-Modus für Tests. Um die echte KI-API zu aktivieren:

1. Umgebungsvariablen setzen
2. Plugin-Quellcode ändern, um Mock-Modus zu deaktivieren
3. Plugin neu bauen

## 📝 Entwicklung

### Code-Stil

- Folge Scribus Coding-Konventionen
- Verwende Qt-Stil-Namensgebung (camelCase für Methoden, m_-Präfix für Member)
- Verwende `tr()` für alle benutzer-sichtbaren Strings
- Kommentiere komplexe Logik

## 📄 Lizenz

Dieses Plugin ist unter der **GPL v2** (oder höher) lizenziert, passend zur Scribus-Lizenz.

## 👤 Autor

**Jochen Weerda**
- E-Mail: jochen.weerda@gmail.com
- GitHub: [@JochenWeerda](https://github.com/JochenWeerda)

## 🙏 Danksagungen

- **Scribus Entwicklerteam** - Für die hervorragende Plugin-API und Dokumentation
- **Qt-Projekt** - Für das leistungsstarke Qt-Framework
- **MCP Dashboard Plugin** - Inspiration für das Dock-Widget-Pattern

---

## 📚 Resources / Ressourcen

- [Scribus Documentation](https://wiki.scribus.net/) | [Scribus Dokumentation](https://wiki.scribus.net/)
- [Scribus Plugin API](https://wiki.scribus.net/canvas/Plugin_API) | [Scribus Plugin API](https://wiki.scribus.net/canvas/Plugin_API)
- [Qt Documentation](https://doc.qt.io/) | [Qt Dokumentation](https://doc.qt.io/)
- [Scribus Forums](https://forums.scribus.net/) | [Scribus Foren](https://forums.scribus.net/)

## 📊 Status

**Current Version / Aktuelle Version:** 1.0.0  
**Status:** ✅ Production Ready / Produktionsreif  
**Scribus Compatibility / Scribus-Kompatibilität:** 1.7.1+  
**Platform / Plattform:** Windows x64  

---

**Note / Hinweis:** This is an independent plugin and is not officially endorsed by the Scribus project.  
Dies ist ein unabhängiges Plugin und wird nicht offiziell vom Scribus-Projekt unterstützt.
