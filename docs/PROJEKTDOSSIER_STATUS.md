# Projektdossier Status vs. MVP-Implementation

Vergleich zwischen den Anforderungen aus dem Projektdossier (`PROJEKTDOSSIER_HEADLESS_SLA_ENGINE.md`) und dem aktuellen MVP-Status.

---

## ✅ Bereits implementiert (MVP v1.0)

### 1. Komponentenübersicht (§3)

#### 3.1 API-Gateway (FastAPI)

✅ **Umgesetzt:**
- Nimmt Layout-JSON entgegen (`POST /v1/jobs`)
- Validiert gegen JSON-Schema (`packages/layout-schema`)
- Startet Compiler + Job-Queue (Redis + RQ)
- Stellt Status, Links bereit (`GET /v1/jobs/{job_id}`)

✅ **Minimal-Endpunkte:**
- ✅ `POST /v1/jobs` → `job_id`
- ✅ `GET /v1/jobs/{job_id}` → Status + Links
- ⚠️ `GET /v1/jobs/{job_id}/preview/{page}` → PNG (TODO: Worker-Export)
- ⚠️ `GET /v1/jobs/{job_id}/artifact/pdf` → PDF (TODO: Worker-Export)

**Status:** 2/4 Endpunkte vollständig, 2/4 warten auf Worker-Export

#### 3.2 Compiler-Service (JSON → SLA)

✅ **Umgesetzt:**
- Mapping von Koordinaten/Boxen in Scribus-Units (pt) - `px_to_pt()`
- Layer/Z-Order deterministisch - `get_layer_zorder()`
- ⚠️ Style-Resolver: Vereinfacht (nur Grund-Formatierung)
- ⚠️ Asset-Resolver: Grundstruktur vorhanden (via Artifact Store)

**Status:** Kern-Funktionalität umgesetzt, Styles/Assets vereinfacht

#### 3.3 Worker-Service (Scribus headless)

⚠️ **Teilweise umgesetzt:**
- ⚠️ Xvfb + Scribus: Dockerfile vorhanden, aber noch nicht getestet
- ✅ Laden SLA: Worker lädt SLA aus Artefakt
- ❌ Relinken Assets: Noch nicht implementiert
- ❌ Export PNG: Noch nicht implementiert
- ❌ Export PDF: Noch nicht implementiert
- ❌ Logs + Preflight-Report: Basis-Logging vorhanden, Preflight nicht

**Status:** Struktur vorhanden, Export-Funktionalität fehlt

#### 3.4 Datenbank (PostgreSQL)

✅ **Umgesetzt:**
- ✅ Jobs (Status, Optionen, Artefakte, Logs)
- ✅ Assets (Metadaten, Checksums, DPI) - Tabelle vorhanden
- ⚠️ Templates (Versionierung) - Nicht im MVP

**Status:** Kern-Funktionalität umgesetzt, Templates optional

---

### 2. Koordinaten & Einheiten (§5)

✅ **Vollständig umgesetzt:**
- `px_to_pt()` Funktion im SLA-Compiler
- `px = (px / dpi) * 72`
- Rundung auf 2 Dezimalstellen (0.01 pt Genauigkeit)

**Status:** ✅ Erfüllt

---

### 3. Nächste Schritte (MVP) (§7)

#### 1. JSON-Schema definieren (Text/Bild/Box/Layer)

✅ **Erledigt:**
- `packages/layout-schema/layout-mvp.schema.json`
- Unterstützt: Text, Image, Rectangle
- Layer, Z-Order, Bounding Boxes

**Status:** ✅ Erledigt

#### 2. Minimal-Compiler: JSON → SLA (1 Seite, 3 Elementtypen)

✅ **Erledigt:**
- `packages/sla-compiler/compiler.py`
- `compile_layout_to_sla()` Funktion
- Unterstützt: Text, Image, Rectangle
- Vereinfacht, aber funktionsfähig

**Status:** ✅ Erledigt (vereinfacht)

#### 3. Worker-Container: Scribus headless Export PNG+PDF

⚠️ **In Arbeit:**
- Dockerfile vorhanden (`docker/worker/Dockerfile`)
- Worker-Struktur vorhanden (`apps/worker-scribus/worker.py`)
- ❌ Export PNG/PDF noch nicht implementiert

