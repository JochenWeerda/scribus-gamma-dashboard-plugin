"""Workflow Orchestration API endpoints.

Runs the end-to-end "PPTX -> layout_json -> variants -> gamma crops -> quality" pipeline as an RQ job.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile, status, Header
from pydantic import BaseModel, Field
from sqlalchemy import text

from config import config
from packages.artifact_store import get_artifact_store
from packages.common.models import ArtifactInfo, ArtifactType, JobResponse, JobStatus, JobType, StorageType
from packages.event_bus import get_event_bus


router = APIRouter(prefix="/v1/workflow", tags=["workflow"])

artifact_store = get_artifact_store()
event_bus = get_event_bus() if config.EVENT_BUS_ENABLED else None


def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    if not config.API_KEY_ENABLED:
        return True
    if not x_api_key or x_api_key != config.API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
    return True


class WorkflowRunOptions(BaseModel):
    priority: int = Field(default=0, ge=0)

    generate_variants: bool = True

    gamma_sync: bool = False
    gamma_crop_kinds: List[str] = Field(default_factory=lambda: ["infobox"])
    gamma_attach_to_variants: bool = False
    gamma_attach_kinds: List[str] = Field(default_factory=lambda: ["image_box"])

    quality_check: bool = True
    quality_on_variants: bool = True
    quality_checks: List[str] = Field(default_factory=lambda: ["preflight", "amazon"])

    publish_artifacts: bool = True
    force: bool = False


@router.post("/run", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def run_workflow(
    req: Request,
    background_tasks: BackgroundTasks,
    bundle: UploadFile = File(..., description="ZIP bundle containing manifest.json + json/*.json + optional gamma/*.zip + optional project_init.json"),
    options_json: str = Form("{}", description="JSON encoded WorkflowRunOptions override"),
    _: bool = Depends(verify_api_key),
):
    """
    Enqueue a workflow job.

    The bundle ZIP should include at minimum:
    - manifest.json
    - json/<pptx_name>.json (pptx extractor outputs)

    Optionally:
    - gamma/<pptx_name>.zip (Gamma exports zip with slide pngs)
    - project_init.json (variant decisions)
    """

    correlation_id = getattr(req.state, "correlation_id", "unknown")

    try:
        opts_dict = json.loads(options_json or "{}")
    except Exception:
        raise HTTPException(status_code=400, detail="options_json must be valid JSON")

    try:
        options = WorkflowRunOptions(**opts_dict)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Read bundle bytes (size guard)
    data = await bundle.read()
    max_mb = int(os.environ.get("MAX_WORKFLOW_BUNDLE_MB", "200"))
    max_bytes = max_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"bundle too large (> {max_mb} MB)")

    file_name = bundle.filename or f"workflow_bundle_{uuid4()}.zip"
    if not file_name.lower().endswith(".zip"):
        file_name = file_name + ".zip"

    storage_uri, stored_name, file_size = artifact_store.upload(
        data,
        ArtifactType.WORKFLOW_BUNDLE,
        file_name=file_name,
        mime_type="application/zip",
    )
    checksum = artifact_store.compute_checksum(data)

    # Late import to avoid circulars: SessionLocal + enqueue helper live in main.py
    from main import SessionLocal, _enqueue_job_task  # type: ignore

    db = SessionLocal()
    try:
        artifact_result = db.execute(
            text(
                """
                INSERT INTO artifacts (
                    artifact_type, storage_type, storage_uri, file_name, file_size,
                    mime_type, checksum_md5, metadata
                )
                VALUES (:type, :storage_type, :uri, :file_name, :file_size, :mime_type, :checksum, :metadata)
                RETURNING id, created_at
            """
            ),
            {
                "type": ArtifactType.WORKFLOW_BUNDLE.value,
                "storage_type": StorageType.S3.value,
                "uri": storage_uri,
                "file_name": stored_name,
                "file_size": file_size,
                "mime_type": "application/zip",
                "checksum": checksum,
                "metadata": json.dumps({"correlation_id": correlation_id}),
            },
        )
        artifact_row = artifact_result.fetchone()
        artifact_id = artifact_row[0]
        artifact_created_at = artifact_row[1]

        job_result = db.execute(
            text(
                """
                INSERT INTO jobs (
                    job_type, status, priority, input_artifact_id, metadata
                )
                VALUES (:job_type, :status, :priority, :input_artifact_id, :metadata)
                RETURNING id, created_at, updated_at
            """
            ),
            {
                "job_type": JobType.WORKFLOW.value,
                "status": JobStatus.PENDING.value,
                "priority": int(options.priority),
                "input_artifact_id": artifact_id,
                "metadata": json.dumps(options.model_dump()),
            },
        )
        job_row = job_result.fetchone()
        job_id = job_row[0]
        job_created_at = job_row[1]
        job_updated_at = job_row[2]
        db.commit()

        background_tasks.add_task(_enqueue_job_task, job_id, JobType.WORKFLOW.value)

        if event_bus is not None and hasattr(event_bus, "publish"):
            event_bus.publish(
                "workflow",
                "workflow.job.created",
                {"job_id": str(job_id), "status": JobStatus.PENDING.value},
            )

        return JobResponse(
            id=job_id,
            status=JobStatus.PENDING,
            job_type=JobType.WORKFLOW,
            priority=int(options.priority),
            input_artifact_id=artifact_id,
            output_artifact_id=None,
            error_message=None,
            metadata=options.model_dump(),
            created_at=job_created_at,
            updated_at=job_updated_at,
            started_at=None,
            completed_at=None,
            input_artifact=ArtifactInfo(
                id=artifact_id,
                artifact_type=ArtifactType.WORKFLOW_BUNDLE,
                storage_type=StorageType.S3,
                storage_uri=storage_uri,
                file_name=stored_name,
                file_size=file_size,
                mime_type="application/zip",
                created_at=artifact_created_at,
            ),
            output_artifact=None,
        )
    finally:
        db.close()
