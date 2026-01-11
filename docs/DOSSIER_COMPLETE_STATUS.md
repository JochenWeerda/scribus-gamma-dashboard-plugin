# Projektdossier: Vollständiger Status-Abgleich

Vergleich zwischen dem umfassenden Projektdossier (`PROJEKTDOSSIER_HYBRIDE_HEADLESS_ENGINE.md`) und dem aktuellen MVP-Status.

---

## Übersicht der Dossiers

1. **PROJEKTDOSSIER_HYBRIDE_HEADLESS_ENGINE.md** (v1.0, 2. Januar 2026)
   - Vollständige technische Spezifikation
   - Detaillierte Komponenten-Beschreibungen
   - Roadmap & Deployment-Strategien

2. **PROJEKTDOSSIER_HEADLESS_SLA_ENGINE.md** (frühere Version)
   - Basis-Systemarchitektur
   - UML-Aktivitätsdiagramm
   - MVP-Schritte

3. **TECHNISCHE_VALIDIERUNG_SIDECAR.md**
   - Performance-Analyse
   - CPU/RAM/I/O-Betrachtungen
   - Sidecar-Architektur

---

## Detaillierter Status-Abgleich

### 1. Ressourcen & Infrastruktur (§2)

#### 2.1 Server-Anforderungen

✅ **Empfehlungen dokumentiert:**
- CPU: Multi-Core
- RAM: 8+ GB (16-32 GB empfohlen)
- OS: Linux (Ubuntu LTS)
- Storage: SSD + Object-Storage

**Status:** Dokumentiert, nicht im MVP-Scope (Infrastruktur-Planung)

#### 2.2 Docker-Container-Architektur

✅ **Umgesetzt:**
- API-Gateway (FastAPI) - ✅ Implementiert
- Compiler-Service (Python) - ✅ Implementiert (SLA-Compiler Package)
- Worker-Node (Scribus headless) - ⚠️ Struktur vorhanden, Export fehlt
- Database (PostgreSQL) - ✅ Implementiert
- Asset Storage (MinIO/S3) - ✅ Implementiert (Artifact Store)

**Status:** 4/5 Komponenten implementiert, Worker-Export fehlt

#### 2.3 WYSIWYG & Viewer

❌ **Noch nicht implementiert:**
- PNG-Preview-Generierung
- React/Canvas-Frontend
- PDF.js-Integration

**Status:** ❌ TODO (abhängig von Worker-Export)

---

### 3. Technische Machbarkeit (§3)

#### 3.1 Koordinaten-Mapping

✅ **Vollständig umgesetzt:**
- `px_to_pt()` Funktion im SLA-Compiler
- Formel: `pt = (px / dpi) * 72`
- Rundung auf 2 Dezimalstellen (0.01 pt)

**Status:** ✅ Erfüllt

#### 3.2 UML Aktivitätsdiagramm

**Vergleich mit MVP:**

| Schritt | MVP-Status |
|---------|------------|
| Schema-Validation | ✅ |
| Assets verfügbar? | ⚠️ Struktur, kein echter Check |
| Template/Styles | ⚠️ Vereinfacht |
| SLA-Compiler | ✅ |
| Persistiere SLA | ✅ |
| Queue Render-Job | ✅ |
| Worker: Scribus headless | ⚠️ Struktur, kein Export |
| Preflight | ❌ |
| PNG 72 DPI Render | ❌ |
| PDF Export | ❌ |
| Quality Checks | ❌ |

**Erfüllung:** ~50% (Kern-Pipeline vorhanden, Export/Preflight fehlen)

---

### 4. Datenmodell (Layout-JSON) (§4)

#### 4.1 Prinzipien

✅ **Umgesetzt:**
- JSON-Schema vorhanden (`layout-mvp.schema.json`)
- Seitenbasiert: ✅
- Komponentisiert: ✅ (Text, Image, Rectangle)
- Stabile IDs: ✅
- Determinismus: ⚠️ (IDs nicht Hash-basiert, aber stabil)

**Status:** ✅ Grundsätzlich erfüllt

