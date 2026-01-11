"""
API Gateway Integration für Figma und RAG

Füge dies zu apps/api-gateway/main.py hinzu:
"""

# ============================================================================
# In apps/api-gateway/main.py:
# ============================================================================

"""
# 1. Imports hinzufügen
import os
from fastapi import FastAPI
from packages.figma_integration.api_endpoints import (
    router as figma_router,
    init_figma_service
)
from packages.rag_service.api_endpoints import (
    router as rag_router,
    init_rag_service
)
from packages.rag_service.auto_indexer import AutoIndexer
from packages.rag_service.database import RAGDatabase
from packages.rag_service.embeddings import EmbeddingModels

# 2. App erstellen
app = FastAPI(title="Gamma API Gateway")

# 3. Startup Event
@app.on_event("startup")
async def startup():
    # RAG Service initialisieren
    init_rag_service(
        chroma_db_path=os.getenv("CHROMA_DB_PATH", "./chroma_db"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-mpnet-base-v2"),
        clip_model=os.getenv("CLIP_MODEL", "clip-ViT-B-32")
    )
    
    # AutoIndexer für Figma-Integration
    db = RAGDatabase(persist_directory=os.getenv("CHROMA_DB_PATH", "./chroma_db"))
    embeddings = EmbeddingModels()
    auto_indexer = AutoIndexer(db, embeddings)
    
    # Figma Service initialisieren (mit AutoIndexer)
    init_figma_service(
        access_token=os.getenv("FIGMA_ACCESS_TOKEN"),
        minio_client=None,  # TODO: MinIO Client übergeben
        minio_bucket="figma-assets",
        auto_indexer=auto_indexer
    )

# 4. Router registrieren
app.include_router(figma_router)
app.include_router(rag_router)

# 5. Health Check
@app.get("/health")
async def health():
    return {"status": "ok", "services": ["figma", "rag"]}
"""

# ============================================================================
# Alternative: Separate Endpoint für vollständige Pipeline
# ============================================================================

"""
from packages.figma_integration.full_integration import (
    import_figma_frame_with_full_pipeline
)

@app.post("/api/figma/frames/import-full")
async def import_frame_full(request: ImportFrameRequest):
    \"\"\"
    Vollständiger Figma-Import mit Compiler und RAG.
    \"\"\"
    result = await import_figma_frame_with_full_pipeline(
        file_key=request.file_key,
        frame_id=request.frame_id,
        dpi=request.dpi,
        page_number=request.page_number
    )
    
    return result
"""

