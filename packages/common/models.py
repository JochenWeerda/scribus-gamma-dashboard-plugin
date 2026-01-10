"""Shared Pydantic Models für die Pipeline."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job-Status Enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Job-Typ Enum."""
    COMPILE = "compile"
    EXPORT_PNG = "export_png"
    EXPORT_PDF = "export_pdf"
    BATCH_EXPORT = "batch_export"


class ArtifactType(str, Enum):
    """Artefakt-Typ Enum."""
    LAYOUT_JSON = "layout_json"
    SLA = "sla"
    PNG = "png"
    PDF = "pdf"
    ASSET_IMAGE = "asset_image"
    PREFLIGHT = "preflight"


class StorageType(str, Enum):
    """Storage-Typ Enum."""
    S3 = "s3"
    MINIO = "minio"
    LOCAL = "local"
    INLINE = "inline"


class ArtifactInfo(BaseModel):
    """Artefakt-Informationen (nur Metadaten, keine Binärdaten)."""
    id: UUID
    artifact_type: ArtifactType
    storage_type: StorageType
    storage_uri: str
    file_name: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    created_at: datetime


class JobCreateRequest(BaseModel):
    """Request für Job-Erstellung."""
    layout_json: dict = Field(..., description="Layout-JSON (wird validiert und als Artefakt gespeichert)")
    priority: int = Field(default=0, ge=0, description="Priorität (höher = wichtiger)")
    metadata: Optional[dict] = Field(default=None, description="Zusätzliche Metadaten")


class JobResponse(BaseModel):
    """Job-Response."""
    id: UUID
    status: JobStatus
    job_type: JobType
    priority: int
    input_artifact_id: Optional[UUID] = None
    output_artifact_id: Optional[UUID] = None
    error_message: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Links zu Artefakten (aus DB)
    input_artifact: Optional[ArtifactInfo] = None
    output_artifact: Optional[ArtifactInfo] = None


class PageInfo(BaseModel):
    """Seiten-Informationen."""
    id: UUID
    page_number: int
    master_page: Optional[str] = None
    object_count: int = 0
    png_artifact_id: Optional[UUID] = None
    pdf_artifact_id: Optional[UUID] = None
    created_at: datetime


class JobLogEntry(BaseModel):
    """Job-Log-Eintrag."""
    id: UUID
    log_level: str
    message: str
    context: Optional[dict] = None
    created_at: datetime

