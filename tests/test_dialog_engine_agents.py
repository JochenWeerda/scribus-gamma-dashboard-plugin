import json

from packages.dialog_engine.agents import AgentExecutor, AGENT_REGISTRY
from packages.dialog_engine.llm_integration import LLMClient, LLMRequest


class FakeLLM(LLMClient):
    def __init__(self, response: dict):
        self.response = response

    def complete(self, request: LLMRequest) -> str:
        # return strict JSON
        return json.dumps(self.response, ensure_ascii=False)


def test_layout_designer_agent_parses_output():
    response = {
        "template_id": "hero_full",
        "spacing_logic": "Whitespace first, hero above body.",
        "visual_weight": 0.8,
        "layout_intent": "image-led",
        "notes": ["ok"],
    }
    agent = AgentExecutor(llm=FakeLLM(response))
    out = agent.prompt_agent("LayoutDesigner", {"headline": "Test", "images": 1, "body_chars": 1000})

    assert out["template_id"] == "hero_full"
    assert out["layout_intent"] == "image-led"


def test_agent_registry_contains_layout_designer():
    assert "LayoutDesigner" in AGENT_REGISTRY

