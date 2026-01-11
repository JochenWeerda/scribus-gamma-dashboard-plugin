# Projektdossier: Hybride Headless Layout-Engine (SLA)

**Datum:** 2. Januar 2026  
**Thema:** Automatisierung von Print-Layouts aus virtuellen Welten  
**Umfang:** Vollständige technische Spezifikation (v1.0)

---

## 1. Einleitung & Zielsetzung

Ziel des Projekts ist die Ablösung instabiler GUI-Automatisierungen (z. B. UI-Scripting/Clicks) durch einen robusten hybriden **Compiler-Ansatz**:

1. Layout-Daten werden aus einer virtuellen Umgebung (3D/Browser/Editor) als **JSON** exportiert.  
2. Ein **SLA-Compiler** übersetzt diese Daten deterministisch in das XML-basierte Scribus-Format **.sla**.  
3. Eine **headless Scribus-Worker-Infrastruktur** rendert daraus Vorschauen (PNG) sowie das finale Druck-PDF.

**Nutzen:**
- Reproduzierbare Builds (Layout = Code)
- Skalierung über Worker-Pools (Parallelisierung pro Dokument/Seite/Job)
- Besseres Debugging (SLA als Artefakt, Diff-fähig)
- Stabilere CI/CD-Pipeline (ohne GUI-Flakes)

---

## 2. Ressourcen & Infrastruktur

### 2.1 Server-Anforderungen

- **CPU:** Multi-Core (Layout-Generierung ist parallelisierbar pro Dokument/Seite)  
- **RAM:** mindestens 8 GB (Scribus benötigt beim Laden großer Assets signifikanten Speicher)  
- **Betriebssystem:** Linux (Ubuntu LTS empfohlen für Docker-Kompatibilität)  
- **Storage:** SSD empfohlen (Assets + Render-Caches), optional Object-Storage (S3/MinIO)  

Empfehlung für produktive Umgebung (Start):
- 8 vCPU / 16–32 GB RAM / 200+ GB SSD

### 2.2 Docker-Container-Architektur

Multi-Container-Setup (logisch getrennte Rollen):

1. **API-Gateway (Python/FastAPI)**  
   - Empfängt Layout-JSON  
   - Validiert Schema & referenzierte Assets  
   - Erzeugt Render-Jobs und orchestriert Worker  
   - Liefert Vorschauen/Status an das Frontend

2. **Compiler-Service (Python)** *(kann Teil des Gateways sein)*  
   - Transformiert JSON → SLA (XML)  
   - Integriert Templates/Styles  
   - Sichert deterministische Builds (IDs, Reihenfolge, Fonts, Fallbacks)

3. **Worker-Node (Scribus headless)**  
   - Basis: Ubuntu mit installiertem **Scribus 1.5.x**  
   - Tooling: **Xvfb** (Virtual Framebuffer), damit Scribus ohne Monitor läuft  
   - Aufgabe: SLA laden, Preflight, PNG-Preview, PDF-Export

4. **Database (PostgreSQL)**  
   - Speicherung von Templates, Style-Presets, Asset-Metadaten, Job-Status, Audit-Logs

5. **Asset Storage**  
   - Start: Volume-Mount (lokal)  
   - Später: S3/MinIO + lokaler Worker-Cache

### 2.3 WYSIWYG & Viewer (Machbarkeit)

Ein nativer .sla-Viewer im Browser ist nicht praktikabel. Der Workflow erfolgt über Proxy-Rendering:

- Server generiert nach dem XML-Compile ein schnelles **PNG** (z. B. 72 DPI) pro Seite  
- Frontend zeigt die PNGs im **React/Canvas** als interaktive Vorschau  
- Finale Validierung findet beim **PDF-Export** statt (Anzeige z. B. über PDF.js im Frontend)

---

## 3. Technische Machbarkeit & Logik

### 3.1 Koordinaten-Mapping

Die Umrechnung von 3D-Koordinaten oder relativen Web-Koordinaten in Scribus-Points (**1/72 Inch**) ist mathematisch stabil:

**Formel:**  
`Points = (Pixel / DPI) * 72`

Zusätzlich empfohlen:
- feste **Referenz-DPI** pro Projekt (z. B. 144 oder 300), um Rundungsartefakte zu minimieren  
- „Snap to grid" in der Compiler-Phase (optional, für konsistente Typografie)

Beispiele:
- 300 px bei 150 DPI → (300/150)*72 = 144 pt  
- 900 px bei 300 DPI → (900/300)*72 = 216 pt  

