"""
Media Indexer für RAG-Service

Indexiert gescannte Texte und Bilder aus Medien-Dateien (PDF, DOCX, PPTX, etc.)
"""

from typing import Dict, List, Optional
from .database import RAGDatabase
from .embeddings import EmbeddingModels
import json
import uuid


class MediaIndexer:
    """Indexiert gescannte Medien-Inhalte in ChromaDB"""
    
    def __init__(self, db: RAGDatabase, embeddings: EmbeddingModels):
        """
        Initialisiert Media Indexer.
        
        Args:
            db: RAGDatabase Instanz
            embeddings: EmbeddingModels Instanz
        """
        self.db = db
        self.embeddings = embeddings
    
    def index_scanned_text(
        self, 
        text: str, 
        source: str, 
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Indexiert gescannten Text (aus PDF, DOCX, PPTX).
        
        Args:
            text: Text-Content
            source: Dateipfad oder Quelle
            metadata: Zusätzliche Metadaten (pageNumber, relatedImageIds, etc.)
            
        Returns:
            Text-ID
        """
        if not text or not text.strip():
            return None
        
        text_id = str(uuid.uuid4())
        embedding = self.embeddings.embed_text(text)
        
        meta = metadata or {}
        meta.update({
            "source": source,
            "type": "scanned_text",
        })
        
        self.db.texts_collection.add(
            ids=[text_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[meta]
        )
        
        return text_id
    
    def index_scanned_image(
        self, 
        image_path: str, 
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Indexiert gescanntes Bild mit CLIP-Embedding.
        
        Args:
            image_path: Pfad zum Bild
            metadata: Metadaten (source, altText, extractedText, relatedTextIds)
            
        Returns:
            Image-ID
        """
        if not image_path:
            return None
        
        image_id = str(uuid.uuid4())
        
        try:
            # CLIP-Embedding für Bild
            embedding = self.embeddings.embed_image(image_path)
            document_text = ""
        except Exception as e:
            # Fallback: Metadaten-Text verwenden
            meta = metadata or {}
            alt_text = meta.get("altText", "") or meta.get("extractedText", "")
            if alt_text:
                embedding = self.embeddings.embed_text(alt_text)
                document_text = alt_text
            else:
                # Letzter Fallback: Dateiname
                document_text = image_path.split("/")[-1]
                embedding = self.embeddings.embed_text(document_text)
        
        meta = metadata or {}
        meta.update({
            "type": "scanned_image",
            "path": image_path,
        })
        
        self.db.images_collection.add(
            ids=[image_id],
            embeddings=[embedding],
            documents=[document_text or image_path],
            metadatas=[meta]
        )
        
        return image_id
    
    def index_text_image_pair(
        self, 
        text_id: str, 
        image_id: str, 
        relationship: str = "related",
        text_content: Optional[str] = None,
        image_path: Optional[str] = None
    ) -> str:
        """
        Indexiert Text-Bild-Zuordnung.
        
        Args:
            text_id: ID des Textes
            image_id: ID des Bildes
            relationship: "describes" | "illustrates" | "references" | "related"
            text_content: Text-Content (optional, für Embedding)
            image_path: Bild-Pfad (optional, für Embedding)
            
        Returns:
            Pair-ID
        """
        pair_id = f"{text_id}_{image_id}"
        
        # Versuche kombiniertes Embedding
        if text_content and image_path:
            try:
                embedding = self.embeddings.embed_text_image_pair(text_content, image_path)
            except:
                # Fallback: Text-Embedding
                combined = f"{text_content} {relationship}"
                embedding = self.embeddings.embed_text(combined)
        else:
            # Fallback: Nur Text
            combined = f"Text-Image pair: {relationship}"
            embedding = self.embeddings.embed_text(combined)
        
        self.db.pairs_collection.add(
            ids=[pair_id],
            embeddings=[embedding],
            documents=[f"Text-Image pair: {relationship}"],
            metadatas=[{
                "text_id": text_id,
                "image_id": image_id,
                "relationship": relationship,
            }]
        )
        
        return pair_id
    
    def index_batch_texts(
        self,
        texts: List[Dict]
    ) -> List[str]:
        """
        Batch-Indexing für mehrere Texte.
        
        Args:
            texts: Liste von Dicts mit "text", "source", "metadata"
            
        Returns:
            Liste von Text-IDs
        """
        text_ids = []
        
        for item in texts:
            text_id = self.index_scanned_text(
                item.get("text", ""),
                item.get("source", ""),
                item.get("metadata")
            )
            if text_id:
                text_ids.append(text_id)
        
        return text_ids
    
    def index_batch_images(
        self,
        images: List[Dict]
    ) -> List[str]:
        """
        Batch-Indexing für mehrere Bilder.
        
        Args:
            images: Liste von Dicts mit "path", "metadata"
            
        Returns:
            Liste von Image-IDs
        """
        image_ids = []
        
        for item in images:
            image_id = self.index_scanned_image(
                item.get("path", ""),
                item.get("metadata")
            )
            if image_id:
                image_ids.append(image_id)
        
        return image_ids

