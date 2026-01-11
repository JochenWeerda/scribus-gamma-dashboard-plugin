"""
Auto Indexer für RAG-Service

Automatisches Indexing bei verschiedenen Events:
- Figma-Frame-Import
- Scribus-Seite-Export
- Medien-Scan
- LLM-Layout-Generierung
"""

from typing import Dict, Optional
from .database import RAGDatabase
from .embeddings import EmbeddingModels
from .indexer import LayoutIndexer
from .media_indexer import MediaIndexer


class AutoIndexer:
    """Automatisches Indexing für verschiedene Quellen"""
    
    def __init__(
        self,
        db: RAGDatabase,
        embeddings: EmbeddingModels
    ):
        """
        Initialisiert Auto Indexer.
        
        Args:
            db: RAGDatabase Instanz
            embeddings: EmbeddingModels Instanz
        """
        self.db = db
        self.embeddings = embeddings
        self.layout_indexer = LayoutIndexer(db, embeddings)
        self.media_indexer = MediaIndexer(db, embeddings)
    
    async def index_figma_import(self, layout_json: Dict) -> str:
        """
        Automatisches Indexing nach Figma-Frame-Import.
        
        Args:
            layout_json: Layout JSON (nach FrameToLayoutConverter)
            
        Returns:
            Layout-ID
        """
        # index_layout ist synchron, daher kein await nötig
        return self.layout_indexer.index_layout(layout_json, source="figma")
    
    async def index_scribus_export(self, layout_json: Dict) -> str:
        """
        Automatisches Indexing nach Scribus-Seite-Export.
        
        Args:
            layout_json: Layout JSON (nach Layout-Extraktion)
            
        Returns:
            Layout-ID
        """
        return self.layout_indexer.index_layout(layout_json, source="scribus")
    
    async def index_llm_generation(self, layout_json: Dict) -> str:
        """
        Automatisches Indexing nach LLM-Layout-Generierung.
        
        Args:
            layout_json: Layout JSON (nach LLM-Generierung)
            
        Returns:
            Layout-ID
        """
        return self.layout_indexer.index_layout(layout_json, source="llm")
    
    async def index_media_scan(
        self,
        texts: Optional[list] = None,
        images: Optional[list] = None
    ) -> Dict[str, list]:
        """
        Automatisches Indexing nach Medien-Scan.
        
        Args:
            texts: Liste von Dicts mit "text", "source", "metadata"
            images: Liste von Dicts mit "path", "metadata"
            
        Returns:
            Dict mit "text_ids" und "image_ids"
        """
        text_ids = []
        image_ids = []
        
        if texts:
            text_ids = self.media_indexer.index_batch_texts(texts)
        
        if images:
            image_ids = self.media_indexer.index_batch_images(images)
        
        return {
            "text_ids": text_ids,
            "image_ids": image_ids,
        }
    
    async def index_compiler_result(
        self,
        layout_json: Dict,
        sla_xml: bytes,
        success: bool,
        errors: Optional[list] = None
    ):
        """
        Indexiert Compiler-Ergebnis für Digital Twin.
        
        Speichert XML-Patterns und deren Verhalten (success/error).
        
        Args:
            layout_json: Input Layout JSON
            sla_xml: Generiertes SLA XML
            success: Ob Compilation erfolgreich war
            errors: Liste von Fehlern (falls vorhanden)
        """
        from .scribus_validator import ScribusValidator
        import xml.etree.ElementTree as ET
        
        validator = ScribusValidator(self.db, self.embeddings)
        
        try:
            # Parse XML
            root = ET.fromstring(sla_xml)
            
            # Indexiere alle XML-Elemente
            for elem in root.iter():
                behavior = "success" if success else "error"
                issue = None
                if errors:
                    issue = "; ".join(errors[:3])  # Erste 3 Fehler
                
                validator.learn_xml_pattern(
                    elem,
                    behavior=behavior,
                    issue=issue,
                    test_result={
                        "success": success,
                        "errors": errors or [],
                    }
                )
        except Exception as e:
            # Fehler beim Parsen ignorieren
            pass

