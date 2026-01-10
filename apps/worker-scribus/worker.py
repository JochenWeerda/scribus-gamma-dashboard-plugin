"""Worker-Scribus - Headless Export (PNG/PDF) via Scribus."""

import json
import os
import sys
import tempfile
import subprocess
from uuid import UUID
from pathlib import Path

import redis
from rq import Worker, Queue
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from packages.artifact_store import get_artifact_store
from packages.common.models import ArtifactType, JobStatus
from packages.sla_compiler import compile_layout_to_sla
from packages.event_bus import get_event_bus
from build_metadata import generate_build_metadata
from retry import retry_on_failure

# Database
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://sla_user:sla_password@localhost:5432/sla_pipeline")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Redis Queue
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis_conn = redis.from_url(REDIS_URL)

# Artifact Store
artifact_store = get_artifact_store()


def _log_job(db, job_id: UUID, level: str, message: str, context: dict = None):
    """Loggt eine Nachricht für einen Job."""
    try:
        db.execute(
            text("""
                INSERT INTO job_logs (job_id, log_level, message, context)
                VALUES (:job_id, :level, :message, :context)
            """),
            {
                "job_id": job_id,
                "level": level,
                "message": message,
                "context": json.dumps(context) if context else None,
            }
        )
        db.commit()
    except Exception as e:
        print(f"[WARN] Failed to log: {e}", file=sys.stderr)


@retry_on_failure(max_retries=3, backoff_factor=2.0, exceptions=(ConnectionError, TimeoutError, IOError))
def _download_artifact_with_retry(artifact_store, storage_uri: str) -> bytes:
    """Lädt Artefakt mit Retry-Logic."""
    return artifact_store.download(storage_uri)


@retry_on_failure(max_retries=3, backoff_factor=2.0, exceptions=(ConnectionError, TimeoutError, IOError))
def _upload_artifact_with_retry(artifact_store, data: bytes, artifact_type, file_name: str, mime_type: str = None):
    """Lädt Artefakt hoch mit Retry-Logic."""
    return artifact_store.upload(data, artifact_type, file_name=file_name, mime_type=mime_type)


