"""Sidecar-MCP Service - Digital Twin, Kollisions-Check, Layout-Compute."""

import json
import os
from typing import Dict, Any, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from packages.artifact_store import get_artifact_store
from packages.common.models import ArtifactType

app = FastAPI(
    title="Sidecar-MCP Service",
    description="Digital Twin, Collision Detection, Layout Compute",
    version="1.0.0",
)

artifact_store = get_artifact_store()


class LayoutComputeRequest(BaseModel):
    """Request für Layout-Compute."""
    layout_json: Dict[str, Any]
    criteria: Optional[List[str]] = None  # z.B. ["collision_check", "layer_safety"]


class LayoutComputeResponse(BaseModel):
    """Response für Layout-Compute."""
    artifact_uri: str
    artifact_id: str
    checksum: str
    metadata: Optional[Dict[str, Any]] = None


@app.get("/health")
async def health_check():
    """Health Check."""
    return {"status": "ok", "service": "sidecar-mcp"}


@app.post("/v1/compute/layout", response_model=LayoutComputeResponse)
async def compute_layout(request: LayoutComputeRequest):
    """
    Führt Layout-Compute aus:
    - Digital Twin State (nur Metadaten für Bilder!)
    - Kollisions-Check (O(n²) baseline)
    - Gibt computed layout als Artefakt zurück (kein inline JSON!)
    """
    layout_json = request.layout_json
    
    # Digital Twin: Extrahiere nur Metadaten (keine Binärdaten)
    computed_layout = _create_digital_twin(layout_json)
    
    # Kollisions-Check (O(n²) baseline)
    collisions = _check_collisions(computed_layout)
    if collisions:
        computed_layout["metadata"] = computed_layout.get("metadata", {})
        computed_layout["metadata"]["collisions"] = collisions
        computed_layout["metadata"]["collision_count"] = len(collisions)
    
    # Als Artefakt speichern (nicht inline!)
    computed_json_bytes = json.dumps(computed_layout, ensure_ascii=False).encode("utf-8")
    file_name = f"computed_layout_{uuid4()}.json"
    storage_uri, file_name, file_size = artifact_store.upload(
        computed_json_bytes,
        ArtifactType.LAYOUT_JSON,
        file_name=file_name,
        mime_type="application/json"
    )
    checksum = artifact_store.compute_checksum(computed_json_bytes)
    
    # Metadata für Response
    metadata = {
        "collision_count": len(collisions) if collisions else 0,
        "object_count": sum(len(page.get("objects", [])) for page in computed_layout.get("pages", [])),
        "page_count": len(computed_layout.get("pages", [])),
    }
    
    return LayoutComputeResponse(
        artifact_uri=storage_uri,
        artifact_id=str(uuid4()),  # In real implementation: DB artifact ID
        checksum=checksum,
        metadata=metadata,
    )


def _create_digital_twin(layout_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Erstellt Digital Twin State (nur Metadaten, keine Binärdaten).
    
    WICHTIG: Bilder werden nur als Metadaten gespeichert (URI, Maße, DPI, Hash),
    nicht als Base64 oder Binärdaten.
    """
    twin = json.loads(json.dumps(layout_json))  # Deep copy
    
    # Für jedes Image-Objekt: Nur Metadaten behalten
    for page in twin.get("pages", []):
        for obj in page.get("objects", []):
            if obj.get("type") == "image":
                # Entferne imageData (Base64), behalte nur imageUrl
                if "imageData" in obj:
                    del obj["imageData"]
                
                # Füge Metadaten hinzu (wenn verfügbar)
                # In real implementation: Lade Bild-Metadaten (Breite, Höhe, DPI, Hash)
                obj["metadata"] = {
                    "source": "artifact_store",
                    "uri": obj.get("imageUrl", ""),
                }
    
    return twin


def _check_collisions(layout_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Führt Kollisions-Check durch (O(n²) baseline).
    
    TODO: Upgrade auf Spatial Index (Grid/R-Tree) für große Seiten.
    
    Returns:
        Liste von Kollisionen: [{"obj1": "id1", "obj2": "id2", "overlap": {...}}]
    """
    collisions = []
    
    for page in layout_json.get("pages", []):
        objects = page.get("objects", [])
        page_num = page.get("pageNumber", 1)
        
        # O(n²) Paarprüfung
        for i, obj1 in enumerate(objects):
            if not obj1.get("visible", True):
                continue
            
            bbox1 = obj1.get("bbox", {})
            x1, y1 = bbox1.get("x", 0), bbox1.get("y", 0)
            w1, h1 = bbox1.get("w", 0), bbox1.get("h", 0)
            
            for j, obj2 in enumerate(objects[i+1:], start=i+1):
                if not obj2.get("visible", True):
                    continue
                
                # Skip wenn auf unterschiedlichen Layers (keine Kollision)
                layer1 = obj1.get("layer", "Text")
                layer2 = obj2.get("layer", "Text")
                if layer1 != layer2:
                    continue
                
                bbox2 = obj2.get("bbox", {})
                x2, y2 = bbox2.get("x", 0), bbox2.get("y", 0)
                w2, h2 = bbox2.get("w", 0), bbox2.get("h", 0)
                
                # Check overlap
                overlap_x = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
                overlap_y = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
                overlap_area = overlap_x * overlap_y
                
                if overlap_area > 0:
                    collisions.append({
                        "page": page_num,
                        "obj1": obj1.get("id"),
                        "obj2": obj2.get("id"),
                        "layer": layer1,
                        "overlap_area": overlap_area,
                        "overlap": {
                            "x": max(x1, x2),
                            "y": max(y1, y2),
                            "w": overlap_x,
                            "h": overlap_y,
                        },
                    })
    
    return collisions

