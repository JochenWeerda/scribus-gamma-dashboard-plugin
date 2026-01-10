# Gamma Dashboard Plugin - Installation

## ✅ Build erfolgreich

Das Plugin wurde erfolgreich kompiliert:
- **DLL**: `build\Release\gamma_dashboard.dll` (67 KB)
- **Build-Typ**: Standalone (wie MCP Dashboard Plugin)
- **Pattern**: Verwendet `/FORCE:UNRESOLVED` für Runtime-Symbol-Auflösung

## 📦 Installation

### Automatisch (empfohlen)

```powershell
cd gamma_scribus_pack\plugin\cpp
.\install_plugin.ps1
```

Das Script sucht automatisch nach Scribus-Installationen.

### Manuell

Kopiere die DLL in eines der folgenden Verzeichnisse:

**System-Installation:**
```
C:\Program Files\Scribus 1.7.1\lib\scribus\plugins\gamma_dashboard.dll
```

**User-Profil (empfohlen, kein Admin nötig):**
```
%APPDATA%\Scribus\plugins\gamma_dashboard.dll
```

**Portable Installation:**
```
<Scribus-Portable>\lib\scribus\plugins\gamma_dashboard.dll
```

### Mit bekanntem Pfad

```powershell
.\install_plugin.ps1 -ScribusPluginPath "C:\Program Files\Scribus 1.7.1\lib\scribus\plugins"
```

## 🔍 Plugin-Verzeichnis finden

Das Plugin-Verzeichnis ist normalerweise:
- `lib\scribus\plugins\` innerhalb der Scribus-Installation

Typische Pfade:
- `C:\Program Files\Scribus 1.7.1\lib\scribus\plugins\`
- `C:\Program Files (x86)\Scribus 1.7.1\lib\scribus\plugins\`
- `%APPDATA%\Scribus\plugins\` (User-Profil, keine Admin-Rechte nötig)

## ✅ Testen

1. **Scribus starten**
2. **Menü öffnen**: `Extras > Tools > Gamma Dashboard`
3. **Plugin-Liste prüfen**: `Extras > Plugins`

## 🐛 Troubleshooting

### Plugin erscheint nicht im Menü

1. Prüfe, ob DLL im richtigen Verzeichnis liegt
2. Prüfe Scribus-Plugin-Liste: `Extras > Plugins`
3. Prüfe Scribus-Log auf Fehler

### Fehler beim Laden

- Stelle sicher, dass alle Qt-DLLs verfügbar sind (normalerweise in Scribus-Installation)
- Prüfe, ob `gamma_dashboard.dll` im Plugin-Verzeichnis liegt
- Prüfe Scribus-Version (kompatibel mit 1.7.x)

### Admin-Rechte erforderlich

Falls System-Installation Admin-Rechte benötigt, nutze User-Profil:
```powershell
$target = "$env:APPDATA\Scribus\plugins\gamma_dashboard.dll"
Copy-Item "build\Release\gamma_dashboard.dll" $target
```

## 📝 Build neu erstellen

```powershell
.\quick_build.ps1 -CmakePath "C:\Development" `
  -ScribusSourcePath "C:\Development\scribus-1.7" `
  -QtPath "C:\Qt\6.5.3\msvc2019_64"
```

## 🔧 Technische Details

- **Pattern**: Standalone-Build (wie MCP Dashboard)
- **Linker-Flag**: `/FORCE:UNRESOLVED` für Runtime-Symbol-Auflösung
- **Abhängigkeiten**: Nur Qt (Core, Widgets, Network), keine Scribus-Libraries
- **MOC**: Automatisch aktiviert für Q_OBJECT

Die fehlenden Symbole (z.B. `ScPlugin::staticMetaObject`) werden zur Laufzeit von Scribus bereitgestellt, wenn das Plugin geladen wird.

