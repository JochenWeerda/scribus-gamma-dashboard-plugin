"""Tests für Database Models."""

import pytest
from datetime import datetime
from uuid import uuid4
from packages.common.db_models import (
    Job, Artifact, JobLog, Page,
    JobStatus, JobType, ArtifactType, StorageType
)


def test_job_creation(db_session):
    """Test: Job erstellen."""
    job = Job(
        id=uuid4(),
        job_type=JobType.COMPILE,
        status=JobStatus.QUEUED,
    )
    db_session.add(job)
    db_session.commit()
    
    assert job.id is not None
    assert job.job_type == JobType.COMPILE
    assert job.status == JobStatus.QUEUED
    assert job.created_at is not None


def test_artifact_creation(db_session):
    """Test: Artifact erstellen."""
    artifact = Artifact(
        id=uuid4(),
        artifact_type=ArtifactType.LAYOUT_JSON,
        storage_type=StorageType.S3,
        storage_uri="s3://bucket/layout.json",
        file_name="layout.json",
        file_size=1024,
        mime_type="application/json",
    )
    db_session.add(artifact)
    db_session.commit()
    
    assert artifact.id is not None
    assert artifact.artifact_type == ArtifactType.LAYOUT_JSON
    assert artifact.file_size == 1024


def test_job_with_artifact(db_session):
    """Test: Job mit Artifact verknüpfen."""
    artifact = Artifact(
        id=uuid4(),
        artifact_type=ArtifactType.LAYOUT_JSON,
        storage_type=StorageType.S3,
        storage_uri="s3://bucket/layout.json",
        file_name="layout.json",
        file_size=1024,
    )
    db_session.add(artifact)
    db_session.flush()
    
    job = Job(
        id=uuid4(),
        job_type=JobType.COMPILE,
        status=JobStatus.QUEUED,
        input_artifact_id=artifact.id,
    )
    db_session.add(job)
    db_session.commit()
    
    assert job.input_artifact_id == artifact.id
    assert job.input_artifact is not None
    assert job.input_artifact.file_name == "layout.json"


def test_job_logs(db_session):
    """Test: Job-Logs erstellen."""
    job = Job(
        id=uuid4(),
        job_type=JobType.COMPILE,
        status=JobStatus.RUNNING,
    )
    db_session.add(job)
    db_session.flush()
    
    log = JobLog(
        id=uuid4(),
        job_id=job.id,
        log_level="INFO",
        message="Test log message",
        context='{"key": "value"}',
    )
    db_session.add(log)
    db_session.commit()
    
    assert log.job_id == job.id
    assert log.log_level == "INFO"
    assert job.logs is not None
    assert len(job.logs) == 1


def test_page_creation(db_session):
    """Test: Page erstellen."""
    job = Job(
        id=uuid4(),
        job_type=JobType.EXPORT,
        status=JobStatus.COMPLETED,
    )
    db_session.add(job)
    db_session.flush()
    
    page = Page(
        id=uuid4(),
        job_id=job.id,
        page_number=1,
        master_page="Default",
        object_count=10,
    )
    db_session.add(page)
    db_session.commit()
    
    assert page.job_id == job.id
    assert page.page_number == 1
    assert page.object_count == 10
    assert job.pages is not None
    assert len(job.pages) == 1

