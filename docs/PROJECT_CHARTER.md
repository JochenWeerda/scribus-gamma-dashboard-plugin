# Project Charter: Scribus Gamma Magazin-Pipeline

## 1) Zweck & Vision
Wir bauen eine **deterministische, reproduzierbare Scribus-Pipeline** („Layout = Code“) für die Magazinproduktion.
Input (PPTX + optionale Gamma-Exports) wird in eine kanonische Layout-Repräsentation überführt, daraus **SLA/PDF/Previews**
generiert und durch automatisierte **Quality Gates** abgesichert. Steuerung über Backend (API) und perspektivisch Plugin-UI.

## 2) North-Star Outcome (Zielzustand)
Aus **14 PPTX-Dateien** (+ optional Gamma-Exports) entstehen automatisiert:
- **Print-PDF Farbe** (mit Bleed) + Preview-PNGs
- **Print-PDF Graustufe/Amazon** + Preview-PNGs
- **Workflow-Report** (State/Logs/Artefaktliste)
- **Quality-Report** (fail/warn, Amazon/Preflight)
- Download aller Artefakte über Backend (`/v1/artifacts/{id}`)

## 3) Scope (In-Scope)
- Backend/Infra: FastAPI + Redis/RQ + PostgreSQL + MinIO (Docker)
- Workflow: Bundle-Standard + Orchestrator + Resume/Idempotenz
- PPTX → Layout-JSON (inkl. Sidecar Overrides)
- Gamma-Sync (optional): Crops aus Gamma-Exports (nur bei Flag)
- Varianten: Farbe/Graustufe, Format/Bleed (schrittweise)
- Quality Checks: Layout-JSON Checks + Amazon/Preflight, schrittweise zur Production-Reife
- Plugin: Auslösen/Status/Download (MVP) + später Dialog/Decisions UI
- Figma AI (Modus 1): Prompt-Pack Generierung + Frame-Import (Figma AI selbst ist UI-getrieben)

## 4) Nicht-Ziele (Out-of-Scope, vorerst)
- LaTeX/lua-pagemaker als Hauptpfad (wird als Wissensquelle/Archiv behandelt)
- Vollautomatische „kreative“ Art-Direction ohne Review-Schritt
- Multi-Tenant/Enterprise Auth (später; aktuell minimaler Schutz/Token)

## 5) Definition of Done (DoD)
**DoD heißt:**
1. **Determinismus:** gleicher Bundle-Input → identisches Output (bis auf erwartbare Metadaten).
2. **E2E Pipeline:** Workflow produziert SLA/PDF/Preview + Reports in einem Run (oder klar definierte, getrackte Missing Steps).
3. **Quality Gate:** Amazon/Print Mindestkriterien automatisiert, mit klarer `fail` vs `warn` Policy.
4. **Resume:** Abbruch/Fehler → Wiederaufnahme ohne doppelte Arbeit (hash-basierte Steps).
5. **Operabilität:** Logs/Artefakte/Timeouts/Limits dokumentiert; keine Secrets im Repo.

## 6) Technischer Ist-Stand (kurz)
- Workflow API: `POST /v1/workflow/run` (Bundle ZIP + `options_json`)
- Artefakte: `GET /v1/artifacts/{artifact_id}`
- RQ Queues: `compile`, `export`, `workflow`
- Bundle-Builder: `tools/build_workflow_bundle.py` / `tools/build_workflow_bundle.ps1`
- Flags: `gamma_sync`, `gamma_crop_kinds`, `gamma_attach_to_variants`, `agents_enabled`, `agent_steps`, `agent_seed`, `agent_version`, `agent_simulate`
- Canonical Docs: `docs/workflow/*` + Cookbook: `gamma_scribus_pack/plugin/cpp/SCRIBUS_PLUGIN_COOKBOOK.md`

## 7) Hauptrisiken & Gegenmaßnahmen
- **Scribus Export ist langsam/blocking:** Timeouts, Worker-Skalierung, klare Artefaktgrößen/Limits.
- **Qualitätskriterien unklar:** DoD/Policy schriftlich fixieren, automatisieren, regressionsfähig machen.
- **PPTX Semantik uneindeutig:** Sidecar Overrides + heuristische Cluster-Detektion + schrittweise Ausbau.
- **Assets/Fonts/ICC in Produktion:** „Assets als Paket“ definieren (Versionierung), Preflight/Validator erzwingen.

## 8) Milestone-Plan (4 Blöcke)

### M1: „Goldener Durchlauf“ (1 Kapitel)
- 1 Bundle → deterministische Layout-JSON → SLA → Preview → PDF
- Quality-Report (MVP) + Artefaktliste/Download stabil
- Abnahmekriterium: 1 Kapitel läuft zuverlässig durch, reproduzierbar, dokumentiert

### M2: „Batch 14 Kapitel“
- Batch-Läufe, stabile Laufzeit, Resume bei Fehler
- Artefakt-Publishing + Limits/Timeouts stabil
- Abnahmekriterium: 14 PPTX laufen automatisiert, Fehler sind resumable und sichtbar

### M3: „Amazon-ready“
- Varianten: Graustufe + Format/Bleed rules verbindlich
- Quality Gate: Amazon/Print Regeln vollständig (fail/warn), Reports konsistent
- Abnahmekriterium: Export erfüllt definierte Amazon/Print Kriterien (nach unserer Policy)

### M4: „Plugin UX & Dialog“
- Plugin: Run/Progress/Download robust
- Dialog-Engine: nur bei Flag, Entscheidungen persistiert (`project_init.json`/Decision Store), Resume kompatibel
- Abnahmekriterium: Non-Dev kann Workflow aus Scribus starten und Artefakte abrufen

## 9) Nächste konkrete Schritte (empfohlen)
1. DoD-Checkliste für Quality Gate konkretisieren (Amazon/Print Kriterienliste + fail/warn).
2. SLA→PDF/Preview Step als expliziten Workflow-Step festziehen (Parameter/Artefakte/Reports).
3. `project_init.json` als kanonische „Machine-Config“ finalisieren (aus Design-Decisions ableiten).
4. Figma AI Modus 1 integrieren: `/api/figma/ai/brief` → Prompt-Pack, danach `frames/import`.
