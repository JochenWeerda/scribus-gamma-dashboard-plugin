# Plugin-Vergleich: MCP Dashboard vs. Gamma Dashboard

## Status: MCP Dashboard Plugin nicht gefunden

Das MCP Dashboard Plugin wurde im Workspace nicht gefunden. Bitte gib an:
- Repository URL
- Lokaler Pfad
- Oder bereitstellen der relevanten Dateien

## Was wir bereits haben (Gamma Dashboard)

Unser Plugin basiert auf den Standard-Scribus-Plugin-Patterns:

### Aktuelle Implementierung:
- **Basis:** `ScActionPlugin` (für Einmal-Aktionen)
- **Architektur:** C++ Plugin → Python Script (QProcess)
- **Vorteil:** Nicht-blockierend, läuft im separaten Prozess

### Verbesserungen, die wir vom MCP Dashboard lernen könnten:

#### 1. **Dock Widget Integration**
Falls MCP Dashboard ein `QDockWidget` verwendet:
- Native Integration in Scribus-UI
- Persistentes Fenster
- Bessere UX als separates Fenster

#### 2. **Direkte Qt-GUI statt Python**
Falls MCP Dashboard die GUI direkt in C++ implementiert:
- Schnellere Performance
- Bessere Integration
- Kein Python-Prozess nötig

#### 3. **ScPersistentPlugin statt ScActionPlugin**
Falls MCP Dashboard persistent läuft:
- Plugin bleibt geladen
- Kann UI-Elemente persistent halten
- Bessere Integration in Scribus-Workflow

## Empfehlung

**Option A: Warte auf MCP Dashboard Code**
- Analysiere die Implementierung
- Übernehme bewährte Patterns
- Mergen relevante Teile

**Option B: Weiter mit aktueller Implementierung**
- Basiert auf Standard-Patterns
- Funktioniert bereits
- Kann später erweitert werden

**Option C: Hybrid-Ansatz**
- Starte mit aktueller Implementierung
- Erweitere später mit Dock-Widget
- Konvertiere zu ScPersistentPlugin wenn nötig

## Nächste Schritte

Bitte gib an:
1. **Wo ist das MCP Dashboard Plugin?**
   - Pfad oder URL
   
2. **Oder soll ich weitermachen?**
   - Aktuelles Plugin ist production-ready
   - Kann später verbessert werden

