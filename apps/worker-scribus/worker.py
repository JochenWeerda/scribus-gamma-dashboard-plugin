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
from packages.workflow import WorkflowConfig, WorkflowOrchestrator
# These imports should work both when the file is imported as a module (`worker`)
# and when imported as a package (`apps.worker-scribus`).
try:
    from .build_metadata import generate_build_metadata  # type: ignore
except Exception:
    from build_metadata import generate_build_metadata  # type: ignore

try:
    from .retry import retry_on_failure  # type: ignore
except Exception:
    from retry import retry_on_failure  # type: ignore

# Database
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://sla_user:sla_password@localhost:5432/sla_pipeline")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Redis Queue
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis_conn = redis.from_url(REDIS_URL)

# Artifact Store
artifact_store = get_artifact_store()

try:
    event_bus = get_event_bus()
except Exception:
    event_bus = None


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
            str(job_uuid),
            str(output_artifact_id),
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
        if event_bus is not None and hasattr(event_bus, "publish"):
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
        if event_bus is not None and hasattr(event_bus, "publish"):
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


def _insert_artifact_row(
    db,
    *,
    artifact_type: ArtifactType,
    storage_uri: str,
    file_name: str,
    file_size: int,
    mime_type: str,
    checksum_md5: str,
    metadata: dict | None = None,
):
    result = db.execute(
        text(
            """
            INSERT INTO artifacts (
                artifact_type, storage_type, storage_uri, file_name, file_size,
                mime_type, checksum_md5, metadata
            )
            VALUES (:type, :storage_type, :uri, :file_name, :file_size, :mime_type, :checksum, :metadata)
            RETURNING id
        """
        ),
        {
            "type": artifact_type.value,
            "storage_type": "s3",
            "uri": storage_uri,
            "file_name": file_name,
            "file_size": file_size,
            "mime_type": mime_type,
            "checksum": checksum_md5,
            "metadata": json.dumps(metadata or {}),
        },
    )
    return result.fetchone()[0]


def _zip_dir(src_dir: Path, zip_path: Path) -> None:
    import zipfile

    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in src_dir.rglob("*"):
            if p.is_file():
                zf.write(p, arcname=str(p.relative_to(src_dir)).replace("\\", "/"))


