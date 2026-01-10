"""API Gateway - Hauptendpunkt für Layout-Kompilierung."""

import json
import logging
import os
from datetime import datetime
from uuid import UUID, uuid4

import redis
from fastapi import FastAPI, HTTPException, status, Depends, Header, Request, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from rq import Queue
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from packages.artifact_store import get_artifact_store
from packages.common.models import (
    ArtifactInfo,
    ArtifactType,
    JobCreateRequest,
    JobResponse,
    JobStatus,
    JobType,
    StorageType,
)
from packages.layout_schema import validate_layout
from events import setup_event_listeners
from config import config
from health import get_health_status
from middleware import CorrelationIDMiddleware, RequestLoggingMiddleware, RateLimitMiddleware
from metrics import PrometheusMiddleware, metrics_endpoint, record_job_created, update_queue_size
from packages.event_bus import get_event_bus
from packages.cache import get_cache

# Logging Setup
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if config.LOG_FORMAT == "text" else None
)
logger = logging.getLogger(__name__)

# FastAPI App
app = FastAPI(
    title="SLA Layout Pipeline API",
    description="Headless Layout Compiler: JSON → SLA → PNG/PDF",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
app.add_middleware(CorrelationIDMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Prometheus Metrics Middleware (wenn aktiviert)
if config.PROMETHEUS_ENABLED:
    app.add_middleware(PrometheusMiddleware)

# Rate Limiting Middleware (wenn aktiviert)
if config.RATE_LIMIT_ENABLED:
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_window=config.RATE_LIMIT_REQUESTS,
        window_seconds=config.RATE_LIMIT_WINDOW,
        use_redis=True,  # Redis für Multi-Instance-Support
        redis_url=config.REDIS_URL,
    )

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
engine = create_engine(config.DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(bind=engine)

# Redis Queue
redis_conn = redis.from_url(config.REDIS_URL, socket_connect_timeout=5, socket_timeout=5)
queue = Queue("compile", connection=redis_conn)

# Artifact Store
artifact_store = get_artifact_store()

# Validate Config
try:
    config.validate()
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    raise

# Setup Event Listeners
if config.EVENT_BUS_ENABLED:
    setup_event_listeners()


def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    """Verifiziert API-Key (wenn aktiviert)."""
    if not config.API_KEY_ENABLED:
        return True
    
    if not x_api_key or x_api_key != config.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return True


def validate_layout_input(layout_json: dict):
    """Validiert Layout-Input (Größe, Elementanzahl)."""
    # Größenprüfung (vereinfacht - in Production sollte Request-Size geprüft werden)
    json_str = json.dumps(layout_json)
    size_mb = len(json_str.encode("utf-8")) / (1024 * 1024)
    
    if size_mb > config.MAX_JSON_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Layout JSON too large: {size_mb:.2f} MB (max: {config.MAX_JSON_SIZE_MB} MB)"
        )
    
    # Seiten-Anzahl prüfen
    pages = layout_json.get("pages", [])
    if len(pages) > config.MAX_PAGES_PER_DOCUMENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many pages: {len(pages)} (max: {config.MAX_PAGES_PER_DOCUMENT})"
        )
    
    # Element-Anzahl pro Seite prüfen
    for page_data in pages:
        objects = page_data.get("objects", [])
        if len(objects) > config.MAX_ELEMENTS_PER_PAGE:
            page_num = page_data.get("pageNumber", "unknown")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Too many elements on page {page_num}: {len(objects)} (max: {config.MAX_ELEMENTS_PER_PAGE})"
            )


@app.get("/health")
async def health_check():
    """Health Check."""
    return {"status": "ok", "service": "api-gateway"}


@app.get("/metrics")
async def metrics():
    """Prometheus Metrics Endpoint."""
    if config.PROMETHEUS_ENABLED:
        return metrics_endpoint()
    else:
        raise HTTPException(status_code=404, detail="Prometheus metrics not enabled")


