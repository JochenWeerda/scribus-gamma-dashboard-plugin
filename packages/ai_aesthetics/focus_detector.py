"""Visueller Fokus-Detektor - Erkennt wichtige Bildbereiche (Gesichter, Symbole)."""

import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class FocusDetector:
    """
    Detektiert visuelle Fokus-Punkte in Bildern.
    
    Erkennt:
    - Gesichter
    - Religiöse Symbole
    - Zentrale Objekte
    - Wichtige Bildbereiche
    """
    
    def __init__(self, model_provider: str = "openai"):
        """
        Initialisiert Focus Detector.
        
        Args:
            model_provider: KI-Provider ("openai", "google", "local")
        """
        self.model_provider = model_provider
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialisiert KI-Modell (Stub für jetzt)."""
        # TODO: Echte KI-Integration (OpenAI Vision, Google Vision, etc.)
        logger.info(f"FocusDetector initialisiert (Provider: {self.model_provider})")
    
    def detect_focus(
        self,
        image_path: str,
        image_data: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Detektiert Fokus-Punkte in einem Bild.
        
        Args:
            image_path: Pfad zum Bild
            image_data: Bilddaten als Bytes (optional)
        
        Returns:
            {
                "focus_center": {"x": 0.5, "y": 0.5},  # Normalisiert 0-1
                "focus_region": {"x": 0.3, "y": 0.3, "width": 0.4, "height": 0.4},
                "focus_type": "face" | "symbol" | "object" | "center",
                "confidence": 0.95,
                "important_regions": [...],  # Liste von Regionen
            }
        """
        logger.debug(f"Detecting focus for image: {image_path} (Provider: {self.model_provider})")
        
        # Verwende KI-Provider wenn verfügbar
        if self.provider:
            try:
                if isinstance(self.provider, OpenAIProvider):
                    result = self.provider.analyze_image(image_path, image_data)
                elif isinstance(self.provider, GoogleVisionProvider):
                    result = self.provider.analyze_image(image_path, image_data)
                else:
                    result = None
                
                if result:
                    # Erweitere Result mit important_regions
                    result["important_regions"] = [
                        {
                            "type": result.get("focus_type", "center"),
                            "bbox": result.get("focus_region", {}),
                            "confidence": result.get("confidence", 0.8),
                        }
                    ]
                    return result
            except Exception as e:
                logger.warning(f"KI-Provider Fehler, verwende Fallback: {e}")
        
        # Fallback: Bildzentrum
        logger.debug("Using fallback focus detection (center)")
        return {
            "focus_center": {"x": 0.5, "y": 0.5},
            "focus_region": {"x": 0.25, "y": 0.25, "width": 0.5, "height": 0.5},
            "focus_type": "center",
            "confidence": 0.8,
            "important_regions": [
                {
                    "type": "center",
                    "bbox": {"x": 0.25, "y": 0.25, "width": 0.5, "height": 0.5},
                    "confidence": 0.8,
                }
            ],
        }
    
    def suggest_crop(
        self,
        image_path: str,
        target_width: int,
        target_height: int,
        current_crop: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Schlägt einen Crop vor, der den Fokus erhält.
        
        Args:
            image_path: Pfad zum Bild
            target_width: Zielbreite
            target_height: Zielhöhe
            current_crop: Aktueller Crop (optional)
        
        Returns:
            {
                "x": 100,
                "y": 150,
                "width": target_width,
                "height": target_height,
                "preserves_focus": True,
                "focus_overlap": 0.95,  # Wie viel Fokus-Bereich im Crop
            }
        """
        focus = self.detect_focus(image_path)
        focus_center = focus["focus_center"]
        
        # TODO: Intelligente Crop-Berechnung basierend auf Fokus
        # Für jetzt: Crop zentriert auf Fokus
        logger.debug(f"Suggesting crop for {image_path}: {target_width}x{target_height}")
        
        return {
            "x": 0,  # Wird von Layout-Engine berechnet
            "y": 0,
            "width": target_width,
            "height": target_height,
            "preserves_focus": True,
            "focus_overlap": 0.95,
            "focus_center": focus_center,
        }


def detect_image_focus(image_path: str, image_data: Optional[bytes] = None) -> Dict[str, Any]:
    """
    Convenience-Funktion für Fokus-Detektion.
    
    Args:
        image_path: Pfad zum Bild
        image_data: Bilddaten als Bytes (optional)
    
    Returns:
        Fokus-Daten (siehe FocusDetector.detect_focus)
    """
    detector = FocusDetector()
    return detector.detect_focus(image_path, image_data)

