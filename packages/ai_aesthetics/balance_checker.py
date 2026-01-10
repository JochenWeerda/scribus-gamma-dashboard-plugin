"""Balance-Checker - KI als "Art Director" für ästhetische Korrekturen."""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class BalanceChecker:
    """
    Prüft Layout-Balance und schlägt ästhetische Korrekturen vor.
    
    Fungiert als "Art Director" für mathematische Präzision + Ästhetik.
    """
    
    def __init__(self, model_provider: str = "openai"):
        """
        Initialisiert Balance Checker.
        
        Args:
            model_provider: KI-Provider ("openai", "google", "local")
        """
        self.model_provider = model_provider
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialisiert KI-Modell (Stub für jetzt)."""
        # TODO: Echte KI-Integration
        logger.info(f"BalanceChecker initialisiert (Provider: {self.model_provider})")
    
    def check_layout_balance(
        self,
        layout_data: Dict[str, Any],
        page_number: int = 1
    ) -> Dict[str, Any]:
        """
        Prüft Layout-Balance einer Seite.
        
        Args:
            layout_data: Layout-Daten (Seite mit Elementen)
            page_number: Seitennummer
        
        Returns:
            {
                "balanced": True | False,
                "score": 0.85,  # Balance-Score 0-1
                "issues": [
                    {
                        "type": "visual_weight" | "spacing" | "alignment" | "contrast",
                        "severity": "low" | "medium" | "high",
                        "element_id": "img_1",
                        "description": "Bild zu nah am Rand",
                        "suggestion": {"x": 120, "y": 140, ...},
                    }
                ],
                "suggestions": [
                    {
                        "action": "adjust_position" | "adjust_size" | "adjust_spacing",
                        "element_id": "img_1",
                        "changes": {...},
                        "reasoning": "Verbessert visuelle Balance",
                    }
                ],
            }
        """
        elements = layout_data.get("elements", [])
        
        # Einfache Balance-Checks (Fallback)
        issues = []
        suggestions = []
        
        # Prüfe Spacing
        for element in elements:
            box = element.get("box", {})
            x = box.get("x_px", 0)
            y = box.get("y_px", 0)
            
            # Zu nah am Rand?
            margin_threshold = 50
            if x < margin_threshold or y < margin_threshold:
                issues.append({
                    "type": "spacing",
                    "severity": "medium",
                    "element_id": element.get("id", "unknown"),
                    "description": f"Element zu nah am Rand (x={x}, y={y})",
                    "suggestion": {
                        "x_px": max(margin_threshold, x),
                        "y_px": max(margin_threshold, y),
                    },
                })
                suggestions.append({
                    "action": "adjust_position",
                    "element_id": element.get("id", "unknown"),
                    "changes": {
                        "x_px": max(margin_threshold, x),
                        "y_px": max(margin_threshold, y),
                    },
                    "reasoning": "Verbessert Spacing zum Seitenrand",
                })
        
        # Balance-Score (vereinfacht)
        score = 1.0 - (len(issues) * 0.1)
        score = max(0.0, min(1.0, score))
        
        balanced = score >= 0.7
        
        logger.debug(f"Layout balance check: score={score:.2f}, issues={len(issues)}")
        
        return {
            "balanced": balanced,
            "score": score,
            "issues": issues,
            "suggestions": suggestions,
        }
    
    def suggest_aesthetic_corrections(
        self,
        layout_data: Dict[str, Any],
        mathematical_precision: bool = True
    ) -> Dict[str, Any]:
        """
        Schlägt ästhetische Korrekturen vor (bei mathematischen Grenzfällen).
        
        Args:
            layout_data: Layout-Daten
            mathematical_precision: Soll mathematische Präzision erhalten bleiben?
        
        Returns:
            {
                "corrections": [
                    {
                        "element_id": "img_1",
                        "type": "micro_adjustment",
                        "changes": {"x_px": 101, "y_px": 203},  # Kleine Anpassung
                        "reasoning": "Verbessert visuelle Balance bei minimalem Impact",
                    }
                ],
                "preserves_precision": True,
            }
        """
        balance = self.check_layout_balance(layout_data)
        
        # Filtere nur kleine Korrekturen (wenn Precision erhalten bleiben soll)
        corrections = []
        if mathematical_precision:
            for suggestion in balance.get("suggestions", []):
                changes = suggestion.get("changes", {})
                # Nur kleine Änderungen (< 10px)
                if all(abs(v) < 10 for v in changes.values() if isinstance(v, (int, float))):
                    corrections.append({
                        "element_id": suggestion.get("element_id"),
                        "type": "micro_adjustment",
                        "changes": changes,
                        "reasoning": suggestion.get("reasoning", "Ästhetische Verbesserung"),
                    })
        else:
            corrections = balance.get("suggestions", [])
        
        logger.debug(f"Suggested {len(corrections)} aesthetic corrections")
        
        return {
            "corrections": corrections,
            "preserves_precision": mathematical_precision,
        }


def check_layout_balance(
    layout_data: Dict[str, Any],
    page_number: int = 1
) -> Dict[str, Any]:
    """
    Convenience-Funktion für Balance-Check.
    
    Args:
        layout_data: Layout-Daten
        page_number: Seitennummer
    
    Returns:
        Balance-Ergebnis (siehe BalanceChecker.check_layout_balance)
    """
    checker = BalanceChecker()
    return checker.check_layout_balance(layout_data, page_number)

