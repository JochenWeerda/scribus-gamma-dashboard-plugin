"""OpenAI Provider für Bild- und Text-Analyse."""

import base64
import logging
import os
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    OpenAI = None


class OpenAIProvider:
    """OpenAI Provider für Vision API und GPT-4."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        Initialisiert OpenAI Provider.
        
        Args:
            api_key: OpenAI API Key (optional, wird aus OPENAI_API_KEY gelesen)
            model: Model-Name (default: "gpt-4o" für Vision + Text)
        """
        if not HAS_OPENAI:
            raise RuntimeError("openai package nicht verfügbar. Installiere mit: pip install openai")
        
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API Key nicht gefunden. Setze OPENAI_API_KEY Environment-Variable.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        logger.info(f"OpenAI Provider initialisiert (Model: {model})")
    
    def analyze_image(
        self,
        image_path: str,
        image_data: Optional[bytes] = None,
        prompt: str = "Analyze this image and identify the most important visual elements. Focus on faces, symbols, and central objects."
    ) -> Dict[str, Any]:
        """
        Analysiert Bild mit OpenAI Vision API.
        
        Args:
            image_path: Pfad zum Bild
            image_data: Bilddaten als Bytes (optional)
            prompt: Prompt für Analyse
        
        Returns:
            {
                "focus_center": {"x": 0.5, "y": 0.5},
                "focus_region": {"x": 0.25, "y": 0.25, "width": 0.5, "height": 0.5},
                "focus_type": "face" | "symbol" | "object" | "center",
                "confidence": 0.95,
                "description": "...",
            }
        """
        try:
            # Lade Bild
            if image_data:
                image_base64 = base64.b64encode(image_data).decode('utf-8')
            else:
                with open(image_path, "rb") as f:
                    image_data = f.read()
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Bestimme MIME-Type
            mime_type = "image/jpeg"
            if image_path.lower().endswith(".png"):
                mime_type = "image/png"
            elif image_path.lower().endswith(".webp"):
                mime_type = "image/webp"
            
            # OpenAI Vision API Call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            # Parse Response
            description = response.choices[0].message.content
            
            # Extrahiere Fokus-Informationen (vereinfacht)
            # In einer echten Implementation würde man strukturierte JSON-Responses verwenden
            focus_type = "center"
            confidence = 0.8
            
            if "face" in description.lower() or "portrait" in description.lower():
                focus_type = "face"
                confidence = 0.9
            elif "symbol" in description.lower() or "icon" in description.lower():
                focus_type = "symbol"
                confidence = 0.85
            elif "object" in description.lower() or "center" in description.lower():
                focus_type = "object"
                confidence = 0.8
            
            # Für jetzt: Zentrierter Fokus (echte Implementation würde Bounding Boxes analysieren)
            return {
                "focus_center": {"x": 0.5, "y": 0.5},
                "focus_region": {"x": 0.25, "y": 0.25, "width": 0.5, "height": 0.5},
                "focus_type": focus_type,
                "confidence": confidence,
                "description": description,
            }
            
        except Exception as e:
            logger.error(f"OpenAI Vision API Fehler: {e}")
            # Fallback
            return {
                "focus_center": {"x": 0.5, "y": 0.5},
                "focus_region": {"x": 0.25, "y": 0.25, "width": 0.5, "height": 0.5},
                "focus_type": "center",
                "confidence": 0.5,
                "description": f"Error: {str(e)}",
            }
    
    def analyze_text(
        self,
        text: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analysiert Text mit GPT-4.
        
        Args:
            text: Textinhalt
            system_prompt: System-Prompt (optional)
        
        Returns:
            {
                "keywords": [...],
                "entities": [...],
                "sentiment": "positive" | "neutral" | "negative",
                "topics": [...],
                "summary": "...",
            }
        """
        try:
            system = system_prompt or """Du bist ein Experte für Text-Analyse. 
Analysiere den Text und extrahiere:
1. Wichtige Keywords
2. Named Entities (Personen, Orte, Konzepte)
3. Sentiment (positive/neutral/negative)
4. Themen/Topics
5. Kurze Zusammenfassung

Antworte im JSON-Format."""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"},
                max_tokens=500
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            return {
                "keywords": result.get("keywords", []),
                "entities": result.get("entities", []),
                "sentiment": result.get("sentiment", "neutral"),
                "topics": result.get("topics", []),
                "summary": result.get("summary", ""),
            }
            
        except Exception as e:
            logger.error(f"OpenAI Text-Analyse Fehler: {e}")
            # Fallback
            return {
                "keywords": [],
                "entities": [],
                "sentiment": "neutral",
                "topics": ["general"],
                "summary": f"Error: {str(e)}",
            }