### 3.2 UML Aktivitätsdiagramm (Pipeline)

```mermaid
flowchart TD
  A[Layout-JSON aus virtueller Welt] --> B[Schema-Validation]
  B --> C{Assets verfügbar?}
  C -- nein --> C1[Fehler + Missing-Asset Report] --> Z[Job FAILED]
  C -- ja --> D[Template/Styles anwenden]
  D --> E[SLA-Compiler: JSON -> .sla XML]
  E --> F[Persistiere SLA + Job-Metadaten]
  F --> G[Queue Render-Job]
  G --> H[Worker: Scribus headless (Xvfb)]
  H --> I[Preflight: Fonts/Links/Overflow]
  I --> J{Preview?}
  J -- ja --> K[PNG 72 DPI Render] --> L[Frontend Preview]
  J -- nein --> M[PDF Export (300 DPI / CMYK)]
  K --> M
  M --> N[Quality Checks: PDF/A, Bleed, Cropmarks]
  N --> O{OK?}
  O -- nein --> O1[Report + Artefakte] --> Z
  O -- ja --> P[Job SUCCESS: PDF + Preview + Logs]
```

---

## 4. Datenmodell (Layout-JSON)

### 4.1 Prinzipien

- JSON ist **seitenbasiert** und **komponentisiert** (Text, Bild, Shape, Gruppe)
- Jede Entität ist **idempotent** und besitzt eine **stabile ID**
- Layout-Engine arbeitet deterministisch: gleiche Inputs → gleiche SLA → gleiches PDF

### 4.2 Beispielstruktur (vereinfachtes Schema)

```json
{
  "document": {
    "id": "doc_2026_01_02_001",
    "format": { "width_mm": 210, "height_mm": 297, "bleed_mm": 3 },
    "color_profile": { "mode": "CMYK", "icc": "ISOcoated_v2_300.icc" },
    "fonts": [
      { "family": "Inter", "files": ["Inter-Regular.ttf", "Inter-Bold.ttf"] }
    ]
  },
  "pages": [
    {
      "index": 1,
      "layers": [
        { "name": "Background", "locked": true },
        { "name": "Content", "locked": false }
      ],
      "elements": [
        {
          "id": "t_hero_title",
          "type": "text",
          "layer": "Content",
          "box": { "x_px": 120, "y_px": 140, "w_px": 1800, "h_px": 240 },
          "style": { "paragraph": "H1", "align": "left" },
          "content": "Automatisierung von Print-Layouts"
        },
        {
          "id": "img_01",
          "type": "image",
          "layer": "Content",
          "box": { "x_px": 120, "y_px": 420, "w_px": 2200, "h_px": 1200 },
          "asset": { "uri": "s3://assets/cover.png" },
          "fit": "cover"
        }
      ]
    }
  ]
}
```

---

## 5. SLA-Compiler-Spezifikation

### 5.1 Eingaben

- Layout-JSON (validiert gegen JSON Schema)  
- Template-Paket (optional):  
  - Scribus-Template (.sla) als Basis  
  - Style-Definitionen (Paragraph/Character Styles)  
  - Farbpalette/ICC Profiles  
- Asset-Repository (Pfad/S3)  
- Build-Konfiguration:
  - Ziel-DPI (Preview/Final)
  - Raster/Snapping-Regeln
  - Fallback-Fonts
  - Preflight-Regeln (Overflows, Missing Fonts, Missing Links)

### 5.2 Ausgaben

- `.sla` (kompilierte Scribus-Datei)  
- `build.json` (Build-Metadaten: Hashes, Zeiten, Versionsinfo)  
- optional: `preflight.json` (Warnings/Errors)  

### 5.3 Determinismus

- Element-Reihenfolge: `z_index` oder stabiler Sort-Key  
- IDs: Hash-basiert (z. B. `sha1(pageIndex + element.id)`)  
- Floating-Point: definierte Rundung (z. B. 1/100 pt)  
- Fonts: ausschließlich aus definiertem Font-Paket (keine Systemabhängigkeit)

---

## 6. Worker-Rendering (Scribus headless)

### 6.1 Aufgaben eines Workers

1. SLA laden  
2. Links/Assets auflösen (lokaler Cache)  
3. Preflight:
   - fehlende Fonts
   - fehlende Bilder/Links
   - Text-Overflow/Unterlauf (sofern erkennbar)
4. Render Preview (PNG 72 DPI) optional  
5. Export Final-PDF (z. B. 300 DPI, CMYK, Beschnitt, Marken)
6. Artefakte + Logs zurückmelden

