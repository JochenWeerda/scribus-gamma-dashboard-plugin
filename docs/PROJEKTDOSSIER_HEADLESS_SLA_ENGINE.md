# Projektdossier: Headless SLA-Layout & Publishing Engine

**Version:** 1.0  
**Status:** Systemarchitektur & Machbarkeitsstudie  
**Fokus:** Automatisierte Generierung von Scribus-Dokumenten aus virtuellen Welten

---

## 1. Executive Summary

Dieses Dossier beschreibt den Übergang von instabiler **GUI-Automatisierung** (klick-/fensterabhängige Abläufe) hin zur direkten Erzeugung des **Scribus-SLA-Formats** (XML-basiert). Durch diesen **Compiler-Ansatz** wird die Layout-Erstellung von der grafischen Oberfläche entkoppelt, was **Skalierbarkeit**, **Geschwindigkeit** und **Fehlerresistenz** deutlich erhöht.

Kernidee:
- Layoutdaten werden aus einer virtuellen Umgebung als **JSON** exportiert.
- Ein **SLA-Compiler** übersetzt JSON deterministisch nach **.sla (XML)**.
- **Headless Scribus-Worker** übernehmen Feinberechnung/Preflight und den **PDF-Export**.

---

## 2. Systemarchitektur & UML

### 2.1 Der hybride Workflow

Die Engine arbeitet in zwei klar getrennten Phasen:

1. **SLA-Compiler (Headless)**
   - Erzeugt die physikalische Struktur: **Seiten**, **Layer**, **Geometrie**, **Z-Order**, **Asset-Links**, **Styles/Defaults**
   - Garantiert deterministische Artefakte (gleiches Input → gleiches SLA)

2. **Scribus-Worker (Docker, headless)**
   - Lädt das SLA in Scribus (z. B. 1.5.x)
   - Übernimmt typografische Feinberechnung, **Preflight** (Fonts/Links/Overflow je nach Machbarkeit)
   - Exportiert **PNG-Previews** und **druckfertige PDFs**

---

### 2.2 UML Aktivitätsdiagramm

```mermaid
flowchart TD
  A[Layoutdaten aus virtueller Welt (JSON)] --> B[Schema-Validation]
  B --> C{Assets & Fonts vorhanden?}
  C -- nein --> C1[Fehlerreport: Missing Assets/Fonts] --> Z[Job FAILED]
  C -- ja --> D[Apply Template/Styles (optional)]
  D --> E[SLA-Compiler: JSON -> Scribus .sla (XML)]
  E --> F[Persistiere SLA + Build-Metadaten]
  F --> G[Queue Render-Job]
  G --> H[Worker: Scribus headless (Xvfb)]
  H --> I[Preflight: Links/Fonts/Overflows]
  I --> J{Preview gewünscht?}
  J -- ja --> K[Render PNG 72 DPI je Seite] --> L[Frontend Vorschau (Canvas)]
  J -- nein --> M[Export Final-PDF (z.B. 300 DPI, CMYK, Bleed)]
  K --> M
  M --> N[Quality Checks: Bleed/Crop/ICC/PDF-Profile]
  N --> O{OK?}
  O -- nein --> O1[Report + Artefakte + Logs] --> Z
  O -- ja --> P[Job SUCCESS: PDF + Previews + Logs]
```

---

## 3. Komponentenübersicht

### 3.1 API-Gateway (FastAPI)

- nimmt Layout-JSON entgegen
- validiert gegen JSON-Schema
- startet Compiler + Job-Queue
- stellt Status, Previews, PDFs bereit

**Minimal-Endpunkte**
- `POST /v1/jobs` → `job_id`
- `GET /v1/jobs/{job_id}` → Status + Links
- `GET /v1/jobs/{job_id}/preview/{page}` → PNG
- `GET /v1/jobs/{job_id}/artifact/pdf` → PDF

### 3.2 Compiler-Service (JSON → SLA)

- Mapping von Koordinaten/Boxen in Scribus-Units (pt)
- Layer/Z-Order deterministisch
- Style-Resolver (Paragraph/Character Styles, Fallbacks)
- Asset-Resolver (lokal/S3/MinIO) inkl. Checksums

### 3.3 Worker-Service (Scribus headless)

- Xvfb + Scribus
- Laden SLA, relinken Assets
- Export PNG (schnell) und PDF (final)
- Logs + Preflight-Report

### 3.4 Datenbank (PostgreSQL)

- Templates (Versionierung)
- Assets (Metadaten, Checksums, DPI)
- Jobs (Status, Optionen, Artefakte, Logs)

---

## 4. Machbarkeit: Viewer & WYSIWYG-Proxy

Ein nativer .sla-Viewer im Browser ist nicht sinnvoll. Ein praktikabler Proxy-Workflow:

- nach Compile: **PNG Preview 72 DPI**
- Frontend: Anzeige per React/Canvas (Zoom, Seitenwechsel, Hotspots)
- finale Kontrolle: PDF-Export + PDF.js im Browser

---

## 5. Koordinaten & Einheiten

Scribus nutzt Punkte (pt) mit 1 pt = 1/72 inch.

**px → pt**
- `pt = (px / dpi) * 72`

**mm → pt**
- `pt = (mm / 25.4) * 72`

Empfehlungen:
- feste Referenz-DPI pro Projekt (z. B. 144/300) zur Stabilität
- definierte Rundung (z. B. 0,01 pt) für deterministische XML-Ausgaben

---

## 6. Risiken & Mitigation (Kurz)

- Scribus-Versionen verhalten sich unterschiedlich → **Image pinnen**, reproduzierbare Worker
- Fonts/Lizenzen → zentral verwaltete Font-Pakete + Nachweise
- Große Assets → Pre-Resize + Worker-Cache
- Layout-Edgecases → Template-first Ansatz (Master Pages, Styles) + Compiler-Regeln

---

## 7. Nächste Schritte (MVP)

1. JSON-Schema definieren (Text/Bild/Box/Layer)
2. Minimal-Compiler: JSON → SLA (1 Seite, 3 Elementtypen)
3. Worker-Container: Scribus headless Export PNG+PDF
4. Preflight-Report (Missing Links/Fonts)
5. Frontend: einfache Preview-Ansicht (PNG-Seiten)

---

**Ende**

