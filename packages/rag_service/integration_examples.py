"""
Integration Examples für RAG-Service

Zeigt, wie RAG in verschiedene Komponenten integriert wird.
"""

# Beispiel 1: Integration in Figma-Import
async def example_figma_import_integration():
    """
    Beispiel: Automatisches RAG-Indexing nach Figma-Frame-Import
    """
    from .auto_indexer import AutoIndexer
    from .database import RAGDatabase
    from .embeddings import EmbeddingModels
    
    # Initialisiere RAG
    db = RAGDatabase()
    embeddings = EmbeddingModels()
    auto_indexer = AutoIndexer(db, embeddings)
    
    # Nach FrameToLayoutConverter
    layout_json = {
        "version": "1.0.0",
        "document": {"width": 4960, "height": 3508, "dpi": 300},
        "pages": [{
            "pageNumber": 1,
            "objects": [...]
        }]
    }
    
    # Automatisches Indexing
    layout_id = await auto_indexer.index_figma_import(layout_json)
    print(f"Layout indexiert: {layout_id}")


# Beispiel 2: Integration in Compiler (Digital Twin)
async def example_compiler_integration():
    """
    Beispiel: Compiler nutzt RAG für XML-Validierung (Digital Twin)
    """
    from .scribus_validator import ScribusValidator
    from .database import RAGDatabase
    from .embeddings import EmbeddingModels
    from .auto_indexer import AutoIndexer
    import xml.etree.ElementTree as ET
    
    # Initialisiere RAG
    db = RAGDatabase()
    embeddings = EmbeddingModels()
    validator = ScribusValidator(db, embeddings)
    auto_indexer = AutoIndexer(db, embeddings)
    
    # Compiler generiert XML
    xml_element = ET.Element("ITEM", ITEMTEXT="Test", FONT="Minion Pro", FONTSIZE="12")
    
    # Validiere vor dem Senden an Scribus
    is_valid, warnings, suggested_fix = validator.validate_xml_construct(xml_element)
    
    if not is_valid:
        print(f"Warnungen: {warnings}")
        if suggested_fix:
            print(f"Vorschlag: {suggested_fix}")
        # Verwende Vorschlag oder verwirf Konstrukt
    
    # Nach erfolgreicher Compilation: Lerne Pattern
    sla_xml = b"<SCRIBUSUTF8NEW>...</SCRIBUSUTF8NEW>"
    await auto_indexer.index_compiler_result(
        layout_json={},
        sla_xml=sla_xml,
        success=is_valid,
        errors=warnings if not is_valid else None
    )


# Beispiel 3: Integration in Media Processor
async def example_media_processor_integration():
    """
    Beispiel: Automatisches RAG-Indexing nach Medien-Scan
    """
    from .auto_indexer import AutoIndexer
    from .database import RAGDatabase
    from .embeddings import EmbeddingModels
    
    # Initialisiere RAG
    db = RAGDatabase()
    embeddings = EmbeddingModels()
    auto_indexer = AutoIndexer(db, embeddings)
    
    # Nach Media Processor
    texts = [
        {
            "text": "Künstliche Intelligenz revolutioniert...",
            "source": "media_pool/articles/ki-article.pdf",
            "metadata": {"pageNumber": 1}
        }
    ]
    
    images = [
        {
            "path": "media_pool/images/ki-diagram.png",
            "metadata": {
                "altText": "KI-Architektur-Diagramm",
                "source": "media_pool/images/ki-diagram.png"
            }
        }
    ]
    
    # Automatisches Indexing
    result = await auto_indexer.index_media_scan(texts=texts, images=images)
    print(f"Indexiert: {len(result['text_ids'])} Texte, {len(result['image_ids'])} Bilder")


# Beispiel 4: Integration in LLM-Generierung
async def example_llm_generation_integration():
    """
    Beispiel: RAG-Kontext für LLM + automatisches Indexing
    """
    from .llm_context import LLMContextBuilder
    from .database import RAGDatabase
    from .embeddings import EmbeddingModels
    from .retriever import LayoutRetriever
    from .matcher import TextImageMatcher
    from .auto_indexer import AutoIndexer
    
    # Initialisiere RAG
    db = RAGDatabase()
    embeddings = EmbeddingModels()
    retriever = LayoutRetriever(db, embeddings)
    matcher = TextImageMatcher(db, embeddings)
    context_builder = LLMContextBuilder(db, embeddings, retriever, matcher)
    auto_indexer = AutoIndexer(db, embeddings)
    
    # 1. Erweitere Prompt mit RAG-Kontext
    user_prompt = "Erstelle ein Magazin-Layout über KI"
    context = context_builder.build_context_for_prompt(
        user_prompt,
        top_k_layouts=3,
        top_k_texts=5,
        top_k_images=3
    )
    
    enhanced_prompt = context["context"]
    print(f"Erweiterter Prompt:\n{enhanced_prompt}")
    
    # 2. LLM generiert Layout JSON
    layout_json = {
        "version": "1.0.0",
        "document": {"width": 2480, "height": 3508, "dpi": 300},
        "pages": [{
            "pageNumber": 1,
            "objects": [...]
        }]
    }
    
    # 3. Automatisches Indexing
    layout_id = await auto_indexer.index_llm_generation(layout_json)
    print(f"Layout indexiert: {layout_id}")


# Beispiel 5: Integration in API Gateway
def example_api_gateway_integration():
    """
    Beispiel: RAG-Endpoints in FastAPI registrieren
    """
    from fastapi import FastAPI
    from .api_endpoints import router, init_rag_service
    
    app = FastAPI()
    
    # Initialisiere RAG beim Start
    @app.on_event("startup")
    async def startup():
        init_rag_service(
            chroma_db_path="./chroma_db",
            embedding_model="all-MiniLM-L6-v2",
            clip_model="clip-ViT-B-32"
        )
    
    # Registriere RAG-Router
    app.include_router(router)
    
    return app

