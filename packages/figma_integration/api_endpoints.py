"""
Figma API Endpoints für FastAPI

Diese Endpoints können in apps/api-gateway/main.py importiert und registriert werden.
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, List, Optional
from pydantic import BaseModel
import os

from .client import FigmaClient
from .converter import FrameToLayoutConverter, LayoutToFrameConverter
from .asset_downloader import FigmaAssetDownloader
from .ai_brief import FigmaAIBriefConfig, build_figma_ai_brief

# Globale Instanzen für AutoIndexer (wird in API Gateway initialisiert)
_auto_indexer = None

# Globale Instanzen (werden beim Start initialisiert)
_figma_client: Optional[FigmaClient] = None
_frame_converter: Optional[FrameToLayoutConverter] = None
_layout_converter: Optional[LayoutToFrameConverter] = None
_asset_downloader: Optional[FigmaAssetDownloader] = None


def init_figma_service(
    access_token: Optional[str] = None,
    minio_client=None,
    minio_bucket: str = "figma-assets",
    auto_indexer=None
):
    """
    Initialisiert Figma-Service (einmalig beim Start).
    
    Args:
        access_token: Figma Personal Access Token (default: aus ENV)
        minio_client: MinIO Client (optional)
        minio_bucket: MinIO Bucket Name
        auto_indexer: AutoIndexer Instanz (optional, für RAG-Integration)
    """
    global _figma_client, _frame_converter, _layout_converter, _asset_downloader, _auto_indexer
    
    if access_token is None:
        access_token = os.getenv("FIGMA_ACCESS_TOKEN")
    if not access_token:
        # Service bleibt deaktiviert; Endpoints liefern 503 (siehe Checks unten).
        return False

    if _figma_client is None:
        _figma_client = FigmaClient(access_token=access_token)
        _frame_converter = FrameToLayoutConverter()
        _layout_converter = LayoutToFrameConverter()
        _asset_downloader = FigmaAssetDownloader(
            minio_client=minio_client,
            minio_bucket=minio_bucket
        )
        _auto_indexer = auto_indexer
    return _figma_client is not None


# Pydantic Models
class ImportFrameRequest(BaseModel):
    file_key: str
    frame_id: str
    dpi: int = 300
    page_number: int = 1


class ExportFrameRequest(BaseModel):
    file_key: str
    frame_id: Optional[str] = None
    frame_name: str = "Exported Page"
    layout_json: Dict


class AIBriefRequest(BaseModel):
    """Mode 1: build a prompt pack for Figma AI (no direct AI API call)."""

    layout_json: Dict
    top_k: int = 5
    rag_enabled: bool = False
    project_init: Optional[Dict] = None


# Router
router = APIRouter(prefix="/api/figma", tags=["Figma"])

@router.get("/me")
async def get_me():
    """Aktuellen User abrufen (inkl. Team-Zugehörigkeiten)."""
    if _figma_client is None:
        raise HTTPException(status_code=503, detail="Figma service not initialized")

    try:
        return _figma_client.get_me()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects")
async def list_projects(team_id: str):
    """Liste der Projekte eines Teams."""
    if _figma_client is None:
        raise HTTPException(status_code=503, detail="Figma service not initialized")

    try:
        projects = _figma_client.list_team_projects(team_id=team_id)
        return {"team_id": team_id, "projects": projects, "count": len(projects)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/files")
async def list_project_files(project_id: str):
    """Liste der Dateien eines Projekts."""
    if _figma_client is None:
        raise HTTPException(status_code=503, detail="Figma service not initialized")

    try:
        files = _figma_client.list_project_files(project_id=project_id)
        return {"project_id": project_id, "files": files, "count": len(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files")
async def list_files(team_id: Optional[str] = None, project_id: Optional[str] = None):
    """
    Dateien auflisten.

    Hinweis: Ohne team_id/project_id wird versucht, über /me -> teams -> projects zu aggregieren.
    """
    if _figma_client is None:
        raise HTTPException(status_code=503, detail="Figma service not initialized")
    
    try:
        if not team_id:
            team_id = os.getenv("FIGMA_TEAM_ID") or None
        if not project_id:
            project_id = os.getenv("FIGMA_PROJECT_ID") or None

        files = _figma_client.list_files(team_id=team_id, project_id=project_id)
        response = {"files": files, "count": len(files)}
        if not team_id and not project_id and len(files) == 0:
            response["note"] = (
                "No files discovered. Depending on your Figma account/token, /v1/me may not expose teams/projects. "
                "Provide a known file_key directly (e.g. GET /api/figma/files/{file_key}) or set FIGMA_TEAM_ID/"
                "FIGMA_PROJECT_ID for listing."
            )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{file_key}")
async def get_file(file_key: str):
    """File-Metadaten abrufen"""
    if _figma_client is None:
        raise HTTPException(status_code=503, detail="Figma service not initialized")
    
    try:
        file_data = _figma_client.get_file(file_key)
        return file_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{file_key}/frames")
async def list_frames(file_key: str):
    """Liste aller Frames in einem File"""
    if _figma_client is None:
        raise HTTPException(status_code=503, detail="Figma service not initialized")
    
    try:
        frames = _figma_client.list_frames(file_key)
        return {"frames": frames, "count": len(frames)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/frames/import")
async def import_frame(request: ImportFrameRequest):
    """
    Importiert Figma Frame als neue Seite.
    
    Returns:
        Layout JSON Schema (Compiler-Input) + SLA XML + RAG Layout ID
    """
    if _figma_client is None or _frame_converter is None:
        raise HTTPException(status_code=503, detail="Figma service not initialized")
    
    try:
        # 1. Frame von Figma abrufen
        frame_json = _figma_client.get_frame(request.file_key, request.frame_id)
        
        # 2. Frame → Layout JSON konvertieren
        layout_json = _frame_converter.convert(
            frame_json,
            dpi=request.dpi,
            page_number=request.page_number
        )
        
        # 3. Images herunterladen und zu MinIO hochladen
        if _asset_downloader:
            image_objects = [
                obj for obj in layout_json["pages"][0]["objects"]
                if obj.get("type") == "image"
            ]
            
            if image_objects:
                minio_urls = _asset_downloader.download_frame_images(
                    _figma_client,
                    request.file_key,
                    frame_json,
                    image_objects
                )
                
                # Ersetze leere mediaId mit MinIO-URLs
                for obj in image_objects:
                    obj_id = obj.get("id", "")
                    if obj_id in minio_urls:
                        obj["mediaId"] = minio_urls[obj_id]
        
        # 4. RAG-Indexing (automatisch)
        layout_id = None
        if _auto_indexer:
            try:
                layout_id = await _auto_indexer.index_figma_import(layout_json)
            except Exception as e:
                # RAG-Indexing-Fehler nicht kritisch, aber loggen
                import logging
                logging.warning(f"RAG Auto-Indexing failed: {e}")
                pass
        
        # 5. Compiler aufrufen
        sla_xml_bytes = None
        try:
            from packages.sla_compiler.compiler import compile_layout_to_sla
            sla_xml_bytes = compile_layout_to_sla(layout_json)
            
            # Compiler-Ergebnis für Digital Twin indexieren
            if _auto_indexer and layout_id:
                try:
                    await auto_indexer.index_compiler_result(
                        layout_json=layout_json,
                        sla_xml=sla_xml_bytes,
                        success=True,
                        errors=None
                    )
                except:
                    pass
        except ImportError:
            # Compiler nicht verfügbar
            pass
        except Exception as e:
            # Compiler-Fehler
            raise HTTPException(status_code=500, detail=f"Compiler error: {e}")
        
        return {
            "layout_json": layout_json,
            "sla_xml_bytes": sla_xml_bytes.hex() if sla_xml_bytes else None,  # Hex für JSON
            "sla_xml_size": len(sla_xml_bytes) if sla_xml_bytes else 0,
            "layout_id": layout_id,  # RAG Layout ID
            "file_key": request.file_key,
            "frame_id": request.frame_id,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/frames/export")
async def export_frame(request: ExportFrameRequest):
    """
    Exportiert Scribus-Seite nach Figma.
    
    Args:
        request: ExportFrameRequest mit layout_json
        
    Returns:
        Frame-Objekt (für create_frame)
    """
    if _layout_converter is None:
        raise HTTPException(status_code=503, detail="Figma service not initialized")
    
    try:
        # 1. Layout JSON → Figma Frame konvertieren
        frame_json = _layout_converter.convert(
            request.layout_json,
            frame_name=request.frame_name
        )
        
        # 2. Frame erstellen (via Plugin API - TODO)
        # frame = _figma_client.create_frame(request.file_key, frame_json)
        
        return {
            "frame": frame_json,
            "file_key": request.file_key,
            "status": "converted",  # "created" wenn Frame erstellt wurde
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def figma_health():
    """Health Check für Figma-Service"""
    return {
        "status": "ok" if _figma_client is not None else "not_initialized",
        "components": {
            "client": _figma_client is not None,
            "frame_converter": _frame_converter is not None,
            "layout_converter": _layout_converter is not None,
            "asset_downloader": _asset_downloader is not None,
        }
    }


@router.post("/ai/brief")
async def figma_ai_brief(request: AIBriefRequest):
    """
    Mode 1: Generates a structured design brief + prompt text for Figma AI.

    Note: Figma AI does not expose a public API. This endpoint creates the "prompt pack" that can be pasted
    into Figma AI (or used by a later automation agent).
    """

    cfg = FigmaAIBriefConfig(top_k=int(request.top_k), rag_enabled=bool(request.rag_enabled))
    return build_figma_ai_brief(layout_json=request.layout_json, project_init=request.project_init, config=cfg)

