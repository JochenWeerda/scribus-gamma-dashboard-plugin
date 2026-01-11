"""
LLM Context Builder für RAG-Service

Erstellt erweiterten Kontext für LLM-Prompts mit ähnlichen Layouts,
relevanten Texten, passenden Bildern und Text-Bild-Vorschlägen.
"""

from typing import Dict, List, Optional
from .database import RAGDatabase
from .embeddings import EmbeddingModels
from .retriever import LayoutRetriever
from .matcher import TextImageMatcher
import json


class LLMContextBuilder:
    """Erstellt erweiterten Kontext für LLM-Prompts"""
    
    def __init__(
        self,
        db: RAGDatabase,
        embeddings: EmbeddingModels,
        retriever: LayoutRetriever,
        matcher: TextImageMatcher
    ):
        """
        Initialisiert LLM Context Builder.
        
        Args:
            db: RAGDatabase Instanz
            embeddings: EmbeddingModels Instanz
            retriever: LayoutRetriever Instanz
            matcher: TextImageMatcher Instanz
        """
        self.db = db
        self.embeddings = embeddings
        self.retriever = retriever
        self.matcher = matcher
    
    def build_context_for_prompt(
        self,
        user_prompt: str,
        top_k_layouts: int = 3,
        top_k_texts: int = 5,
        top_k_images: int = 3
    ) -> Dict:
        """
        Erstellt erweiterten Kontext für LLM-Prompt.
        
        Args:
            user_prompt: User-Prompt
            top_k_layouts: Anzahl ähnlicher Layouts
            top_k_texts: Anzahl relevanter Texte
            top_k_images: Anzahl passender Bilder
            
        Returns:
            Dict mit "context" (Text) und "sources" (Liste von Quellen)
        """
        context_parts = [f"User Prompt: {user_prompt}\n"]
        sources = []
        
        # 1. Ähnliche Layouts finden
        similar_layouts = self.retriever.find_similar_layouts(
            user_prompt,
            top_k=top_k_layouts,
            include_content=True
        )
        
        if similar_layouts:
            context_parts.append("\nSimilar Layouts:")
            for i, layout in enumerate(similar_layouts, 1):
                source = layout.get("source", "unknown")
                layout_id = layout.get("layout_id", "")
                similarity = layout.get("similarity", 0.0)
                
                context_parts.append(f"\n{i}. Layout from {source} (ID: {layout_id[:8]}..., similarity: {similarity:.2f}):")
                
                # Struktur-Info
                doc = layout.get("document", "")
                if doc:
                    context_parts.append(f"   - Structure: {doc[:200]}...")
                
                # Layout JSON Details
                layout_json = layout.get("layout_json")
                if layout_json:
                    pages = layout_json.get("pages", [])
                    if pages:
                        page = pages[0]
                        objects = page.get("objects", [])
                        
                        texts = [obj for obj in objects if obj.get("type") == "text"]
                        images = [obj for obj in objects if obj.get("type") == "image"]
                        
                        if texts:
                            key_texts = [obj.get("content", "")[:50] for obj in texts[:3]]
                            context_parts.append(f"   - Key Texts: {', '.join(key_texts)}")
                        
                        if images:
                            key_images = []
                            for img in images[:3]:
                                media_id = img.get("mediaId", "")
                                alt_text = img.get("metadata", {}).get("altText", "")
                                if alt_text:
                                    key_images.append(f"{alt_text} ({media_id})")
                                else:
                                    key_images.append(media_id)
                            context_parts.append(f"   - Key Images: {', '.join(key_images)}")
                
                sources.append({
                    "type": "layout",
                    "source": source,
                    "layout_id": layout_id,
                    "similarity": similarity,
                })
        
        # 2. Relevante gescannte Texte
        relevant_texts = self.retriever.find_layouts_by_text(user_prompt, top_k=top_k_texts)
        
        if relevant_texts:
            context_parts.append("\n\nRelevant Scanned Content:")
            
            # Hole Text-Details
            text_ids = []
            for layout_info in relevant_texts[:top_k_texts]:
                layout_id = layout_info.get("layout_id")
                # Finde Texte für dieses Layout
                try:
                    results = self.db.texts_collection.get(
                        where={"layout_id": layout_id},
                        include=["documents", "metadatas"]
                    )
                    for doc, meta in zip(results.get("documents", []), results.get("metadatas", [])):
                        source = meta.get("source", "")
                        context_parts.append(f"   - Text from {source}: {doc[:100]}...")
                        sources.append({
                            "type": "text",
                            "source": source,
                            "content_preview": doc[:100],
                        })
                except:
                    pass
        
        # 3. Passende Bilder
        # Versuche Bilder aus dem Prompt zu extrahieren oder verwende allgemeine Suche
        matching_images = []
        try:
            # Suche nach Bildern, die zum Prompt passen könnten
            # (vereinfacht: verwende ersten relevanten Text für Bild-Suche)
            if relevant_texts:
                # Hole ein Beispiel-Text für Bild-Suche
                try:
                    example_results = self.db.texts_collection.get(
                        limit=1,
                        include=["documents"]
                    )
                    if example_results.get("documents"):
                        example_text = example_results["documents"][0]
                        matching_images = self.matcher.find_images_for_text(example_text, top_k=top_k_images)
                except:
                    pass
        except:
            pass
        
        if matching_images:
            context_parts.append("\n\nSuggested Images:")
            for img in matching_images[:top_k_images]:
                path = img.get("path", "")
                similarity = img.get("similarity", 0.0)
                doc = img.get("document", "")
                context_parts.append(f"   - {path} (similarity: {similarity:.2f}): {doc}")
                sources.append({
                    "type": "image",
                    "path": path,
                    "similarity": similarity,
                })
        
        # 4. Text-Bild-Vorschläge (wenn Layout vorhanden)
        # Für jetzt: Allgemeine Vorschläge basierend auf Prompt
        
        # Zusammenfügen
        context_text = "\n".join(context_parts)
        
        return {
            "context": context_text,
            "sources": sources,
            "stats": {
                "similar_layouts": len(similar_layouts),
                "relevant_texts": len(relevant_texts),
                "matching_images": len(matching_images),
            }
        }

