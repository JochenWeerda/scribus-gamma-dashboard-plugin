# Architektur-Analyse: Event-Bus & Performance-Flaschenhälse

**Datum:** 2025-01-27

---

## Aktuelle Architektur

```
Client → API-Gateway → Redis Queue → Worker → MinIO/S3
                      ↓
                   PostgreSQL
```

---

## Identifizierte Flaschenhälse

### 1. Synchrones Job-Enqueuing ⚠️

**Problem:**
- `queue.enqueue()` blockiert API-Response
- Redis-Kommunikation synchron
- API-Gateway wartet auf Queue-Bestätigung

**Impact:** Niedrig-Mittel (Redis ist schnell, aber verzögert Response)

**Lösung:** Asynchrones Enqueuing (optional, nicht kritisch)

---

### 2. Artifact Store I/O (MinIO/S3) 🔴

**Problem:**
- Upload/Download blockieren Worker
- Große Dateien (SLA, PNG, PDF) können mehrere Sekunden dauern
- Worker blockiert während I/O

**Impact:** Hoch (große Artefakte = langsame Verarbeitung)

**Lösung:**
- ✅ Retry-Mechanismus bereits implementiert
- ⚠️ Asynchrones I/O (async/await) könnte helfen
- ⚠️ Streaming für große Dateien

---

### 3. Scribus Export (Blocking) 🔴

**Problem:**
- Scribus Export läuft synchron
- Worker blockiert während Export
- Kann bei großen Dokumenten Minuten dauern

**Impact:** Sehr hoch (Hauptflaschenhals für Render-Pipeline)

**Lösung:**
- ✅ Worker läuft asynchron (RQ)
- ⚠️ Scribus Export selbst ist blocking (nicht vermeidbar)
- ✅ Timeouts bereits implementiert

---

### 4. Database Queries (N+1 Problem) ⚠️

**Problem:**
- Mehrere DB-Queries pro Request
- Mögliche N+1 Queries bei Relations

**Impact:** Mittel (bei hoher Last)

**Lösung:**
- ✅ Connection Pooling bereits implementiert
- ⚠️ Query-Optimierung (JOINs statt separate Queries)
- ⚠️ Caching für häufig gelesene Daten

---

### 5. Schema-Validierung (JSON) ⚠️

**Problem:**
- JSON Schema-Validierung blockiert API-Thread
- Große Layouts können mehrere MB sein

**Impact:** Niedrig-Mittel (validierung ist schnell, aber blockiert)

**Lösung:**
- ⚠️ Asynchrone Validierung (optional)
- ✅ Input-Validierung bereits implementiert

---

## Event-Bus: Benötigt?

### Aktuelle Kommunikation

**Pattern:** Request-Response + Queue

1. **API-Gateway → Worker:** Redis Queue (RQ)
2. **Worker → API-Gateway:** Database (Status-Updates)
3. **Worker → MinIO:** Direkt (kein Bus nötig)

### Wann wäre Event-Bus sinnvoll?

#### ✅ Event-Bus würde helfen bei:

1. **Multi-Worker-Koordination**
   - Worker müssen sich koordinieren
   - Status-Updates an mehrere Services
   - Load-Balancing zwischen Workern

2. **Real-Time Updates**
   - Frontend braucht Live-Updates
   - WebSocket-Integration
   - Event-Streaming

3. **Event-Sourcing**
   - Vollständige Audit-Trail
   - Event-Replay
   - CQRS-Pattern

4. **Service-Dekoupling**
   - Sidecar-MCP sendet Events
   - Monitoring-Service hört Events
   - Notification-Service für Alerts

#### ❌ Event-Bus ist NICHT nötig für:

1. **Aktuelle MVP-Architektur**
   - Request-Response-Pattern reicht
   - Redis Queue ist bereits Event-Bus-light
   - Keine komplexe Event-Orchestrierung

2. **Synchroner Workflow**
   - API → Queue → Worker → DB
   - Einfacher, linearer Flow
   - Keine komplexe Event-Choreographie

