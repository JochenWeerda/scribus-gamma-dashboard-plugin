"""Build-Metadaten Generator."""

import json
import hashlib
from datetime import datetime
from typing import Dict, Any


def generate_build_metadata(
    layout_json: Dict[str, Any],
    sla_bytes: bytes,
    compilation_time_ms: int = None
) -> Dict[str, Any]:
    """
    Generiert Build-Metadaten.
    
    Args:
        layout_json: Original Layout-JSON
        sla_bytes: Kompilierte SLA-Datei
        compilation_time_ms: Kompilierungszeit in Millisekunden
    
    Returns:
        Build-Metadaten als Dict
    """
    # Hashes berechnen
    layout_hash = hashlib.sha256(
        json.dumps(layout_json, sort_keys=True).encode("utf-8")
    ).hexdigest()
    sla_hash = hashlib.sha256(sla_bytes).hexdigest()
    
    metadata = {
        "version": "1.0.0",
        "build_time": datetime.utcnow().isoformat() + "Z",
        "compilation_time_ms": compilation_time_ms,
        "hashes": {
            "layout_json": layout_hash,
            "sla": sla_hash,
        },
        "layout_info": {
            "version": layout_json.get("version", "unknown"),
            "page_count": len(layout_json.get("pages", [])),
            "total_objects": sum(
                len(page.get("objects", [])) for page in layout_json.get("pages", [])
            ),
        },
        "sla_info": {
            "size_bytes": len(sla_bytes),
        },
    }
    
    return metadata

