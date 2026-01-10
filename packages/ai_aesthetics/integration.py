"""Integration von AI-Enhanced Aesthetics in Layout-Pipeline."""

import logging
from typing import Dict, Any, List, Optional

from .focus_detector import FocusDetector
from .contextual_placer import ContextualPlacer
from .balance_checker import BalanceChecker

logger = logging.getLogger(__name__)


class AIAestheticsEngine:
    """
    Haupt-Engine für AI-Enhanced Aesthetics.
    
    Kombiniert Fokus-Detektion, kontextuelle Platzierung und Balance-Checks.
    """
    
    def __init__(
        self,
        enabled: bool = True,
        focus_provider: str = "openai",
        text_provider: str = "openai",
        api_key: Optional[str] = None
    ):
        """
        Initialisiert AI Aesthetics Engine.
        
        Args:
            enabled: Aktiviert KI-Features (default: True)
            focus_provider: Provider für Fokus-Detektion ("openai", "google", "fallback")
            text_provider: Provider für Text-Analyse ("openai", "fallback")
            api_key: API Key (optional, wird aus Environment gelesen)
        """
        self.enabled = enabled
        self.api_key = api_key
        
        if enabled:
            self.focus_detector = FocusDetector(model_provider=focus_provider, api_key=api_key)
            self.contextual_placer = ContextualPlacer(model_provider=text_provider, api_key=api_key)
            self.balance_checker = BalanceChecker()
        else:
            self.focus_detector = None
            self.contextual_placer = None
            self.balance_checker = None
        
        logger.info(f"AIAestheticsEngine initialisiert (enabled={enabled}, focus={focus_provider}, text={text_provider})")
    
    def optimize_layout(
        self,
        layout_json: Dict[str, Any],
        apply_corrections: bool = False
    ) -> Dict[str, Any]:
        """
        Optimiert Layout mit KI-Enhanced Aesthetics.
        
        Args:
            layout_json: Layout-JSON
            apply_corrections: Sollen Korrekturen automatisch angewendet werden?
        
        Returns:
            {
                "optimized_layout": {...},  # Wenn apply_corrections=True
                "optimizations": [
                    {
                        "type": "focus_adjustment" | "contextual_placement" | "balance_correction",
                        "element_id": "img_1",
                        "changes": {...},
                        "reasoning": "...",
                    }
                ],
                "summary": {
                    "focus_adjustments": 2,
                    "contextual_placements": 1,
                    "balance_corrections": 3,
                },
            }
        """
        if not self.enabled:
            return {
                "optimized_layout": layout_json,
                "optimizations": [],
                "summary": {},
            }
        
        optimizations = []
        pages = layout_json.get("pages", [])
        
        for page_data in pages:
            page_number = page_data.get("pageNumber", 1)
            elements = page_data.get("elements", [])
            text_blocks = [e for e in elements if e.get("type") == "text"]
            image_elements = [e for e in elements if e.get("type") == "image"]
            
            # 1. Fokus-Detektion für Bilder
            for img_element in image_elements:
                image_path = img_element.get("asset", {}).get("uri", "")
                if image_path and self.focus_detector:
                    focus = self.focus_detector.detect_focus(image_path)
                    crop_suggestion = self.focus_detector.suggest_crop(
                        image_path,
                        img_element.get("box", {}).get("w_px", 0),
                        img_element.get("box", {}).get("h_px", 0)
                    )
                    
                    if crop_suggestion.get("preserves_focus"):
                        optimizations.append({
                            "type": "focus_adjustment",
                            "element_id": img_element.get("id"),
                            "changes": {"crop": crop_suggestion},
                            "reasoning": f"Fokus erhalten (Type: {focus.get('focus_type')})",
                        })
            
            # 2. Kontextuelle Platzierung
            if self.contextual_placer and text_blocks and image_elements:
                for img_element in image_elements:
                    image_metadata = {
                        "keywords": img_element.get("metadata", {}).get("keywords", []),
                        "type": img_element.get("metadata", {}).get("type", "image"),
                    }
                    available_positions = [img_element.get("box", {})]
                    
                    placement = self.contextual_placer.suggest_image_placement(
                        text_blocks,
                        image_metadata,
                        available_positions
                    )
                    
                    if placement.get("relevance_score", 0) > 0.7:
                        optimizations.append({
                            "type": "contextual_placement",
                            "element_id": img_element.get("id"),
                            "changes": {"position": placement.get("recommended_position")},
                            "reasoning": placement.get("reasoning", "Kontextuelle Platzierung"),
                        })
            
            # 3. Balance-Checks
            if self.balance_checker:
                balance_result = self.balance_checker.check_layout_balance(page_data, page_number)
                
                for suggestion in balance_result.get("suggestions", []):
                    optimizations.append({
                        "type": "balance_correction",
                        "element_id": suggestion.get("element_id"),
                        "changes": suggestion.get("changes", {}),
                        "reasoning": suggestion.get("reasoning", "Balance-Verbesserung"),
                    })
        
        # Wende Korrekturen an (wenn gewünscht)
        optimized_layout = layout_json
        if apply_corrections:
            optimized_layout = self._apply_optimizations(layout_json, optimizations)
        
        # Zusammenfassung
        summary = {
            "focus_adjustments": len([o for o in optimizations if o["type"] == "focus_adjustment"]),
            "contextual_placements": len([o for o in optimizations if o["type"] == "contextual_placement"]),
            "balance_corrections": len([o for o in optimizations if o["type"] == "balance_correction"]),
        }
        
        logger.info(f"Layout optimization: {summary}")
        
        return {
            "optimized_layout": optimized_layout,
            "optimizations": optimizations,
            "summary": summary,
        }
    
    def _apply_optimizations(
        self,
        layout_json: Dict[str, Any],
        optimizations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Wendet Optimierungen auf Layout an."""
        # Deep copy
        import json
        optimized = json.loads(json.dumps(layout_json))
        
        # Erstelle Lookup für Elemente
        element_map = {}
        for page in optimized.get("pages", []):
            for element in page.get("elements", []):
                element_map[element.get("id")] = element
        
        # Wende Optimierungen an
        for opt in optimizations:
            element_id = opt.get("element_id")
            changes = opt.get("changes", {})
            
            if element_id in element_map:
                element = element_map[element_id]
                # Merge changes
                if "crop" in changes:
                    element.setdefault("crop", {}).update(changes["crop"])
                if "position" in changes:
                    element.setdefault("box", {}).update(changes["position"])
                if "x_px" in changes or "y_px" in changes:
                    box = element.setdefault("box", {})
                    box.update({k: v for k, v in changes.items() if k in ["x_px", "y_px", "w_px", "h_px"]})
        
        return optimized


def get_ai_aesthetics_engine(
    enabled: Optional[bool] = None,
    focus_provider: Optional[str] = None,
    text_provider: Optional[str] = None,
    api_key: Optional[str] = None
) -> AIAestheticsEngine:
    """
    Erstellt AIAestheticsEngine aus Umgebungsvariablen.
    
    Args:
        enabled: Aktiviert KI-Features (default: aus AI_AESTHETICS_ENABLED)
        focus_provider: Provider für Fokus-Detektion (default: aus AI_FOCUS_PROVIDER oder "openai")
        text_provider: Provider für Text-Analyse (default: aus AI_TEXT_PROVIDER oder "openai")
        api_key: API Key (default: aus OPENAI_API_KEY)
    
    Environment Variables:
        AI_AESTHETICS_ENABLED: 'true' zum Aktivieren (default: 'true')
        AI_FOCUS_PROVIDER: 'openai', 'google', 'fallback' (default: 'openai')
        AI_TEXT_PROVIDER: 'openai', 'fallback' (default: 'openai')
        OPENAI_API_KEY: OpenAI API Key
        GOOGLE_APPLICATION_CREDENTIALS: Pfad zu Google Service Account JSON
    """
    import os
    
    enabled = enabled if enabled is not None else os.environ.get("AI_AESTHETICS_ENABLED", "true").lower() == "true"
    focus_provider = focus_provider or os.environ.get("AI_FOCUS_PROVIDER", "openai")
    text_provider = text_provider or os.environ.get("AI_TEXT_PROVIDER", "openai")
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    
    return AIAestheticsEngine(
        enabled=enabled,
        focus_provider=focus_provider,
        text_provider=text_provider,
        api_key=api_key
    )

