"""
Text-Image Matcher für RAG-Service

Findet passende Bilder für Texte und umgekehrt basierend auf CLIP-Similarity.
"""

from typing import Dict, List, Optional
from .database import RAGDatabase
from .embeddings import EmbeddingModels
import json


class TextImageMatcher:
    """Text-Bild-Matching mit CLIP-Similarity"""
    
    def __init__(self, db: RAGDatabase, embeddings: EmbeddingModels):
        """
        Initialisiert Text-Image Matcher.
        
        Args:
            db: RAGDatabase Instanz
            embeddings: EmbeddingModels Instanz
        """
        self.db = db
        self.embeddings = embeddings
    
    def find_images_for_text(self, text: str, top_k: int = 5) -> List[Dict]:
        """
        Findet Bilder, die zu einem Text passen (CLIP-Similarity).
        
        Args:
            text: Text-Query
            top_k: Anzahl der Ergebnisse
            
        Returns:
            Liste von Bildern mit Similarity-Scores
        """
        # Text-Embedding mit CLIP (für gemeinsamen Space)
        try:
            query_embedding = self.embeddings.clip_model.encode(text, convert_to_numpy=True).tolist()
        except:
            # Fallback: Text-Model
            query_embedding = self.embeddings.embed_text(text)
        
        # Suche in Image-Collection
        results = self.db.images_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        images = []
        for i, metadata in enumerate(results["metadatas"][0]):
            image_data = {
                "imageId": results["ids"][0][i],
                "path": metadata.get("path") or metadata.get("media_id", ""),
                "similarity": 1.0 - results["distances"][0][i],
                "document": results["documents"][0][i],
                "metadata": metadata,
            }
            
            # Finde zugehörige Texte
            related_texts = self._find_related_texts(results["ids"][0][i])
            image_data["relatedTexts"] = related_texts
            
            images.append(image_data)
        
        return images
    
    def find_texts_for_image(self, image_path: str, top_k: int = 5) -> List[Dict]:
        """
        Findet Texte, die zu einem Bild passen (CLIP-Similarity).
        
        Args:
            image_path: Pfad zum Bild
            top_k: Anzahl der Ergebnisse
            
        Returns:
            Liste von Texten mit Similarity-Scores
        """
        try:
            # Bild-Embedding mit CLIP
            query_embedding = self.embeddings.embed_image(image_path)
        except:
            # Fallback: Text-Embedding für Dateiname
            image_name = image_path.split("/")[-1]
            query_embedding = self.embeddings.embed_text(image_name)
        
        # Suche in Text-Collection
        results = self.db.texts_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        texts = []
        for i, metadata in enumerate(results["metadatas"][0]):
            text_data = {
                "textId": results["ids"][0][i],
                "content": results["documents"][0][i],
                "similarity": 1.0 - results["distances"][0][i],
                "source": metadata.get("source", ""),
                "metadata": metadata,
            }
            
            # Finde zugehörige Bilder
            related_images = self._find_related_images(results["ids"][0][i])
            text_data["relatedImages"] = related_images
            
            texts.append(text_data)
        
        return texts
    
    def suggest_text_image_pairs(
        self,
        layout_json: Dict
    ) -> List[Dict]:
        """
        Schlägt Text-Bild-Zuordnungen vor basierend auf:
        - Semantische Ähnlichkeit (CLIP)
        - Räumliche Nähe im Layout
        - Bestehende Zuordnungen in ähnlichen Layouts
        
        Args:
            layout_json: Layout JSON Schema
            
        Returns:
            Liste von Vorschlägen: [{"textId": "...", "imageId": "...", "similarity": 0.85}]
        """
        suggestions = []
        
        # Extrahiere Text- und Bild-Objekte
        texts = []
        images = []
        
        for page in layout_json.get("pages", []):
            for obj in page.get("objects", []):
                if obj.get("type") == "text":
                    content = obj.get("content", "")
                    if content:
                        texts.append({
                            "id": obj.get("id"),
                            "content": content,
                            "bbox": obj.get("bbox", {}),
                        })
                elif obj.get("type") == "image":
                    media_id = obj.get("mediaId", "")
                    if media_id:
                        images.append({
                            "id": obj.get("id"),
                            "mediaId": media_id,
                            "bbox": obj.get("bbox", {}),
                            "metadata": obj.get("metadata", {}),
                        })
        
        # Für jeden Text: Finde passende Bilder
        for text_obj in texts:
            text_content = text_obj["content"]
            text_bbox = text_obj["bbox"]
            
            # Semantische Suche: Finde ähnliche Bilder
            similar_images = self.find_images_for_text(text_content, top_k=10)
            
            for img_data in similar_images:
                # Finde entsprechendes Bild-Objekt im Layout
                for img_obj in images:
                    if img_obj["mediaId"] == img_data.get("path") or \
                       img_obj["mediaId"] == img_data.get("metadata", {}).get("media_id"):
                        
                        # Berechne räumliche Nähe
                        img_bbox = img_obj["bbox"]
                        spatial_score = self._calculate_spatial_proximity(text_bbox, img_bbox)
                        
                        # Kombinierte Similarity
                        combined_similarity = (img_data["similarity"] * 0.7) + (spatial_score * 0.3)
                        
                        suggestions.append({
                            "textId": text_obj["id"],
                            "imageId": img_obj["id"],
                            "similarity": combined_similarity,
                            "semantic_similarity": img_data["similarity"],
                            "spatial_proximity": spatial_score,
                        })
        
        # Sortiere nach Similarity
        suggestions.sort(key=lambda x: x["similarity"], reverse=True)
        
        return suggestions[:20]  # Top 20 Vorschläge
    
    def _find_related_texts(self, image_id: str) -> List[Dict]:
        """Findet zugehörige Texte für ein Bild (aus Pairs-Collection)"""
        # Suche in Pairs-Collection nach image_id
        try:
            results = self.db.pairs_collection.get(
                where={"image_id": image_id},
                include=["metadatas"]
            )
            
            text_ids = [meta.get("text_id") for meta in results.get("metadatas", [])]
            
            # Hole Text-Details
            if text_ids:
                text_results = self.db.texts_collection.get(
                    ids=text_ids,
                    include=["documents", "metadatas"]
                )
                return [
                    {
                        "textId": tid,
                        "content": doc[:100] if doc else "",  # Erste 100 Zeichen
                    }
                    for tid, doc in zip(text_ids, text_results.get("documents", []))
                ]
        except:
            pass
        
        return []
    
    def _find_related_images(self, text_id: str) -> List[Dict]:
        """Findet zugehörige Bilder für einen Text (aus Pairs-Collection)"""
        # Suche in Pairs-Collection nach text_id
        try:
            results = self.db.pairs_collection.get(
                where={"text_id": text_id},
                include=["metadatas"]
            )
            
            image_ids = [meta.get("image_id") for meta in results.get("metadatas", [])]
            
            # Hole Image-Details
            if image_ids:
                image_results = self.db.images_collection.get(
                    ids=image_ids,
                    include=["documents", "metadatas"]
                )
                return [
                    {
                        "imageId": iid,
                        "path": meta.get("path") or meta.get("media_id", ""),
                    }
                    for iid, meta in zip(image_ids, image_results.get("metadatas", []))
                ]
        except:
            pass
        
        return []
    
    def _calculate_spatial_proximity(self, bbox1: Dict, bbox2: Dict) -> float:
        """
        Berechnet räumliche Nähe zwischen zwei Bounding Boxes.
        
        Returns:
            Score zwischen 0.0 (weit entfernt) und 1.0 (sehr nah)
        """
        x1, y1 = bbox1.get("x", 0), bbox1.get("y", 0)
        w1, h1 = bbox1.get("w", 0), bbox1.get("h", 0)
        x2, y2 = bbox2.get("x", 0), bbox2.get("y", 0)
        w2, h2 = bbox2.get("w", 0), bbox2.get("h", 0)
        
        # Zentren
        cx1 = x1 + w1 / 2
        cy1 = y1 + h1 / 2
        cx2 = x2 + w2 / 2
        cy2 = y2 + h2 / 2
        
        # Euklidische Distanz
        distance = ((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2) ** 0.5
        
        # Normalisiere (angenommen max. Distanz = 5000px)
        max_distance = 5000.0
        normalized = min(distance / max_distance, 1.0)
        
        # Invertiere für Similarity (0 = nah, 1 = weit)
        return 1.0 - normalized

