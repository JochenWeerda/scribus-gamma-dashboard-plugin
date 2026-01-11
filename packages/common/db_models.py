"""SQLAlchemy Database Models für Alembic Migrations."""

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from enum import Enum

from .types import GUID

Base = declarative_base()


class JobStatus(str, Enum):
    """Job-Status Enum."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(str, Enum):
    """Job-Typ Enum."""
    COMPILE = "compile"
    EXPORT = "export"


class ArtifactType(str, Enum):
    """Artefakt-Typ Enum."""
    LAYOUT_JSON = "layout_json"
    SLA = "sla"
    PNG = "png"
    PDF = "pdf"
    BUILD_METADATA = "build_metadata"
    PREFLIGHT = "preflight"


class StorageType(str, Enum):
    """Storage-Typ Enum."""
    S3 = "s3"
    LOCAL = "local"


class Job(Base):
    """Job-Tabelle."""
    __tablename__ = "jobs"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    job_type = Column(SQLEnum(JobType), nullable=False)
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.QUEUED)
    input_artifact_id = Column(GUID(), ForeignKey("artifacts.id"), nullable=True)
    output_artifact_id = Column(GUID(), ForeignKey("artifacts.id"), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    input_artifact = relationship("Artifact", foreign_keys=[input_artifact_id])
    output_artifact = relationship("Artifact", foreign_keys=[output_artifact_id])


class Artifact(Base):
    """Artefakt-Tabelle."""
    __tablename__ = "artifacts"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    artifact_type = Column(SQLEnum(ArtifactType), nullable=False)
    storage_type = Column(SQLEnum(StorageType), nullable=False)
    storage_uri = Column(String(2048), nullable=False)
    file_name = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(128), nullable=True)
    checksum_md5 = Column(String(32), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class JobLog(Base):
    """Job-Log-Tabelle."""
    __tablename__ = "job_logs"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id = Column(GUID(), ForeignKey("jobs.id"), nullable=False)
    log_level = Column(String(16), nullable=False)  # INFO, WARN, ERROR
    message = Column(Text, nullable=False)
    context = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationship
    job = relationship("Job", backref="logs")


class Page(Base):
    """Page-Tabelle."""
    __tablename__ = "pages"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id = Column(GUID(), ForeignKey("jobs.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    master_page = Column(String(128), nullable=True)
    object_count = Column(Integer, nullable=False, default=0)
    png_artifact_id = Column(GUID(), ForeignKey("artifacts.id"), nullable=True)
    pdf_artifact_id = Column(GUID(), ForeignKey("artifacts.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", backref="pages")
    png_artifact = relationship("Artifact", foreign_keys=[png_artifact_id])
    pdf_artifact = relationship("Artifact", foreign_keys=[pdf_artifact_id])

