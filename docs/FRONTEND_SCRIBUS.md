# Frontend in Scribus - Notwendigkeit?

**Frage:** Benötigen wir ein Frontend als Erweiterung in Scribus?

---

## Antwort: ❌ Nicht nötig

### Warum kein Frontend in Scribus?

**Unsere Architektur ist headless:**

1. **Server-seitige Pipeline**
   - JSON → SLA Compiler → Worker
   - Komplett serverseitig
   - Keine GUI-Interaktion nötig

2. **Scribus läuft headless**
   - Docker-Container mit Xvfb
   - Keine GUI vorhanden
   - Script-basiert (Python-Skripte)

3. **API-basiertes Frontend (optional)**
   - Frontend wäre eine **separate Web-App** (React, Vue, etc.)
   - Nicht in Scribus integriert
   - Kommuniziert mit API-Gateway

---

## Architektur-Überblick

```
┌─────────────┐
│   Client    │ (Browser, Mobile, etc.)
│  Frontend   │ ← Separate Web-App (optional)
└──────┬──────┘
       │ HTTP/REST
       ↓
┌─────────────────┐
│  API-Gateway    │ ← FastAPI
└────────┬────────┘
         │
         ├─→ Redis Queue
         ├─→ PostgreSQL
         ├─→ MinIO/S3
         └─→ Worker (Headless Scribus)
```

**Scribus:**
- Läuft **headless** im Docker-Container
- Wird von **Worker-Skripten** gesteuert
- Keine GUI, keine Frontend-Integration

---

## Wenn Frontend, dann wo?

### Option 1: Separate Web-App (empfohlen) ✅

**Technologie:**
- React, Vue, Angular, etc.
- Kommuniziert mit API-Gateway
- Zeigt PNG-Previews, PDF-Downloads

**Vorteile:**
- Flexibel
- Multi-Device (Desktop, Mobile)
- Keine Scribus-Abhängigkeit

**Beispiel:**
```
Frontend (React)
  → API: POST /v1/jobs (Layout-JSON)
  → API: GET /v1/jobs/{id} (Status)
  → API: GET /v1/jobs/{id}/preview/{page} (PNG)
  → API: GET /v1/jobs/{id}/artifact/pdf (PDF)
```

---

### Option 2: Scribus-Plugin (nicht empfohlen) ❌

**Warum nicht:**
- Scribus läuft headless (keine GUI)
- Plugin würde GUI benötigen
- Widerspricht unserer Architektur

---

## Zusammenfassung

| Frage | Antwort |
|-------|---------|
| Frontend in Scribus? | ❌ Nein |
| Frontend generell? | ✅ Optional (separate Web-App) |
| Scribus GUI? | ❌ Nicht nötig (headless) |

**Empfehlung:**
- ✅ Separate Web-App für Frontend (falls gewünscht)
- ✅ API-Gateway für Backend-Kommunikation
- ❌ Kein Frontend in Scribus

---

*Letzte Aktualisierung: 2025-01-27*