def process_workflow_job(job_id: str):
    """
    Prozessiert einen Workflow-Job.

    Input: workflow bundle ZIP (manifest.json + json/*.json + optional gamma/*.zip + optional project_init.json)
    Output: zipped workflow outputs uploaded as ArtifactType.WORKFLOW_REPORT.
    """

    db = SessionLocal()
    job_uuid = UUID(job_id)

    try:
        db.execute(
            text("UPDATE jobs SET status = :status, started_at = NOW() WHERE id = :job_id"),
            {"status": JobStatus.RUNNING.value, "job_id": job_uuid},
        )
        db.commit()
        _log_job(db, job_uuid, "INFO", f"Job {job_id} started: Workflow")

        result = db.execute(
            text("SELECT input_artifact_id, metadata FROM jobs WHERE id = :job_id"),
            {"job_id": job_uuid},
        )
        row = result.fetchone()
        if not row or not row[0]:
            raise ValueError(f"Job {job_id} hat kein input_artifact_id")

        input_artifact_id = row[0]
        job_metadata_raw = row[1]
        if isinstance(job_metadata_raw, dict):
            job_metadata = job_metadata_raw
        elif isinstance(job_metadata_raw, str):
            try:
                job_metadata = json.loads(job_metadata_raw) if job_metadata_raw else {}
            except Exception:
                job_metadata = {}
        else:
            job_metadata = {}

        result = db.execute(
            text("SELECT storage_uri, file_name FROM artifacts WHERE id = :artifact_id"),
            {"artifact_id": input_artifact_id},
        )
        row = result.fetchone()
        if not row:
            raise ValueError(f"Artefakt {input_artifact_id} nicht gefunden")
        storage_uri, in_file_name = row[0], row[1]

        bundle_bytes = _download_artifact_with_retry(artifact_store, storage_uri)

        with tempfile.TemporaryDirectory(prefix="workflow_") as tmp:
            tmp_path = Path(tmp)
            in_zip = tmp_path / "bundle.zip"
            in_zip.write_bytes(bundle_bytes)

            import zipfile

            extract_root = tmp_path / "input"
            extract_root.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(in_zip, "r") as zf:
                zf.extractall(extract_root)

            # locate manifest.json
            manifests = list(extract_root.rglob("manifest.json"))
            if not manifests:
                raise ValueError("bundle missing manifest.json")
            manifest_path = manifests[0]
            pptx_root = manifest_path.parent

            # locate optional project_init.json
            project_init_path = None
            for cand in ["project_init.json", "project_init.json.template"]:
                found = list(extract_root.rglob(cand))
                if found:
                    project_init_path = found[0]
                    break

            # gamma dir: collect any *.zip (excluding bundle) into a dedicated folder
            gamma_dir = tmp_path / "gamma"
            gamma_dir.mkdir(parents=True, exist_ok=True)
            for zp in extract_root.rglob("*.zip"):
                try:
                    if zp.resolve() == in_zip.resolve():
                        continue
                except Exception:
                    pass
                # Gamma exports are expected to be named <pptx_stem>.zip
                target = gamma_dir / zp.name
                if target.exists():
                    continue
                try:
                    target.write_bytes(zp.read_bytes())
                except Exception:
                    continue

            out_root = tmp_path / "out"
            layout_out = out_root / "layout_json"
            variants_out = out_root / "layout_json_variants"
            gamma_crops_out = out_root / "gamma_crops"
            quality_out = out_root / "quality"
            render_out = out_root / "render"
            resume_path = out_root / "workflow_state.json"

            cfg = WorkflowConfig(
                manifest_path=manifest_path,
                pptx_root=pptx_root,
                layout_out=layout_out,
                variants_out=variants_out,
                project_init=project_init_path,
                resume_path=resume_path,
                generate_variants=bool(job_metadata.get("generate_variants", True)),
                gamma_png_dir=gamma_dir if gamma_dir.exists() and any(gamma_dir.glob("*.zip")) else None,
                gamma_crops_out=gamma_crops_out,
                gamma_sync=bool(job_metadata.get("gamma_sync", False)),
                gamma_crop_kinds=tuple(job_metadata.get("gamma_crop_kinds") or ("infobox",)),
                gamma_attach_to_variants=bool(job_metadata.get("gamma_attach_to_variants", False)),
                gamma_attach_kinds=tuple(job_metadata.get("gamma_attach_kinds") or ("image_box",)),
                quality_check=bool(job_metadata.get("quality_check", True)),
                quality_on_variants=bool(job_metadata.get("quality_on_variants", True)),
                quality_out=quality_out,
                quality_checks=tuple(job_metadata.get("quality_checks") or ("preflight", "amazon")),
                render=bool(job_metadata.get("render", False)),
                render_on_variants=bool(job_metadata.get("render_on_variants", True)),
                render_out=render_out,
                render_pdf=bool(job_metadata.get("render_pdf", True)),
                render_png=bool(job_metadata.get("render_png", True)),
                agents_enabled=bool(job_metadata.get("agents_enabled", False)),
                agent_steps=tuple(job_metadata.get("agent_steps") or ("SemanticEnricher", "LayoutDesigner", "QualityCritic")),
                agent_seed=job_metadata.get("agent_seed"),
                agent_version=str(job_metadata.get("agent_version") or "v1"),
                agent_simulate=bool(job_metadata.get("agent_simulate", False)),
                force=bool(job_metadata.get("force", False)),
                retry_max=1,
            )

            wf = WorkflowOrchestrator(cfg)
            wf.run()

            publish_artifacts = bool(job_metadata.get("publish_artifacts", True))
            published = {"crops": [], "variants": [], "layouts": [], "quality": None}

            if publish_artifacts:
                # Upload gamma crops and rewrite variant json imageUrl to /v1/artifacts/{id}
                crop_id_by_path: dict[str, str] = {}
                for png in gamma_crops_out.rglob("*.png"):
                    data = png.read_bytes()
                    uri, fname, fsize = _upload_artifact_with_retry(
                        artifact_store,
                        data,
                        ArtifactType.PNG,
                        file_name=f"gamma_crop_{job_id}_{png.name}",
                        mime_type="image/png",
                    )
                    checksum = artifact_store.compute_checksum(data)
                    aid = _insert_artifact_row(
                        db,
                        artifact_type=ArtifactType.PNG,
                        storage_uri=uri,
                        file_name=fname,
                        file_size=fsize,
                        mime_type="image/png",
                        checksum_md5=checksum,
                        metadata={"job_id": job_id, "kind": "gamma_crop", "path": str(png.relative_to(out_root)).replace("\\", "/")},
                    )
                    crop_id_by_path[str(png)] = str(aid)
                    published["crops"].append({"path": str(png.relative_to(out_root)).replace("\\", "/"), "artifact_id": str(aid)})

                def _rewrite_json_images(path: Path):
                    try:
                        doc = json.loads(path.read_text(encoding="utf-8"))
                    except Exception:
                        return
                    changed = False
                    for page in doc.get("pages", []) or []:
                        for obj in page.get("objects", []) or []:
                            if obj.get("type") != "image":
                                continue
                            if not obj.get("gammaCrop"):
                                continue
                            url = obj.get("imageUrl")
                            if not url:
                                continue
                            local = url
                            # resolve relative paths against out_root
                            try:
                                if not Path(local).is_absolute():
                                    local = str((out_root / local).resolve())
                            except Exception:
                                pass
                            aid = crop_id_by_path.get(local)
                            if aid:
                                obj["imageUrl"] = f"/v1/artifacts/{aid}"
                                obj["gammaCropArtifactId"] = aid
                                changed = True
                    if changed:
                        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

                for vj in variants_out.rglob("*.json"):
                    _rewrite_json_images(vj)

                # Upload updated layout_json + variants + quality report
                for lp in layout_out.rglob("*.json"):
                    data = lp.read_bytes()
                    uri, fname, fsize = _upload_artifact_with_retry(
                        artifact_store,
                        data,
                        ArtifactType.LAYOUT_JSON,
                        file_name=f"workflow_layout_{job_id}_{lp.name}",
                        mime_type="application/json",
                    )
                    checksum = artifact_store.compute_checksum(data)
                    aid = _insert_artifact_row(
                        db,
                        artifact_type=ArtifactType.LAYOUT_JSON,
                        storage_uri=uri,
                        file_name=fname,
                        file_size=fsize,
                        mime_type="application/json",
                        checksum_md5=checksum,
                        metadata={"job_id": job_id, "kind": "layout_json"},
                    )
                    published["layouts"].append(str(aid))

                for vp in variants_out.rglob("*.json"):
                    data = vp.read_bytes()
                    uri, fname, fsize = _upload_artifact_with_retry(
                        artifact_store,
                        data,
                        ArtifactType.LAYOUT_JSON,
                        file_name=f"workflow_variant_{job_id}_{vp.name}",
                        mime_type="application/json",
                    )
                    checksum = artifact_store.compute_checksum(data)
                    aid = _insert_artifact_row(
                        db,
                        artifact_type=ArtifactType.LAYOUT_JSON,
                        storage_uri=uri,
                        file_name=fname,
                        file_size=fsize,
                        mime_type="application/json",
                        checksum_md5=checksum,
                        metadata={"job_id": job_id, "kind": "variant_json"},
                    )
                    published["variants"].append(str(aid))

                qrep = quality_out / "quality_report.json"
                if qrep.exists():
                    data = qrep.read_bytes()
                    uri, fname, fsize = _upload_artifact_with_retry(
                        artifact_store,
                        data,
                        ArtifactType.PREFLIGHT,
                        file_name=f"workflow_quality_{job_id}.json",
                        mime_type="application/json",
                    )
                    checksum = artifact_store.compute_checksum(data)
                    aid = _insert_artifact_row(
                        db,
                        artifact_type=ArtifactType.PREFLIGHT,
                        storage_uri=uri,
                        file_name=fname,
                        file_size=fsize,
                        mime_type="application/json",
                        checksum_md5=checksum,
                        metadata={"job_id": job_id, "kind": "quality_report"},
                    )
                    published["quality"] = str(aid)

                # Upload render outputs (PDF/PNG placeholders or real exports)
                published["renders"] = []
                max_png = int(os.environ.get("MAX_RENDER_PREVIEW_UPLOADS", "10"))

                for rp in render_out.rglob("*.pdf"):
                    data = rp.read_bytes()
                    uri, fname, fsize = _upload_artifact_with_retry(
                        artifact_store,
                        data,
                        ArtifactType.PDF,
                        file_name=f"workflow_render_{job_id}_{rp.name}",
                        mime_type="application/pdf",
                    )
                    checksum = artifact_store.compute_checksum(data)
                    aid = _insert_artifact_row(
                        db,
                        artifact_type=ArtifactType.PDF,
                        storage_uri=uri,
                        file_name=fname,
                        file_size=fsize,
                        mime_type="application/pdf",
                        checksum_md5=checksum,
                        metadata={"job_id": job_id, "kind": "render_pdf"},
                    )
                    published["renders"].append(str(aid))

                png_uploaded = 0
                for rp in render_out.rglob("*.png"):
                    if png_uploaded >= max_png:
                        break
                    data = rp.read_bytes()
                    uri, fname, fsize = _upload_artifact_with_retry(
                        artifact_store,
                        data,
                        ArtifactType.PNG,
                        file_name=f"workflow_render_{job_id}_{rp.name}",
                        mime_type="image/png",
                    )
                    checksum = artifact_store.compute_checksum(data)
                    aid = _insert_artifact_row(
                        db,
                        artifact_type=ArtifactType.PNG,
                        storage_uri=uri,
                        file_name=fname,
                        file_size=fsize,
                        mime_type="image/png",
                        checksum_md5=checksum,
                        metadata={"job_id": job_id, "kind": "render_png"},
                    )
                    published["renders"].append(str(aid))
                    png_uploaded += 1

            # Always upload a single bundle of the output dir
            out_zip = tmp_path / f"workflow_{job_id}.zip"
            _zip_dir(out_root, out_zip)
            out_data = out_zip.read_bytes()
            out_uri, out_fname, out_size = _upload_artifact_with_retry(
                artifact_store,
                out_data,
                ArtifactType.WORKFLOW_REPORT,
                file_name=f"workflow_{job_id}.zip",
                mime_type="application/zip",
            )
            out_checksum = artifact_store.compute_checksum(out_data)
            out_artifact_id = _insert_artifact_row(
                db,
                artifact_type=ArtifactType.WORKFLOW_REPORT,
                storage_uri=out_uri,
                file_name=out_fname,
                file_size=out_size,
                mime_type="application/zip",
                checksum_md5=out_checksum,
                metadata={"job_id": job_id, "kind": "workflow_report", "input_bundle": in_file_name, "published": published},
            )

            db.execute(
                text(
                    """
                    UPDATE jobs
                    SET status = :status, completed_at = NOW(), output_artifact_id = :out_id, metadata = :metadata
                    WHERE id = :job_id
                """
                ),
                {
                    "status": JobStatus.COMPLETED.value,
                    "out_id": out_artifact_id,
                    "job_id": job_uuid,
                    "metadata": json.dumps({**job_metadata, "published": published, "output_artifact_id": str(out_artifact_id)}),
                },
            )
            db.commit()

            if event_bus is not None and hasattr(event_bus, "publish"):
                event_bus.publish(
                    "workflow",
                    "workflow.job.completed",
                    {"job_id": job_id, "output_artifact_id": str(out_artifact_id)},
                )

            _log_job(db, job_uuid, "INFO", f"Workflow completed: output -> {out_uri}")

    except Exception as e:
        db.rollback()
        error_msg = str(e)
        _log_job(db, job_uuid, "ERROR", f"Workflow failed: {error_msg}", {"error": error_msg})
        db.execute(
            text(
                """
                UPDATE jobs
                SET status = :status, error_message = :error, completed_at = NOW()
                WHERE id = :job_id
            """
            ),
            {"status": JobStatus.FAILED.value, "error": error_msg, "job_id": job_uuid},
        )
        db.commit()

        if event_bus is not None and hasattr(event_bus, "publish"):
            event_bus.publish("workflow", "workflow.job.failed", {"job_id": job_id, "error": error_msg})

        print(f"[ERROR] Workflow job {job_id} failed: {error_msg}", file=sys.stderr)
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
            if event_bus is not None and hasattr(event_bus, "publish"):
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
    worker = Worker(["compile", "export", "workflow"], connection=redis_conn)
    worker.work()
