# MVP Artefakte: Layout JSON → SLA Compiler

## Übersicht

Dieses MVP-Paket enthält die Grundlagen für einen **Headless Layout-Compiler**, der:
- **JSON-Layout-Definitionen** (nach Schema) entgegennimmt
- Diese in **Scribus SLA-Dateien** kompiliert
- **PNG (72 DPI)** und **PDF (300 DPI)** exportiert
- Alles über **MinIO/S3** speichert (keine großen Inline-Payloads)

## Dateien

| Datei | Beschreibung |
|-------|-------------|
| `layout-mvp.schema.json` | JSON Schema für Layout-Definitionen |
| `example_layout_mvp.json` | Beispiel-Dokument (1 Seite: Background + Hero + Titel + Subtitle) |
| `db_mvp.sql` | PostgreSQL Schema (Jobs, Artefakte, Logs, Pages, Assets) |
| `README_MVP_Artefakte.md` | Diese Datei |

## Kurzregeln

### 1. Einheiten

- **Koordinaten/Abmessungen:** Pixel (px)
- **Schriftgröße:** Punkt (pt) - Standard DTP-Einheit
- **DPI:** Standard 72 DPI (Screen), 300 DPI (Print)

**Wichtig:** Bei der Kompilierung von px → mm/pt muss die DPI berücksichtigt werden:
- `mm = (px / DPI) * 25.4`
- Beispiel: 2480 px @ 300 DPI = 210 mm (A4 Breite)

### 2. Layer-Reihenfolge (Z-Order)

Standard-Layer-Namen (von unten nach oben):
1. `Background` (zOrder: 0-9)
2. `Images_BG` (zOrder: 10-19)
3. `Images` (zOrder: 20-29)
4. `Text` (zOrder: 30-39)
5. `Overlay` (zOrder: 40-49)
6. `Wrap` (zOrder: 50+)

**Regel:** Falls `zOrder` nicht gesetzt ist, wird es automatisch aus dem Layer-Namen abgeleitet.

### 3. Objekt-Typen

#### Text
- `content`: Text-Inhalt (kann leer sein für Platzhalter)
- `fontFamily`, `fontSize`, `fontWeight`, `color`: Text-Formatierung
- `align`: Ausrichtung (left, center, right, justify)
- `columns`, `columnGap`: Spaltensatz

#### Image
- `imageUrl`: URL/Pfad zum Bild (vorzuziehen)
- `imageData`: Base64-encodiertes Bild (Alternative)
- `scaleToFrame`, `maintainAspectRatio`: Skalierungs-Optionen

#### Rectangle
- `fillColor`, `fillOpacity`: Füllung
- `strokeColor`, `strokeWidth`, `strokeOpacity`: Umrandung
- `cornerRadius`: Eckradius (0 = scharfe Ecken)

### 4. Storage-Strategie

**Prinzip:** Keine großen Inline-Payloads in der DB!

- **Layout-JSON:** Als Artefakt in MinIO/S3 → `artifacts.storage_uri`
- **SLA-Dateien:** Als Artefakt in MinIO/S3 → `artifacts.storage_uri`
- **PNG/PDF-Exporte:** Als Artefakt in MinIO/S3 → `artifacts.storage_uri`
- **Bilder:** Als Artefakt in MinIO/S3 → `artifacts.storage_uri`

**DB speichert nur:**
- Metadaten (IDs, URIs, Checksums, Größen)
- Referenzen (`artifacts.id`, `jobs.input_artifact_id`, etc.)

### 5. MVP-Flow

```
1. API nimmt JSON an
   → Validierung gegen Schema
   → Speichern als Artefakt (MinIO/S3)
   → Job erstellen (status: 'pending')

2. Worker pickt Job
   → Job-Status: 'running'
   → JSON aus Artefakt laden
   → Kompilierung (JSON → SLA)
   → SLA als Artefakt speichern
   → Job.output_artifact_id setzen
   → Job-Status: 'completed'

3. Export-Job (optional)
   → SLA aus Artefakt laden
   → PNG exportieren (72 DPI)
   → PDF exportieren (300 DPI)
   → Artefakte speichern
   → pages.png_artifact_id / pdf_artifact_id setzen
```

## Schema-Validierung

```python
import json
import jsonschema

# Schema laden
with open('layout-mvp.schema.json', 'r') as f:
    schema = json.load(f)

# Layout-JSON laden
with open('example_layout_mvp.json', 'r') as f:
    layout = json.load(f)

# Validieren
jsonschema.validate(instance=layout, schema=schema)
```

## DB-Verwendung

### Job erstellen