@app.get("/health/detailed")
async def detailed_health_check():
    """Detaillierter Health Check mit Dependency-Prüfung."""
    health_status = get_health_status(
        db_url=config.DATABASE_URL,
        redis_url=config.REDIS_URL,
        minio_config={
            "endpoint": config.MINIO_ENDPOINT,
            "access_key": config.MINIO_ACCESS_KEY,
            "secret_key": config.MINIO_SECRET_KEY,
            "bucket": config.MINIO_BUCKET,
            "secure": config.MINIO_SECURE,
        }
    )
    status_code = 200 if health_status["status"] == "ok" else 503
    return JSONResponse(content=health_status, status_code=status_code)


@app.post("/v1/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(request: JobCreateRequest, req: Request, _: bool = Depends(verify_api_key)):
    """
    Erstellt einen neuen Kompilierungs-Job.
    
    - Validiert Layout-JSON gegen Schema
    - Prüft Input-Größen (max. Größe, Seiten, Elemente)
    - Speichert JSON als Artefakt in MinIO
    - Erstellt Job-Datensatz in DB
    - Enqueued Render-Job
    """
    correlation_id = getattr(req.state, "correlation_id", "unknown")
    logger.info("Creating job", extra={"correlation_id": correlation_id})
    
    db = SessionLocal()
    try:
        # 1. Input-Validierung (Größe, Seiten, Elemente)
        validate_layout_input(request.layout_json)
        
        # 2. Schema-Validierung
        is_valid, errors = validate_layout(request.layout_json)
        if not is_valid:
            logger.warning("Layout validation failed", extra={"correlation_id": correlation_id, "errors": errors})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"validation_errors": errors}
            )
        
        # 2. JSON als Artefakt speichern
        json_bytes = json.dumps(request.layout_json, ensure_ascii=False).encode("utf-8")
        file_name = f"layout_{uuid4()}.json"
        storage_uri, file_name, file_size = artifact_store.upload(
            json_bytes,
            ArtifactType.LAYOUT_JSON,
            file_name=file_name,
            mime_type="application/json"
        )
        checksum = artifact_store.compute_checksum(json_bytes)
        
        # 3. Artefakt in DB speichern
        artifact_result = db.execute(
            text("""
                INSERT INTO artifacts (
                    artifact_type, storage_type, storage_uri, file_name, file_size,
                    mime_type, checksum_md5
                )
                VALUES (:type, :storage_type, :uri, :file_name, :file_size, :mime_type, :checksum)
                RETURNING id, created_at
            """),
            {
                "type": ArtifactType.LAYOUT_JSON.value,
                "storage_type": StorageType.S3.value,
                "uri": storage_uri,
                "file_name": file_name,
                "file_size": file_size,
                "mime_type": "application/json",
                "checksum": checksum,
            }
        )
        artifact_row = artifact_result.fetchone()
        artifact_id = artifact_row[0]
        artifact_created_at = artifact_row[1]
        
        # 4. Job in DB erstellen
        job_result = db.execute(
            text("""
                INSERT INTO jobs (
                    job_type, status, priority, input_artifact_id, metadata
                )
                VALUES (:job_type, :status, :priority, :input_artifact_id, :metadata)
                RETURNING id, created_at, updated_at
            """),
            {
                "job_type": JobType.COMPILE.value,
                "status": JobStatus.PENDING.value,
                "priority": request.priority,
                "input_artifact_id": artifact_id,
                "metadata": json.dumps(request.metadata or {}),
            }
        )
        job_row = job_result.fetchone()
        job_id = job_row[0]
        job_created_at = job_row[1]
        job_updated_at = job_row[2]
        
        db.commit()
        
        # 5. Job enqueuen (Background-Task für bessere Response-Zeit)
        background_tasks.add_task(_enqueue_job_task, job_id, JobType.COMPILE.value)
        
        # Event-Bus: Job created
        event_bus.publish(
            "jobs",
            "job.created",
            {
                "job_id": str(job_id),
                "job_type": JobType.COMPILE.value,
                "status": JobStatus.PENDING.value,
                "input_artifact_id": str(artifact_id),
            }
        )
        
        # 6. Response
        return JobResponse(
            id=job_id,
            status=JobStatus.PENDING,
            job_type=JobType.COMPILE,
            priority=request.priority,
            input_artifact_id=artifact_id,
            output_artifact_id=None,
            error_message=None,
            metadata=request.metadata,
            created_at=job_created_at,
            updated_at=job_updated_at,
            started_at=None,
            completed_at=None,
            input_artifact=ArtifactInfo(
                id=artifact_id,
                artifact_type=ArtifactType.LAYOUT_JSON,
                storage_type=StorageType.S3,
                storage_uri=storage_uri,
                file_name=file_name,
                file_size=file_size,
                mime_type="application/json",
                created_at=artifact_created_at,
            ),
            output_artifact=None,
        )
    
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Erstellen des Jobs: {str(e)}"
        )
    finally:
        db.close()


