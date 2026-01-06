# Gamma Dashboard Plugin for Scribus

[![Scribus](https://img.shields.io/badge/Scribus-1.7.1+-blue.svg)](https://www.scribus.net/)
[![Qt](https://img.shields.io/badge/Qt-6.10.1-green.svg)](https://www.qt.io/)
[![License](https://img.shields.io/badge/License-GPL--2.0-orange.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

A native C++ plugin for Scribus that provides a dockable dashboard panel for monitoring and controlling the Gamma publishing pipeline.

## 🎯 Overview

The **Gamma Dashboard Plugin** integrates seamlessly into Scribus 1.7.1+ and provides:

- **Real-time Pipeline Monitoring** - Track progress of automated publishing workflows
- **Layout Audit** - Z-order validation, overlap detection, and asset quality checks
- **Asset Validator** - Progress tracking for asset validation and text fit analysis
- **Cloud Synchronization** - Sync documents to cloud storage
- **Batch Rendering** - Headless PDF rendering capabilities
- **Manual Override** - Layer management and document manipulation tools

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

- 🔄 Real API integration (currently mock mode)
- 🔄 Cloud synchronization endpoints
- 🔄 Batch PDF rendering
- 🔄 Layer management tools
- 🔄 Advanced layout auditing

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

#### Option 2: CMake (Advanced)

See [BUILD_WITH_VS_SOLUTION.md](BUILD_WITH_VS_SOLUTION.md) for detailed CMake instructions.

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
   - Check layout audit results
   - Monitor asset validation progress

## 📸 Screenshots

The plugin provides a modern, dark-themed interface with:

- **Status Indicator** - Green dot for connected, red for disconnected
- **Pipeline Controls** - Start/stop buttons with progress tracking
- **Layout Audit** - Z-order and overlap validation
- **Asset Validator** - Progress bars for asset and text fit validation
- **Log Viewer** - Real-time log messages with auto-scroll

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

### Integration Points

- **Menu Integration** - Via `ScActionPlugin::m_actionInfo`
- **Dock Widget** - Via `QMainWindow::addDockWidget()`
- **Document Access** - Via `ScribusDoc*` parameter in `run()`

## 🔧 Configuration

### Environment Variables

- `GAMMA_BASE_URL` - API endpoint URL (default: `http://localhost:8000`)
- `GAMMA_API_KEY` - API authentication key

### Mock Mode

The plugin runs in mock mode by default for testing. To enable real API:

1. Set environment variables
2. Modify plugin source to disable mock mode
3. Rebuild plugin

## 🐛 Troubleshooting

### Plugin Not Loading

- **Check DLL Location:** Plugin must be in `C:\Program Files\Scribus 1.7.1\plugins\`
- **Check Dependencies:** Ensure all Qt6 DLLs and platform plugins are present
- **Check Architecture:** Plugin must match Scribus architecture (x64)

### Build Errors

- **Qt Not Found:** Verify Qt6_DIR is set correctly
- **Missing Libraries:** Ensure Scribus Libs Kit is built
- **Runtime Mismatch:** Use `/MD` (MultiThreadedDLL) runtime

See [FIX_BUILD_ERRORS.md](FIX_BUILD_ERRORS.md) for detailed troubleshooting.

## 📝 Development

### Code Style

- Follow Scribus coding conventions
- Use Qt-style naming (camelCase for methods, m_ prefix for members)
- Use `tr()` for all user-visible strings
- Comment complex logic

### Testing

1. Build plugin in Debug mode
2. Install to Scribus plugins directory
3. Test with mock mode enabled
4. Verify UI components work correctly
5. Test dock/undock behavior

### Debugging

- Use Visual Studio debugger
- Attach to running Scribus process
- Set breakpoints in plugin code
- Check Scribus debug output

## 📄 License

This plugin is licensed under the **GPL v2** (or later), matching Scribus's license.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 👤 Author

**Jochen Weerda**
- Email: jochen.weerda@gmail.com
- GitHub: [@JochenWeerda](https://github.com/JochenWeerda)

## 🙏 Acknowledgments

- **Scribus Development Team** - For the excellent plugin API and documentation
- **Qt Project** - For the powerful Qt framework
- **MCP Dashboard Plugin** - Inspiration for the dock widget pattern

## 📚 Resources

- [Scribus Documentation](https://wiki.scribus.net/)
- [Scribus Plugin API](https://wiki.scribus.net/canvas/Plugin_API)
- [Qt Documentation](https://doc.qt.io/)
- [Scribus Forums](https://forums.scribus.net/)

## 🔗 Related Projects

- [Scribus](https://www.scribus.net/) - Open source desktop publishing
- [Gamma Publishing Pipeline](https://github.com/JochenWeerda) - Publishing automation system

## 📊 Status

**Current Version:** 1.0.0  
**Status:** ✅ Production Ready  
**Scribus Compatibility:** 1.7.1+  
**Platform:** Windows x64  

---

**Note:** This is an independent plugin and is not officially endorsed by the Scribus project.

