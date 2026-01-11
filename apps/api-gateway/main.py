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
from dialog import router as dialog_router
from variants import router as variants_router
from quality import router as quality_router
from workflow import router as workflow_router

# Optional integrations (Figma/RAG)
try:
    from packages.figma_integration.api_endpoints import (
        router as figma_router,
        init_figma_service,
    )
    from packages.figma_integration.minio_integration import (
        create_minio_client,
        ensure_minio_bucket,
    )
except Exception:
    figma_router = None
    init_figma_service = None
    create_minio_client = None
    ensure_minio_bucket = None

try:
    from packages.rag_service.api_endpoints import (
        router as rag_router,
        init_rag_service,
    )
except Exception:
    rag_router = None
    init_rag_service = None

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

# Register optional routers (they may still return 503 until initialized)
if figma_router is not None:
    app.include_router(figma_router)
if rag_router is not None:
    app.include_router(rag_router)
app.include_router(dialog_router)
app.include_router(variants_router)
app.include_router(quality_router)
app.include_router(workflow_router)

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
compile_queue = Queue("compile", connection=redis_conn)
workflow_queue = Queue("workflow", connection=redis_conn)

# Artifact Store
artifact_store = get_artifact_store()

# Optional runtime services
event_bus = get_event_bus() if config.EVENT_BUS_ENABLED else None
cache = get_cache() if config.CACHE_ENABLED else None

# Validate Config
try:
    config.validate()
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    raise

# Setup Event Listeners
if config.EVENT_BUS_ENABLED:
    setup_event_listeners()


@app.on_event("startup")
async def init_optional_integrations():
    """Initialisiert optionale Subsysteme (Figma/RAG) anhand ENV/Config."""
    # RAG (optional)
    if init_rag_service is not None and os.getenv("ENABLE_RAG", "0") == "1":
        init_rag_service(
            chroma_db_path=os.getenv("CHROMA_DB_PATH"),
            embedding_model=os.getenv("EMBEDDING_MODEL"),
            clip_model=os.getenv("CLIP_MODEL"),
        )

    # Figma (optional)
    if init_figma_service is not None and os.getenv("ENABLE_FIGMA", "0") == "1":
        minio_client = None
        bucket = os.getenv("FIGMA_MINIO_BUCKET", "figma-assets")

        if create_minio_client is not None and ensure_minio_bucket is not None:
            minio_client = create_minio_client(
                endpoint=config.MINIO_ENDPOINT,
                access_key=config.MINIO_ACCESS_KEY,
                secret_key=config.MINIO_SECRET_KEY,
                secure=config.MINIO_SECURE,
            )
            if minio_client:
                ensure_minio_bucket(minio_client, bucket)

        init_figma_service(
            access_token=os.getenv("FIGMA_ACCESS_TOKEN"),
            minio_client=minio_client,
            minio_bucket=bucket,
            auto_indexer=None,  # später: RAG AutoIndexer verdrahten
        )


def _enqueue_job_task(job_id: UUID, job_type: str) -> None:
    """RQ Enqueue im BackgroundTask-Kontext."""
    try:
        # Worker läuft in apps/worker-scribus/worker.py (Module: worker)
        if job_type == JobType.COMPILE.value:
            compile_queue.enqueue(
                "worker.process_compile_job",
                str(job_id),
                job_timeout="20m",
            )
        elif job_type == JobType.WORKFLOW.value:
            workflow_queue.enqueue(
                "worker.process_workflow_job",
                str(job_id),
                job_timeout="60m",
            )
        else:
            compile_queue.enqueue(
                "worker.process_compile_job",
                str(job_id),
                job_timeout="20m",
            )

        try:
            update_queue_size(compile_queue.count + workflow_queue.count)
        except Exception:
            pass
    except Exception:
        logger.exception("Failed to enqueue job", extra={"job_id": str(job_id), "job_type": job_type})


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


# -----------------------------------------------------------------------------
# Plugin Compatibility Endpoints (/api/*)
# -----------------------------------------------------------------------------

@app.get("/api/status")
async def plugin_status(_: bool = Depends(verify_api_key)):
    """Legacy-Status für das Scribus-Plugin."""
    return {
        "status": "ok",
        "service": "api-gateway",
        "services": {
            "jobs": "enabled",
            "figma": "enabled" if os.getenv("ENABLE_FIGMA", "0") == "1" and figma_router is not None else "disabled",
            "rag": "enabled" if os.getenv("ENABLE_RAG", "0") == "1" and rag_router is not None else "disabled",
        },
        "endpoints": {
            "jobs": "/v1/jobs",
            "figma": "/api/figma",
            "rag": "/api/rag",
        },
    }


