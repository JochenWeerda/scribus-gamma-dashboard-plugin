# Analyse: Scribus MCP Dashboard Package

**Datum:** 2025-01-27  
**Quelle:** PowerShell-Script zur Erstellung eines vollständigen Python-Pakets  
**Ziel:** Dockable MCP AI Dashboard für Scribus 1.7.1

---

## 📦 Paket-Struktur

Das PowerShell-Script erstellt folgende Dateistruktur:

```
scribus_mcp_dashboard/
├── __init__.py                    # Qt-Binding Loader
├── log_buffer.py                  # Log-Buffer (deque)
├── qss_dark.py                    # Dark Theme Stylesheet
├── settings_dialog.py             # Settings-Dialog
├── sidecar_client_qt.py           # Qt-basierter HTTP-Client
├── scribus_bridge.py              # Scribus API Bridge
├── mcp_dashboard.py               # Haupt-Dashboard-Widget
└── README.md                      # Dokumentation

install/
└── mcp_dashboard_entry.py        # Entry-Point für Scribus
```

---

## 🔍 Komponenten-Analyse

### 1. `__init__.py` - Qt-Binding Loader

**Funktionalität:**
- Automatische Erkennung verfügbarer Qt-Bindings
- Unterstützt: PySide6, PyQt6, PySide2, PyQt5
- Fallback-Mechanismus (versucht alle Bindings)
- Helper-Funktionen für Signal/Slot (kompatibel mit PyQt/PySide)

**Besonderheiten:**
- `qt_signal()` - Kompatibilität zwischen PyQt/PySide
- `qt_slot()` - Kompatibilität zwischen PyQt/PySide
- `qt_available()` - Prüfung ob Qt verfügbar ist

**Vorteil:** Funktioniert mit allen gängigen Qt-Bindings ohne Code-Änderungen

---

### 2. `log_buffer.py` - Log-Buffer

**Funktionalität:**
- Ring-Buffer mit `deque` (max. 500 Zeilen)
- Automatisches Überschreiben alter Einträge
- `append()` / `extend()` / `text()` / `clear()`

**Vorteil:** Speicher-effizient, verhindert unbegrenztes Wachstum

---

### 3. `qss_dark.py` - Dark Theme

**Funktionalität:**
- GitHub-ähnliches Dark Theme
- QSS (Qt Style Sheets) für alle Widgets
- Konsistente Farbpalette:
  - Background: `#1f2328`
  - Cards: `#2b3036`
  - Buttons: `#2f6fed`
  - Text: `#e6edf3`

**Vorteil:** Modernes, professionelles Aussehen

---

### 4. `settings_dialog.py` - Settings-Management

**Funktionalität:**
- QSettings-basiertes Persistieren
- Environment-Variable-Override:
  - `MCP_BASE_URL`
  - `MCP_API_KEY`
  - `MCP_POLL_MS`
  - `MCP_MOCK`
- Dialog mit Form-Layout
- Defaults:
  - Base URL: `http://127.0.0.1:7777`
  - Polling: 2000 ms
  - Mock mode: ON

**Vorteil:** Flexible Konfiguration (UI + ENV)

---

### 5. `sidecar_client_qt.py` - HTTP-Client

**Funktionalität:**
- Qt-basierter asynchroner HTTP-Client
- Signal-basierte Kommunikation (`response` Signal)
- Timeout-Handling (8 Sekunden)
- Mock-Mode für Tests ohne Server
- Unterstützte Endpoints:
  - `GET /v1/status`
  - `POST /v1/sync`
  - `POST /v1/audit/layout`
  - `POST /v1/validate/assets`
  - `POST /v1/render/batch_pdf`
  - `GET /v1/jobs/{job_id}/logs?tail=200`

**Besonderheiten:**
- `QNetworkAccessManager` für HTTP-Requests
- Request-ID-System für Tracking
- Mock-Responses für alle Endpoints
- JSON-Payload-Support

**Vorteil:** Asynchron, nicht-blockierend, testbar ohne Server

---

### 6. `scribus_bridge.py` - Scribus API Bridge

**Funktionalität:**
- Wrapper um Scribus Python API
- Safe-Wrapper (`_safe()`) für alle API-Calls
- Features:
  - `have_doc()` - Prüft ob Dokument geöffnet
  - `get_doc_ref()` - Dokument-Metadaten
  - `list_layers()` - Layer-Liste
  - `get_selection_items()` - Ausgewählte Objekte
  - `move_selected_to_layer()` - Objekte verschieben