```sql
-- 1. Artefakt (JSON) erstellen
INSERT INTO artifacts (artifact_type, storage_type, storage_uri, file_name, file_size, mime_type)
VALUES ('layout_json', 's3', 's3://bucket/layouts/layout_001.json', 'layout_001.json', 1024, 'application/json')
RETURNING id;

-- 2. Job erstellen
INSERT INTO jobs (input_artifact_id, status, job_type, metadata)
VALUES ('<artifact_id>', 'pending', 'compile', '{"dpi": 300, "export_formats": ["png", "pdf"]}'::jsonb)
RETURNING id;
```

### Job-Status prüfen

```sql
SELECT j.*, input_a.storage_uri AS input_uri, output_a.storage_uri AS output_uri
FROM jobs j
LEFT JOIN artifacts input_a ON j.input_artifact_id = input_a.id
LEFT JOIN artifacts output_a ON j.output_artifact_id = output_a.id
WHERE j.id = '<job_id>';
```

### Logs abrufen

```sql
SELECT log_level, message, created_at
FROM job_logs
WHERE job_id = '<job_id>'
ORDER BY created_at ASC;
```

### Pages mit Export-URIs

```sql
SELECT p.page_number, png_a.storage_uri AS png_uri, pdf_a.storage_uri AS pdf_uri
FROM pages p
LEFT JOIN artifacts png_a ON p.png_artifact_id = png_a.id
LEFT JOIN artifacts pdf_a ON p.pdf_artifact_id = pdf_a.id
WHERE p.job_id = '<job_id>'
ORDER BY p.page_number;
```

## Nächste Schritte

### 1. FastAPI-Routes (MVP)

```python
POST /api/v1/layouts/compile
  → Nimmt JSON entgegen
  → Validiert gegen Schema
  → Speichert als Artefakt
  → Erstellt Job
  → Gibt job_id zurück

GET /api/v1/jobs/{job_id}
  → Gibt Job-Status + Artefakt-URIs zurück

GET /api/v1/jobs/{job_id}/logs
  → Gibt Job-Logs zurück

GET /api/v1/jobs/{job_id}/pages
  → Gibt Pages mit Export-URIs zurück
```

### 2. Worker (RQ/Celery)

```python
@worker.task
def compile_layout_job(job_id):
    # 1. Job aus DB laden
    # 2. JSON-Artefakt aus MinIO/S3 laden
    # 3. Validierung (optional, nochmal prüfen)
    # 4. JSON → SLA Kompilierung
    # 5. SLA als Artefakt speichern
    # 6. Job-Status aktualisieren
    # 7. Optional: PNG/PDF-Export triggern
```

### 3. Kompilierung (JSON → SLA)

```python
def compile_json_to_sla(layout_json: dict) -> bytes:
    # 1. Scribus-Dokument erstellen
    # 2. Seiten erstellen
    # 3. Objekte aus JSON erstellen (Text/Image/Rectangle)
    # 4. Layer + Z-Order anwenden
    # 5. SLA-Datei exportieren
    # 6. Bytes zurückgeben
```

## Beispiel: Komplette Pipeline

```python
# 1. Layout-JSON validieren
layout = json.load(open('example_layout_mvp.json'))
validate_layout(layout)  # gegen Schema

# 2. Als Artefakt speichern
artifact_id = save_artifact_to_s3(layout, 'layout_001.json')

# 3. Job erstellen
job_id = create_job(artifact_id, job_type='compile')

# 4. Worker triggern (async)
compile_layout_job.delay(job_id)

# 5. Status prüfen (polling oder Webhook)
status = get_job_status(job_id)
# → 'running' → 'completed'

# 6. Export-URIs abrufen
output_uri = get_job_output_uri(job_id)
# → 's3://bucket/outputs/layout_001.sla'

# 7. Optional: PNG/PDF exportieren
export_job_id = create_export_job(output_artifact_id, formats=['png', 'pdf'])
```

## Technologie-Stack (Empfehlung)

- **API:** FastAPI (Python)
- **Validation:** jsonschema (Python)
- **Database:** PostgreSQL
- **Storage:** MinIO (S3-kompatibel) oder AWS S3
- **Queue:** RQ (Redis Queue) oder Celery (Redis/RabbitMQ)
- **Worker:** Python (Scribus Python API)
- **Export:** Scribus Headless (via Python API)

## Hinweise

- **MVP-Fokus:** Einfache Text/Bild/Rechteck-Objekte
- **Erweiterbar:** Schema kann später erweitert werden (z.B. Spaltensatz, Tabellen, etc.)
- **Storage:** MinIO für lokale Entwicklung, S3 für Production
- **Skalierung:** Worker können horizontal skaliert werden (mehrere Worker pro Queue)

---

*Letzte Aktualisierung: 2025-01-27*

