"""
MinIO Integration für Figma Asset Storage

Beispiel-Integration für MinIO Client in Figma Service.
"""

from typing import Optional
import os


def create_minio_client(
    endpoint: Optional[str] = None,
    access_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    secure: bool = False
):
    """
    Erstellt MinIO Client.
    
    Args:
        endpoint: MinIO Endpoint (default: aus ENV)
        access_key: Access Key (default: aus ENV)
        secret_key: Secret Key (default: aus ENV)
        secure: HTTPS verwenden (default: False)
        
    Returns:
        MinIO Client oder None (falls nicht konfiguriert)
    """
    try:
        from minio import Minio
        
        endpoint = endpoint or os.getenv("MINIO_ENDPOINT", "localhost:9000")
        access_key = access_key or os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        secret_key = secret_key or os.getenv("MINIO_SECRET_KEY", "minioadmin")
        
        client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        
        return client
    except ImportError:
        # MinIO nicht installiert
        return None
    except Exception as e:
        print(f"MinIO client creation failed: {e}")
        return None


def ensure_minio_bucket(client, bucket_name: str):
    """
    Stellt sicher, dass MinIO Bucket existiert.
    
    Args:
        client: MinIO Client
        bucket_name: Bucket Name
        
    Returns:
        True wenn Bucket existiert oder erstellt wurde
    """
    if not client:
        return False
    
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
        return True
    except Exception as e:
        print(f"MinIO bucket creation failed: {e}")
        return False


# Beispiel für API Gateway Integration
"""
from packages.figma_integration.minio_integration import create_minio_client, ensure_minio_bucket
from packages.figma_integration.api_endpoints import init_figma_service

@app.on_event("startup")
async def startup():
    # MinIO Client erstellen
    minio_client = create_minio_client()
    if minio_client:
        ensure_minio_bucket(minio_client, "figma-assets")
    
    # Figma Service mit MinIO Client initialisieren
    init_figma_service(
        access_token=os.getenv("FIGMA_ACCESS_TOKEN"),
        minio_client=minio_client,
        minio_bucket="figma-assets"
    )
"""