**Besonderheiten:**
- Kompatibilität mit verschiedenen Scribus-Versionen
- Fallback-Mechanismen für API-Varianten
- Fehlerbehandlung (keine Crashes bei fehlenden Features)

**Vorteil:** Robuste Integration mit Scribus

---

### 7. `mcp_dashboard.py` - Haupt-Dashboard

**Funktionalität:**
- `QDockWidget` für Scribus-Integration
- 6 Haupt-Sektionen:
  1. **Connection Status** - Verbindungsanzeige + Sync-Button
  2. **Layout Audit** - Z-Order, Overlaps, Low-Res Images
  3. **Asset Validator** - Asset Analyst + Text Fit (Progress Bars)
  4. **Headless Control** - Batch Render PDF
  5. **Log Viewer** - Live-Logs mit Auto-Scroll
  6. **Manual Override** - Move Selected To Layer

**Features:**
- Auto-Polling (konfigurierbar, default 2000ms)
- Status-Dot (grün/rot) für Verbindung
- Progress Bars für Metriken
- Settings-Dialog
- Dark Theme

**Vorteil:** Vollständige UI-Integration in Scribus

---

### 8. `install/mcp_dashboard_entry.py` - Entry-Point

**Funktionalität:**
- Installiert Dashboard im Scribus-Menü
- Toggle-Funktion (ein/aus)
- Dock-Widget-Integration
- Menü-Integration (Tools oder Extras)

**Vorteil:** Einfache Installation und Aktivierung

---

## 🔄 Vergleich: Neues Package vs. Vorhandenes Dashboard

### Vorhanden (von mir erstellt):
- `mcp_ai_dashboard.html` - HTML/JS/CSS Dashboard
- `mcp_dashboard_launcher.py` - Launcher für Qt-Dialog

### Neues Package (aus PowerShell-Script):
- Vollständiges Python-Paket
- Native Qt-Widget-Integration (Dock-Widget)
- Asynchroner HTTP-Client
- Settings-Management
- Scribus-Bridge

### Unterschiede:

| Feature | HTML-Dashboard | Qt-Package |
|---------|----------------|------------|
| Integration | Externer Dialog | Native Dock-Widget |
| Kommunikation | Fetch API | QtNetwork (asynchron) |
| Settings | JavaScript | QSettings (persistent) |
| Scribus-Integration | Keine | Vollständig (Bridge) |
| Mock-Mode | Manuell | Integriert |
| Auto-Polling | JavaScript | Qt-Timer |
| Menü-Integration | Nein | Ja (Tools/Extras) |

**Vorteil Qt-Package:** Native Integration, bessere Performance, persistent Settings

---

## 🎯 API-Endpoints (erwartet)

Das Dashboard erwartet folgende Endpoints:

### 1. `GET /v1/status`
```json
{
  "connected": true,
  "sidecar_version": "1.0.0",
  "latency_ms": 5
}
```

### 2. `POST /v1/sync`
```json
{
  "ok": true,
  "sync_id": "sync-001"
}
```

### 3. `POST /v1/audit/layout`
```json
{
  "z_order_ok": true,
  "overlaps": 0,
  "low_res_images": 2,
  "issues": []
}
```

### 4. `POST /v1/validate/assets`
```json
{
  "bars": {
    "asset": 82,
    "text_fit": 98
  }
}
```

### 5. `POST /v1/render/batch_pdf`
```json
{
  "job_id": "job-123",
  "pdf_uri": "s3://bucket/job-123.pdf"
}
```

### 6. `GET /v1/jobs/{job_id}/logs?tail=200`
```json
{
  "lines": [
    "[INFO] Checking fonts...",
    "[WARN] Hyphenation issue..."
  ]
}
```

**Hinweis:** Diese Endpoints müssen im MCP Gateway Server implementiert werden!

---

## 🔧 Integration in bestehendes Projekt

### Schritt 1: Dateien erstellen

Das PowerShell-Script erstellt alle Dateien automatisch. Alternativ manuell:

```powershell
# Im Projekt-Root ausführen
# (Script aus User-Query)
```

### Schritt 2: MCP Gateway Server erweitern

Die Endpoints müssen im `mcp_gateway_server.py` hinzugefügt werden:

