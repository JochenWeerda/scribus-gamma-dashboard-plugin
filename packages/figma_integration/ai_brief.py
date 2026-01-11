from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class FigmaAIBriefConfig:
    top_k: int = 5
    rag_enabled: bool = False


def _extract_content_snippets(layout_json: Dict[str, Any], *, max_items: int = 40) -> List[Dict[str, Any]]:
    snippets: List[Dict[str, Any]] = []
    for page in layout_json.get("pages", []) or []:
        pn = page.get("pageNumber")
        for obj in page.get("objects", []) or []:
            if obj.get("type") != "text":
                continue
            text = (obj.get("content") or "").strip()
            if not text:
                continue
            snippets.append(
                {
                    "page": pn,
                    "id": obj.get("id"),
                    "role": obj.get("role") or obj.get("semantic") or None,
                    "text": text[:400],
                }
            )
            if len(snippets) >= max_items:
                return snippets
    return snippets


def _rag_retrieve_similar(layout_json: Dict[str, Any], *, top_k: int) -> List[Dict[str, Any]]:
    """
    Best-effort RAG retrieval. This is intentionally optional and guarded:
    - It can be expensive (model load).
    - It requires ChromaDB + sentence-transformers runtime.
    """

    try:
        from packages.rag_service.database import RAGDatabase
        from packages.rag_service.embeddings import EmbeddingModels
        from packages.rag_service.retriever import LayoutRetriever

        chroma_path = os.getenv("CHROMA_DB_PATH") or os.getenv("RAG_DB_PATH") or "data/chroma_db"
        db = RAGDatabase(persist_path=chroma_path)
        embeddings = EmbeddingModels()
        retriever = LayoutRetriever(db=db, embeddings=embeddings)
        return retriever.find_similar_layouts(layout_json, top_k=int(top_k), include_content=False)
    except Exception:
        return []


def build_figma_ai_brief(
    *,
    layout_json: Dict[str, Any],
    project_init: Optional[Dict[str, Any]] = None,
    config: Optional[FigmaAIBriefConfig] = None,
) -> Dict[str, Any]:
    """
    Create a "Mode 1" brief for Figma AI:
    - We do NOT call Figma AI via API (no public API); instead we generate a prompt pack
      that can be pasted into Figma AI / used as a structured design brief.
    - Optionally augments the brief with RAG-retrieved similar layouts (if enabled).
    """

    project_init = project_init or {}
    config = config or FigmaAIBriefConfig()

    doc = layout_json.get("document") or {}
    variant = layout_json.get("variant") or {}
    src = layout_json.get("source") or {}

    decisions = project_init.get("design_decisions") or {}
    typography = project_init.get("typography") or {}
    layout_cfg = project_init.get("layout") or {}
    print_cfg = project_init.get("print") or {}

    content_snippets = _extract_content_snippets(layout_json)
    similar = _rag_retrieve_similar(layout_json, top_k=config.top_k) if config.rag_enabled else []

    prompt_lines: List[str] = []
    prompt_lines.append("You are Figma AI. Create a print magazine double-page layout.")
    prompt_lines.append("Constraints:")
    prompt_lines.append(f"- Document size: {doc.get('width')}x{doc.get('height')} px @ {doc.get('dpi')} DPI")
    if variant:
        prompt_lines.append(f"- Variant: {variant}")
    if print_cfg:
        prompt_lines.append(f"- Print constraints: {print_cfg}")
    if layout_cfg:
        prompt_lines.append(f"- Layout system: {layout_cfg}")
    if typography:
        prompt_lines.append(f"- Typography: {typography}")
    if decisions:
        prompt_lines.append(f"- Design decisions: {decisions}")
    prompt_lines.append("")
    prompt_lines.append("Content to place (prioritized):")
    for s in content_snippets[:20]:
        role = f" ({s['role']})" if s.get("role") else ""
        prompt_lines.append(f"- {s.get('text')}{role}")
    if similar:
        prompt_lines.append("")
        prompt_lines.append("Reference patterns (RAG, similar layouts):")
        for r in similar[: config.top_k]:
            prompt_lines.append(f"- source={r.get('source')} similarity={r.get('similarity'):.3f} id={r.get('layout_id')}")

    return {
        "mode": 1,
        "source": {"pptx": src.get("name"), "chapter": src.get("chapter"), "act": src.get("act"), "act_title": src.get("act_title")},
        "document": {"width": doc.get("width"), "height": doc.get("height"), "dpi": doc.get("dpi")},
        "variant": variant,
        "content_snippets": content_snippets,
        "rag_similar_layouts": similar,
        "figma_ai_prompt": "\n".join(prompt_lines).strip(),
        "notes": [
            "Mode 1: The backend generates a prompt pack. A human (or a separate automation agent) triggers Figma AI in the UI.",
            "After frames are created, use /api/figma/frames/import to pull results back into the pipeline.",
        ],
    }

