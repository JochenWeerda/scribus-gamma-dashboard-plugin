from __future__ import annotations

from typing import Any, Dict, Optional


def build_rag_context(prompt: str, *, decisions: Dict[str, Any], max_items: int = 5) -> Dict[str, Any]:
    """
    Optional RAG helper. Tries to use `packages.rag_service` when available.
    Returns a stable dict that can be embedded into a downstream LLM prompt.
    """

    try:
        from packages.rag_service import LLMContextBuilder, RAGDatabase, EmbeddingModels  # type: ignore
    except Exception:
        return {"enabled": False, "items": [], "note": "rag_service not available"}

    try:
        db = RAGDatabase()
        embeddings = EmbeddingModels()
        builder = LLMContextBuilder(db=db, embeddings=embeddings)
        context = builder.build_context(prompt, max_items=max_items)
        return {"enabled": True, "items": context, "decisions": decisions}
    except Exception as exc:
        return {"enabled": False, "items": [], "note": f"rag_service error: {exc}"}

