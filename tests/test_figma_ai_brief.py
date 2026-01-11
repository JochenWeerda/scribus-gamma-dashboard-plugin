import json

from packages.figma_integration.ai_brief import FigmaAIBriefConfig, build_figma_ai_brief


def _sample_layout():
    return {
        "version": "1.0.0",
        "document": {"width": 1000, "height": 2000, "dpi": 300},
        "source": {"name": "sample"},
        "pages": [
            {
                "pageNumber": 1,
                "objects": [
                    {
                        "id": "t1",
                        "type": "text",
                        "bbox": {"x": 10, "y": 20, "w": 100, "h": 30},
                        "layer": "TEXT",
                        "content": "Headline: Hello World",
                        "fontFamily": "Inter",
                        "fontSize": 42,
                    }
                ],
            }
        ],
    }


def test_build_figma_ai_brief_mode1_smoke():
    brief = build_figma_ai_brief(
        layout_json=_sample_layout(),
        project_init={"layout": {"layers": ["TEXT"]}},
        config=FigmaAIBriefConfig(top_k=2, rag_enabled=False),
    )

    assert brief["mode"] == 1
    assert "figma_ai_prompt" in brief
    assert "Headline: Hello World" in brief["figma_ai_prompt"]
    assert brief["rag_similar_layouts"] == []

