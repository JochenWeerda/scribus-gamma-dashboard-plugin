"""Artifact Store Package - MinIO/S3 Storage für Artefakte."""

from .store import ArtifactStore, get_artifact_store

__all__ = ["ArtifactStore", "get_artifact_store"]

