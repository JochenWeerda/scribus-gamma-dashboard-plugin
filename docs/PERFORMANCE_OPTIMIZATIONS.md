# Performance-Optimierungen

Empfohlene Performance-Optimierungen für die Pipeline.

---

## Identifizierte Flaschenhälse

### 🔴 Kritisch (Hoher Impact)

#### 1. Artifact Store I/O (Blocking)

**Problem:**
- Upload/Download blockieren Worker-Thread
- Große Dateien (SLA, PNG, PDF) = mehrere Sekunden
- Worker kann nicht parallel arbeiten

**Lösung:**
- Asynchrones I/O (async/await)
- Streaming für große Dateien
- Background-Tasks für Uploads

**Status:** ⚠️ TODO

---

#### 2. Scribus Export (Blocking)

**Problem:**
- Scribus Export läuft synchron
- Kann bei großen Dokumenten Minuten dauern
- Worker blockiert während Export

**Lösung:**
- ✅ Worker läuft bereits asynchron (RQ)
- ⚠️ Scribus Export selbst ist blocking (nicht vermeidbar)
- ✅ Timeouts implementiert
- ✅ Retry-Mechanismus implementiert

**Status:** ⚠️ Teilweise (Scribus selbst ist blocking)

---

### ⚠️ Wichtig (Mittlerer Impact)

#### 3. Database Queries (N+1 Problem)

**Problem:**
- Mehrere DB-Queries pro Request
- Mögliche N+1 Queries bei Relations

**Beispiel:**
```python
# Aktuell (N+1 Problem):
for job in jobs:
    artifact = db.query(Artifact).filter(Artifact.id == job.input_artifact_id).first()
    # Separate Query pro Job!
```

**Lösung:**
- JOINs statt separate Queries
- Eager Loading (SQLAlchemy)
- Query-Optimierung

**Status:** ⚠️ TODO

---

#### 4. Synchrones Job-Enqueuing

**Problem:**
- `queue.enqueue()` blockiert API-Response
- Redis-Kommunikation synchron

**Lösung:**
- Background-Tasks (FastAPI BackgroundTasks)
- Asynchrones Enqueuing

**Status:** ⚠️ Optional (Redis ist schnell)

---

### ✅ Bereits Optimiert

1. ✅ Connection Pooling (SQLAlchemy)
2. ✅ Retry-Mechanismus (Artifact Store)
3. ✅ Asynchroner Worker (RQ)
4. ✅ Timeouts (Worker, Redis)

---

## Empfohlene Optimierungen

### Priorität 1: Artifact Store I/O

**Datei:** `packages/artifact-store/store.py`

**Änderung:**
```python
async def upload_async(self, data: bytes, ...):
    """Asynchrones Upload."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, self.upload, data, ...)
```

**Impact:** Hoch  
**Aufwand:** Mittel

---

### Priorität 2: Database Query-Optimierung

**Datei:** `apps/api-gateway/main.py`

**Aktuell:**
```python
# N+1 Problem
result = db.execute(text("SELECT * FROM jobs WHERE id = :id"), {"id": job_id})
job = result.fetchone()
artifact_result = db.execute(text("SELECT * FROM artifacts WHERE id = :id"), {"id": job.input_artifact_id})
```

**Optimiert:**
```python
# Mit JOIN
result = db.execute(text("""
    SELECT j.*, a.*
    FROM jobs j
    LEFT JOIN artifacts a ON j.input_artifact_id = a.id
    WHERE j.id = :id
"""), {"id": job_id})
```

**Impact:** Mittel  
**Aufwand:** Niedrig

---

### Priorität 3: Streaming für große Dateien

**Datei:** `packages/artifact-store/store.py`

**Änderung:**
```python
def upload_stream(self, stream, ...):
    """Streaming-Upload für große Dateien."""
    # Upload in Chunks
    # Keine vollständige Datei im RAM
```

**Impact:** Hoch (bei großen Dateien)  
**Aufwand:** Mittel

---

## Event-Bus: Empfehlung

### ❌ Nicht nötig für MVP

**Begründung:**
- Redis Queue erfüllt bereits Anforderungen
- Einfacher Request-Response-Flow
- Overhead nicht gerechtfertigt

### ⚠️ Optional für spätere Features

**Event-Bus (RabbitMQ/Kafka) würde helfen bei:**
- Real-Time Updates (WebSocket)
- Event-Sourcing
- Multi-Worker-Koordination
- Event-Replay

**Für MVP:** Redis Queue reicht aus!

---

## Performance-Metriken

### Aktuelle Metriken (via Prometheus)

- `http_request_duration_seconds` - Request-Dauer
- `jobs_processing_duration_seconds` - Job-Verarbeitungsdauer
- `queue_size` - Queue-Größe

### Ziel-Metriken

- **API Response Time:** < 200ms (ohne Job-Enqueuing)
- **Job Processing:** < 30s (für kleine Jobs)
- **Queue Wait Time:** < 5s (bei normaler Last)

---

## Nächste Schritte

1. **Kurzfristig:**
   - Database Query-Optimierung
   - Connection Pooling optimieren

2. **Mittelfristig:**
   - Asynchrones Artifact I/O
   - Streaming für große Dateien

3. **Langfristig:**
   - Event-Bus (wenn nötig)
   - Real-Time Updates

---

*Letzte Aktualisierung: 2025-01-27*