```python
@app.route("/v1/status", methods=["GET"])
def status():
    return jsonify({
        "connected": True,
        "sidecar_version": "1.0.0",
        "latency_ms": 5
    })

@app.route("/v1/sync", methods=["POST"])
def sync():
    # Sync-Logik
    return jsonify({"ok": True, "sync_id": "sync-001"})

# etc.
```

### Schritt 3: Installation in Scribus

1. Kopiere `scribus_mcp_dashboard/` und `install/` in Scribus Scripts-Ordner
2. In Scribus: Script → Execute Script → `install/mcp_dashboard_entry.py`
3. Dashboard aktivieren: Tools → MCP AI Dashboard

---

## 📊 Architektur-Vergleich

### Aktuelle Architektur:
```
Scribus → mcp_dashboard_launcher.py → Qt-Dialog → HTML (mcp_ai_dashboard.html)
```

### Neue Architektur (Package):
```
Scribus → install/mcp_dashboard_entry.py → Qt-Dock-Widget → sidecar_client_qt.py → MCP Gateway
```

**Vorteil:** Direkte Integration, keine externe HTML-Datei nötig

---

## ✅ Vorteile des neuen Packages

1. **Native Integration**
   - Dock-Widget statt externer Dialog
   - Menü-Integration
   - Persistente Settings

2. **Bessere Performance**
   - QtNetwork statt Fetch API
   - Asynchron, nicht-blockierend
   - Effizienter Memory-Management

3. **Vollständige Scribus-Integration**
   - Bridge zu Scribus API
   - Direkter Zugriff auf Dokument/Selection
   - Move To Layer funktioniert direkt

4. **Robustheit**
   - Safe-Wrapper für alle API-Calls
   - Fehlerbehandlung
   - Mock-Mode für Tests

5. **Wartbarkeit**
   - Modulare Struktur
   - Klare Trennung der Verantwortlichkeiten
   - Dokumentiert

---

## ⚠️ Anpassungen nötig

### 1. MCP Gateway Server erweitern

Die Endpoints müssen implementiert werden:
- `/v1/status`
- `/v1/sync`
- `/v1/audit/layout`
- `/v1/validate/assets`
- `/v1/render/batch_pdf`
- `/v1/jobs/{job_id}/logs`

### 2. Port-Anpassung

Default: `http://127.0.0.1:7777`  
Aktueller MCP Gateway: `http://localhost:3000`

**Lösung:** Settings-Dialog oder Environment-Variable

### 3. API-Key-Authentifizierung

Das Package unterstützt Bearer-Token:
```python
req.setRawHeader(b'Authorization', ('Bearer ' + self._api_key).encode('utf-8'))
```

MCP Gateway muss das unterstützen.

---

## 🎯 Empfehlung

### Option 1: Package verwenden (empfohlen)
- ✅ Native Integration
- ✅ Bessere Performance
- ✅ Vollständige Scribus-Integration
- ⚠️ MCP Gateway muss erweitert werden

### Option 2: Beide behalten
- HTML-Dashboard für Browser-Tests
- Qt-Package für Production-Integration

### Option 3: Hybrid
- Qt-Package als Haupt-Dashboard
- HTML-Dashboard als Fallback/Preview

---

## 📝 Nächste Schritte

1. **Package-Dateien erstellen** (PowerShell-Script ausführen)
2. **MCP Gateway erweitern** (neue Endpoints hinzufügen)
3. **Port konfigurieren** (7777 → 3000 oder umgekehrt)
4. **In Scribus installieren** (Entry-Script ausführen)
5. **Testen** (Mock-Mode zuerst, dann mit Server)

---

## 🔍 Code-Qualität

### Stärken:
- ✅ Modulare Architektur
- ✅ Fehlerbehandlung (try/except)
- ✅ Kompatibilität (PyQt/PySide)
- ✅ Mock-Mode für Tests
- ✅ Dokumentiert

### Verbesserungspotenzial:
- ⚠️ Keine Unit-Tests
- ⚠️ Hardcoded Defaults (könnten konfigurierbar sein)
- ⚠️ Keine Logging-Library (nur LogBuffer)

**Gesamtbewertung:** ⭐⭐⭐⭐ (4/5) - Sehr gut strukturiert, production-ready mit kleinen Anpassungen

---

*Erstellt: 2025-01-27*

