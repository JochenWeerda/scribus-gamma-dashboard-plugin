# Technische Validierung: Scribus-MCP & Digital Twin (Sidecar-Vollintegration)

**Ziel:** Analyse von Systemlast und Machbarkeit der vorgeschlagenen Architektur (Vollintegration via Sidecar / MCP-Server).  
**Stand:** Arbeitsversion (v1.0) – 02. Januar 2026

---

## 0. Kurzfazit (Executive Summary)

Die Architektur ist **machbar**, aber nur dann **stabil skalierbar**, wenn:

- **alle rechenintensiven Operationen** (Kollisionen, Layout-Optimierung, Heuristiken, KI-Auswertung, RAG-Abfragen) **außerhalb** des Scribus-Python-Interpreters im **Sidecar (MCP-Server)** laufen,
- Scribus nur noch als **Render- und Export-Backend** fungiert (SLA laden, Assets final relinken, PDF/PNG exportieren),
- große Payloads über **Chunking / Artefakt-Referenzen** statt Inline-Strings übertragen werden (1‑MB-Limit bleibt sonst der größte Showstopper).

---

## 1. Rechenkapazität (CPU-Last)

### 1.1 Engpass: Scribus Main-Thread

Scribus führt Python-Skripte **synchron im Haupt-Thread** aus. Während Skripte rechnen, **blockiert** (oder „friert") die GUI bzw. der Prozess ist nicht responsiv.

**Beobachtung / Vergleich**
- **Heuristische Engine (bisher):** < 5% CPU-Last, ms-Bereich
- **Virtual Canvas Logic (neu):** Kollisionsprüfungen im Speicher mit **O(n²)**

**Komplexität / Beispiel**
- Bei `n = 100` Objekten:
  - grobe Abschätzung: `n² = 10.000` Vergleiche (wie beschrieben)
  - exakter Pairwise-Check: `n(n-1)/2 = 4.950` Paarprüfungen  
  - In der Praxis kommen je nach Datenstruktur weitere Checks hinzu (Bounds, Snap, Constraints).

### 1.2 Konsequenz

Die Berechnung **darf nicht** im Scribus-Python-Interpreter laufen.

**Lösung:**  
- **Sidecar (MCP-Server)** übernimmt:
  - Kollisions- und Constraint-Checks
  - Layout-Optimierung (Packing/Flow/Breaking)
  - Audit-Logik, Validierung, RAG-Abfragen
  - KI-Orchestrierung
- Scribus bekommt nur „fertige" Kommandos/Artefakte:
  - „Setze Box X auf Position…", „Erzeuge Rahmen…", „Exportiere…"

### 1.3 KI-Inferenz-Latenz

- KI-Inferenz erfolgt remote (Google)  
- **Latenz pro Audit:** ca. **1,5 s – 3,0 s**

**Risiko-Rechnung (Beispiel):**
- Wenn **jede Seite** oder **jede Aktion** auditiert wird:
  - 100 Seiten × 1 Audit/Seite × 1,5–3,0 s = **150–300 s** ≈ **2,5–5 min**
- Bei mehreren Audits pro Seite skaliert das linear nach oben.

**Mitigation (empfohlen):**
- Audits **batchen** (Seiten- oder Kapitelweise)
- Nur **Delta-Audits** (nur wenn sich relevante Layoutzustände ändern)
- **Caching** (Hash über Layoutzustand → Audit-Ergebnis wiederverwenden)
- **Asynchroner Audit-Modus** (Audit läuft parallel; Export wird nur bei „Hard-Fails" blockiert)

---

## 2. Speicherbedarf (RAM & RAG)

### 2.1 Telemetrie-Speicher (RAG)

Das Sammeln von „Fahrdaten" (Telemetrie) erzeugt wachsende Datenmengen.

- **Pro Interaktion:** ~2 KB (JSON-Metadaten)
- **Bei 1.000 Objekten:** ~2 MB pro Dokument-Lauf

**RAG-Index (Sidecar):**
- Vektorindex für Scribus-API-Docs: ca. **50–100 MB RAM** im Sidecar-Prozess (Richtwert)

**Mitigation (empfohlen):**
- Telemetrie **kompakt** halten (IDs, Deltas, keine Duplikate)
- Rolling-Window / Sampling (z. B. „nur letzte N Aktionen")
- Persistierung in DB/Object Storage + nur „Hot Set" im RAM

### 2.2 Bilddaten & Buffering

**Problem:**  
Scribus lädt Bilder beim `createImage` (oder vergleichbaren API-Pfaden) typischerweise direkt in den RAM.

**Strategie (sehr wichtig):**
- Der **Digital Twin** führt Bilder **nur als Metadaten**:
  - Pfad/URI, Breite/Höhe, DPI, Hash/Checksum
- Erst im finalen **Render-Pass** (Scribus Worker) werden Binärdaten tatsächlich geladen.

**Zusätzliche Maßnahmen:**
- Asset-Preflight: Mindest-DPI am finalen Einsatzmaß
- Worker-Cache: lokale Cache-Policy für wiederkehrende Assets
- Optional: Vorab-Downsampling für Previews (nicht fürs Final-PDF)

---

## 3. Datenübertragung (I/O & Payload)

### 3.1 Hauptproblem: `string_above_max_length` (≈ 1 MB Limit)

Das 1‑MB-Limit bleibt die größte Hürde, wenn große Layoutzustände, Telemetrie oder Inline-Assets als String übertragen werden.

**Konsequenz:**  
- **Keine** großen Inline-Payloads (keine Base64-Bilder, keine kompletten Seiten als unkomprimiertes JSON im String-Feld)

### 3.2 Mitigation-Strategien (empfohlen)

**A) Artefakt-Referenzen statt Inline**
- Sidecar schreibt große Ergebnisse als Datei/Objekt:
  - `job://<id>/page/12/layout.json`
  - `s3://bucket/jobs/<id>/page_12_preview.png`
- Scribus/MCP tauschen nur **IDs/URIs** aus

**B) Chunking**
- JSON in Blöcke < 1 MB teilen:
  - `chunk_index`, `chunk_count`, `checksum`
- Sidecar setzt wieder zusammen

**C) Kompression**
- gzip/zstd auf Payloads (vor Chunking) – spart drastisch bei JSON

