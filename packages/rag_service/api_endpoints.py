"""
RAG API Endpoints für FastAPI

Diese Endpoints können in apps/api-gateway/main.py importiert und registriert werden.
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel
import os

# Globale Instanzen (werden beim Start initialisiert)
_rag_db: Optional[Any] = None
_rag_embeddings: Optional[Any] = None
_rag_indexer: Optional[Any] = None
_rag_media_indexer: Optional[Any] = None
_rag_retriever: Optional[Any] = None
_rag_matcher: Optional[Any] = None
_rag_context_builder: Optional[Any] = None
_rag_auto_indexer: Optional[Any] = None
_rag_validator: Optional[Any] = None
_rag_init_error: Optional[str] = None


def init_rag_service(
    chroma_db_path: Optional[str] = None,
    embedding_model: Optional[str] = None,
    clip_model: Optional[str] = None
):
    """
    Initialisiert RAG-Service (einmalig beim Start).
    
    Args:
        chroma_db_path: Pfad für ChromaDB (default: aus ENV)
        embedding_model: Text-Embedding-Model (default: aus ENV)
        clip_model: CLIP-Model (default: aus ENV)
    """
    global _rag_db, _rag_embeddings, _rag_indexer, _rag_media_indexer
    global _rag_retriever, _rag_matcher, _rag_context_builder, _rag_auto_indexer, _rag_validator, _rag_init_error

    if _rag_db is not None:
        return

    try:
        from .database import RAGDatabase
        from .embeddings import EmbeddingModels
        from .indexer import LayoutIndexer
        from .media_indexer import MediaIndexer
        from .retriever import LayoutRetriever
        from .matcher import TextImageMatcher
        from .llm_context import LLMContextBuilder
        from .auto_indexer import AutoIndexer
        from .scribus_validator import ScribusValidator

        _rag_db = RAGDatabase(persist_directory=chroma_db_path)

        if embedding_model:
            os.environ["EMBEDDING_MODEL"] = embedding_model
        if clip_model:
            os.environ["CLIP_MODEL"] = clip_model

        _rag_embeddings = EmbeddingModels()
        _rag_indexer = LayoutIndexer(_rag_db, _rag_embeddings)
        _rag_media_indexer = MediaIndexer(_rag_db, _rag_embeddings)
        _rag_retriever = LayoutRetriever(_rag_db, _rag_embeddings)
        _rag_matcher = TextImageMatcher(_rag_db, _rag_embeddings)
        _rag_context_builder = LLMContextBuilder(
            _rag_db, _rag_embeddings, _rag_retriever, _rag_matcher
        )
        _rag_auto_indexer = AutoIndexer(_rag_db, _rag_embeddings)
        _rag_validator = ScribusValidator(_rag_db, _rag_embeddings)

        _rag_init_error = None
    except Exception as e:
        _rag_init_error = str(e)
        _rag_db = None
        _rag_embeddings = None
        _rag_indexer = None
        _rag_media_indexer = None
        _rag_retriever = None
        _rag_matcher = None
        _rag_context_builder = None
        _rag_auto_indexer = None
        _rag_validator = None


# Pydantic Models für Request/Response
class SimilarLayoutsRequest(BaseModel):
    query: Union[str, Dict]
    top_k: int = 5
    include_content: bool = True


class FindImagesForTextRequest(BaseModel):
    text: str
    top_k: int = 5


class FindTextsForImageRequest(BaseModel):
    image_path: str
    top_k: int = 5


class SuggestPairsRequest(BaseModel):
    layout_json: Dict


class LLMContextRequest(BaseModel):
    prompt: str
    top_k_layouts: int = 3
    top_k_texts: int = 5
    top_k_images: int = 3


class IndexLayoutRequest(BaseModel):
    layout_json: Dict
    source: str = "unknown"  # figma|scribus|llm|unknown


class IndexMediaRequest(BaseModel):
    texts: Optional[List[Dict]] = None
    images: Optional[List[Dict]] = None


# Router
router = APIRouter(prefix="/api/rag", tags=["RAG"])


@router.post("/layouts/similar")
async def find_similar_layouts(request: SimilarLayoutsRequest):
    """Findet ähnliche Layouts"""
    if _rag_retriever is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        layouts = _rag_retriever.find_similar_layouts(
            request.query,
            top_k=request.top_k,
            include_content=request.include_content
        )
        return {"layouts": layouts, "count": len(layouts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/images/for-text")
async def find_images_for_text(request: FindImagesForTextRequest):
    """Findet passende Bilder für Text"""
    if _rag_matcher is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        images = _rag_matcher.find_images_for_text(request.text, top_k=request.top_k)
        return {"images": images, "count": len(images)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/texts/for-image")
async def find_texts_for_image(request: FindTextsForImageRequest):
    """Findet passende Texte für Bild"""
    if _rag_matcher is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        texts = _rag_matcher.find_texts_for_image(request.image_path, top_k=request.top_k)
        return {"texts": texts, "count": len(texts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest-pairs")
async def suggest_text_image_pairs(request: SuggestPairsRequest):
    """Schlägt Text-Bild-Zuordnungen vor"""
    if _rag_matcher is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        suggestions = _rag_matcher.suggest_text_image_pairs(request.layout_json)
        return {"suggestions": suggestions, "count": len(suggestions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm-context")
async def build_llm_context(request: LLMContextRequest):
    """Erstellt erweiterten Kontext für LLM"""
    if _rag_context_builder is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        context = _rag_context_builder.build_context_for_prompt(
            request.prompt,
            top_k_layouts=request.top_k_layouts,
            top_k_texts=request.top_k_texts,
            top_k_images=request.top_k_images
        )
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/layout")
async def index_layout(request: IndexLayoutRequest):
    """Manuelles Layout-Indexing"""
    if _rag_indexer is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        layout_id = _rag_indexer.index_layout(request.layout_json, source=request.source)
        return {"layout_id": layout_id, "status": "indexed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/media")
async def index_media(request: IndexMediaRequest):
    """Manuelles Medien-Indexing"""
    if _rag_auto_indexer is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        result = await _rag_auto_indexer.index_media_scan(
            texts=request.texts,
            images=request.images
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def rag_health():
    """Health Check für RAG-Service"""
    return {
        "status": "ok" if _rag_db is not None else "not_initialized",
        "components": {
            "database": _rag_db is not None,
            "embeddings": _rag_embeddings is not None,
            "indexer": _rag_indexer is not None,
            "retriever": _rag_retriever is not None,
            "matcher": _rag_matcher is not None,
        },
        "init_error": _rag_init_error,
    }

