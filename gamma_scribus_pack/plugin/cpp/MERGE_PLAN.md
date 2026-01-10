# Merge-Plan: MCP Dashboard Patterns → Gamma Dashboard

## Analyse-Ergebnisse

### ✅ Wichtige Patterns aus MCP Dashboard:

#### 1. **ScPlugin statt ScActionPlugin**
- MCP verwendet: `ScPlugin` (Basis-Klasse, kein ScActionPlugin)
- Unser Ansatz: `ScActionPlugin` (für Einmal-Aktionen)
- **Empfehlung:** Wechseln zu `ScPlugin` für persistentes Plugin

#### 2. **initPlugin() / cleanupPlugin() Pattern**
- MCP: `initPlugin()` und `cleanupPlugin()` Methods
- Unser Ansatz: `run()` Method (wird bei jedem Aufruf ausgeführt)
- **Empfehlung:** Übernehmen für Initialisierung

#### 3. **QDockWidget Integration**
- MCP: `QDockWidget` wird im Plugin erstellt und zu MainWindow hinzugefügt
- Unser Ansatz: Externes Python-Script via QProcess
- **Empfehlung:** Native Dock Widget implementieren

#### 4. **QNetworkAccessManager für HTTP**
- MCP: `QNetworkAccessManager` mit async callbacks
- Unser Ansatz: Python-Script macht HTTP-Calls
- **Empfehlung:** Native Qt Network verwenden

#### 5. **Environment Variables**
- MCP: `qEnvironmentVariable("MCP_BASE_URL")`, `qEnvironmentVariable("MCP_API_KEY")`
- Unser Ansatz: Konfigurationsdateien
- **Empfehlung:** ENV-Variablen übernehmen

#### 6. **Helper Functions**
- MCP: `resolveMainWindow()`, `ensureMenu()` - sehr nützlich!
- Unser Ansatz: Direkt QApplication verwenden
- **Empfehlung:** Übernehmen

#### 7. **QTimer für Polling**
- MCP: `QTimer` für regelmäßige Status-Updates
- Unser Ansatz: Kein Polling
- **Empfehlung:** Übernehmen für Live-Updates

#### 8. **Reply Tracking mit QHash**
- MCP: `QHash<QNetworkReply*, QString> m_replyTags`
- **Empfehlung:** Übernehmen für Request/Response-Matching

## Konkrete Migrations-Schritte

### Phase 1: Plugin-Basis ändern

**Von:**
```cpp
class GammaDashboardPlugin : public ScActionPlugin
{
    bool run(ScribusDoc* doc, const QString& target = QString()) override;
};
```

**Zu:**
```cpp
class GammaDashboardPlugin : public ScPlugin
{
    bool initPlugin() override;
    bool cleanupPlugin() override;
    void languageChange() override;
    // ... andere ScPlugin Methods
};
```

### Phase 2: Dock Widget hinzufügen

**Neue Datei:** `gamma_dashboard_dock.h/.cpp`
- Basis: `QDockWidget`
- UI-Komponenten für Pipeline-Status
- Log-Viewer
- Pipeline-Steuerung

### Phase 3: Network Manager

**Ersetzen:**
- Python-Script HTTP-Calls
- Durch: `QNetworkAccessManager`

### Phase 4: Helper Functions übernehmen

- `resolveMainWindow()` 
- `ensureMenu()`

### Phase 5: Environment Variables

- `GAMMA_API_KEY`
- `GAMMA_BASE_URL`

## Code-Übernahmen

### 1. resolveMainWindow() Helper
```cpp
QMainWindow* GammaDashboardPlugin::resolveMainWindow() const
{
    if (ScCore && ScCore->primaryMainWindow())
        return ScCore->primaryMainWindow();
    // ... Rest wie in MCP
}
```

### 2. ensureMenu() Helper
```cpp
QMenu* GammaDashboardPlugin::ensureMenu(QMenuBar* bar, const QStringList& names) const
{
    // Übernehmen von MCP
}
```

### 3. Network Pattern
```cpp
m_net = new QNetworkAccessManager(this);
connect(m_net, &QNetworkAccessManager::finished, this, &GammaDashboardPlugin::onReplyFinished);
```

### 4. Environment Variables
```cpp
m_baseUrl = qEnvironmentVariable("GAMMA_BASE_URL", "http://127.0.0.1:8000");
m_apiKey = qEnvironmentVariable("GAMMA_API_KEY");
```

## Implementierungs-Reihenfolge

1. ✅ Plugin-Basis ändern (ScPlugin)
2. ✅ Dock Widget erstellen
3. ✅ Network Manager integrieren
4. ✅ Helper Functions übernehmen
5. ✅ ENV-Variables implementieren
6. ✅ Polling für Status-Updates

## Beibehaltenswertes aus Gamma Dashboard

- Pipeline-Funktionalität (Gamma-spezifisch)
- JSON-Configuration für Pipelines
- Crop-Generation Logic
- Card-Clustering Logic