def process_compile_job(job_id: str):
    """
    Prozessiert einen Kompilierungs-Job.
    
    1. Lädt Layout-JSON aus Artefakt
    2. Kompiliert JSON → SLA
    3. Speichert SLA als Artefakt
    4. Enqueued Export-Job
    """
    db = SessionLocal()
    job_uuid = UUID(job_id)
    
    try:
        # 1. Job-Status auf "running" setzen
        db.execute(
            text("UPDATE jobs SET status = :status, started_at = NOW() WHERE id = :job_id"),
            {"status": JobStatus.RUNNING.value, "job_id": job_uuid}
        )
        db.commit()
        _log_job(db, job_uuid, "INFO", f"Job {job_id} started: Compilation")
        
        # 2. Input-Artefakt laden
        result = db.execute(
            text("SELECT input_artifact_id FROM jobs WHERE id = :job_id"),
            {"job_id": job_uuid}
        )
        row = result.fetchone()
        if not row or not row[0]:
            raise ValueError(f"Job {job_id} hat kein input_artifact_id")
        
        input_artifact_id = row[0]
        
        # Artefakt-URI laden
        result = db.execute(
            text("SELECT storage_uri FROM artifacts WHERE id = :artifact_id"),
            {"artifact_id": input_artifact_id}
        )
        row = result.fetchone()
        if not row:
            raise ValueError(f"Artefakt {input_artifact_id} nicht gefunden")
        
        storage_uri = row[0]
        
        # JSON aus Artefakt laden (mit Retry)
        json_bytes = _download_artifact_with_retry(artifact_store, storage_uri)
        layout_json = json.loads(json_bytes.decode("utf-8"))
        _log_job(db, job_uuid, "INFO", f"Loaded layout JSON: {len(json_bytes)} bytes")
        
        # 3. Kompilierung (JSON → SLA)
        import time
        compile_start = time.time()
        sla_xml_bytes = compile_layout_to_sla(layout_json)
        compile_time_ms = int((time.time() - compile_start) * 1000)
        _log_job(db, job_uuid, "INFO", f"Compiled SLA: {len(sla_xml_bytes)} bytes in {compile_time_ms}ms")
        
        # 3a. Build-Metadaten generieren
        build_metadata = generate_build_metadata(layout_json, sla_xml_bytes, compile_time_ms)
        build_metadata_bytes = json.dumps(build_metadata, indent=2).encode("utf-8")
        
        # Build-Metadaten als Artefakt speichern (optional, mit Retry)
        build_file_name = f"build_{job_id}.json"
        build_storage_uri, _, build_size = _upload_artifact_with_retry(
            artifact_store,
            build_metadata_bytes,
            ArtifactType.LAYOUT_JSON,
            file_name=build_file_name,
            mime_type="application/json"
        )
        _log_job(db, job_uuid, "INFO", f"Build metadata saved: {build_storage_uri}")
        
        # 4. SLA als Artefakt speichern (mit Retry)
        file_name = f"layout_{job_id}.sla"
        output_storage_uri, file_name, file_size = _upload_artifact_with_retry(
            artifact_store,
            sla_xml_bytes,
            ArtifactType.SLA,
            file_name=file_name,
            mime_type="application/x-scribus"
        )
        checksum = artifact_store.compute_checksum(sla_xml_bytes)
        
        # Artefakt in DB speichern
        result = db.execute(
            text("""
                INSERT INTO artifacts (
                    artifact_type, storage_type, storage_uri, file_name, file_size,
                    mime_type, checksum_md5
                )
                VALUES (:type, :storage_type, :uri, :file_name, :file_size, :mime_type, :checksum)
                RETURNING id
            """),
            {
                "type": ArtifactType.SLA.value,
                "storage_type": "s3",
                "uri": output_storage_uri,
                "file_name": file_name,
                "file_size": file_size,
                "mime_type": "application/x-scribus",
                "checksum": checksum,
            }
        )
        output_artifact_id = result.fetchone()[0]
        _log_job(db, job_uuid, "INFO", f"SLA artifact saved: {output_storage_uri}")
        
        # 5. Job-Status aktualisieren (noch nicht completed, wartet auf Export)
        db.execute(
            text("""
                UPDATE jobs 
                SET output_artifact_id = :output_id
                WHERE id = :job_id
            """),
            {
                "output_id": output_artifact_id,
                "job_id": job_uuid,
            }
        )
        
        # 6. Export-Job enqueuen (PNG/PDF)
        export_queue = Queue("export", connection=redis_conn)
        export_queue.enqueue(
            "worker.process_export_job",
            job_id=str(job_uuid),
            sla_artifact_id=str(output_artifact_id),
            job_timeout="20m"
        )
        _log_job(db, job_uuid, "INFO", "Export job enqueued")
        
        # 7. Pages erstellen (Metadaten)
        pages = layout_json.get("pages", [])
        for page_data in pages:
            page_num = page_data.get("pageNumber", 1)
            objects = page_data.get("objects", [])
            
            db.execute(
                text("""
                    INSERT INTO pages (job_id, page_number, master_page, object_count)
                    VALUES (:job_id, :page_num, :master_page, :obj_count)
                """),
                {
                    "job_id": job_uuid,
                    "page_num": page_num,
                    "master_page": page_data.get("masterPage"),
                    "obj_count": len(objects),
                }
            )
        
        db.commit()
        
        # Event-Bus: Job compilation completed (wenn aktiviert)
        if hasattr(event_bus, 'publish'):
            event_bus.publish(
                "jobs",
                "job.compilation.completed",
                {
                    "job_id": job_id,
                    "sla_artifact_id": str(output_artifact_id),
                    "output_uri": output_storage_uri,
                }
            )
        
        print(f"[OK] Job {job_id} compilation completed: SLA -> {output_storage_uri}")
    
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        _log_job(db, job_uuid, "ERROR", f"Compilation failed: {error_msg}", {"error": error_msg})
        
        # Fehler in DB speichern
        db.execute(
            text("""
                UPDATE jobs 
                SET status = :status, error_message = :error, completed_at = NOW()
                WHERE id = :job_id
            """),
            {
                "status": JobStatus.FAILED.value,
                "error": error_msg,
                "job_id": job_uuid,
            }
        )
        db.commit()
        
        # Event-Bus: Job failed (wenn aktiviert)
        if hasattr(event_bus, 'publish'):
            event_bus.publish(
                "jobs",
                "job.failed",
                {
                    "job_id": job_id,
                    "error": error_msg,
                }
            )
        
        print(f"[ERROR] Job {job_id} failed: {error_msg}", file=sys.stderr)
        raise
    
    finally:
        db.close()


