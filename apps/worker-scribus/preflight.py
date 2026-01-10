"""Preflight-Check für Scribus-Dokumente."""

import json
from typing import Dict, List, Any


class PreflightReport:
    """Preflight-Report mit Warnings und Errors."""
    
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
    
    def add_error(self, category: str, message: str, details: Dict[str, Any] = None):
        """Fügt einen Error hinzu."""
        self.errors.append({
            "category": category,
            "message": message,
            "details": details or {},
        })
    
    def add_warning(self, category: str, message: str, details: Dict[str, Any] = None):
        """Fügt eine Warning hinzu."""
        self.warnings.append({
            "category": category,
            "message": message,
            "details": details or {},
        })
    
    def is_valid(self) -> bool:
        """Gibt zurück, ob der Report keine Errors enthält."""
        return len(self.errors) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Report zu Dict."""
        return {
            "valid": self.is_valid(),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
        }
    
    def to_json(self) -> str:
        """Konvertiert Report zu JSON."""
        return json.dumps(self.to_dict(), indent=2)


def check_missing_fonts(scribus_doc) -> List[str]:
    """
    Prüft auf fehlende Fonts.
    
    Returns:
        Liste von fehlenden Font-Namen
    """
    try:
        import scribus
        missing_fonts = []
        
        # Alle Objekte durchgehen
        all_objects = scribus.getAllObjects()
        for obj_name in all_objects:
            try:
                font = scribus.getFont(obj_name)
                # Prüfe, ob Font verfügbar ist
                if font and font not in scribus.getFontNames():
                    if font not in missing_fonts:
                        missing_fonts.append(font)
            except Exception:
                pass
        
        return missing_fonts
    except Exception:
        return []


def check_missing_images(scribus_doc) -> List[Dict[str, Any]]:
    """
    Prüft auf fehlende Bilder/Links.
    
    Returns:
        Liste von fehlenden Bild-Informationen
    """
    try:
        import scribus
        missing_images = []
        
        all_objects = scribus.getAllObjects()
        for obj_name in all_objects:
            try:
                obj_type = scribus.getObjectType(obj_name)
                if obj_type == "ImageFrame":
                    image_file = scribus.getImageFile(obj_name)
                    if not image_file or not os.path.exists(image_file):
                        missing_images.append({
                            "object_name": obj_name,
                            "image_file": image_file,
                        })
            except Exception:
                pass
        
        return missing_images
    except Exception:
        return []


def run_preflight(sla_path: str) -> PreflightReport:
    """
    Führt Preflight-Check durch.
    
    Args:
        sla_path: Pfad zur SLA-Datei
    
    Returns:
        PreflightReport
    """
    report = PreflightReport()
    
    try:
        import scribus
        
        # Dokument laden (falls nicht bereits geladen)
        if not scribus.haveDoc():
            scribus.openDoc(sla_path)
        
        # Missing Fonts prüfen
        missing_fonts = check_missing_fonts(None)
        if missing_fonts:
            for font in missing_fonts:
                report.add_error(
                    "missing_font",
                    f"Font '{font}' nicht gefunden",
                    {"font_name": font}
                )
        
        # Missing Images prüfen
        missing_images = check_missing_images(None)
        if missing_images:
            for img_info in missing_images:
                report.add_error(
                    "missing_image",
                    f"Bild nicht gefunden: {img_info.get('image_file', 'unknown')}",
                    img_info
                )
        
        # Text-Overflow prüfen (vereinfacht)
        # TODO: Echte Overflow-Prüfung via Scribus-API
        
    except Exception as e:
        report.add_error("preflight_error", f"Fehler beim Preflight: {str(e)}")
    
    return report

