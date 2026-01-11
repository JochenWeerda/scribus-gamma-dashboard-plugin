# Figma AI (Modus 1) + RAG: Integration in die Scribus-Pipeline

## Ziel
Figma soll als **Layout-Generator** genutzt werden (Figma AI/Autolayout). RAG liefert **Content/Pattern/Referenzen**.

Wichtig: Figma AI hat aktuell keine stabile öffentliche „Generate Design“-API. Daher ist **Modus 1**:
„Prompt-Pack erzeugen → in Figma AI nutzen → Ergebnis-Frames importieren“.

## Ablauf (Mode 1)
1. **RAG/Backend erzeugt Prompt-Pack**
   - Input: Layout-JSON (aus PPTX oder bestehendem Layout), `project_init.json` (Constraints)
   - Optional: RAG Retrieval Top‑K ähnliche Layouts
2. **Figma AI erzeugt Frames (UI Schritt)**
   - Prompt aus dem Pack in Figma AI verwenden
3. **Import zurück in Pipeline**
   - `POST /api/figma/frames/import` → Layout‑JSON
4. **Weiterverarbeitung**
   - Varianten/Quality/Gamma‑Crops (optional) → Scribus Render → PDF/PNG

## Endpoint
- `POST /api/figma/ai/brief`
  - Erzeugt den Prompt-Pack (`figma_ai_prompt` + strukturierte Daten)
  - Parameter:
    - `rag_enabled`: bool
    - `top_k`: int

Beispiel:
```bash
curl -X POST http://localhost:8003/api/figma/ai/brief ^
  -H "Content-Type: application/json" ^
  -d "{\"layout_json\": {\"document\": {\"width\": 1000, \"height\": 2000, \"dpi\": 300}, \"pages\": []}, \"rag_enabled\": true, \"top_k\": 5}"
```

## Konfiguration
Kanonisch in `project_init.json.template`:
- `figma.enabled`
- `figma.mode = 1`
- `figma.file_key`
- `figma.ai.rag_enabled`, `figma.ai.top_k`

