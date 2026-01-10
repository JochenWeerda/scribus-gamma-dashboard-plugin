"""SLA Compiler - Konvertiert JSON Layout zu Scribus SLA XML."""

import xml.etree.ElementTree as ET
from typing import Dict, Any
from xml.dom import minidom


def px_to_pt(px: float, dpi: float = 300) -> float:
    """Konvertiert Pixel zu Punkten: pt = (px / dpi) * 72"""
    return round((px / dpi) * 72, 2)


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Konvertiert Hex-Farbe (#RRGGBB) zu RGB (0-255)."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 6:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return (0, 0, 0)


def rgb_to_scribus(r: int, g: int, b: int) -> str:
    """Konvertiert RGB zu Scribus-Farbformat (0-255 -> 0-1 mit Komma)."""
    return f"{r/255:.3f},{g/255:.3f},{b/255:.3f}"


def get_layer_zorder(layer_name: str, zorder: int = None) -> int:
    """Gibt Z-Order basierend auf Layer-Namen zurück (falls nicht gesetzt)."""
    if zorder is not None:
        return zorder
    
    layer_zorders = {
        "Background": 0,
        "Images_BG": 10,
        "Images": 20,
        "Text": 30,
        "Overlay": 40,
        "Wrap": 50,
    }
    return layer_zorders.get(layer_name, 30)


def compile_layout_to_sla(layout_json: Dict[str, Any], template: Dict[str, Any] = None) -> bytes:
    """
    Kompiliert JSON Layout zu Scribus SLA XML.
    
    Args:
        layout_json: Layout-JSON (validiert)
        template: Optional Template (nicht im MVP verwendet)
    
    Returns:
        SLA XML als Bytes
    """
    # Document settings
    doc = layout_json.get("document", {})
    width_px = doc.get("width", 2480)
    height_px = doc.get("height", 3508)
    dpi = doc.get("dpi", 300)
    
    width_pt = px_to_pt(width_px, dpi)
    height_pt = px_to_pt(height_px, dpi)
    
    # Root element
    root = ET.Element("SCRIBUSUTF8NEW")
    root.set("Version", "1.5.8")
    
    # Document element
    doc_elem = ET.SubElement(root, "DOCUMENT")
    doc_elem.set("ANIM", "0")
    doc_elem.set("ANNOT", "0")
    doc_elem.set("AUTOSP", "0")
    doc_elem.set("AUTOTEXT", "0")
    doc_elem.set("BOOK", "0")
    doc_elem.set("CHANGE", "")
    doc_elem.set("CURRENTPAGE", "1")
    doc_elem.set("DP", "0")
    doc_elem.set("FSTPAGE", "1")
    doc_elem.set("LANGUAGE", "de")
    doc_elem.set("MAG", "1")
    doc_elem.set("MARGPRESET", "0")
    doc_elem.set("MINOR", "8")
    doc_elem.set("PAGES", str(len(layout_json.get("pages", []))))
    doc_elem.set("PAGEWIDTH", str(width_pt))
    doc_elem.set("PAGEHEIGHT", str(height_pt))
    doc_elem.set("PAGEWIDTH", str(width_pt))
    doc_elem.set("UNIT", "0")  # Points
    doc_elem.set("UNITR", "0")
    
    # Colors (Standard-Farben)
    colors = ET.SubElement(doc_elem, "COLOR")
    colors.set("Black", "0,0,0,255")
    colors.set("White", "255,255,255,255")
    
    # Pages
    pages_elem = ET.SubElement(doc_elem, "PAGE")
    
    pages = layout_json.get("pages", [])
    for page_data in sorted(pages, key=lambda p: p.get("pageNumber", 1)):
        page_num = page_data.get("pageNumber", 1)
        objects = page_data.get("objects", [])
        
        # Sort objects by zOrder
        sorted_objects = sorted(objects, key=lambda obj: get_layer_zorder(
            obj.get("layer", "Text"),
            obj.get("zOrder")
        ))
        
        for obj in sorted_objects:
            obj_type = obj.get("type")
            if obj_type == "rectangle":
                _add_rectangle(pages_elem, obj, dpi, page_num)
            elif obj_type == "text":
                _add_textframe(pages_elem, obj, dpi, page_num)
            elif obj_type == "image":
                _add_imageframe(pages_elem, obj, dpi, page_num)
    
    # Format XML
    xml_str = ET.tostring(root, encoding="utf-8")
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ", encoding="utf-8")
    
    return pretty_xml


def _add_rectangle(parent: ET.Element, obj: Dict, dpi: float, page_num: int):
    """Fügt Rechteck-Objekt hinzu."""
    bbox = obj.get("bbox", {})
    x_pt = px_to_pt(bbox.get("x", 0), dpi)
    y_pt = px_to_pt(bbox.get("y", 0), dpi)
    w_pt = px_to_pt(bbox.get("w", 100), dpi)
    h_pt = px_to_pt(bbox.get("h", 100), dpi)
    
    # Scribus Rechteck-Element (vereinfacht für MVP)
    rect_elem = ET.SubElement(parent, "PAGEOBJECT")
    rect_elem.set("PTYPE", "4")  # Rectangle
    rect_elem.set("XPOS", str(x_pt))
    rect_elem.set("YPOS", str(y_pt))
    rect_elem.set("WIDTH", str(w_pt))
    rect_elem.set("HEIGHT", str(h_pt))
    rect_elem.set("PAGE", str(page_num))
    rect_elem.set("LAYER", obj.get("layer", "Background"))
    
    # Fill color
    fill_color = obj.get("fillColor", "#FFFFFF")
    r, g, b = hex_to_rgb(fill_color)
    rect_elem.set("FLCOLOR", rgb_to_scribus(r, g, b))
    
    # Stroke
    stroke_width = obj.get("strokeWidth", 0)
    if stroke_width > 0:
        stroke_color = obj.get("strokeColor", "#000000")
        r, g, b = hex_to_rgb(stroke_color)
        rect_elem.set("LINEW", str(px_to_pt(stroke_width, dpi)))
        rect_elem.set("LINECOLOR", rgb_to_scribus(r, g, b))


def _add_textframe(parent: ET.Element, obj: Dict, dpi: float, page_num: int):
    """Fügt Textframe hinzu."""
    bbox = obj.get("bbox", {})
    x_pt = px_to_pt(bbox.get("x", 0), dpi)
    y_pt = px_to_pt(bbox.get("y", 0), dpi)
    w_pt = px_to_pt(bbox.get("w", 100), dpi)
    h_pt = px_to_pt(bbox.get("h", 100), dpi)
    
    text_elem = ET.SubElement(parent, "PAGEOBJECT")
    text_elem.set("PTYPE", "4")  # TextFrame
    text_elem.set("XPOS", str(x_pt))
    text_elem.set("YPOS", str(y_pt))
    text_elem.set("WIDTH", str(w_pt))
    text_elem.set("HEIGHT", str(h_pt))
    text_elem.set("PAGE", str(page_num))
    text_elem.set("LAYER", obj.get("layer", "Text"))
    
    # Text content (vereinfacht für MVP)
    content = obj.get("content", "")
    text_elem.set("TEXT", content)
    
    # Font (vereinfacht)
    font_family = obj.get("fontFamily", "Arial")
    font_size = obj.get("fontSize", 12)
    text_elem.set("FONT", font_family)
    text_elem.set("FONTSIZE", str(font_size))
    
    # Color
    color = obj.get("color", "#000000")
    r, g, b = hex_to_rgb(color)
    text_elem.set("COLOR", rgb_to_scribus(r, g, b))


def _add_imageframe(parent: ET.Element, obj: Dict, dpi: float, page_num: int):
    """Fügt Imageframe hinzu."""
    bbox = obj.get("bbox", {})
    x_pt = px_to_pt(bbox.get("x", 0), dpi)
    y_pt = px_to_pt(bbox.get("y", 0), dpi)
    w_pt = px_to_pt(bbox.get("w", 100), dpi)
    h_pt = px_to_pt(bbox.get("h", 100), dpi)
    
    img_elem = ET.SubElement(parent, "PAGEOBJECT")
    img_elem.set("PTYPE", "2")  # ImageFrame
    img_elem.set("XPOS", str(x_pt))
    img_elem.set("YPOS", str(y_pt))
    img_elem.set("WIDTH", str(w_pt))
    img_elem.set("HEIGHT", str(h_pt))
    img_elem.set("PAGE", str(page_num))
    img_elem.set("LAYER", obj.get("layer", "Images"))
    
    # Image path (vereinfacht für MVP)
    image_url = obj.get("imageUrl", "")
    img_elem.set("PFILE", image_url)
    img_elem.set("SCALETYPE", "1" if obj.get("scaleToFrame", True) else "0")

