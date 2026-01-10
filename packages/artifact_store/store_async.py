"""Asynchrones Artifact Store - Async I/O für bessere Performance."""

import asyncio
import hashlib
import os
from io import BytesIO
from typing import Optional, AsyncIterator
from uuid import uuid4

try:
    from minio import Minio
    from minio.error import S3Error
    HAS_MINIO = True
except ImportError:
    HAS_MINIO = False

from packages.common.models import ArtifactType, StorageType


class AsyncArtifactStore:
    """
    Asynchrones Artifact Store für Non-Blocking I/O.
    
    Verwendet Thread-Pool für synchrone MinIO-Operationen.
    """
    
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool = False
    ):
        """
        Initialisiert den Async Artifact Store.
        
        Args:
            endpoint: MinIO/S3 Endpoint
            access_key: Access Key
            secret_key: Secret Key
            bucket_name: Bucket-Name
            secure: HTTPS verwenden
        """
        if not HAS_MINIO:
            raise RuntimeError("minio package nicht verfügbar")
        
        self.sync_client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.bucket_name = bucket_name
        self._ensure_bucket()
        self._executor = None  # Wird bei Bedarf erstellt
    
    def _ensure_bucket(self):
        """Stellt sicher, dass der Bucket existiert."""
        try:
            if not self.sync_client.bucket_exists(self.bucket_name):
                self.sync_client.make_bucket(self.bucket_name)
        except S3Error as e:
            raise RuntimeError(f"Fehler beim Erstellen des Buckets: {e}")
    
    def _get_object_path(self, artifact_type: ArtifactType, file_name: str) -> str:
        """Generiert einen Objekt-Pfad im Bucket."""
        return f"{artifact_type.value}/{file_name}"
    
    async def upload(
        self,
        data: bytes,
        artifact_type: ArtifactType,
        file_name: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> tuple[str, str, int]:
        """
        Asynchrones Upload.
        
        Args:
            data: Binärdaten
            artifact_type: Artefakt-Typ
            file_name: Dateiname (optional)
            mime_type: MIME-Typ (optional)
        
        Returns:
            (storage_uri, file_name, file_size)
        """
        if file_name is None:
            file_name = f"{uuid4()}.bin"
        
        object_path = self._get_object_path(artifact_type, file_name)
        
        def _sync_upload():
            try:
                self.sync_client.put_object(
                    self.bucket_name,
                    object_path,
                    BytesIO(data),
                    length=len(data),
                    content_type=mime_type or "application/octet-stream"
                )
            except S3Error as e:
                raise RuntimeError(f"Fehler beim Hochladen: {e}")
        
        # Führe synchrone Operation in Thread-Pool aus
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _sync_upload)
        
        storage_uri = f"s3://{self.bucket_name}/{object_path}"
        return storage_uri, file_name, len(data)
    
    async def download(self, storage_uri: str) -> bytes:
        """
        Asynchrones Download.
        
        Args:
            storage_uri: Storage-URI
        
        Returns:
            Binärdaten
        """
        if not storage_uri.startswith("s3://"):
            raise ValueError(f"Ungültige Storage-URI: {storage_uri}")
        
        uri_parts = storage_uri[5:].split("/", 1)
        if len(uri_parts) != 2:
            raise ValueError(f"Ungültige Storage-URI: {storage_uri}")
        
        bucket_name, object_path = uri_parts
        
        def _sync_download():
            try:
                response = self.sync_client.get_object(bucket_name, object_path)
                data = response.read()
                response.close()
                response.release_conn()
                return data
            except S3Error as e:
                raise RuntimeError(f"Fehler beim Herunterladen: {e}")
        
        # Führe synchrone Operation in Thread-Pool aus
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_download)
    
    async def upload_stream(
        self,
        stream: AsyncIterator[bytes],
        artifact_type: ArtifactType,
        file_name: str,
        mime_type: Optional[str] = None,
        chunk_size: int = 8 * 1024 * 1024  # 8 MB
    ) -> tuple[str, str, int]:
        """
        Streaming-Upload für große Dateien.
        
        Args:
            stream: Async Iterator von Daten-Chunks
            artifact_type: Artefakt-Typ
            file_name: Dateiname
            mime_type: MIME-Typ
            chunk_size: Chunk-Größe in Bytes
        
        Returns:
            (storage_uri, file_name, file_size)
        """
        # Für jetzt: Sammle alle Chunks und lade hoch
        # TODO: Implementiere echten Streaming-Upload (MinIO multipart upload)
        chunks = []
        total_size = 0
        
        async for chunk in stream:
            chunks.append(chunk)
            total_size += len(chunk)
        
        data = b"".join(chunks)
        return await self.upload(data, artifact_type, file_name, mime_type)
    
    def compute_checksum(self, data: bytes) -> str:
        """Berechnet MD5-Checksumme."""
        return hashlib.md5(data).hexdigest()


def get_async_artifact_store() -> AsyncArtifactStore:
    """
    Erstellt AsyncArtifactStore aus Umgebungsvariablen.
    """
    endpoint = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
    access_key = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
    bucket_name = os.environ.get("MINIO_BUCKET", "sla-artifacts")
    secure = os.environ.get("MINIO_SECURE", "false").lower() == "true"
    
    return AsyncArtifactStore(endpoint, access_key, secret_key, bucket_name, secure)

