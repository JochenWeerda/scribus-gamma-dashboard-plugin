"""
Embedding-Modelle für RAG-Service

- Text-Embeddings: paraphrase-multilingual-mpnet-base-v2
- Bild-Embeddings: CLIP (clip-ViT-B-32)
- Kombinierte Embeddings für Text-Bild-Paare
"""

from typing import List, Optional, TYPE_CHECKING
import os

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


class EmbeddingModels:
    """Verwaltet Embedding-Modelle für Text und Bilder"""
    
    def __init__(self):
        """Initialisiert Embedding-Modelle.

        Hinweis: Modelle werden lazy geladen, damit der API-Start schnell bleibt und
        Model-Downloads nicht den Startup blockieren.
        """
        # Hard-coded default for our German/English technical mix.
        # Intentionally not configurable via env to keep embeddings consistent across runs.
        self._text_model_name = "paraphrase-multilingual-mpnet-base-v2"
        self._clip_model_name = os.getenv("CLIP_MODEL", "clip-ViT-B-32")
        self._text_model = None
        self._clip_model = None

    def _get_text_model(self) -> "SentenceTransformer":
        if self._text_model is None:
            from sentence_transformers import SentenceTransformer

            self._text_model = SentenceTransformer(self._text_model_name)
        return self._text_model

    def _get_clip_model(self) -> "SentenceTransformer":
        if self._clip_model is None:
            from sentence_transformers import SentenceTransformer

            self._clip_model = SentenceTransformer(self._clip_model_name)
        return self._clip_model
    
    def embed_text(self, text: str) -> List[float]:
        """
        Text-Embedding für Layout-Strukturen und Texte.
        
        Args:
            text: Text-Input
            
        Returns:
            Embedding-Vektor als Liste von Floats
        """
        return self._get_text_model().encode(text, convert_to_numpy=True).tolist()
    
    def embed_image(self, image_path: str) -> List[float]:
        """
        Bild-Embedding mit CLIP.
        
        Args:
            image_path: Pfad zum Bild
            
        Returns:
            Embedding-Vektor als Liste von Floats
        """
        try:
            from PIL import Image

            image = Image.open(image_path)
            return self._get_clip_model().encode(image, convert_to_numpy=True).tolist()
        except Exception as e:
            raise ValueError(f"Fehler beim Laden des Bildes {image_path}: {e}")
    
    def embed_text_image_pair(
        self, 
        text: str, 
        image_path: str
    ) -> List[float]:
        """
        Kombiniertes Embedding für Text-Bild-Paare.
        
        Verwendet CLIP für gemeinsamen Embedding-Space.
        
        Args:
            text: Text-Input
            image_path: Pfad zum Bild
            
        Returns:
            Kombiniertes Embedding-Vektor
        """
        # CLIP kann sowohl Text als auch Bilder encodieren
        text_emb = self._get_clip_model().encode(text, convert_to_numpy=True)
        
        try:
            from PIL import Image

            image = Image.open(image_path)
            image_emb = self._get_clip_model().encode(image, convert_to_numpy=True)
            
            # Gewichtete Kombination (50/50)
            combined = (text_emb + image_emb) / 2.0
            return combined.tolist()
        except Exception as e:
            # Fallback: Nur Text-Embedding
            return text_emb.tolist()
    
    def embed_batch_texts(self, texts: List[str]) -> List[List[float]]:
        """Batch-Embedding für mehrere Texte"""
        embeddings = self._get_text_model().encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def embed_batch_images(self, image_paths: List[str]) -> List[List[float]]:
        """Batch-Embedding für mehrere Bilder"""
        from PIL import Image

        images = [Image.open(path) for path in image_paths]
        embeddings = self._get_clip_model().encode(images, convert_to_numpy=True)
        return embeddings.tolist()