### 6.2 Prozesse & Isolation

- Jeder Job läuft in eigenem Container-Prozess (oder Job-Slot)  
- Ressourcenlimits:
  - `--cpus`, `--memory` pro Worker  
  - Timeout (z. B. 10–20 min pro großes Dokument)  
- Output: Artefakt-Upload (S3/Volume), Status in PostgreSQL

---

## 7. API-Design (FastAPI)

### 7.1 Endpunkte (Minimum Viable)

- `POST /v1/jobs`  
  - Body: Layout-JSON + Template-Ref + Optionen  
  - Response: job_id

- `GET /v1/jobs/{job_id}`  
  - Status: queued/running/success/failed  
  - Links zu Artefakten (SLA, PNGs, PDF, Logs)

- `GET /v1/jobs/{job_id}/preview/{page}`  
  - Liefert PNG

- `GET /v1/jobs/{job_id}/artifact/pdf`  
  - Liefert PDF

### 7.2 Auth & Security

- API-Key/JWT  
- Rate-Limits am Gateway  
- Asset-URIs nur aus Whitelist-Domains/Buckets  
- Input-Härtung:
  - JSON Schema Validation
  - maximale Dokumentgröße/Elementzahl
  - Virus-Scan optional für User-Uploads

---

## 8. Datenbankmodell (PostgreSQL)

### 8.1 Tabellen (Vorschlag)

- `templates`
  - id, name, version, sla_base_uri, created_at
- `assets`
  - id, uri, type, checksum, width, height, created_at
- `jobs`
  - id, status, options_json, template_id, created_at, updated_at
- `job_pages`
  - job_id, page_index, preview_uri, render_time_ms
- `job_logs`
  - job_id, level, message, created_at
- `job_artifacts`
  - job_id, kind (sla/pdf/preflight), uri, checksum

---

## 9. Qualitätskontrollen (Preflight)

Empfohlene Regeln:

- **Fonts:** vollständig eingebettet oder verlinkt; keine Substitutionswarnungen  
- **Bilder:** Mindestauflösung (z. B. 250–300 DPI am Endformat)  
- **Farben:** CMYK konform (bei Print), optional Spot Colors  
- **Beschnitt:** Bleed vorhanden; keine wichtigen Inhalte in Bleed/Trim-Zone  
- **Text:** Overflow-Check (wenn Scribus-API dies zuverlässig meldet)  
- **PDF:** optional PDF/X-Profile (Druckerei-Anforderung)

---

## 10. Observability & Betrieb

- Logging: strukturierte Logs (JSON), Job-correlation-id  
- Metrics:
  - Queue-Länge, Render-Zeiten, Fehlerraten
  - CPU/RAM pro Job
- Tracing: optional OpenTelemetry  
- Dashboards: Grafana + Prometheus (oder Alternativen)

---

## 11. CI/CD & Deployment

- GitHub Actions / GitLab CI:
  - Lint + Tests (Compiler)
  - Integrationstests (kleines SLA + Headless Export)
  - Build/Push Docker-Images
  - Deploy (Compose/K8s)

Deployment-Optionen:
- **Docker Compose** (Start)  
- **Kubernetes** (Scale-out) mit Worker-Autoscaling

---

## 12. Risiken & Mitigation

- **Scribus-Versionen:** Verhalten kann je nach 1.5.x variieren → pinnen, reproduzierbare Images  
- **Fonts & Lizenz:** klare Font-Pakete + Lizenznachweise  
- **Performance:** große Assets → Pre-Resize + Cache  
- **Feature-Lücken:** manche Layout-Details evtl. nicht trivial in SLA → Template-first Ansatz

---

## 13. Roadmap (empfohlen)

1. **MVP**
   - JSON Schema + Compiler (Text/Bild/Boxen)
   - Headless Worker exportiert PNG+PDF
2. **Template-System**
   - Styles, Master-Pages, automatische Inhaltsverzeichnisse
3. **Erweiterter Preflight**
   - DPI-Regeln, Color-Policy, Overflow
4. **Scaling**
   - Worker-Pool, Retry-Policy, Autoscaling
5. **WYSIWYG-Proxy**
   - Interaktive Vorschau (PNG + Hotspots) + Diff-Ansicht

---

## Anhang A – Einheiten & Konvertierungen

- 1 Inch = 25,4 mm  
- 1 pt = 1/72 Inch  
- mm → pt: `pt = (mm / 25.4) * 72`  
- px → pt: `pt = (px / dpi) * 72`

---

**Ende des Dokuments**

