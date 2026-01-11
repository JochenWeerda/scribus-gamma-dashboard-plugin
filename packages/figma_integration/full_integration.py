"""
Vollständige Figma-Integration mit Compiler und RAG

Diese Datei zeigt, wie Figma-Import vollständig integriert wird:
1. Frame von Figma abrufen
2. Frame → Layout JSON konvertieren
3. Images zu MinIO migrieren
4. RAG-Indexing
5. Compiler aufrufen
6. SLA zurückgeben
"""

from typing import Dict, Optional
import os

# Imports (werden in apps/api-gateway/main.py verwendet)
try:
    from packages.figma_integration.client import FigmaClient
    from packages.figma_integration.converter import FrameToLayoutConverter
    from packages.figma_integration.asset_downloader import FigmaAssetDownloader
    from packages.rag_service.auto_indexer import AutoIndexer
    from packages.rag_service.database import RAGDatabase
    from packages.rag_service.embeddings import EmbeddingModels
    from packages.sla_compiler.compiler import compile_layout_to_sla
except ImportError:
    # Fallback für Entwicklung
    pass


async def import_figma_frame_with_full_pipeline(
    file_key: str,
    frame_id: str,
    dpi: int = 300,
    page_number: int = 1,
    figma_client: Optional[FigmaClient] = None,
    frame_converter: Optional[FrameToLayoutConverter] = None,
    asset_downloader: Optional[FigmaAssetDownloader] = None,
    auto_indexer: Optional[AutoIndexer] = None
) -> Dict:
    """
    Vollständiger Figma-Import-Pipeline:
    1. Frame von Figma abrufen
    2. Frame → Layout JSON konvertieren
    3. Images zu MinIO migrieren
    4. RAG-Indexing
    5. Compiler aufrufen
    6. SLA zurückgeben
    
    Args:
        file_key: Figma File Key
        frame_id: Frame Node ID
        dpi: DPI für Dokument
        page_number: Seitenzahl
        figma_client: FigmaClient Instanz (optional)
        frame_converter: FrameToLayoutConverter Instanz (optional)
        asset_downloader: FigmaAssetDownloader Instanz (optional)
        auto_indexer: AutoIndexer Instanz (optional)
        
    Returns:
        Dict mit layout_json, sla_xml_bytes, layout_id (RAG)
    """
    # 1. Initialisiere Services (falls nicht übergeben)
    if not figma_client:
        figma_client = FigmaClient(access_token=os.getenv("FIGMA_ACCESS_TOKEN"))
    
    if not frame_converter:
        frame_converter = FrameToLayoutConverter()
    
    if not asset_downloader:
        asset_downloader = FigmaAssetDownloader(
            minio_client=None,  # TODO: MinIO Client übergeben
            minio_bucket="figma-assets"
        )
    
    if not auto_indexer:
        db = RAGDatabase()
        embeddings = EmbeddingModels()
        auto_indexer = AutoIndexer(db, embeddings)
    
    # 2. Frame von Figma abrufen
    frame_json = figma_client.get_frame(file_key, frame_id)
    
    # 3. Frame → Layout JSON konvertieren
    layout_json = frame_converter.convert(
        frame_json,
        dpi=dpi,
        page_number=page_number
    )
    
    # 4. Images herunterladen und zu MinIO hochladen
    image_objects = [
        obj for obj in layout_json["pages"][0]["objects"]
        if obj.get("type") == "image"
    ]
    
    if image_objects:
        minio_urls = asset_downloader.download_frame_images(
            figma_client,
            file_key,
            frame_json,
            image_objects
        )
        
        # Ersetze leere mediaId mit MinIO-URLs
        for obj in image_objects:
            obj_id = obj.get("id", "")
            if obj_id in minio_urls:
                obj["mediaId"] = minio_urls[obj_id]
    
    # 5. RAG-Indexing (automatisch)
    layout_id = await auto_indexer.index_figma_import(layout_json)
    
    # 6. Compiler aufrufen
    try:
        sla_xml_bytes = compile_layout_to_sla(layout_json)
    except Exception as e:
        raise ValueError(f"Compiler error: {e}")
    
    # 7. Compiler-Ergebnis für Digital Twin indexieren
    await auto_indexer.index_compiler_result(
        layout_json=layout_json,
        sla_xml=sla_xml_bytes,
        success=True,
        errors=None
    )
    
    return {
        "layout_json": layout_json,
        "sla_xml_bytes": sla_xml_bytes,
        "sla_xml_size": len(sla_xml_bytes),
        "layout_id": layout_id,  # RAG Layout ID
        "file_key": file_key,
        "frame_id": frame_id,
    }


async def export_scribus_page_to_figma(
    layout_json: Dict,
    file_key: str,
    frame_name: str = "Exported Page",
    layout_converter: Optional[LayoutToFrameConverter] = None,
    auto_indexer: Optional[AutoIndexer] = None
) -> Dict:
    """
    Exportiert Scribus-Seite nach Figma:
    1. Layout JSON → Figma Frame konvertieren
    2. RAG-Indexing (als Scribus-Export)
    3. Frame zurückgeben (für create_frame)
    
    Args:
        layout_json: Layout JSON Schema (von Scribus-Seite)
        file_key: Figma File Key
        frame_name: Name für Frame
        layout_converter: LayoutToFrameConverter Instanz (optional)
        auto_indexer: AutoIndexer Instanz (optional)
        
    Returns:
        Dict mit frame_json, layout_id (RAG)
    """
    from packages.figma_integration.converter import LayoutToFrameConverter
    
    if not layout_converter:
        layout_converter = LayoutToFrameConverter()
    
    if not auto_indexer:
        db = RAGDatabase()
        embeddings = EmbeddingModels()
        auto_indexer = AutoIndexer(db, embeddings)
    
    # 1. Layout JSON → Figma Frame konvertieren
    frame_json = layout_converter.convert(layout_json, frame_name=frame_name)
    
    # 2. RAG-Indexing (als Scribus-Export)
    layout_id = await auto_indexer.index_scribus_export(layout_json)
    
    return {
        "frame": frame_json,
        "file_key": file_key,
        "layout_id": layout_id,
        "status": "converted",  # "created" wenn Frame erstellt wurde
    }