#### 4.2 Beispielstruktur

⚠️ **Unterschied zum MVP-Schema:**
- Dossier: `document.format.width_mm`, `document.color_profile`, `document.fonts`
- MVP: `document.width` (px), `document.dpi`

**Status:** MVP-Schema ist vereinfacht, kann erweitert werden

---

### 5. SLA-Compiler-Spezifikation (§5)

#### 5.1 Eingaben

✅ **Umgesetzt:**
- Layout-JSON (validiert) - ✅
- Template-Paket - ❌ Nicht im MVP
- Asset-Repository - ✅ (Artifact Store)
- Build-Konfiguration - ⚠️ Vereinfacht

#### 5.2 Ausgaben

✅ **Umgesetzt:**
- `.sla` (kompilierte Datei) - ✅
- `build.json` - ❌ Nicht im MVP
- `preflight.json` - ❌ Nicht im MVP

#### 5.3 Determinismus

⚠️ **Teilweise umgesetzt:**
- Element-Reihenfolge (z_index) - ✅
- IDs (Hash-basiert) - ❌ Nicht Hash-basiert, aber stabil
- Floating-Point-Rundung - ✅ (0.01 pt)
- Fonts (definiertes Paket) - ❌ Nicht im MVP

**Status:** Kern-Funktionalität vorhanden, erweiterte Features fehlen

---

### 6. Worker-Rendering (§6)

#### 6.1 Aufgaben eines Workers

| Aufgabe | MVP-Status |
|---------|------------|
| SLA laden | ✅ |
| Links/Assets auflösen | ❌ |
| Preflight (Fonts/Links/Overflow) | ❌ |
| Render Preview (PNG 72 DPI) | ❌ |
| Export Final-PDF | ❌ |
| Artefakte + Logs zurückmelden | ⚠️ Teilweise (Logs, keine Artefakte) |

**Erfüllung:** ~15% (nur SLA-Laden implementiert)

#### 6.2 Prozesse & Isolation

✅ **Umgesetzt:**
- Docker-Container - ✅ (Dockerfile vorhanden)
- Ressourcenlimits - ❌ Nicht konfiguriert
- Timeout - ✅ (RQ: 10min default)
- Output (S3/Volume) - ✅ (MinIO)

**Status:** Grundstruktur vorhanden, Ressourcenlimits fehlen

---

### 7. API-Design (§7)

#### 7.1 Endpunkte (Minimum Viable)

| Endpunkt | MVP-Status |
|----------|------------|
| `POST /v1/jobs` | ✅ |
| `GET /v1/jobs/{job_id}` | ✅ |
| `GET /v1/jobs/{job_id}/preview/{page}` | ❌ (abhängig von Worker-Export) |
| `GET /v1/jobs/{job_id}/artifact/pdf` | ❌ (abhängig von Worker-Export) |

**Erfüllung:** 50% (2/4 Endpunkte)

#### 7.2 Auth & Security

❌ **Noch nicht implementiert:**
- API-Key/JWT
- Rate-Limits
- Asset-URI-Whitelist
- Input-Härtung (max. Größe/Elementzahl)
- Virus-Scan

**Status:** ❌ Nicht im MVP-Scope

---

### 8. Datenbankmodell (§8)

#### 8.1 Tabellen

| Tabelle | MVP-Status | Unterschied |
|---------|------------|-------------|
| `templates` | ❌ | Nicht im MVP |
| `assets` | ✅ | `artifacts` (erweitert) |
| `jobs` | ✅ | Erweitert (input/output_artifact_id) |
| `job_pages` | ✅ | `pages` (ähnlich) |
| `job_logs` | ✅ | Identisch |
| `job_artifacts` | ⚠️ | Integriert in `artifacts` + `jobs` |

**Erfüllung:** ~70% (Kern-Tabellen vorhanden, Templates fehlen)

---

### 9. Qualitätskontrollen (Preflight) (§9)

❌ **Noch nicht implementiert:**
- Fonts (eingebettet/verlinkt)
- Bilder (Mindestauflösung)
- Farben (CMYK)
- Beschnitt (Bleed)
- Text (Overflow)
- PDF (PDF/X-Profile)

