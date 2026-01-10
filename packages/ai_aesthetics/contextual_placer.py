"""Kontextuelle Platzierung - KI-gestützte Bild-Platzierung basierend auf Textinhalt."""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ContextualPlacer:
    """
    Plaziert Bilder basierend auf Textinhalt.
    
    Analysiert Text und schlägt vor, wo Bilder inhaltlich hingehören.
    """
    
    def __init__(self, model_provider: str = "openai"):
        """
        Initialisiert Contextual Placer.
        
        Args:
            model_provider: KI-Provider ("openai", "google", "local")
        """
        self.model_provider = model_provider
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialisiert KI-Modell (Stub für jetzt)."""
        # TODO: Echte KI-Integration (OpenAI, Google, etc.)
        logger.info(f"ContextualPlacer initialisiert (Provider: {self.model_provider})")
    
    def analyze_text_context(
        self,
        text: str
    ) -> Dict[str, Any]:
        """
        Analysiert Text und extrahiert Kontext für Bild-Platzierung.
        
        Args:
            text: Textinhalt
        
        Returns:
            {
                "keywords": ["religion", "symbol", "face", ...],
                "entities": [...],  # Named Entities
                "sentiment": "positive" | "neutral" | "negative",
                "topics": ["religion", "art", "history", ...],
                "image_suggestions": [
                    {
                        "position": "top" | "center" | "bottom" | "inline",
                        "relevance": 0.95,
                        "keywords": ["face", "portrait"],
                    }
                ],
            }
        """
        logger.debug(f"Analyzing text context: {len(text)} chars (Provider: {self.model_provider})")
        
        # Verwende KI-Provider wenn verfügbar
        if self.provider and isinstance(self.provider, OpenAIProvider):
            try:
                result = self.provider.analyze_text(text)
                # Erweitere Result mit image_suggestions
                keywords = result.get("keywords", [])
                result["image_suggestions"] = [
                    {
                        "position": "inline" if keywords else "center",
                        "relevance": 0.8 if keywords else 0.5,
                        "keywords": keywords[:5],  # Top 5 Keywords
                    }
                ]
                return result
            except Exception as e:
                logger.warning(f"KI-Provider Fehler, verwende Fallback: {e}")
        
        # Fallback: Einfache Keyword-Erkennung
        keywords = []
        text_lower = text.lower()
        if "gesicht" in text_lower or "face" in text_lower or "portrait" in text_lower:
            keywords.append("face")
        if "symbol" in text_lower or "kreuz" in text_lower or "icon" in text_lower:
            keywords.append("symbol")
        if "religion" in text_lower or "gott" in text_lower or "religious" in text_lower:
            keywords.append("religion")
        if "art" in text_lower or "kunst" in text_lower:
            keywords.append("art")
        if "history" in text_lower or "geschichte" in text_lower:
            keywords.append("history")
        
        return {
            "keywords": keywords,
            "entities": [],
            "sentiment": "neutral",
            "topics": keywords if keywords else ["general"],
            "image_suggestions": [
                {
                    "position": "inline" if keywords else "center",
                    "relevance": 0.8 if keywords else 0.5,
                    "keywords": keywords,
                }
            ],
        }
    
    def suggest_image_placement(
        self,
        text_blocks: List[Dict[str, Any]],
        image_metadata: Dict[str, Any],
        available_positions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Schlägt Bild-Platzierung basierend auf Textkontext vor.
        
        Args:
            text_blocks: Liste von Text-Blöcken mit Inhalt und Position
            image_metadata: Bild-Metadaten (Keywords, Typ, etc.)
            available_positions: Verfügbare Platzierungs-Positionen
        
        Returns:
            {
                "recommended_position": {"x": 100, "y": 200, ...},
                "relevance_score": 0.95,
                "reasoning": "Bild zeigt Gesicht, Text erwähnt Person",
                "alternative_positions": [...],
            }
        """
        # Analysiere Text-Kontext
        all_text = " ".join([block.get("content", "") for block in text_blocks])
        context = self.analyze_text_context(all_text)
        
        # Match Bild-Keywords mit Text-Kontext
        image_keywords = image_metadata.get("keywords", [])
        text_keywords = context.get("keywords", [])
        
        relevance = 0.0
        if image_keywords and text_keywords:
            # Berechne Keyword-Overlap
            overlap = len(set(image_keywords) & set(text_keywords))
            relevance = min(1.0, overlap / max(len(image_keywords), len(text_keywords), 1))
        
        # Finde beste Position (für jetzt: erste verfügbare)
        recommended_position = available_positions[0] if available_positions else {}
        
        logger.debug(f"Suggesting image placement: relevance={relevance:.2f}")
        
        return {
            "recommended_position": recommended_position,
            "relevance_score": relevance,
            "reasoning": f"Bild-Keywords: {image_keywords}, Text-Keywords: {text_keywords}",
            "alternative_positions": available_positions[1:3] if len(available_positions) > 1 else [],
        }


def suggest_image_placement(
    text_blocks: List[Dict[str, Any]],
    image_metadata: Dict[str, Any],
    available_positions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Convenience-Funktion für kontextuelle Bild-Platzierung.
    
    Args:
        text_blocks: Liste von Text-Blöcken
        image_metadata: Bild-Metadaten
        available_positions: Verfügbare Positionen
    
    Returns:
        Platzierungs-Empfehlung (siehe ContextualPlacer.suggest_image_placement)
    """
    placer = ContextualPlacer()
    return placer.suggest_image_placement(text_blocks, image_metadata, available_positions)

