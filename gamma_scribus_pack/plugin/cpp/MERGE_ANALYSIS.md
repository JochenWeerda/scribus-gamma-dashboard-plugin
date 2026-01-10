# Merge-Analyse: MCP Dashboard → Gamma Dashboard

## Erkenntnisse aus MCP Dashboard Plugin

### 1. **Native Dock Widget Integration** ⭐ WICHTIG
- **MCP verwendet:** `QDockWidget` für native Scribus-Integration
- **Unser Ansatz:** Externes Python-Script via QProcess
- **Vorteil Dock Widget:**
  - Persistent in Scribus-UI
  - Docking-Möglichkeit
  - Bessere Integration

### 2. **Non-Blocking HTTP via QNetworkAccessManager**
- **MCP verwendet:** `QNetworkAccessManager` für async HTTP
- **Unser Ansatz:** Python-Script mit separatem Prozess
- **Vorteil QNetworkAccessManager:**
  - Native Qt-Integration
  - Nicht-blockierend
  - Bessere Fehlerbehandlung

### 3. **Environment Variables für API-Keys**
- **MCP verwendet:** `MCP_API_KEY`, `MCP_BASE_URL` aus ENV
- **Unser Ansatz:** Konfigurationsdateien
- **Vorteil ENV:**
  - Keine Keys in Dateien
  - Sicherer
  - DevOps-freundlich

### 4. **Native C++ UI**
- **MCP verwendet:** C++ Qt-Widgets (MCPDashboardDock.cpp/.h)
- **Unser Ansatz:** Python Qt-Widgets
- **Vorteil C++:**
  - Schneller
  - Bessere Integration
  - Kein Python-Prozess nötig

## Empfohlene Verbesserungen für Gamma Dashboard

### Phase 1: Dock Widget Integration
```cpp
// Statt externes Python-Script:
// Erstelle QDockWidget direkt im Plugin
QDockWidget* dock = new QDockWidget("Gamma Dashboard", mainWindow);
GammaDashboardWidget* widget = new GammaDashboardWidget(dock);
dock->setWidget(widget);
mainWindow->addDockWidget(Qt::RightDockWidgetArea, dock);
```

### Phase 2: Native HTTP statt Python
```cpp
// QNetworkAccessManager für Pipeline-Calls
QNetworkAccessManager* manager = new QNetworkAccessManager(this);
QNetworkRequest request(QUrl("https://gamma-api.example.com/pipeline"));
request.setRawHeader("Authorization", "Bearer " + apiKey.toUtf8());
QNetworkReply* reply = manager->post(request, data);
```

### Phase 3: Environment Variables
```cpp
QString apiKey = qgetenv("GAMMA_API_KEY");
QString baseUrl = qgetenv("GAMMA_BASE_URL");
if (apiKey.isEmpty()) {
    // Zeige Konfigurations-Dialog
}
```

## Migrations-Plan

### Option A: Hybrid-Ansatz (Empfohlen)
1. ✅ Behalte aktuelles Plugin (funktioniert bereits)
2. 🔄 Erweitere um Dock Widget
3. 🔄 Migriere HTTP zu QNetworkAccessManager
4. 🔄 Übernehme ENV-Variable-Pattern

### Option B: Vollständige Migration
1. 🔄 Konvertiere Python-Widget zu C++ Widget
2. 🔄 Integriere Dock Widget
3. 🔄 Ersetze Python-HTTP durch C++ HTTP
4. 🔄 Übernehme ENV-Pattern

## Konkrete Code-Übernahmen

### 1. Dock Widget Pattern
```cpp
// Aus MCP Dashboard:
QDockWidget* mcpDock = new QDockWidget(tr("MCP Dashboard"), m_mainWindow);
mcpDock->setObjectName("MCPDashboardDock");
m_mainWindow->addDockWidget(Qt::RightDockWidgetArea, mcpDock);
```

### 2. Network Manager Pattern
```cpp
// Aus MCP Dashboard:
m_networkManager = new QNetworkAccessManager(this);
connect(m_networkManager, &QNetworkAccessManager::finished,
        this, &MCPDashboardDock::onNetworkReply);
```

### 3. Environment Variables
```cpp
// Aus MCP Dashboard:
QString apiKey = qgetenv("MCP_API_KEY");
QString baseUrl = qgetenv("MCP_BASE_URL").isEmpty() 
    ? "http://localhost:8080" 
    : qgetenv("MCP_BASE_URL");
```

## Nächste Schritte

1. **Sofort:** Analysiere MCP Dashboard Code (sobald verfügbar)
2. **Phase 1:** Füge Dock Widget zum Gamma Dashboard hinzu
3. **Phase 2:** Ersetze Python-HTTP durch QNetworkAccessManager
4. **Phase 3:** Übernehme ENV-Variable-Pattern

