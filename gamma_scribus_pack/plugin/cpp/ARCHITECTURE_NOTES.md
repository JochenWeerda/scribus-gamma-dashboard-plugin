# Architektur-Hinweise & Compile-Fallen

## Kritische Punkte für Plugin-Entwicklung

### 1. ScPlugin + Q_OBJECT Kompatibilität

**Problem:** `Q_OBJECT` und `slots` funktionieren nur, wenn die Basisklasse von `QObject` erbt.

**Status:** 
- Plugin verwendet `class GammaDashboardPlugin : public ScPlugin` mit `Q_OBJECT`
- Dies funktioniert **nur**, wenn `ScPlugin` von `QObject` erbt

**Prüfung:**
```cpp
// In scplugin.h sollte stehen:
class ScPlugin : public QObject { ... }
// ODER
class ScPlugin : public ScPersistentPlugin { ... }
// und ScPersistentPlugin erbt von QObject
```

**Falls ScPlugin NICHT von QObject erbt:**

Optionen:
1. **Zu ScActionPlugin wechseln** (einfachste Lösung für Menü-basierte Plugins)
2. **Multiple Inheritance:** `class GammaDashboardPlugin : public QObject, public ScPlugin` (QObject MUSS zuerst stehen)
3. **QObject-Helper:** Separater `QObject`-Member für Signals/Slots

**Aktueller Build-Status:** Plugin wurde erfolgreich kompiliert (siehe BUILD_SUCCESS.md), daher scheint ScPlugin von QObject zu erben.

---

### 2. initPlugin() / cleanupPlugin() - Virtualität

**Problem:** Diese Methoden sind nur in `ScPersistentPlugin` virtual, nicht in `ScPlugin`.

**Lösung:**
- Für `ScPlugin`: Initialisierung in `addToMainWindowMenu()` durchführen
- `initPlugin()`/`cleanupPlugin()` werden hier als normale Methoden bereitgestellt (falls Scribus sie dennoch aufruft)

**Aktueller Code:**
```cpp
bool initPlugin();  // NICHT virtual, daher kein override
bool cleanupPlugin(); // NICHT virtual
```

---

### 3. Forward Declarations

**Behoben:**
- `QWidget`, `QJsonObject`, `QStringList` - hinzugefügt
- `ScribusDoc`, `Prefs_Pane` - Forward Declarations hinzugefügt

**Header:**
```cpp
#include <QStringList>

class QWidget;
class QJsonObject;
class ScribusDoc;
struct Prefs_Pane;
```

---

### 4. Dock-Widget-Struktur

**Status: OK**

`GammaDashboardDock` erbt direkt von `QDockWidget`, daher:
- Kein zusätzlicher `QDockWidget`-Container nötig
- Direkte Verwendung: `mw->addDockWidget(Qt::RightDockWidgetArea, m_dock);`

**Code:**
```cpp
class GammaDashboardDock : public QDockWidget { ... }
```

---

### 5. Pointer-Initialisierung

**Behoben:** Alle Pointer werden jetzt im Header initialisiert:

```cpp
QPointer<GammaDashboardDock> m_dock = nullptr;
QAction* m_action = nullptr;
QAction* m_settingsAction = nullptr;
GammaApiClient* m_apiClient = nullptr;
QTimer* m_mockTimer = nullptr;
bool m_useMockMode = false;
```

---

### 6. Export-Funktionen

**Status: OK**

Export-Funktionen sind korrekt deklariert und definiert:

```cpp
// Header (Deklaration)
extern "C" PLUGIN_API int gamma_dashboard_getPluginAPIVersion();
extern "C" PLUGIN_API ScPlugin* gamma_dashboard_getPlugin();
extern "C" PLUGIN_API void gamma_dashboard_freePlugin(ScPlugin* plugin);

// CPP (Definition - nur EINMAL)
extern "C" PLUGIN_API int gamma_dashboard_getPluginAPIVersion() { ... }
```

---

## Typische Compile-Fehler & Lösungen

### Fehler: "Class contains Q_OBJECT macro but does not inherit QObject"
**Lösung:** Prüfe ob `ScPlugin` von `QObject` erbt. Falls nicht, siehe Optionen oben.

### Fehler: "undefined reference to vtable"
**Lösung:** Stelle sicher, dass `Q_OBJECT` in einer Klasse verwendet wird, die von `QObject` erbt.

### Fehler: "Plugin lädt nicht / Menüeintrag fehlt"
**Ursachen:**
- `addToMainWindowMenu()` wird nicht aufgerufen → prüfe Plugin-Loading
- DLL nicht im richtigen Verzeichnis → `plugins/` oder `lib/scribus/plugins/`
- Export-Funktionen falsch → prüfe `PLUGIN_API` Makro

### Fehler: "Dock lässt sich nicht andocken"
**Ursache:** Dock-Widget ist kein `QDockWidget`
**Lösung:** Sicherstellen, dass `GammaDashboardDock : public QDockWidget`

---

## Empfohlene Build-Reihenfolge

1. **Compile-Prüfung:**
   ```bash
   # Prüfe ob ScPlugin von QObject erbt
   grep -A 5 "class ScPlugin" <path-to-scribus>/scplugin.h
   ```

2. **Build testen:**
   ```powershell
   cmake --build build --config Release
   ```

3. **Lint-Prüfung:**
   - Alle Forward Declarations vorhanden?
   - Pointer initialisiert?
   - Q_OBJECT nur in QObject-Erben?

4. **Installation testen:**
   - DLL kopieren
   - Scribus starten
   - Menü prüfen
   - Dock öffnen

---

## Referenzen

- BUILD_SUCCESS.md - Erfolgreicher Build mit ScPlugin
- MCP Dashboard Plugin Pattern - Referenz-Implementierung
- Scribus Plugin API Documentation