---

## Empfehlung: Event-Bus

### Für MVP: ❌ Nicht nötig

**Begründung:**
- Redis Queue erfüllt bereits die Queue-Anforderungen
- Einfacher Request-Response-Flow
- Keine Multi-Service-Koordination nötig
- Overhead nicht gerechtfertigt

### Für Production (später): ⚠️ Optional

**Szenarien wo Event-Bus hilft:**

1. **RabbitMQ / Kafka** wenn:
   - Real-Time Updates nötig
   - Event-Sourcing gewünscht
   - Multi-Worker-Koordination
   - Event-Replay-Funktionalität

2. **Redis Pub/Sub** (leichter) wenn:
   - Einfache Event-Benachrichtigung
   - Real-Time Status-Updates
   - Worker-Koordination

---

## Performance-Optimierungen (ohne Event-Bus)

### Priorität 1: Kritische Flaschenhälse

1. **Asynchrones Artifact I/O** 🔴
   ```python
   # Statt:
   artifact_store.upload(data)
   
   # Besser:
   await artifact_store.upload_async(data)
   ```
   - **Impact:** Hoch
   - **Aufwand:** Mittel
   - **Status:** ⚠️ TODO

2. **Streaming für große Dateien** 🔴
   - Download/Upload in Chunks
   - Keine vollständige Datei im RAM
   - **Impact:** Hoch (bei großen Dateien)
   - **Aufwand:** Mittel
   - **Status:** ⚠️ TODO

### Priorität 2: Wichtige Optimierungen

3. **Database Query-Optimierung** ⚠️
   - JOINs statt N+1 Queries
   - Indices prüfen
   - Query-Caching
   - **Impact:** Mittel
   - **Aufwand:** Niedrig
   - **Status:** ⚠️ TODO

4. **Connection Pooling erweitern** ⚠️
   - Pool-Größe optimieren
   - Connection-Timeouts
   - **Impact:** Mittel
   - **Aufwand:** Niedrig
   - **Status:** ✅ Teilweise (pool_pre_ping vorhanden)

### Priorität 3: Nice-to-Have

5. **Asynchrones Job-Enqueuing** ⚠️
   - Background-Tasks
   - **Impact:** Niedrig
   - **Aufwand:** Niedrig
   - **Status:** ⚠️ Optional

6. **Caching** ⚠️
   - Redis-Cache für häufig gelesene Daten
   - **Impact:** Mittel (bei hoher Last)
   - **Aufwand:** Mittel
   - **Status:** ⚠️ Optional

---

## Zusammenfassung

### Event-Bus: ❌ Nicht nötig für MVP

**Redis Queue reicht aus:**
- ✅ Einfacher, bewährter Ansatz
- ✅ Bereits implementiert
- ✅ Erfüllt Anforderungen
- ✅ Niedriger Overhead

### Flaschenhälse: Identifiziert

**Kritisch:**
1. 🔴 Artifact Store I/O (blocking)
2. 🔴 Scribus Export (blocking, nicht vermeidbar)

**Wichtig:**
3. ⚠️ Database Queries (N+1 Problem)
4. ⚠️ Synchrones Job-Enqueuing

**Empfohlene Optimierungen:**
1. Asynchrones Artifact I/O
2. Streaming für große Dateien
3. Database Query-Optimierung

---

## Nächste Schritte

1. **Kurzfristig (MVP):**
   - ✅ Redis Queue beibehalten
   - ⚠️ Database Query-Optimierung
   - ⚠️ Connection Pooling optimieren

2. **Mittelfristig (Production):**
   - ⚠️ Asynchrones Artifact I/O
   - ⚠️ Streaming für große Dateien
   - ⚠️ Caching (Redis)

3. **Langfristig (Skalierung):**
   - ⚠️ Event-Bus (RabbitMQ/Kafka) wenn nötig
   - ⚠️ Real-Time Updates (WebSocket)
   - ⚠️ Event-Sourcing

---

*Letzte Aktualisierung: 2025-01-27*

