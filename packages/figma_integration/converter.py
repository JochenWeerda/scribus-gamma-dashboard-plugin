"""
Figma Frame ↔ Layout JSON Converter

Konvertiert zwischen Figma Frame JSON und Layout JSON Schema.
"""

from typing import Dict, List, Any, Optional
import json


class FrameToLayoutConverter:
    """
    Konvertiert Figma Frame → Layout JSON Schema.
    
    MUSS exakt dasselbe Schema erzeugen wie der Compiler erwartet!
    """
    
    def convert(
        self,
        frame_json: Dict,
        dpi: int = 300,
        page_number: int = 1
    ) -> Dict:
        """
        Konvertiert Figma Frame zu Layout JSON Schema.
        
        Args:
            frame_json: Figma Frame JSON (von get_frame)
            dpi: DPI für Dokument (default: 300)
            page_number: Seitenzahl (default: 1)
            
        Returns:
            Layout JSON Schema (Compiler-Input)
        """
        # Extrahiere Frame-Dimensionen
        bbox = frame_json.get("absoluteBoundingBox", {})
        width = bbox.get("width", 2480)
        height = bbox.get("height", 3508)
        
        # Erstelle Layout JSON Schema
        layout = {
            "version": "1.0.0",
            "document": {
                "width": int(width),
                "height": int(height),
                "dpi": dpi,
            },
            "pages": [{
                "pageNumber": page_number,
                "objects": [],
                "scannedContent": {
                    "texts": [],
                    "images": [],
                }
            }]
        }
        
        # Konvertiere Children zu Objects
        children = frame_json.get("children", [])
        objects = []
        z_order = 0
        
        for child in children:
            obj = self._convert_node_to_object(child, z_order)
            if obj:
                objects.append(obj)
                z_order += 1
        
        layout["pages"][0]["objects"] = objects
        
        return layout
    
    def _convert_node_to_object(
        self,
        node: Dict,
        z_order: int
    ) -> Optional[Dict]:
        """
        Konvertiert einen Figma Node zu Layout JSON Object.
        
        Args:
            node: Figma Node
            z_order: Z-Order für Layer
            
        Returns:
            Layout JSON Object oder None (falls nicht unterstützt)
        """
        node_type = node.get("type", "")
        bbox = node.get("absoluteBoundingBox", {})
        
        if not bbox:
            return None
        
        obj = {
            "id": node.get("id", "").replace(":", "_"),  # Ersetze : durch _ für IDs
            "bbox": {
                "x": int(bbox.get("x", 0)),
                "y": int(bbox.get("y", 0)),
                "w": int(bbox.get("width", 0)),
                "h": int(bbox.get("height", 0)),
            },
            "layer": self._determine_layer(node_type),
            "zOrder": z_order,
        }
        
        # Text-Objekt
        if node_type == "TEXT":
            obj["type"] = "text"
            obj["content"] = node.get("characters", "")
            
            # Font-Styling
            style = node.get("style", {})
            if style:
                obj["fontFamily"] = style.get("fontFamily", "Arial")
                obj["fontSize"] = style.get("fontSize", 12)
                obj["fontWeight"] = style.get("fontWeight", 400)
            
            # Text-Bild-Zuordnungen (später aus Metadaten)
            obj["relatedImageIds"] = []
        
        # Image-Objekt
        elif node_type == "VECTOR" or node_type == "RECTANGLE" or node_type == "ELLIPSE":
            # Prüfe ob es ein Image ist (hat fills mit image)
            fills = node.get("fills", [])
            is_image = any(
                fill.get("type") == "IMAGE" 
                for fill in fills
            )
            
            if is_image:
                obj["type"] = "image"
                # Image-URL wird später von get_frame_images geholt
                obj["mediaId"] = ""  # Wird später gesetzt
                obj["metadata"] = {
                    "altText": node.get("name", ""),
                    "description": "",
                }
                obj["relatedTextIds"] = []
            else:
                # Shape ohne Image → Rectangle
                obj["type"] = "rectangle"
                fills = node.get("fills", [])
                if fills:
                    fill = fills[0]
                    if fill.get("type") == "SOLID":
                        color = fill.get("color", {})
                        obj["fillColor"] = self._color_to_hex(color)
        
        # Frame/Group → Rekursiv durchlaufen (für verschachtelte Strukturen)
        elif node_type == "FRAME" or node_type == "GROUP":
            # Frame/Group selbst nicht als Object, aber Children
            children = node.get("children", [])
            # Children werden separat verarbeitet
            return None
        
        else:
            # Nicht unterstützter Typ
            return None
        
        return obj
    
    def _determine_layer(self, node_type: str) -> str:
        """Bestimmt Layer basierend auf Node-Typ"""
        if node_type == "TEXT":
            return "Text"
        elif node_type in ["VECTOR", "RECTANGLE", "ELLIPSE"]:
            return "Images"
        else:
            return "Background"
    
    def _color_to_hex(self, color: Dict) -> str:
        """Konvertiert Figma Color (0-1) zu Hex"""
        r = int(color.get("r", 0) * 255)
        g = int(color.get("g", 0) * 255)
        b = int(color.get("b", 0) * 255)
        return f"#{r:02x}{g:02x}{b:02x}"


