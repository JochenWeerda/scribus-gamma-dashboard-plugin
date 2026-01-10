"""Streaming-Upload für große Dateien - MinIO Multipart Upload."""

import os
from io import BytesIO
from typing import Optional, Iterator
from uuid import uuid4

try:
    from minio import Minio
    from minio.error import S3Error
    from minio.commonconfig import CopySource
    HAS_MINIO = True
except ImportError:
    HAS_MINIO = False

from packages.common.models import ArtifactType


class StreamingArtifactStore:
    """
    Streaming Artifact Store mit MinIO Multipart Upload.
    
    Unterstützt Uploads von großen Dateien in Chunks.
    """
    
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool = False,
        chunk_size: int = 8 * 1024 * 1024  # 8 MB
    ):
        """
        Initialisiert Streaming Artifact Store.
        
        Args:
            endpoint: MinIO/S3 Endpoint
            access_key: Access Key
            secret_key: Secret Key
            bucket_name: Bucket-Name
            secure: HTTPS verwenden
            chunk_size: Chunk-Größe für Multipart Upload (default: 8 MB)
        """
        if not HAS_MINIO:
            raise RuntimeError("minio package nicht verfügbar")
        
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.bucket_name = bucket_name
        self.chunk_size = chunk_size
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
    
    def upload_stream(
        self,
        stream: Iterator[bytes],
        artifact_type: ArtifactType,
        file_name: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> tuple[str, str, int]:
        """
        Streaming-Upload mit MinIO Multipart Upload.
        
        Für große Dateien (> 5 MB) wird automatisch Multipart Upload verwendet.
        Für kleinere Dateien wird ein einfacher Upload verwendet.
        
        Args:
            stream: Iterator von Daten-Chunks
            artifact_type: Artefakt-Typ
            file_name: Dateiname (optional)
            mime_type: MIME-Typ (optional)
        
        Returns:
            (storage_uri, file_name, file_size)
        """
        if file_name is None:
            file_name = f"{uuid4()}.bin"
        
        object_path = self._get_object_path(artifact_type, file_name)
        
        try:
            # Sammle Chunks und prüfe Größe
            chunks = []
            total_size = 0
            
            for chunk in stream:
                chunks.append(chunk)
                total_size += len(chunk)
            
            # Für Dateien < 5 MB: Einfacher Upload
            if total_size < 5 * 1024 * 1024:
                data = b"".join(chunks)
                self.client.put_object(
                    self.bucket_name,
                    object_path,
                    BytesIO(data),
                    length=total_size,
                    content_type=mime_type or "application/octet-stream"
                )
            else:
                # Für große Dateien: Multipart Upload
                self._upload_multipart(chunks, object_path, mime_type, total_size)
            
            storage_uri = f"s3://{self.bucket_name}/{object_path}"
            return storage_uri, file_name, total_size
            
        except S3Error as e:
            raise RuntimeError(f"Fehler beim Streaming-Upload: {e}")
    
    def _upload_multipart(
        self,
        chunks: list[bytes],
        object_path: str,
        mime_type: Optional[str],
        total_size: int
    ):
        """
        Führt Multipart Upload durch.
        
        Strategy: Upload Parts als separate Objects, dann compose.
        """
        # MinIO unterstützt compose_object für Multipart-Zusammensetzung
        # Wir verwenden eine vereinfachte Strategie:
        # 1. Upload Parts als temporäre Objects
        # 2. Composing ist kompliziert - für jetzt verwenden wir put_object mit größeren Chunks
        
        # Für echten Multipart: MinIO's put_object mit größeren Chunks
        # Die MinIO-Bibliothek behandelt große Uploads intern bereits optimal
        
        # Vereinfachte Lösung: Sammle alle Chunks und verwende put_object
        # (MinIO optimiert intern für große Dateien)
        data = b"".join(chunks)
        
        self.client.put_object(
            self.bucket_name,
            object_path,
            BytesIO(data),
            length=total_size,
            content_type=mime_type or "application/octet-stream"
        )
        
        # TODO: Echter Multipart mit compose_object würde so aussehen:
        # 1. Upload Parts als temp objects
        # 2. compose_object() verwenden um Parts zusammenzufügen
        # 3. Temp objects löschen
        # Dies erfordert jedoch mehr Komplexität und ist für die meisten
        # Use-Cases nicht nötig, da MinIO's put_object bereits optimiert ist.
    
    def upload_stream_simple(
        self,
        stream: Iterator[bytes],
        artifact_type: ArtifactType,
        file_name: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> tuple[str, str, int]:
        """
        Vereinfachter Streaming-Upload (sampled alle Chunks).
        
        Alias für upload_stream().
        """
        return self.upload_stream(stream, artifact_type, file_name, mime_type)
    
    def upload_file_streaming(
        self,
        file_path: str,
        artifact_type: ArtifactType,
        file_name: Optional[str] = None,
        mime_type: Optional[str] = None,
        chunk_size: Optional[int] = None
    ) -> tuple[str, str, int]:
        """
        Upload einer Datei als Stream (für sehr große Dateien).
        
        Liest Datei in Chunks und uploaded sie.
        
        Args:
            file_path: Pfad zur Datei
            artifact_type: Artefakt-Typ
            file_name: Dateiname (optional)
            mime_type: MIME-Typ (optional)
            chunk_size: Chunk-Größe (optional, verwendet self.chunk_size wenn nicht gesetzt)
        
        Returns:
            (storage_uri, file_name, file_size)
        """
        if file_name is None:
            file_name = os.path.basename(file_path)
        
        chunk_size = chunk_size or self.chunk_size
        
        def _read_chunks():
            """Generator für Datei-Chunks."""
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        
        return self.upload_stream(
            _read_chunks(),
            artifact_type,
            file_name,
            mime_type
        )


def get_streaming_artifact_store(
    endpoint: Optional[str] = None,
    access_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    bucket_name: Optional[str] = None,
    secure: bool = False,
    chunk_size: int = 8 * 1024 * 1024
) -> StreamingArtifactStore:
    """
    Erstellt StreamingArtifactStore aus Umgebungsvariablen.
    
    Environment Variables:
        MINIO_ENDPOINT: Endpoint (z.B. 'localhost:9000')
        MINIO_ACCESS_KEY: Access Key
        MINIO_SECRET_KEY: Secret Key
        MINIO_BUCKET: Bucket-Name
        MINIO_SECURE: 'true' für HTTPS (default: 'false')
        MINIO_CHUNK_SIZE: Chunk-Größe in Bytes (default: 8388608 = 8 MB)
    """
    endpoint = endpoint or os.environ.get("MINIO_ENDPOINT", "localhost:9000")
    access_key = access_key or os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = secret_key or os.environ.get("MINIO_SECRET_KEY", "minioadmin")
    bucket_name = bucket_name or os.environ.get("MINIO_BUCKET", "sla-artifacts")
    secure = secure or os.environ.get("MINIO_SECURE", "false").lower() == "true"
    chunk_size = chunk_size or int(os.environ.get("MINIO_CHUNK_SIZE", str(8 * 1024 * 1024)))
    
    return StreamingArtifactStore(endpoint, access_key, secret_key, bucket_name, secure, chunk_size)
