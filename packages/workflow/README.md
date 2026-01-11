# Workflow Orchestrator (MVP)

Minimaler Runner, um die Pipeline schrittweise zu automatisieren.

Aktuell:
- `WorkflowOrchestrator.run()` konvertiert `manifest.json` → `media_pool/layout_json/*`
- Persistiert `temp_analysis/workflow_state.json` als Resume-State
- Publish optionaler Progress-Events über den Redis Event-Bus (Channel `workflow`, wenn `EVENT_BUS_ENABLED=true`)

Später:
- Dialog-Engine UI/LLM
- Varianten-Generator
- Quality-Checks
- Jobs/Queue-Integration