class LayoutToFrameConverter:
    """
    Konvertiert Layout JSON Schema → Figma Frame.
    
    Für Export von Scribus-Seiten nach Figma.
    """
    
    def convert(
        self,
        layout_json: Dict,
        frame_name: str = "Exported Page"
    ) -> Dict:
        """
        Konvertiert Layout JSON zu Figma Frame-Struktur.
        
        Args:
            layout_json: Layout JSON Schema
            frame_name: Name für Frame
            
        Returns:
            Figma Frame JSON (für create_frame)
        """
        doc = layout_json.get("document", {})
        width = doc.get("width", 2480)
        height = doc.get("height", 3508)
        
        # Erstelle Frame-Struktur
        frame = {
            "name": frame_name,
            "type": "FRAME",
            "absoluteBoundingBox": {
                "x": 0,
                "y": 0,
                "width": width,
                "height": height,
            },
            "children": [],
        }
        
        # Konvertiere Objects zu Figma Nodes
        pages = layout_json.get("pages", [])
        if pages:
            page = pages[0]
            objects = page.get("objects", [])
            
            for obj in objects:
                node = self._convert_object_to_node(obj)
                if node:
                    frame["children"].append(node)
        
        return frame
    
    def _convert_object_to_node(self, obj: Dict) -> Optional[Dict]:
        """
        Konvertiert Layout JSON Object zu Figma Node.
        
        Args:
            obj: Layout JSON Object
            
        Returns:
            Figma Node oder None
        """
        obj_type = obj.get("type", "")
        obj_id = obj.get("id", "")
        bbox = obj.get("bbox", {})
        
        if not bbox:
            return None
        
        node = {
            "id": obj_id.replace("_", ":"),  # Ersetze _ durch : für Figma IDs
            "name": obj_id,
            "absoluteBoundingBox": {
                "x": bbox.get("x", 0),
                "y": bbox.get("y", 0),
                "width": bbox.get("w", 0),
                "height": bbox.get("h", 0),
            },
        }
        
        # Text-Objekt
        if obj_type == "text":
            node["type"] = "TEXT"
            node["characters"] = obj.get("content", "")
            
            # Font-Styling
            style = {}
            if "fontFamily" in obj:
                style["fontFamily"] = obj["fontFamily"]
            if "fontSize" in obj:
                style["fontSize"] = obj["fontSize"]
            if "fontWeight" in obj:
                style["fontWeight"] = obj["fontWeight"]
            
            if style:
                node["style"] = style
        
        # Image-Objekt
        elif obj_type == "image":
            node["type"] = "RECTANGLE"  # Figma verwendet RECTANGLE für Images
            node["fills"] = [{
                "type": "IMAGE",
                "imageRef": obj.get("mediaId", ""),  # Wird später zu Image-URL
            }]
        
        # Rectangle-Objekt
        elif obj_type == "rectangle":
            node["type"] = "RECTANGLE"
            fill_color = obj.get("fillColor", "#000000")
            color = self._hex_to_color(fill_color)
            node["fills"] = [{
                "type": "SOLID",
                "color": color,
            }]
        
        else:
            return None
        
        return node
    
    def _hex_to_color(self, hex_color: str) -> Dict:
        """Konvertiert Hex zu Figma Color (0-1)"""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return {"r": r, "g": g, "b": b, "a": 1.0}