**Status:** ⚠️ Struktur vorhanden, Export fehlt

#### 4. Preflight-Report (Missing Links/Fonts)

❌ **Noch nicht implementiert:**
- Kein Preflight-Check
- Kein Missing Links/Fonts Report

**Status:** ❌ TODO

#### 5. Frontend: einfache Preview-Ansicht (PNG-Seiten)

❌ **Noch nicht implementiert:**
- Kein Frontend
- Kein PNG-Preview-Endpoint (weil Export fehlt)

**Status:** ❌ TODO (abhängig von Worker-Export)

---

## 📊 Erfüllungsgrad

### Komponenten (§3)

| Komponente | Status | Erfüllung |
|------------|--------|-----------|
| API-Gateway | ✅ | 75% (2/4 Endpunkte) |
| Compiler-Service | ✅ | 80% (Kern-Funktionalität) |
| Worker-Service | ⚠️ | 30% (Struktur, kein Export) |
| Datenbank | ✅ | 90% (Kern-Funktionalität) |

### MVP-Schritte (§7)

| Schritt | Status | Erfüllung |
|---------|--------|-----------|
| 1. JSON-Schema | ✅ | 100% |
| 2. Minimal-Compiler | ✅ | 100% (vereinfacht) |
| 3. Worker-Container | ⚠️ | 50% (Struktur, kein Export) |
| 4. Preflight-Report | ❌ | 0% |
| 5. Frontend Preview | ❌ | 0% |

**Gesamt-Erfüllung:** ~60% (Kern-Architektur vorhanden, Export/Preflight/Frontend fehlen)

---

## 🎯 Kritische TODOs für Vollständigkeit

### Phase 1: Worker-Export (kritisch)

1. **Scribus Headless Export implementieren**
   - PNG-Export (72 DPI) pro Seite
   - PDF-Export (300 DPI) final
   - Asset-Relinking im Worker

2. **Preflight-Report**
   - Missing Links/Fonts erkennen
   - Report generieren
   - In Job-Logs speichern

### Phase 2: API-Endpunkte vervollständigen

3. **Preview-Endpunkte**
   - `GET /v1/jobs/{job_id}/preview/{page}` → PNG
   - `GET /v1/jobs/{job_id}/artifact/pdf` → PDF

### Phase 3: Frontend (optional)

4. **Frontend Preview**
   - React/Canvas-Ansicht
   - PNG-Seiten anzeigen
   - Zoom, Seitenwechsel, Hotspots

---

## 🔄 Vergleich mit UML-Aktivitätsdiagramm (§2.2)

### ✅ Umgesetzt

- ✅ Schema-Validation (API-Gateway)
- ✅ SLA-Compiler (JSON → SLA XML)
- ✅ Persistiere SLA (Artifact Store)
- ✅ Queue Render-Job (Redis + RQ)
- ✅ Worker-Struktur (Docker + Xvfb)

### ⚠️ Teilweise / Vereinfacht

- ⚠️ Assets & Fonts Check (nur Struktur, kein echter Check)
- ⚠️ Template/Styles (vereinfacht)
- ⚠️ Worker: Scribus headless (Struktur vorhanden)

### ❌ Noch nicht implementiert

- ❌ Preflight: Links/Fonts/Overflows
- ❌ Render PNG 72 DPI
- ❌ Export Final-PDF
- ❌ Quality Checks: Bleed/Crop/ICC/PDF-Profile
- ❌ Frontend Vorschau (Canvas)

---

## Fazit

**Kern-Architektur vorhanden:**
- ✅ JSON-Schema
- ✅ SLA-Compiler
- ✅ API-Gateway
- ✅ Worker-Struktur
- ✅ Datenbank
- ✅ Artifact Store

**Kritische Lücken:**
- ❌ Worker-Export (PNG/PDF)
- ❌ Preflight-Report
- ❌ Frontend Preview

**Nächster Meilenstein:** Worker-Export-Implementierung (PNG/PDF) ist der kritische Block für einen vollständigen MVP-Zyklus.

---

*Letzte Aktualisierung: 2025-01-27*

