"""
Layout Retriever für RAG-Service

Findet ähnliche Layouts basierend auf Struktur, Text, Bildern und Kombinationen.
"""

from typing import Dict, List, Union, Optional
from .database import RAGDatabase
from .embeddings import EmbeddingModels
import json


class LayoutRetriever:
    """Retrieval für ähnliche Layouts"""
    
    def __init__(self, db: RAGDatabase, embeddings: EmbeddingModels):
        """
        Initialisiert Layout Retriever.
        
        Args:
            db: RAGDatabase Instanz
            embeddings: EmbeddingModels Instanz
        """
        self.db = db
        self.embeddings = embeddings
    
    def find_similar_layouts(
        self,
        query: Union[str, Dict],
        top_k: int = 5,
        include_content: bool = True
    ) -> List[Dict]:
        """
        Findet ähnliche Layouts basierend auf:
        - Struktur-Ähnlichkeit
        - Text-Ähnlichkeit
        - Bild-Ähnlichkeit
        - Text-Bild-Kombinationen
        
        Args:
            query: Text-Query oder Layout JSON
            top_k: Anzahl der Ergebnisse
            include_content: Ob Layout JSON inkludiert werden soll
            
        Returns:
            Liste von ähnlichen Layouts mit Similarity-Scores
        """
        if isinstance(query, dict):
            # Layout JSON → Struktur-Text
            from .indexer import LayoutIndexer
            indexer = LayoutIndexer(self.db, self.embeddings)
            query_text = indexer._extract_layout_structure(query)
        else:
            query_text = query
        
        # Query-Embedding
        query_embedding = self.embeddings.embed_text(query_text)
        
        # Similarity Search
        results = self.db.layouts_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        layouts = []
        for i, metadata in enumerate(results["metadatas"][0]):
            layout_data = {
                "layout_id": results["ids"][0][i],
                "similarity": 1.0 - results["distances"][0][i],  # Cosine distance → similarity
                "source": metadata.get("source", "unknown"),
                "document": results["documents"][0][i] if include_content else None,
            }
            
            if include_content and "layout_json" in metadata:
                try:
                    layout_data["layout_json"] = json.loads(metadata["layout_json"])
                except:
                    pass
            
            layouts.append(layout_data)
        
        return layouts
    
    def find_layouts_by_text(self, text: str, top_k: int = 5) -> List[Dict]:
        """
        Findet Layouts mit ähnlichem Text-Content.
        
        Args:
            text: Text-Query
            top_k: Anzahl der Ergebnisse
            
        Returns:
            Liste von Layouts mit Text-Ähnlichkeit
        """
        # Text-Embedding
        query_embedding = self.embeddings.embed_text(text)
        
        # Suche in Text-Collection
        text_results = self.db.texts_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 2,  # Mehr Ergebnisse für Aggregation
            include=["metadatas", "distances"]
        )
        
        # Gruppiere nach layout_id
        layout_scores = {}
        for i, metadata in enumerate(text_results["metadatas"][0]):
            layout_id = metadata.get("layout_id")
            if layout_id:
                similarity = 1.0 - text_results["distances"][0][i]
                if layout_id not in layout_scores:
                    layout_scores[layout_id] = []
                layout_scores[layout_id].append(similarity)
        
        # Durchschnittliche Similarity pro Layout
        layouts = []
        for layout_id, scores in layout_scores.items():
            avg_similarity = sum(scores) / len(scores)
            layouts.append({
                "layout_id": layout_id,
                "similarity": avg_similarity,
                "text_matches": len(scores),
            })
        
        # Sortiere nach Similarity
        layouts.sort(key=lambda x: x["similarity"], reverse=True)
        
        return layouts[:top_k]
    
    def find_layouts_by_image(self, image_path: str, top_k: int = 5) -> List[Dict]:
        """
        Findet Layouts mit ähnlichen Bildern (CLIP-Similarity).
        
        Args:
            image_path: Pfad zum Bild
            top_k: Anzahl der Ergebnisse
            
        Returns:
            Liste von Layouts mit Bild-Ähnlichkeit
        """
        try:
            # Bild-Embedding
            query_embedding = self.embeddings.embed_image(image_path)
        except:
            # Fallback: Metadaten-Text
            image_name = image_path.split("/")[-1]
            query_embedding = self.embeddings.embed_text(image_name)
        
        # Suche in Image-Collection
        image_results = self.db.images_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 2,
            include=["metadatas", "distances"]
        )
        
        # Gruppiere nach layout_id
        layout_scores = {}
        for i, metadata in enumerate(image_results["metadatas"][0]):
            layout_id = metadata.get("layout_id")
            if layout_id:
                similarity = 1.0 - image_results["distances"][0][i]
                if layout_id not in layout_scores:
                    layout_scores[layout_id] = []
                layout_scores[layout_id].append(similarity)
        
        # Durchschnittliche Similarity pro Layout
        layouts = []
        for layout_id, scores in layout_scores.items():
            avg_similarity = sum(scores) / len(scores)
            layouts.append({
                "layout_id": layout_id,
                "similarity": avg_similarity,
                "image_matches": len(scores),
            })
        
        # Sortiere nach Similarity
        layouts.sort(key=lambda x: x["similarity"], reverse=True)
        
        return layouts[:top_k]
    
    def find_layouts_by_text_image_pair(
        self,
        text: str,
        image_path: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Findet Layouts mit ähnlichen Text-Bild-Kombinationen.
        
        Args:
            text: Text-Query
            image_path: Pfad zum Bild
            top_k: Anzahl der Ergebnisse
            
        Returns:
            Liste von Layouts mit Text-Bild-Pair-Ähnlichkeit
        """
        try:
            # Kombiniertes Embedding
            query_embedding = self.embeddings.embed_text_image_pair(text, image_path)
        except:
            # Fallback: Text-Embedding
            combined = f"{text} {image_path}"
            query_embedding = self.embeddings.embed_text(combined)
        
        # Suche in Pairs-Collection
        pair_results = self.db.pairs_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 2,
            include=["metadatas", "distances"]
        )
        
        # Gruppiere nach layout_id
        layout_scores = {}
        for i, metadata in enumerate(pair_results["metadatas"][0]):
            layout_id = metadata.get("layout_id")
            if layout_id:
                similarity = 1.0 - pair_results["distances"][0][i]
                if layout_id not in layout_scores:
                    layout_scores[layout_id] = []
                layout_scores[layout_id].append(similarity)
        
        # Durchschnittliche Similarity pro Layout
        layouts = []
        for layout_id, scores in layout_scores.items():
            avg_similarity = sum(scores) / len(scores)
            layouts.append({
                "layout_id": layout_id,
                "similarity": avg_similarity,
                "pair_matches": len(scores),
            })
        
        # Sortiere nach Similarity
        layouts.sort(key=lambda x: x["similarity"], reverse=True)
        
        return layouts[:top_k]

