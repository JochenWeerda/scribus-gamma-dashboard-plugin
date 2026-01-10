"""Google Cloud Vision Provider für Bild-Analyse."""

import base64
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    from google.cloud import vision
    HAS_GOOGLE_VISION = True
except ImportError:
    HAS_GOOGLE_VISION = False
    vision = None


class GoogleVisionProvider:
    """Google Cloud Vision Provider für Bild-Analyse."""
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialisiert Google Vision Provider.
        
        Args:
            credentials_path: Pfad zu Service Account JSON (optional, verwendet GOOGLE_APPLICATION_CREDENTIALS)
        """
        if not HAS_GOOGLE_VISION:
            raise RuntimeError("google-cloud-vision package nicht verfügbar. Installiere mit: pip install google-cloud-vision")
        
        credentials_path = credentials_path or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path and os.path.exists(credentials_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        
        try:
            self.client = vision.ImageAnnotatorClient()
            logger.info("Google Vision Provider initialisiert")
        except Exception as e:
            logger.warning(f"Google Vision Client konnte nicht initialisiert werden: {e}")
            self.client = None
    
    def analyze_image(
        self,
        image_path: str,
        image_data: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Analysiert Bild mit Google Cloud Vision API.
        
        Args:
            image_path: Pfad zum Bild
            image_data: Bilddaten als Bytes (optional)
        
        Returns:
            {
                "focus_center": {"x": 0.5, "y": 0.5},
                "focus_region": {...},
                "focus_type": "face" | "symbol" | "object" | "center",
                "confidence": 0.95,
                "faces": [...],  # Face Detection Results
                "labels": [...],  # Label Detection Results
            }
        """
        if not self.client:
            # Fallback
            return {
                "focus_center": {"x": 0.5, "y": 0.5},
                "focus_region": {"x": 0.25, "y": 0.25, "width": 0.5, "height": 0.5},
                "focus_type": "center",
                "confidence": 0.5,
            }
        
        try:
            # Lade Bild
            if image_data:
                image = vision.Image(content=image_data)
            else:
                with open(image_path, "rb") as f:
                    image_data = f.read()
                    image = vision.Image(content=image_data)
            
            # Face Detection
            face_response = self.client.face_detection(image=image)
            faces = face_response.face_annotations
            
            # Label Detection
            label_response = self.client.label_detection(image=image)
            labels = label_response.label_annotations
            
            # Object Detection (optional)
            object_response = self.client.object_localization(image=image)
            objects = object_response.localized_object_annotations
            
            # Bestimme Fokus
            focus_type = "center"
            confidence = 0.5
            focus_center = {"x": 0.5, "y": 0.5}
            
            if faces:
                # Verwende erstes Gesicht als Fokus
                face = faces[0]
                bounds = face.bounding_poly.vertices
                if bounds:
                    # Berechne Zentrum
                    x_coords = [v.x for v in bounds if v.x]
                    y_coords = [v.y for v in bounds if v.y]
                    if x_coords and y_coords:
                        # Normalisiert auf 0-1 (benötigt Bildgröße, vereinfacht hier)
                        focus_center = {
                            "x": sum(x_coords) / len(x_coords) / 1000.0,  # Vereinfacht
                            "y": sum(y_coords) / len(y_coords) / 1000.0,
                        }
                focus_type = "face"
                confidence = 0.9
            elif objects:
                # Verwende erstes Objekt
                obj = objects[0]
                focus_type = "object"
                confidence = obj.score if hasattr(obj, 'score') else 0.8
            elif labels:
                # Prüfe Labels für Symbole
                symbol_labels = ["symbol", "icon", "logo", "emblem"]
                for label in labels:
                    if any(s in label.description.lower() for s in symbol_labels):
                        focus_type = "symbol"
                        confidence = label.score if hasattr(label, 'score') else 0.85
                        break
            
            return {
                "focus_center": focus_center,
                "focus_region": {"x": 0.25, "y": 0.25, "width": 0.5, "height": 0.5},
                "focus_type": focus_type,
                "confidence": confidence,
                "faces": len(faces),
                "labels": [label.description for label in labels[:5]],
                "objects": [obj.name for obj in objects[:5]] if objects else [],
            }
            
        except Exception as e:
            logger.error(f"Google Vision API Fehler: {e}")
            # Fallback
            return {
                "focus_center": {"x": 0.5, "y": 0.5},
                "focus_region": {"x": 0.25, "y": 0.25, "width": 0.5, "height": 0.5},
                "focus_type": "center",
                "confidence": 0.5,
            }

