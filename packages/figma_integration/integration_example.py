"""
Beispiel-Integration für Figma in API Gateway

Füge dies zu apps/api-gateway/main.py hinzu:
"""

# In apps/api-gateway/main.py:

# 1. Imports hinzufügen
"""
from packages.figma_integration.api_endpoints import router as figma_router, init_figma_service
from packages.rag_service.api_endpoints import router as rag_router, init_rag_service
from packages.rag_service.auto_indexer import AutoIndexer
from packages.sla_compiler.compiler import compile_layout_to_sla
"""

# 2. Beim Startup initialisieren
"""
@app.on_event("startup")
async def startup():
    # Figma Service initialisieren
    init_figma_service(
        access_token=os.getenv("FIGMA_ACCESS_TOKEN"),
        minio_client=minio_client,  # Dein MinIO Client
        minio_bucket="figma-assets"
    )
    
    # RAG Service initialisieren
    init_rag_service(
        chroma_db_path=os.getenv("CHROMA_DB_PATH", "./chroma_db"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-mpnet-base-v2"),
        clip_model=os.getenv("CLIP_MODEL", "clip-ViT-B-32")
    )
"""

# 3. Router registrieren
"""
app.include_router(figma_router)
app.include_router(rag_router)
"""

# 4. Frame-Import mit Compiler-Integration
"""
from packages.figma_integration.api_endpoints import _figma_client, _frame_converter, _asset_downloader
from packages.rag_service.auto_indexer import AutoIndexer
from packages.rag_service.database import RAGDatabase
from packages.rag_service.embeddings import EmbeddingModels

@app.post("/api/figma/frames/import-with-compile")
async def import_frame_with_compile(request: ImportFrameRequest):
    # 1. Frame importieren (wie in api_endpoints.py)
    layout_json = ...  # Aus api_endpoints.py
    
    # 2. RAG-Indexing
    db = RAGDatabase()
    embeddings = EmbeddingModels()
    auto_indexer = AutoIndexer(db, embeddings)
    await auto_indexer.index_figma_import(layout_json)
    
    # 3. Compiler aufrufen
    sla_xml_bytes = compile_layout_to_sla(layout_json)
    
    # 4. Job einreihen (falls Worker vorhanden)
    # job = queue.enqueue(process_compile_job, layout_json, sla_xml_bytes)
    
    return {
        "layout_json": layout_json,
        "sla_xml_size": len(sla_xml_bytes),
        # "job_id": job.id,
    }
"""

