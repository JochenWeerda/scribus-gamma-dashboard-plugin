from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError

from .llm_integration import LLMClient, LLMRequest, DisabledLLM


class AgentPrompt(BaseModel):
    role: str
    context: str
    constraints: List[str]
    output_format: str
    few_shots: List[Dict[str, Any]] = Field(default_factory=list)


class SemanticEnricherOutput(BaseModel):
    title: str
    summary: str
    keywords: List[str]


class LayoutDesignerOutput(BaseModel):
    template_id: str
    spacing_logic: str
    visual_weight: float
    layout_intent: str
    notes: List[str]


class QualityCriticOutput(BaseModel):
    score: int
    issues: List[str]
    approved: bool


AGENT_OUTPUT_MODELS: Dict[str, BaseModel] = {
    "SemanticEnricher": SemanticEnricherOutput,
    "LayoutDesigner": LayoutDesignerOutput,
    "QualityCritic": QualityCriticOutput,
}


AGENT_REGISTRY: Dict[str, AgentPrompt] = {
    "SemanticEnricher": AgentPrompt(
        role="Du bist ein Content-Analyst für Fachpublikationen.",
        context=(
            "Analysiere den extrahierten Text einer PowerPoint-Folie und extrahiere "
            "Kernaussagen, Fachbegriffe und einen passenden Titel."
        ),
        constraints=[
            "Verwende keine Floskeln.",
            "Maximal 5 Keywords.",
            "Titel muss aktiv formuliert sein.",
            "Gib ausschließlich gültiges JSON zurück.",
        ],
        output_format="JSON { 'title': str, 'summary': str, 'keywords': list }",
    ),
    "LayoutDesigner": AgentPrompt(
        role="Du bist ein Senior Art Director für Editorial Design.",
        context=(
            "Basierend auf Content-Umfang und Bildanzahl sollst du eine Layout-Strategie "
            "aus der Template-Bibliothek vorschlagen."
        ),
        constraints=[
            "Gib ausschließlich gültiges JSON zurück, ohne zusätzliche Texte.",
            "Priorisiere Weißraum.",
            "Beachte die Hierarchie: Headline > Visual > Body.",
            "Wähle zwischen 'Fokus-Bild' oder 'Text-Lastig'.",
            "Nutze nur definierte Templates: ['hero_full', 'hero_left', 'two_column', 'text_heavy', 'quote_focus']",
            "visual_weight ist Float zwischen 0.0 und 1.0",
        ],
        output_format=(
            "JSON { 'template_id': str, 'spacing_logic': str, 'visual_weight': float, "
            "'layout_intent': str, 'notes': list[str] }"
        ),
        few_shots=[
            {
                "input": {"headline": "Die verborgene Uhr", "body_chars": 2400, "images": 1, "infoboxes": 0, "quotes": 0},
                "output": {
                    "template_id": "hero_full",
                    "spacing_logic": "Großzügiger Top‑Margin, Body unterhalb des Hero, ruhige Zeilenlänge",
                    "visual_weight": 0.78,
                    "layout_intent": "image-led",
                    "notes": ["Hero dominiert, Body kompakter Block"],
                },
            },
            {
                "input": {"headline": "Daniel 9: 70 Jahrwochen", "body_chars": 5200, "images": 0, "infoboxes": 1, "quotes": 1},
                "output": {
                    "template_id": "text_heavy",
                    "spacing_logic": "Zweispaltig, größere Zeilenabstände, Infobox rechts oben",
                    "visual_weight": 0.22,
                    "layout_intent": "text-led",
                    "notes": ["Text dominiert, klare Leseführung", "Quote als optische Zäsur"],
                },
            },
            {
                "input": {"headline": "Endzeit – Der Greuel", "body_chars": 3200, "images": 2, "infoboxes": 1, "quotes": 0},
                "output": {
                    "template_id": "hero_left",
                    "spacing_logic": "Hero links, Textblock rechts; Infobox unter Text",
                    "visual_weight": 0.6,
                    "layout_intent": "balanced",
                    "notes": ["Bild + Text gleichgewichtet"],
                },
            },
        ],
    ),
    "QualityCritic": AgentPrompt(
        role="Du bist ein pedantischer Schlussredakteur und Preflight-Experte.",
        context="Prüfe das generierte Layout-Manifest auf semantische Konsistenz und Lesbarkeit.",
        constraints=[
            "Prüfe, ob der Text zum Bild passt.",
            "Markiere potenzielle Trennungsfehler.",
            "Bewerte die Gesamtharmonie auf einer Skala von 1-10.",
            "Gib ausschließlich gültiges JSON zurück.",
        ],
        output_format="JSON { 'score': int, 'issues': list, 'approved': bool }",
    ),
}


class AgentExecutor:
    """
    Runs a specialized agent prompt via an injected LLM client.
    The response must be strict JSON and is validated against the agent schema.
    """

    def __init__(self, llm: Optional[LLMClient] = None):
        self.llm = llm or DisabledLLM()

    def build_prompt(self, agent_id: str, input_data: Dict[str, Any]) -> LLMRequest:
        cfg = AGENT_REGISTRY[agent_id]
        system = f"{cfg.role}\n{cfg.context}\nRegeln: {', '.join(cfg.constraints)}"
        shots = ""
        if cfg.few_shots:
            shots = "\n\n".join(
                f"Beispiel Input: {json.dumps(s['input'], ensure_ascii=False)}\n"
                f"Beispiel Output: {json.dumps(s['output'], ensure_ascii=False)}"
                for s in cfg.few_shots
            )
        user = (
            f"Eingangsdaten: {json.dumps(input_data, ensure_ascii=False)}\n"
            f"Gib das Ergebnis strikt im Format aus: {cfg.output_format}\n"
        )
        if shots:
            user = f"{shots}\n\n{user}"
        return LLMRequest(system=system, user=user)

    def prompt_agent(self, agent_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        req = self.build_prompt(agent_id, input_data)
        raw = self.llm.complete(req)
        try:
            parsed = json.loads(raw)
        except Exception as exc:
            raise ValueError(f"Agent {agent_id} returned non-JSON output: {exc}") from exc

        model = AGENT_OUTPUT_MODELS.get(agent_id)
        if model is None:
            return parsed

        try:
            validated = model.model_validate(parsed)
        except ValidationError as exc:
            raise ValueError(f"Agent {agent_id} output schema invalid: {exc}") from exc

        return validated.model_dump()

