"""
SLA Inserter für Scribus

Hilfsfunktionen zum Einfügen von SLA XML in Scribus-Dokumente.
"""

from typing import Optional
import base64


def prepare_sla_for_plugin(sla_xml_bytes: bytes) -> dict:
    """
    Bereitet SLA XML für Plugin-Übertragung vor.
    
    Args:
        sla_xml_bytes: SLA XML als Bytes
        
    Returns:
        Dict mit base64-encoded SLA und Metadaten
    """
    return {
        "sla_xml_base64": base64.b64encode(sla_xml_bytes).decode("utf-8"),
        "sla_xml_size": len(sla_xml_bytes),
        "format": "sla",
    }


def decode_sla_from_plugin(sla_data: dict) -> bytes:
    """
    Dekodiert SLA XML aus Plugin-Format.
    
    Args:
        sla_data: Dict mit sla_xml_base64
        
    Returns:
        SLA XML als Bytes
    """
    sla_base64 = sla_data.get("sla_xml_base64", "")
    return base64.b64decode(sla_base64)


def create_sla_insert_request(
    sla_xml_bytes: bytes,
    page_number: Optional[int] = None,
    insert_after: bool = True
) -> dict:
    """
    Erstellt Request für SLA-Einfügung.
    
    Args:
        sla_xml_bytes: SLA XML als Bytes
        page_number: Seitenzahl (optional, für spezifische Position)
        insert_after: Ob nach page_number eingefügt werden soll
        
    Returns:
        Request-Dict für API
    """
    return {
        "sla_xml": prepare_sla_for_plugin(sla_xml_bytes),
        "page_number": page_number,
        "insert_after": insert_after,
    }