**Status:** ❌ Nicht im MVP-Scope

---

### 10. Observability & Betrieb (§10)

❌ **Noch nicht implementiert:**
- Strukturierte Logs (JSON) - ⚠️ Basis-Logging vorhanden
- Metrics (Queue, Render-Zeiten, Fehlerraten)
- Tracing (OpenTelemetry)
- Dashboards (Grafana + Prometheus)

**Status:** ❌ Nicht im MVP-Scope

---

### 11. CI/CD & Deployment (§11)

❌ **Noch nicht implementiert:**
- GitHub Actions / GitLab CI
- Lint + Tests
- Integrationstests
- Build/Push Docker-Images
- Deploy (Compose/K8s)

**Status:** ❌ Nicht im MVP-Scope (Docker Compose vorhanden, aber kein CI/CD)

---

### 12. Risiken & Mitigation (§12)

✅ **Dokumentiert:**
- Scribus-Versionen → Pinning
- Fonts & Lizenz → Font-Pakete
- Performance → Pre-Resize + Cache
- Feature-Lücken → Template-first

**Status:** Dokumentiert, nicht im MVP umgesetzt

---

### 13. Roadmap (§13)

#### Phase 1: MVP

✅ **Teilweise erledigt:**
- ✅ JSON Schema + Compiler (Text/Bild/Boxen)
- ❌ Headless Worker exportiert PNG+PDF

**Status:** 50% (Compiler fertig, Worker-Export fehlt)

#### Phase 2-5: Template-System, Preflight, Scaling, WYSIWYG

❌ **Noch nicht begonnen**

**Status:** ❌ Nicht im MVP-Scope

---

## Gesamt-Erfüllungsgrad

### Nach Komponenten

| Komponente | Erfüllung | Status |
|------------|-----------|--------|
| API-Gateway | 75% | ✅ Basis vorhanden |
| Compiler-Service | 80% | ✅ Kern-Funktionalität |
| Worker-Service | 15% | ❌ Export fehlt |
| Datenbank | 70% | ✅ Kern-Tabellen |
| Asset Storage | 90% | ✅ MinIO/S3 |
| Koordinaten-Mapping | 100% | ✅ Vollständig |
| Preflight | 0% | ❌ Nicht implementiert |
| Observability | 10% | ❌ Nicht implementiert |
| CI/CD | 0% | ❌ Nicht implementiert |
| Security/Auth | 0% | ❌ Nicht implementiert |

**Gesamt-Erfüllung:** ~45%

---

## Kritische Lücken für Production

### Phase 1 (kritisch für MVP-Vollständigkeit)

1. **Worker-Export (PNG/PDF)**
   - Render Preview (PNG 72 DPI)
   - Export Final-PDF (300 DPI, CMYK)
   - Asset-Relinking

2. **Preflight-Basis**
   - Missing Fonts/Links
   - Basis-Report

### Phase 2 (für Production)

3. **Security & Auth**
   - API-Key/JWT
   - Rate-Limits
   - Input-Härtung

4. **Observability**
   - Strukturierte Logs
   - Metrics
   - Dashboards

5. **CI/CD**
   - Tests
   - Docker-Images
   - Deployment-Automation

---

## Fazit

**MVP v1.0 deckt die Kern-Architektur ab:**
- ✅ JSON-Schema
- ✅ SLA-Compiler
- ✅ API-Gateway (Basis)
- ✅ Datenbank (Kern-Tabellen)
- ✅ Artifact Store
- ✅ Koordinaten-Mapping

**Kritische Lücke für MVP-Vollständigkeit:**
- ❌ Worker-Export (PNG/PDF) - Blockiert Preview/PDF-Endpunkte

**Für Production zusätzlich nötig:**
- Preflight
- Security/Auth
- Observability
- CI/CD
- Template-System
- Erweiterte Features

**Nächster Meilenstein:** Worker-Export-Implementierung ist der kritische Block für MVP-Vollständigkeit.

---

*Letzte Aktualisierung: 2025-01-27*

