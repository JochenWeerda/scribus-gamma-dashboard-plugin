"""Artifact Store - MinIO/S3 Storage Implementation."""

import hashlib
import os
from io import BytesIO
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

try:
    from minio import Minio  # type: ignore
    from minio.error import S3Error  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    Minio = None  # type: ignore

    class S3Error(Exception):  # type: ignore
        pass

from packages.common.models import ArtifactType, StorageType


class ArtifactStore:
    """Artifact Store für MinIO/S3 Storage."""
    
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool = False
    ):
        """
        Initialisiert den Artifact Store.
        
        Args:
            endpoint: MinIO/S3 Endpoint (z.B. 'localhost:9000')
            access_key: Access Key
            secret_key: Secret Key
            bucket_name: Bucket-Name
            secure: HTTPS verwenden (default: False)
        """
        if Minio is None:
            raise RuntimeError(
                "minio Python package is not installed; set ARTIFACT_STORE=local for tests/dev "
                "or install dependencies from requirements.txt"
            )

        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.bucket_name = bucket_name
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """Stellt sicher, dass der Bucket existiert."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            raise RuntimeError(f"Fehler beim Erstellen des Buckets: {e}")
    
    def _get_object_path(self, artifact_type: ArtifactType, file_name: str) -> str:
        """Generiert einen Objekt-Pfad im Bucket."""
        return f"{artifact_type.value}/{file_name}"
    
    def upload(
        self,
        data: bytes,
        artifact_type: ArtifactType,
        file_name: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> tuple[str, str, int]:
        """
        Lädt Daten in den Store.
        
        Args:
            data: Binärdaten
            artifact_type: Artefakt-Typ
            file_name: Dateiname (optional, wird generiert wenn nicht gesetzt)
            mime_type: MIME-Typ (optional)
        
        Returns:
            (storage_uri, file_name, file_size): Storage-URI, Dateiname, Dateigröße
        """
        if file_name is None:
            file_name = f"{uuid4()}.bin"
        
        object_path = self._get_object_path(artifact_type, file_name)
        
        try:
            self.client.put_object(
                self.bucket_name,
                object_path,
                BytesIO(data),
                length=len(data),
                content_type=mime_type or "application/octet-stream"
            )
        except S3Error as e:
            raise RuntimeError(f"Fehler beim Hochladen: {e}")
        
        storage_uri = f"s3://{self.bucket_name}/{object_path}"
        return storage_uri, file_name, len(data)
    
    def download(self, storage_uri: str) -> bytes:
        """
        Lädt Daten aus dem Store.
        
        Args:
            storage_uri: Storage-URI (z.B. 's3://bucket/path/file.bin')
        
        Returns:
            Binärdaten
        """
        # Parse URI: s3://bucket/path
        if not storage_uri.startswith("s3://"):
            raise ValueError(f"Ungültige Storage-URI: {storage_uri}")
        
        uri_parts = storage_uri[5:].split("/", 1)
        if len(uri_parts) != 2:
            raise ValueError(f"Ungültige Storage-URI: {storage_uri}")
        
        bucket_name, object_path = uri_parts
        
        try:
            response = self.client.get_object(bucket_name, object_path)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            raise RuntimeError(f"Fehler beim Herunterladen: {e}")
    
    def delete(self, storage_uri: str):
        """
        Löscht Daten aus dem Store.
        
        Args:
            storage_uri: Storage-URI
        """
        if not storage_uri.startswith("s3://"):
            raise ValueError(f"Ungültige Storage-URI: {storage_uri}")
        
        uri_parts = storage_uri[5:].split("/", 1)
        if len(uri_parts) != 2:
            raise ValueError(f"Ungültige Storage-URI: {storage_uri}")
        
        bucket_name, object_path = uri_parts
        
        try:
            self.client.remove_object(bucket_name, object_path)
        except S3Error as e:
            raise RuntimeError(f"Fehler beim Löschen: {e}")
    
    def compute_checksum(self, data: bytes) -> str:
        """Berechnet MD5-Checksumme."""
        return hashlib.md5(data).hexdigest()


class LocalArtifactStore:
    """Minimal local artifact store used as fallback when MinIO deps are missing."""

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, artifact_type: ArtifactType, file_name: str) -> Path:
        p = self.base_dir / artifact_type.value / file_name
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def upload(
        self,
        data: bytes,
        artifact_type: ArtifactType,
        file_name: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> tuple[str, str, int]:
        if file_name is None:
            file_name = f"{uuid4()}.bin"
        path = self._path_for(artifact_type, file_name)
        path.write_bytes(data)
        return f"local://{artifact_type.value}/{file_name}", file_name, len(data)

    def download(self, storage_uri: str) -> bytes:
        if not storage_uri.startswith("local://"):
            raise ValueError(f"Ung\u00fcltige Storage-URI: {storage_uri}")
        rel = storage_uri[len("local://") :]
        path = self.base_dir / rel
        return path.read_bytes()

    def delete(self, storage_uri: str):
        if not storage_uri.startswith("local://"):
            raise ValueError(f"Ung\u00fcltige Storage-URI: {storage_uri}")
        rel = storage_uri[len("local://") :]
        path = self.base_dir / rel
        if path.exists():
            path.unlink()

    def compute_checksum(self, data: bytes) -> str:
        return hashlib.md5(data).hexdigest()


def get_artifact_store() -> ArtifactStore:
    """
    Erstellt einen ArtifactStore aus Umgebungsvariablen.
    
    Environment Variables:
        MINIO_ENDPOINT: Endpoint (z.B. 'localhost:9000')
        MINIO_ACCESS_KEY: Access Key
        MINIO_SECRET_KEY: Secret Key
        MINIO_BUCKET: Bucket-Name
        MINIO_SECURE: 'true' für HTTPS (default: 'false')
    """
    store_kind = (os.environ.get("ARTIFACT_STORE") or "").strip().lower()
    if store_kind == "local" or Minio is None:
        base_dir = os.environ.get("LOCAL_ARTIFACT_DIR", ".local_artifacts")
        return LocalArtifactStore(base_dir)  # type: ignore[return-value]

    endpoint = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
    access_key = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
    bucket_name = os.environ.get("MINIO_BUCKET", "sla-artifacts")
    secure = os.environ.get("MINIO_SECURE", "false").lower() == "true"

    return ArtifactStore(endpoint, access_key, secret_key, bucket_name, secure)