@app.get("/api/pipeline")
async def plugin_pipeline(_: bool = Depends(verify_api_key)):
    """Legacy-Pipeline-Endpunkt; mappt intern auf Job-Queue/DB."""
    db = SessionLocal()
    try:
        recent = db.execute(
            text(
                """
                SELECT id, job_type, status, priority, created_at, updated_at
                FROM jobs
                ORDER BY created_at DESC
                LIMIT 20
                """
            )
        ).mappings().all()
        return {
            "pipelines": [
                {
                    "id": "compile",
                    "name": "Compile",
                    "queue_size": compile_queue.count,
                },
                {
                    "id": "workflow",
                    "name": "Workflow",
                    "queue_size": workflow_queue.count,
                }
            ],
            "recent_jobs": list(recent),
        }
    finally:
        db.close()


@app.get("/api/assets")
async def plugin_assets(_: bool = Depends(verify_api_key)):
    """Legacy-Assets-Endpunkt (Artefakte aus DB)."""
    db = SessionLocal()
    try:
        artifacts = db.execute(
            text(
                """
                SELECT id, artifact_type, storage_uri, file_name, file_size, created_at
                FROM artifacts
                ORDER BY created_at DESC
                LIMIT 50
                """
            )
        ).mappings().all()
        return {"artifacts": list(artifacts)}
    finally:
        db.close()


@app.get("/api/layout/audit")
async def plugin_layout_audit(_: bool = Depends(verify_api_key)):
    """Legacy-Layout-Audit-Endpunkt (noch nicht im Job-Backend verdrahtet)."""
    return {
        "status": "not_implemented",
        "detail": "Layout audit is not wired into the job pipeline yet.",
    }


@app.post("/api/pipeline/{pipeline_id}/start")
async def plugin_pipeline_start(pipeline_id: str, _: bool = Depends(verify_api_key)):
    raise HTTPException(status_code=501, detail=f"Pipeline '{pipeline_id}' start not supported via legacy endpoint")


@app.post("/api/pipeline/{pipeline_id}/stop")
async def plugin_pipeline_stop(pipeline_id: str, _: bool = Depends(verify_api_key)):
    raise HTTPException(status_code=501, detail=f"Pipeline '{pipeline_id}' stop not supported via legacy endpoint")


@app.post("/v1/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    request: JobCreateRequest,
    req: Request,
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_api_key),
):
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
        if event_bus is not None and hasattr(event_bus, "publish"):
            event_bus.publish(
                "jobs",
                "job.created",
                {
                    "job_id": str(job_id),
                    "job_type": JobType.COMPILE.value,
                    "status": JobStatus.PENDING.value,
                    "input_artifact_id": str(artifact_id),
                },
            )
        
        # 6. Response
        job_response = JobResponse(
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

        return job_response
    
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
    if cache is not None and hasattr(cache, "get"):
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
        if row[12]:  # input_a_id
            input_artifact = ArtifactInfo(
                id=row[12],
                artifact_type=ArtifactType(row[13]),
                storage_type=StorageType(row[14]),
                storage_uri=row[15],
                file_name=row[16],
                file_size=row[17],
                mime_type=row[18],
                created_at=row[19],
            )
        
        output_artifact = None
        if row[20]:  # output_a_id
            output_artifact = ArtifactInfo(
                id=row[20],
                artifact_type=ArtifactType(row[21]),
                storage_type=StorageType(row[22]),
                storage_uri=row[23],
                file_name=row[24],
                file_size=row[25],
                mime_type=row[26],
                created_at=row[27],
            )
        
        return JobResponse(
            id=row[0],
            status=JobStatus(row[2]),
            job_type=JobType(row[1]),
            priority=row[3] or 0,
            input_artifact_id=row[4],
            output_artifact_id=row[5],
            error_message=row[6],
            metadata=row[7] if row[7] else None,
            created_at=row[8],
            updated_at=row[9],
            started_at=row[10],
            completed_at=row[11],
            input_artifact=input_artifact,
            output_artifact=output_artifact,
        )
        
        # Cache response (nur wenn completed oder failed - für finaler Status)
        if cache is not None and hasattr(cache, "set") and job_response.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
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


@app.get("/v1/artifacts/{artifact_id}")
async def download_artifact(artifact_id: UUID, _: bool = Depends(verify_api_key)):
    """Streams any artifact by id (generic downloader)."""
    db = SessionLocal()
    try:
        result = db.execute(
            text(
                """
                SELECT storage_uri, file_name, mime_type
                FROM artifacts
                WHERE id = :artifact_id
            """
            ),
            {"artifact_id": artifact_id},
        )
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

        storage_uri, file_name, mime_type = row[0], row[1], row[2] or "application/octet-stream"
        data = artifact_store.download(storage_uri)
        return StreamingResponse(
            iter([data]),
            media_type=mime_type,
            headers={"Content-Disposition": f'inline; filename=\"{file_name}\"'},
        )
    finally:
        db.close()
