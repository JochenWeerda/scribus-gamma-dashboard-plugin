"""Artifact Store - MinIO/S3 Storage Implementation."""

import hashlib
import os
from io import BytesIO
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from minio import Minio
from minio.error import S3Error

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
    endpoint = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
    access_key = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
    bucket_name = os.environ.get("MINIO_BUCKET", "sla-artifacts")
    secure = os.environ.get("MINIO_SECURE", "false").lower() == "true"
    
    return ArtifactStore(endpoint, access_key, secret_key, bucket_name, secure)

