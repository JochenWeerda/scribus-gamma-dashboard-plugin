"""
ChromaDB Setup für RAG-Service

Verwaltet die Vector Database mit Collections für:
- layouts: Layout-Strukturen
- texts: Gescannte Texte
- images: Bilder mit Metadaten
- text_image_pairs: Text-Bild-Zuordnungen
"""

from typing import Optional
import os


class RAGDatabase:
    """ChromaDB Client für RAG-Service"""
    
    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialisiert ChromaDB Client.
        
        Args:
            persist_directory: Pfad für persistente Datenbank (default: ./chroma_db)
        """
        if persist_directory is None:
            persist_directory = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        
        # Erstelle Verzeichnis falls nicht vorhanden
        os.makedirs(persist_directory, exist_ok=True)
        
        try:
            import chromadb
            from chromadb.config import Settings
        except Exception as e:
            raise RuntimeError(
                "RAGDatabase requires 'chromadb'. Install with: pip install chromadb"
            ) from e

        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )
        
        # Collections
        self.layouts_collection = self.client.get_or_create_collection(
            name="layouts",
            metadata={"hnsw:space": "cosine"}
        )
        self.texts_collection = self.client.get_or_create_collection(
            name="texts",
            metadata={"hnsw:space": "cosine"}
        )
        self.images_collection = self.client.get_or_create_collection(
            name="images",
            metadata={"hnsw:space": "cosine"}
        )
        self.pairs_collection = self.client.get_or_create_collection(
            name="text_image_pairs",
            metadata={"hnsw:space": "cosine"}
        )
    
    def get_collection(self, name: str):
        """Gibt Collection nach Namen zurück"""
        collections = {
            "layouts": self.layouts_collection,
            "texts": self.texts_collection,
            "images": self.images_collection,
            "text_image_pairs": self.pairs_collection,
        }
        return collections.get(name)

