# Dialog Engine (MVP)

Dieses Paket ist ein leichtes Grundgerüst für den späteren interaktiven Workflow (Plugin/UI):

- `question_engine.py`: stabiler Fragekatalog + Validierung
- `decision_store.py`: Entscheidungen als JSON persistieren (z.B. `project_init.json`)
- `rag_context.py`: optionaler Hook zu `packages/rag_service` (lazy import)
- `llm_integration.py`: Provider-agnostisches Interface (standardmäßig deaktiviert)
- `session.py`: kleine State Machine (next_question/answer/resume)
- `cli.py`: CLI-first Einstiegspunkt

Aktuell wird nichts "automatisch" ausgeführt – das Paket ist eine Basis zum schrittweisen Ausbau.

## CLI

```powershell
# Interaktiv (speichert nach jeder Antwort)
python -m packages.dialog_engine run --file temp_analysis\dialog_decisions.json

# Non-interactive (nimmt Defaults)
python -m packages.dialog_engine run --file temp_analysis\dialog_decisions.json --non-interactive

# Validieren
python -m packages.dialog_engine validate --file temp_analysis\dialog_decisions.json

# Export in project_init.json (merge in Template)
python -m packages.dialog_engine export-project-init `
  --file temp_analysis\dialog_decisions.json `
  --template .cursor\project_init.json.template `
  --out temp_analysis\project_init.from_dialog.json
```