@app.get("/v1/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: UUID, _: bool = Depends(verify_api_key)):
    """Gibt Job-Status und Artefakt-URIs zurück."""
    # Cache-Check (wenn aktiviert)
    cache_key = f"job:{job_id}"
    if hasattr(cache, 'get'):
        cached_job = cache.get(cache_key)
        if cached_job:
            return JobResponse(**cached_job)
    
    db = SessionLocal()
    try:
        result = db.execute(
            text("""
                SELECT j.id, j.job_type, j.status, j.priority, j.input_artifact_id, j.output_artifact_id,
                       j.error_message, j.metadata, j.created_at, j.updated_at, j.started_at, j.completed_at,
                       input_a.id as input_a_id, input_a.artifact_type as input_a_type,
                       input_a.storage_type as input_a_storage, input_a.storage_uri as input_a_uri,
                       input_a.file_name as input_a_name, input_a.file_size as input_a_size,
                       input_a.mime_type as input_a_mime, input_a.created_at as input_a_created,
                       output_a.id as output_a_id, output_a.artifact_type as output_a_type,
                       output_a.storage_type as output_a_storage, output_a.storage_uri as output_a_uri,
                       output_a.file_name as output_a_name, output_a.file_size as output_a_size,
                       output_a.mime_type as output_a_mime, output_a.created_at as output_a_created
                FROM jobs j
                LEFT JOIN artifacts input_a ON j.input_artifact_id = input_a.id
                LEFT JOIN artifacts output_a ON j.output_artifact_id = output_a.id
                WHERE j.id = :job_id
            """),
            {"job_id": job_id}
        )
        row = result.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} nicht gefunden"
            )
        
        # Build response
        input_artifact = None
        if row[13]:  # input_a_id
            input_artifact = ArtifactInfo(
                id=row[13],
                artifact_type=ArtifactType(row[14]),
                storage_type=StorageType(row[15]),
                storage_uri=row[16],
                file_name=row[17],
                file_size=row[18],
                mime_type=row[19],
                created_at=row[20],
            )
        
        output_artifact = None
        if row[21]:  # output_a_id
            output_artifact = ArtifactInfo(
                id=row[21],
                artifact_type=ArtifactType(row[22]),
                storage_type=StorageType(row[23]),
                storage_uri=row[24],
                file_name=row[25],
                file_size=row[26],
                mime_type=row[27],
                created_at=row[28],
            )
        
        return JobResponse(
            id=row[0],
            status=JobStatus(row[2]),
            job_type=JobType(row[1]),
            priority=row[3] or 0,
            input_artifact_id=row[4],
            output_artifact_id=row[5],
            error_message=row[6],
            metadata=json.loads(row[7]) if row[7] else None,
            created_at=row[8],
            updated_at=row[9],
            started_at=row[10],
            completed_at=row[11],
            input_artifact=input_artifact,
            output_artifact=output_artifact,
        )
        
        # Cache response (nur wenn completed oder failed - für finaler Status)
        if hasattr(cache, 'set') and job_response.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            cache.set(cache_key, job_response.dict(), ttl=3600)  # 1 Stunde
        
        return job_response
    
    finally:
        db.close()


@app.get("/v1/jobs/{job_id}/logs")
async def get_job_logs(job_id: UUID, _: bool = Depends(verify_api_key)):
    """Gibt Job-Logs zurück."""
    db = SessionLocal()
    try:
        result = db.execute(
            text("""
                SELECT id, log_level, message, context, created_at
                FROM job_logs
                WHERE job_id = :job_id
                ORDER BY created_at ASC
            """),
            {"job_id": job_id}
        )
        logs = []
        for row in result:
            logs.append({
                "id": str(row[0]),
                "log_level": row[1],
                "message": row[2],
                "context": json.loads(row[3]) if row[3] else None,
                "created_at": row[4].isoformat(),
            })
        return {"job_id": str(job_id), "logs": logs}
    finally:
        db.close()


