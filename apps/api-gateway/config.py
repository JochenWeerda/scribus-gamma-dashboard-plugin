"""Configuration Management für API-Gateway."""

import os
from typing import Optional


class Config:
    """Application Configuration."""
    
    # Database
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        "postgresql://sla_user:sla_password@localhost:5432/sla_pipeline"
    )
    
    # Redis
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    
    # MinIO/S3
    MINIO_ENDPOINT: str = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET: str = os.environ.get("MINIO_BUCKET", "sla-artifacts")
    MINIO_SECURE: bool = os.environ.get("MINIO_SECURE", "false").lower() == "true"
    
    # Security
    API_KEY: Optional[str] = os.environ.get("API_KEY")
    API_KEY_ENABLED: bool = os.environ.get("API_KEY_ENABLED", "false").lower() == "true"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.environ.get("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.environ.get("RATE_LIMIT_WINDOW", "60"))  # seconds
    
    # Input Validation
    MAX_JSON_SIZE_MB: int = int(os.environ.get("MAX_JSON_SIZE_MB", "10"))
    MAX_ELEMENTS_PER_PAGE: int = int(os.environ.get("MAX_ELEMENTS_PER_PAGE", "1000"))
    MAX_PAGES_PER_DOCUMENT: int = int(os.environ.get("MAX_PAGES_PER_DOCUMENT", "1000"))
    
    # Sidecar-MCP
    SIDECAR_MCP_URL: str = os.environ.get("SIDECAR_MCP_URL", "http://sidecar-mcp:8001")
    
    # Logging
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.environ.get("LOG_FORMAT", "json")  # json or text
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = os.environ.get("PROMETHEUS_ENABLED", "true").lower() == "true"
    
    # Event Bus
    EVENT_BUS_ENABLED: bool = os.environ.get("EVENT_BUS_ENABLED", "true").lower() == "true"
    
    # Cache
    CACHE_ENABLED: bool = os.environ.get("CACHE_ENABLED", "true").lower() == "true"
    CACHE_DEFAULT_TTL: int = int(os.environ.get("CACHE_DEFAULT_TTL", "3600"))  # seconds
    
    @classmethod
    def validate(cls):
        """Validiert Konfiguration."""
        errors = []
        
        if cls.API_KEY_ENABLED and not cls.API_KEY:
            errors.append("API_KEY_ENABLED is true but API_KEY is not set")
        
        if cls.MAX_JSON_SIZE_MB <= 0:
            errors.append("MAX_JSON_SIZE_MB must be > 0")
        
        if cls.MAX_ELEMENTS_PER_PAGE <= 0:
            errors.append("MAX_ELEMENTS_PER_PAGE must be > 0")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True


config = Config()

