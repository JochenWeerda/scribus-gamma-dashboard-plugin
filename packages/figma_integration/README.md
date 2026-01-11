# Figma Integration

Bidirektionale Integration mit Figma für Frame-Import und -Export.

## Features

- **Frame-Import**: Importiert Figma Frames als neue Scribus-Seiten
- **Frame-Export**: Exportiert Scribus-Seiten als Figma Frames
- **Asset-Download**: Lädt Images aus Figma herunter und speichert sie in MinIO
- **Layout-Konvertierung**: Konvertiert zwischen Figma Frame JSON und Layout JSON Schema
- **Compiler-Integration**: Automatischer Compiler-Aufruf nach Import
- **RAG-Integration**: Automatisches RAG-Indexing nach Import

## Installation

```bash
pip install -r requirements.txt
```

## Konfiguration

### Figma Personal Access Token

```bash
export FIGMA_ACCESS_TOKEN=<TOKEN>
```

### MinIO (optional, für Asset-Storage)

```bash
export MINIO_ENDPOINT=localhost:9000
export MINIO_ACCESS_KEY=minioadmin
export MINIO_SECRET_KEY=minioadmin
```

## Verwendung

### Backend

```python
from packages.figma_integration import FigmaClient, FrameToLayoutConverter

# Initialisiere Client
client = FigmaClient(access_token="...")

# Liste aller Files
# Hinweis: Figma bietet kein generisches "GET /files". Ohne Parameter wird versucht, über
# /me -> teams -> projects zu aggregieren. Je nach Account/API kann `/me` keine Teams liefern;
# dann ist eine Datei-Liste nicht automatisch möglich (verwende direkt bekannte `file_key`s).
files = client.list_files()

# Frame abrufen und konvertieren
frame = client.get_frame(file_key="abc123", frame_id="123:456")
converter = FrameToLayoutConverter()
layout_json = converter.convert(frame, dpi=300, page_number=1)
```

### API Endpoints

- `GET /api/figma/health` - Service-Status
- `GET /api/figma/me` - Aktueller User (inkl. teams)
- `GET /api/figma/projects?team_id=...` - Projekte eines Teams
- `GET /api/figma/projects/{project_id}/files` - Dateien eines Projekts
- `GET /api/figma/files?team_id=...&project_id=...` - Aggregierte Datei-Liste (optional)
- `GET /api/figma/files/{file_key}/frames` - Liste aller Frames
- `POST /api/figma/frames/import` - Import Frame (mit Compiler + RAG)
- `POST /api/figma/frames/export` - Export Scribus-Seite nach Figma

### Frontend (Plugin)

1. **Import Frame**: Menü "Extras → Import Frame from Figma..."
2. **Export Page**: Menü "Extras → Export Page to Figma..."

## Import-Pipeline

Der `/api/figma/frames/import` Endpoint führt automatisch aus:

1. Frame von Figma abrufen
2. Frame → Layout JSON konvertieren
3. Images zu MinIO migrieren
4. RAG-Indexing (automatisch)
5. Compiler aufrufen (`compile_layout_to_sla`)
6. Digital Twin Indexing (Compiler-Ergebnis)
7. Response: Layout JSON + SLA XML (hex) + RAG Layout ID

## Integration mit Compiler

Nach Frame-Import wird automatisch:
1. Layout JSON erstellt
2. Images zu MinIO migriert
3. RAG-Indexing durchgeführt
4. Compiler aufgerufen (`compile_layout_to_sla`)
5. SLA XML zurückgegeben
6. Neue Seite in Scribus eingefügt (via Plugin)

## Integration mit RAG

Figma-Import wird automatisch im RAG-System indexiert:
- Layout-Struktur
- Text-Objekte
- Bild-Objekte
- Text-Bild-Zuordnungen
- Compiler-Ergebnisse (Digital Twin)

## Beispiel

```python
# Frame importieren
response = requests.post(
    "http://localhost:8005/api/figma/frames/import",
    json={
        "file_key": "abc123",
        "frame_id": "123:456",
        "dpi": 300,
        "page_number": 1
    }
)

result = response.json()
layout_json = result["layout_json"]
sla_xml_hex = result["sla_xml_bytes"]  # Hex-encoded
sla_xml = bytes.fromhex(sla_xml_hex)   # Decode
layout_id = result["layout_id"]        # RAG Layout ID
```

## SLA-Einfügung in Scribus

Das Plugin verwendet `GammaSLAInserter` zum Einfügen von SLA XML:

1. SLA XML aus API-Response extrahieren (hex → bytes)
2. `insertSLAAsPage()` aufrufen
3. Neue Seite wird automatisch eingefügt

## Token-Sicherheit

**WICHTIG**: Token niemals in Git committen!

- Verwende Environment-Variablen
- Verwende `.env` Dateien (in `.gitignore`)
- Token regelmäßig rotieren