@app.get("/v1/jobs/{job_id}/pages")
async def get_job_pages(job_id: UUID, _: bool = Depends(verify_api_key)):
    """Gibt Pages mit Export-URIs zurück."""
    db = SessionLocal()
    try:
        result = db.execute(
            text("""
                SELECT p.id, p.page_number, p.master_page, p.object_count,
                       png_a.storage_uri as png_uri, pdf_a.storage_uri as pdf_uri,
                       p.created_at
                FROM pages p
                LEFT JOIN artifacts png_a ON p.png_artifact_id = png_a.id
                LEFT JOIN artifacts pdf_a ON p.pdf_artifact_id = pdf_a.id
                WHERE p.job_id = :job_id
                ORDER BY p.page_number
            """),
            {"job_id": job_id}
        )
        pages = []
        for row in result:
            pages.append({
                "id": str(row[0]),
                "page_number": row[1],
                "master_page": row[2],
                "object_count": row[3],
                "png_uri": row[4],
                "pdf_uri": row[5],
                "created_at": row[6].isoformat(),
            })
        return {"job_id": str(job_id), "pages": pages}
    finally:
        db.close()


@app.get("/v1/jobs/{job_id}/preview/{page_number}")
async def get_preview(job_id: UUID, page_number: int, _: bool = Depends(verify_api_key)):
    """Gibt PNG-Preview für eine Seite zurück."""
    db = SessionLocal()
    try:
        # Finde PNG-Artefakt für diese Seite
        result = db.execute(
            text("""
                SELECT a.storage_uri, a.file_name, a.mime_type
                FROM pages p
                JOIN artifacts a ON p.png_artifact_id = a.id
                WHERE p.job_id = :job_id AND p.page_number = :page_num
            """),
            {"job_id": job_id, "page_num": page_number}
        )
        row = result.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preview für Seite {page_number} nicht gefunden"
            )
        
        storage_uri = row[0]
        file_name = row[1]
        mime_type = row[2] or "image/png"
        
        # Lade PNG aus Artifact Store
        png_bytes = artifact_store.download(storage_uri)
        
        return StreamingResponse(
            iter([png_bytes]),
            media_type=mime_type,
            headers={"Content-Disposition": f'inline; filename="{file_name}"'}
        )
    
    finally:
        db.close()


@app.get("/v1/jobs/{job_id}/artifact/pdf")
async def get_pdf(job_id: UUID, _: bool = Depends(verify_api_key)):
    """Gibt PDF-Artefakt zurück."""
    db = SessionLocal()
    try:
        # Finde PDF-Artefakt für diesen Job
        result = db.execute(
            text("""
                SELECT a.storage_uri, a.file_name, a.mime_type
                FROM jobs j
                JOIN artifacts a ON j.output_artifact_id = a.id
                WHERE j.id = :job_id AND a.artifact_type = 'pdf'
            """),
            {"job_id": job_id}
        )
        row = result.fetchone()
        
        if not row:
            # Fallback: Suche nach PDF in artifacts
            result = db.execute(
                text("""
                    SELECT a.storage_uri, a.file_name, a.mime_type
                    FROM artifacts a
                    WHERE a.artifact_type = 'pdf' AND a.file_name LIKE :pattern
                    ORDER BY a.created_at DESC
                    LIMIT 1
                """),
                {"pattern": f"%{job_id}%"}
            )
            row = result.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"PDF für Job {job_id} nicht gefunden"
            )
        
        storage_uri = row[0]
        file_name = row[1]
        mime_type = row[2] or "application/pdf"
        
        # Lade PDF aus Artifact Store
        pdf_bytes = artifact_store.download(storage_uri)
        
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type=mime_type,
            headers={"Content-Disposition": f'inline; filename="{file_name}"'}
        )
    
    finally:
        db.close()