def process_export_job(job_id: str, sla_artifact_id: str):
    """
    Prozessiert einen Export-Job (PNG/PDF).
    
    1. Lädt SLA aus Artefakt
    2. Führt Preflight durch
    3. Exportiert PNG (72 DPI) pro Seite
    4. Exportiert PDF (300 DPI)
    5. Speichert Artefakte
    """
    db = SessionLocal()
    job_uuid = UUID(job_id)
    sla_uuid = UUID(sla_artifact_id)
    
    try:
        _log_job(db, job_uuid, "INFO", f"Export job started for SLA {sla_artifact_id}")
        
        # 1. SLA-Artefakt laden
        result = db.execute(
            text("SELECT storage_uri FROM artifacts WHERE id = :artifact_id"),
            {"artifact_id": sla_uuid}
        )
        row = result.fetchone()
        if not row:
            raise ValueError(f"SLA-Artefakt {sla_artifact_id} nicht gefunden")
        
        sla_storage_uri = row[0]
        sla_bytes = artifact_store.download(sla_storage_uri)
        
        # 2. Temporäres Verzeichnis für Export
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            sla_path = temp_path / f"layout_{job_id}.sla"
            output_dir = temp_path / "output"
            output_dir.mkdir()
            
            # SLA-Datei speichern
            sla_path.write_bytes(sla_bytes)
            _log_job(db, job_uuid, "INFO", f"SLA downloaded: {len(sla_bytes)} bytes")
            
            # 3. Preflight (vereinfacht - kann erweitert werden)
            # TODO: Echter Preflight mit Scribus Python API
            
            # 4. Export via Scribus (Dummy für MVP - wird durch echten Export ersetzt)
            # Für MVP: Erstelle Dummy-PNG/PDF, damit die Pipeline funktioniert
            pdf_path = output_dir / f"output_{job_id}.pdf"
            png_paths = []
            
            # Dummy-Export (für MVP)
            # In Production: Hier würde Scribus Python API aufgerufen werden
            _log_job(db, job_uuid, "WARN", "Using dummy export - Scribus export not implemented yet")
            
            # Erstelle Dummy-PDF (leeres PDF)
            try:
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import A4
                
                c = canvas.Canvas(str(pdf_path), pagesize=A4)
                c.drawString(100, 750, f"Placeholder PDF for Job {job_id}")
                c.drawString(100, 730, "Scribus export not yet implemented")
                c.save()
                _log_job(db, job_uuid, "INFO", f"Dummy PDF created: {pdf_path}")
            except ImportError:
                # Fallback: Leere Datei
                pdf_path.write_bytes(b"")
            
            # 5. PDF als Artefakt speichern (mit Retry)
            pdf_bytes = pdf_path.read_bytes()
            pdf_storage_uri, pdf_file_name, pdf_size = _upload_artifact_with_retry(
                artifact_store,
                pdf_bytes,
                ArtifactType.PDF,
                file_name=f"output_{job_id}.pdf",
                mime_type="application/pdf"
            )
            pdf_checksum = artifact_store.compute_checksum(pdf_bytes)
            
            result = db.execute(
                text("""
                    INSERT INTO artifacts (
                        artifact_type, storage_type, storage_uri, file_name, file_size,
                        mime_type, checksum_md5
                    )
                    VALUES (:type, :storage_type, :uri, :file_name, :file_size, :mime_type, :checksum)
                    RETURNING id
                """),
                {
                    "type": ArtifactType.PDF.value,
                    "storage_type": "s3",
                    "uri": pdf_storage_uri,
                    "file_name": pdf_file_name,
                    "file_size": pdf_size,
                    "mime_type": "application/pdf",
                    "checksum": pdf_checksum,
                }
            )
            pdf_artifact_id = result.fetchone()[0]
            
            # 6. PNG-Previews (Dummy)
            # In Production: Hier würden echte PNG-Exports gespeichert werden
            page_count = 1  # TODO: Aus SLA ermitteln
            
            for page_num in range(1, page_count + 1):
                png_path = output_dir / f"preview_{job_id}_p{page_num:04d}.png"
                # Dummy PNG (1x1 transparent)
                png_path.write_bytes(
                    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
                )
                
                png_bytes = png_path.read_bytes()
                png_storage_uri, png_file_name, png_size = _upload_artifact_with_retry(
                    artifact_store,
                    png_bytes,
                    ArtifactType.PNG,
                    file_name=f"preview_{job_id}_p{page_num:04d}.png",
                    mime_type="image/png"
                )
                png_checksum = artifact_store.compute_checksum(png_bytes)
                
                png_result = db.execute(
                    text("""
                        INSERT INTO artifacts (
                            artifact_type, storage_type, storage_uri, file_name, file_size,
                            mime_type, checksum_md5
                        )
                        VALUES (:type, :storage_type, :uri, :file_name, :file_size, :mime_type, :checksum)
                        RETURNING id
                    """),
                    {
                        "type": ArtifactType.PNG.value,
                        "storage_type": "s3",
                        "uri": png_storage_uri,
                        "file_name": png_file_name,
                        "file_size": png_size,
                        "mime_type": "image/png",
                        "checksum": png_checksum,
                    }
                )
                png_artifact_id = png_result.fetchone()[0]
                png_paths.append({"page": page_num, "artifact_id": str(png_artifact_id), "uri": png_storage_uri})
                
                # Update page record
                db.execute(
                    text("""
                        UPDATE pages 
                        SET png_artifact_id = :png_id
                        WHERE job_id = :job_id AND page_number = :page_num
                    """),
                    {
                        "png_id": png_artifact_id,
                        "job_id": job_uuid,
                        "page_num": page_num,
                    }
                )
            
            # 7. Job-Status aktualisieren
            db.execute(
                text("""
                    UPDATE jobs 
                    SET status = :status, completed_at = NOW()
                    WHERE id = :job_id
                """),
                {
                    "status": JobStatus.COMPLETED.value,
                    "job_id": job_uuid,
                }
            )
            
            db.commit()
            
            # Event-Bus: Export completed (wenn aktiviert)
            if hasattr(event_bus, 'publish'):
                event_bus.publish(
                    "jobs",
                    "job.export.completed",
                    {
                        "job_id": job_id,
                        "pdf_uri": pdf_storage_uri,
                        "png_count": len(png_paths),
                    }
                )
            
            _log_job(db, job_uuid, "INFO", f"Export completed: PDF -> {pdf_storage_uri}, {len(png_paths)} PNGs")
            print(f"[OK] Export job {job_id} completed: PDF -> {pdf_storage_uri}")
    
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        _log_job(db, job_uuid, "ERROR", f"Export failed: {error_msg}", {"error": error_msg})
        
        db.execute(
            text("""
                UPDATE jobs 
                SET status = :status, error_message = :error, completed_at = NOW()
                WHERE id = :job_id
            """),
            {
                "status": JobStatus.FAILED.value,
                "error": error_msg,
                "job_id": job_uuid,
            }
        )
        db.commit()
        
        print(f"[ERROR] Export job {job_id} failed: {error_msg}", file=sys.stderr)
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    # RQ Worker starten
    worker = Worker(["compile", "export"], connection=redis_conn)
    worker.work()
