"""Health Check Utilities."""

import time
from typing import Dict, Any
from sqlalchemy import create_engine, text
import redis


def check_database(db_url: str) -> Dict[str, Any]:
    """Prüft Datenbank-Verbindung."""
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "latency_ms": 0}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_redis(redis_url: str) -> Dict[str, Any]:
    """Prüft Redis-Verbindung."""
    try:
        start = time.time()
        conn = redis.from_url(redis_url)
        conn.ping()
        latency_ms = int((time.time() - start) * 1000)
        return {"status": "ok", "latency_ms": latency_ms}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_minio(endpoint: str, access_key: str, secret_key: str, bucket: str, secure: bool) -> Dict[str, Any]:
    """Prüft MinIO-Verbindung."""
    try:
        from minio import Minio
        start = time.time()
        client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        exists = client.bucket_exists(bucket)
        latency_ms = int((time.time() - start) * 1000)
        return {
            "status": "ok" if exists else "warning",
            "bucket_exists": exists,
            "latency_ms": latency_ms
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def get_health_status(db_url: str, redis_url: str, minio_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gibt vollständigen Health-Status zurück.
    
    Returns:
        {
            "status": "ok" | "degraded" | "error",
            "checks": {
                "database": {...},
                "redis": {...},
                "minio": {...}
            }
        }
    """
    checks = {
        "database": check_database(db_url),
        "redis": check_redis(redis_url),
        "minio": check_minio(**minio_config),
    }
    
    # Bestimme Gesamt-Status
    statuses = [check.get("status") for check in checks.values()]
    if "error" in statuses:
        overall_status = "error"
    elif "warning" in statuses:
        overall_status = "degraded"
    else:
        overall_status = "ok"
    
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": time.time(),
    }