**D) Streaming-Transport (wenn möglich)**
- gRPC/HTTP streaming oder WebSocket zwischen Gateway↔Sidecar
- Scribus bleibt „thin": ruft nur Job-ID ab

---

## 4. Architektur-Empfehlung: Sidecar „führt", Scribus „rendert"

### 4.1 Verantwortlichkeiten

**Sidecar (MCP-Server)**
- Digital Twin (State)
- Kollisions-/Constraint-Engine
- RAG + KI-Orchestrierung
- Job-Queue/Retry/Timeouts
- Artefakt-Speicher & Checksums

**Scribus Worker (Headless)**
- SLA laden
- Elemente erzeugen/positionieren (nur finaler Render-Befehlssatz)
- Assets final relinken
- Export PNG/PDF
- Preflight soweit Scribus das zuverlässig meldet

### 4.2 Betriebsmodus (stabil)

- Scribus wird **niemals** als „Compute Engine" missbraucht
- Scribus wird **kurzlebig** pro Job/Seite gestartet (oder pro Job-Slot), um Memory-Leaks/State-Dreck zu vermeiden
- Timeouts + Retries auf Worker-Level

---

## 5. Konkrete Akzeptanzkriterien (MVP)

1. **100 Seiten** Render-Job ohne UI-/Thread-Block im Scribus-Skriptmodus (weil Berechnung extern)  
2. **PNG Preview** pro Seite in definierter Zeit (z. B. < 2–5 s/Seite bei Standardassets)  
3. Final-PDF Export stabil inkl. Bleed/Cropmarks/ICC  
4. Kein Payload-Fehler durch 1‑MB-Limit (nur IDs/URIs übertragen)  
5. Telemetrie + Audit optional, aber **nicht export-blockierend** (außer Hard-Fails)

---

## 6. Nächste Schritte (empfohlener Proof)

1. Sidecar-Prototyp:
   - Digital Twin Datenmodell + Collision O(n²) baseline + Spatial Index (Grid/R-Tree) als Upgrade
2. Payload-Proof:
   - Artefakt-Store + Referenzen + Checksums + gzip/chunking
3. Scribus Headless Worker:
   - „Load SLA → relink assets → export PNG/PDF" als stabiler Batch
4. Audit-Policy:
   - Delta-Audit + Caching + Batch-Audit (keine per-Action Vollprüfung)

---

**Ende des Dokuments**

