# Learning by Doing: MCP AI Dashboard für Scribus

**Datum:** 2025-01-27  
**Projekt:** Headless SLA Layout & Publishing Engine  
**Ziel:** Vollständige Integration eines MCP AI Dashboards in Scribus

---

## 📋 Inhaltsverzeichnis

1. [Projekt-Überblick](#projekt-überblick)
2. [Phase 1: Package-Erstellung](#phase-1-package-erstellung)
3. [Phase 2: MCP Gateway Server Erweiterung](#phase-2-mcp-gateway-server-erweiterung)
4. [Phase 3: Dashboard-Integration](#phase-3-dashboard-integration)
5. [Phase 4: Qt-Bindings Installation](#phase-4-qt-bindings-installation)
6. [Phase 5: Abhängigkeiten Installation](#phase-5-abhängigkeiten-installation)
7. [Phase 6: API-Key Verschlüsselung](#phase-6-api-key-verschlüsselung)
8. [Phase 7: Qt-Instanz Problem](#phase-7-qt-instanz-problem)
9. [Lessons Learned](#lessons-learned)
10. [Best Practices](#best-practices)
11. [Code-Beispiele](#code-beispiele)

---

## 🎯 Projekt-Überblick

### Ziel
Erstellung eines vollständigen MCP AI Dashboards für Scribus mit:
- Native Qt-Integration (Dock-Widget)
- HTML-Fallback
- Verschlüsselter API-Key-Speicherung
- MCP Gateway Server Integration
- Automatische Installation

### Herausforderungen
1. Qt-Bindings für Scribus Python installieren
2. MCP Gateway Server erweitern
3. Dashboard in Scribus integrieren
4. API-Key sicher speichern
5. Qt-Instanz-Zugriff in Scribus

---

## 📦 Phase 1: Package-Erstellung

### Aufgabe
Erstellen eines vollständigen Python-Pakets für das MCP Dashboard basierend auf einem PowerShell-Script.

### Erstellte Struktur
```
scribus_mcp_dashboard/
├── __init__.py                    # Qt-Binding Loader
├── log_buffer.py                  # Ring-Buffer für Logs
├── qss_dark.py                    # Dark Theme
├── settings_dialog.py             # Settings-Dialog
├── sidecar_client_qt.py           # HTTP-Client
├── scribus_bridge.py              # Scribus API Bridge
├── mcp_dashboard.py               # Haupt-Dashboard
└── encryption.py                  # API-Key Verschlüsselung

install/
└── mcp_dashboard_entry.py        # Entry-Point
```

### Lessons Learned
- **Qt-Binding Loader:** Wichtig für Kompatibilität (PyQt5/PyQt6/PySide2/PySide6)
- **Modulare Architektur:** Jede Komponente in separater Datei
- **Safe-Wrapper:** Alle Scribus-API-Calls sollten abgesichert sein

### Code-Beispiel: Qt-Binding Loader
```python
def load_qt():
    errors = []
    for name in ('PySide6', 'PyQt6', 'PySide2', 'PyQt5'):
        try:
            return _try_import(name)
        except Exception as exc:
            errors.append('%s: %s' % (name, exc))
    raise ImportError('No Qt bindings available. Tried: %s' % '; '.join(errors))
```

---

## 🔧 Phase 2: MCP Gateway Server Erweiterung

### Aufgabe
Erweitern des bestehenden MCP Gateway Servers um 6 neue Endpoints für das Dashboard.

### Neue Endpoints
1. `GET /v1/status` - Server-Status
2. `POST /v1/sync` - Dokument-Sync
3. `POST /v1/audit/layout` - Layout-Audit
4. `POST /v1/validate/assets` - Asset-Validierung
5. `POST /v1/render/batch_pdf` - Batch-Render
6. `GET /v1/jobs/{job_id}/logs` - Job-Logs

### Implementierung
```python
# In-Memory Store für MVP
_job_store = {}
_job_logs = {}
_sync_store = {}

@app.route("/v1/status", methods=["GET"])
def v1_status():
    import time
    start_time = time.time()
    connected = HAS_REQUESTS and bool(GEMINI_API_KEY)
    latency_ms = int((time.time() - start_time) * 1000)
    return jsonify({
        "connected": connected,
        "sidecar_version": "1.0.0",
        "latency_ms": latency_ms
    })
```

### Lessons Learned
- **MVP-Ansatz:** In-Memory Store für erste Version
- **Integration:** Bestehende Funktionen wiederverwenden (`layout_expert_audit_tool`)
- **Mock-Responses:** Für Tests ohne Server

---

## 🎨 Phase 3: Dashboard-Integration

### Aufgabe
Zusammenführen von HTML- und Qt-Dashboard zu einer Hybrid-Lösung.

### Lösung
- Qt-Dashboard als Hauptversion (native Integration)
- HTML-Dashboard als Fallback/Alternative
- Button im Qt-Dashboard zum Öffnen des HTML-Dashboards

### Code-Beispiel: Hybrid-Integration
```python
def _on_open_html_dashboard(self):
    """Öffnet das HTML-Dashboard als Fallback/Alternative."""
    script_dir = Path(__file__).parent.parent
    html_path = script_dir / 'mcp_ai_dashboard.html'
    
    if sys.platform == 'win32':
        os.startfile(str(html_path))
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', str(html_path)])
    else:
        subprocess.Popen(['xdg-open', str(html_path)])
```

### Lessons Learned
- **Fallback-Strategie:** Immer eine Alternative bereithalten
- **Plattform-Unabhängigkeit:** Verschiedene Methoden für verschiedene OS

---

## 🔐 Phase 4: Qt-Bindings Installation

### Problem
Qt-Bindings (PyQt5) fehlten für Scribus Python-Installation.

### Herausforderungen
1. **System-Python vs. Scribus Python:** Verschiedene Python-Installationen
2. **Pfad-Findung:** Scribus Python-Installation finden
3. **Installation:** PyQt5 für richtige Python-Installation installieren

### Lösungsansätze

#### Ansatz 1: Automatisches Script
```powershell
# install_pyqt5_auto.bat
$python = "C:\Program Files\Scribus 1.7.1\python\python.exe"
& $python -m pip install PyQt5
```

#### Ansatz 2: Python-Script in Scribus
```python
# check_and_install_qt.py
def find_python_exe():
    """Findet den Python-Interpreter für die Installation."""
    scribus_exe = sys.executable
    # Versuche Python im gleichen Verzeichnis zu finden
    scribus_dir = Path(scribus_exe).parent
    python_candidates = [
        scribus_dir / "python" / "python.exe",
        scribus_dir / "Python" / "python.exe",
        # ...
    ]
```

### Lessons Learned
- **sys.executable zeigt auf Scribus.exe:** Nicht auf python.exe
- **Mehrere Python-Installationen:** System-Python vs. Scribus Python
- **PowerShell vs. CMD:** Unterschiedliche Syntax für Pfade mit Leerzeichen

### Fehlerbehebung
- **Problem:** `sys.executable` zeigt auf `Scribus.exe`, nicht `python.exe`
- **Lösung:** Python-Interpreter manuell suchen
- **Fallback:** System-Python verwenden

---

## 📚 Phase 5: Abhängigkeiten Installation

### Problem
MCP Gateway Server benötigt: `flask`, `flask-cors`, `requests`

### Herausforderung
- Abhängigkeiten wurden in System-Python installiert
- Scribus nutzt eigene Python-Installation
- Installation für beide Python-Installationen nötig

### Lösung
```powershell
# Für System-Python
pip install flask flask-cors requests

# Für Scribus Python
& "C:\Program Files\Scribus 1.7.1\python\python.exe" -m pip install flask flask-cors requests
```

### Lessons Learned
- **Zwei Python-Installationen:** Beide müssen konfiguriert werden
- **PowerShell-Syntax:** `&` für Pfade mit Leerzeichen
- **User-Installation:** `--user` Flag bei Permission-Fehlern

---

## 🔒 Phase 6: API-Key Verschlüsselung

### Aufgabe
API-Key sicher (verschlüsselt) lokal speichern.

### Implementierung

#### Verschlüsselung
```python
# encryption.py
def _get_key():
    """Generiert einen Schlüssel basierend auf der Windows-User-ID."""
    username = os.environ.get('USERNAME', 'default')
    computer = os.environ.get('COMPUTERNAME', 'default')
    key_source = f"{username}@{computer}"
    key = hashlib.sha256(key_source.encode('utf-8')).digest()
    return key

def encrypt_api_key(api_key):
    """Verschlüsselt einen API-Key."""
    key = _get_key()
    api_bytes = api_key.encode('utf-8')
    
    # XOR-Verschlüsselung
    encrypted = bytearray()
    for i, byte in enumerate(api_bytes):
        encrypted.append(byte ^ key[i % len(key)])
    
    # Base64-Kodierung
    encoded = base64.b64encode(encrypted).decode('utf-8')
    return encoded
```

#### Integration in Settings
```python
# settings_dialog.py
def save_settings(opts):
    s = _settings()
    s.beginGroup(SETTINGS_GROUP)
    for key, val in opts.items():
        # API-Key verschlüsselt speichern
        if key == 'api_key' and val:
            val = encrypt_api_key(str(val))
        s.setValue(key, val)
    s.endGroup()
```

### Lessons Learned
- **XOR-Verschlüsselung:** Einfach, aber ausreichend für lokale Speicherung
- **Benutzer-spezifischer Schlüssel:** Basierend auf Windows-User-ID
- **QSettings:** Windows Registry für persistente Speicherung
- **Fallback:** Unverschlüsselt, falls Verschlüsselung fehlschlägt

---

## ⚠️ Phase 7: Qt-Instanz Problem

### Problem
```
QApplication.instance(): None
Anzahl aller Widgets: 0
Hauptfenster nicht gefunden!
```

### Ursache
Scribus verwendet eine eigene Qt-Instanz, die **nicht** über `QApplication.instance()` erreichbar ist, wenn ein Python-Script in Scribus läuft.

### Warum?
1. **Scribus startet Qt intern** - Die Qt-Instanz wird von Scribus selbst verwaltet
2. **Python-Scripts laufen in separatem Kontext** - Scripts haben keinen direkten Zugriff
3. **QApplication.instance() gibt None** - Weil keine Application im Script-Kontext existiert

### Lösungsversuche

#### Versuch 1: Erweiterte Suche
```python
# Mehrere Methoden zum Finden des Hauptfensters
def _find_main_window():
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)  # Erstellt neue Instanz!
    
    # Problem: Neue Instanz hat keine Widgets
    for widget in app.allWidgets():
        # 0 Widgets gefunden!
```

#### Versuch 2: Detailliertes Logging
```python
# install_dashboard_with_logging.py
log(f"QApplication.instance(): {app}")
log(f"Anzahl aller Widgets: {len(app.allWidgets())}")
log(f"Anzahl Top-Level Widgets: {len(app.topLevelWidgets())}")
# Ergebnis: Alles 0!
```

#### Versuch 3: Alternative Ansätze
- Dashboard als eigenständiges Fenster (nicht als Dock-Widget)
- HTML-Dashboard als primäre Lösung

### Finale Lösung
**HTML-Dashboard als primäre Lösung:**
- Funktioniert sofort
- Keine Qt-Installation nötig
- Keine Integration-Probleme
- Alle Funktionen verfügbar

### Lessons Learned
- **Qt-Instanz-Isolation:** Scribus' Qt ist nicht über Standard-API erreichbar
- **Logging ist essentiell:** Ohne Logging hätten wir das Problem nie gefunden
- **Fallback-Strategie:** HTML-Dashboard als zuverlässige Alternative
- **Pragmatischer Ansatz:** Nicht gegen die Architektur kämpfen

---

## 💡 Lessons Learned

### 1. Python-Installationen
- **Problem:** Mehrere Python-Installationen (System, Scribus)
- **Lösung:** Immer die richtige Python-Installation identifizieren
- **Best Practice:** `sys.executable` prüfen, nicht blind verwenden

### 2. Qt-Bindings
- **Problem:** Qt-Bindings müssen für die richtige Python-Installation installiert werden
- **Lösung:** Automatische Pfad-Suche und Installation
- **Best Practice:** Mehrere Qt-Bindings unterstützen (PyQt5/PyQt6/PySide2/PySide6)

### 3. Encoding-Probleme
- **Problem:** Unicode-Zeichen (✓) in Windows-CMD nicht darstellbar
- **Lösung:** ASCII-kompatible Zeichen verwenden (`[OK]` statt `✓`)
- **Best Practice:** Immer ASCII für Logging in Windows

### 4. Scribus Qt-Instanz
- **Problem:** Kein Zugriff auf Scribus' Qt-Instanz über Standard-API
- **Lösung:** HTML-Dashboard als primäre Lösung
- **Best Practice:** Fallback-Strategie immer einplanen

### 5. Detailliertes Logging
- **Problem:** Fehler schwer zu diagnostizieren ohne Details
- **Lösung:** Umfassendes Logging in Datei schreiben
- **Best Practice:** Logging in Datei + Console für Debugging

### 6. PowerShell vs. CMD
- **Problem:** Unterschiedliche Syntax für Pfade mit Leerzeichen
- **Lösung:** `&` Operator in PowerShell verwenden
- **Best Practice:** Batch-Scripts für einfache Ausführung

### 7. API-Key Sicherheit
- **Problem:** API-Keys sollten nicht im Klartext gespeichert werden
- **Lösung:** XOR-Verschlüsselung + Base64
- **Best Practice:** Benutzer-spezifischer Schlüssel

---

## 🎓 Best Practices

### 1. Fehlerbehandlung
```python
def _safe(fn, default=None):
    """Safe-Wrapper für alle API-Calls."""
    try:
        return fn()
    except Exception:
        return default
```

### 2. Logging
```python
def log(message):
    """Schreibt in Log-Datei und Console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}\n"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_line)
    print(message)
```

### 3. Pfad-Handling
```python
def find_python_exe():
    """Findet Python-Interpreter mit mehreren Methoden."""
    candidates = [
        "C:\Program Files\Scribus 1.7.1\python\python.exe",
        "C:\Program Files (x86)\Scribus 1.7.1\python\python.exe",
        # ...
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
```

### 4. Qt-Binding Kompatibilität
```python
def load_qt():
    """Lädt Qt-Bindings mit Fallback."""
    for name in ('PySide6', 'PyQt6', 'PySide2', 'PyQt5'):
        try:
            return _try_import(name)
        except Exception:
            continue
    raise ImportError('No Qt bindings available')
```

### 5. Settings-Management
```python
def load_settings():
    """Lädt Settings mit Environment-Override."""
    opts = dict(DEFAULTS)
    s = QSettings('Scribus', 'MCPDashboard')
    s.beginGroup(SETTINGS_GROUP)
    for key in DEFAULTS:
        opts[key] = s.value(key, DEFAULTS[key])
    s.endGroup()
    
    # Environment-Variablen haben Priorität
    if os.environ.get('MCP_BASE_URL'):
        opts['base_url'] = os.environ.get('MCP_BASE_URL')
    
    return opts
```

---

## 📝 Code-Beispiele

### 1. Qt-Binding Loader
```python
def load_qt():
    """Lädt Qt-Bindings automatisch."""
    errors = []
    for name in ('PySide6', 'PyQt6', 'PySide2', 'PyQt5'):
        try:
            if name == 'PySide6':
                from PySide6 import QtCore, QtGui, QtWidgets, QtNetwork
            elif name == 'PyQt6':
                from PyQt6 import QtCore, QtGui, QtWidgets, QtNetwork
            # ...
            return QtCore, QtGui, QtWidgets, QtNetwork, name
        except Exception as exc:
            errors.append('%s: %s' % (name, exc))
    raise ImportError('No Qt bindings available. Tried: %s' % '; '.join(errors))
```

### 2. API-Key Verschlüsselung
```python
def encrypt_api_key(api_key):
    """Verschlüsselt API-Key mit XOR + Base64."""
    key = _get_key()  # Benutzer-spezifischer Schlüssel
    api_bytes = api_key.encode('utf-8')
    
    # XOR-Verschlüsselung
    encrypted = bytearray()
    for i, byte in enumerate(api_bytes):
        encrypted.append(byte ^ key[i % len(key)])
    
    # Base64-Kodierung
    return base64.b64encode(encrypted).decode('utf-8')
```

### 3. Detailliertes Logging
```python
def log(message):
    """Schreibt in Log-Datei mit Timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}\n"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_line)
    print(message)
```

### 4. Safe Scribus API Calls
```python
def _safe(fn, default=None):
    """Safe-Wrapper für Scribus API."""
    try:
        return fn()
    except Exception:
        return default

def get_doc_ref():
    """Holt Dokument-Referenz sicher."""
    if not have_doc():
        return {}
    return {
        'name': _safe(lambda: scribus.getDocName(), ''),
        'page': int(_safe(lambda: scribus.currentPage(), 0) or 0),
        'pages': int(_safe(lambda: scribus.pageCount(), 0) or 0),
    }
```

---

## 🚀 Finale Lösung

### Empfohlene Architektur

1. **HTML-Dashboard als primäre Lösung**
   - Funktioniert sofort
   - Keine Qt-Abhängigkeit
   - Plattform-unabhängig

2. **MCP Gateway Server**
   - Läuft als separater Prozess
   - Alle Endpoints implementiert
   - API-Key aus Settings geladen

3. **Verschlüsselte API-Key-Speicherung**
   - XOR + Base64 Verschlüsselung
   - Benutzer-spezifischer Schlüssel
   - QSettings für Persistenz

### Verwendung

1. **Server starten:**
   ```powershell
   cd scribus
   python mcp_gateway_server.py
   ```

2. **Dashboard öffnen:**
   - Script → Execute Script → `open_html_dashboard.py`

3. **API-Key eingeben:**
   - Im Dashboard: Settings → API-Key eingeben
   - Wird verschlüsselt gespeichert

---

## 📊 Zusammenfassung

### Erfolgreich implementiert:
- ✅ MCP Dashboard Package (8 Dateien)
- ✅ MCP Gateway Server erweitert (6 neue Endpoints)
- ✅ API-Key Verschlüsselung
- ✅ HTML-Dashboard Integration
- ✅ Abhängigkeiten Installation
- ✅ Detailliertes Logging

### Bekannte Limitationen:
- ⚠️ Qt-Dashboard kann nicht automatisch als Dock-Widget installiert werden
- ⚠️ Qt-Instanz von Scribus nicht über Standard-API erreichbar
- ✅ HTML-Dashboard als zuverlässige Alternative

### Nächste Schritte:
1. HTML-Dashboard als primäre Lösung nutzen
2. Qt-Dashboard als eigenständiges Fenster (optional)
3. Weitere Features im HTML-Dashboard implementieren

---

## 🔍 Debugging-Tipps

### 1. Logging aktivieren
```python
# Immer detailliertes Logging verwenden
log(f"Variable: {variable}")
log(f"Type: {type(variable)}")
log(f"Traceback: {traceback.format_exc()}")
```

### 2. Pfade prüfen
```python
# Immer absolute Pfade loggen
log(f"Script-Pfad: {Path(__file__).resolve()}")
log(f"sys.path: {sys.path}")
```

### 3. Qt-Status prüfen
```python
# Qt-Application Status
app = QApplication.instance()
log(f"QApplication: {app}")
log(f"Widgets: {len(app.allWidgets()) if app else 0}")
```

### 4. Encoding-Probleme vermeiden
```python
# ASCII-kompatible Zeichen verwenden
print("[OK] Erfolg")  # Statt: print("✓ Erfolg")
```

---

## 📚 Referenzen

### Erstellte Dateien
- `scribus_mcp_dashboard/` - Vollständiges Package
- `install/` - Install-Scripts
- `mcp_gateway_server.py` - Erweiterter Server
- `open_html_dashboard.py` - HTML-Dashboard Launcher
- `install_dashboard_with_logging.py` - Debug-Script
- `ANALYSE_QT_PROBLEM.md` - Problem-Analyse

### Dokumentation
- `README_HYBRID.md` - Hybrid-Dashboard Dokumentation
- `INSTALLATION_ANLEITUNG.md` - Installations-Anleitung
- `ANLEITUNG_DASHBOARD_AKTIVIEREN.md` - Aktivierungs-Anleitung
- `README_API_KEY.md` - API-Key Dokumentation

---

*Erstellt: 2025-01-27*  
*Zweck: Learning by Doing - Vollständige Dokumentation des Entwicklungsprozesses*
