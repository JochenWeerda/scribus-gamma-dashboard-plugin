"""Tests für API-Gateway."""

import os
import pytest
from fastapi.testclient import TestClient

if os.environ.get("RUN_API_GATEWAY_TESTS") != "1":
    pytest.skip("Set RUN_API_GATEWAY_TESTS=1 to run API gateway integration tests", allow_module_level=True)

from apps.api_gateway.main import app


@pytest.fixture
def client():
    """Test Client."""
    return TestClient(app)


def test_health_check(client):
    """Test: Health Check Endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "api-gateway"


def test_create_job_requires_api_key(client):
    """Test: Job-Erstellung erfordert API-Key (wenn aktiviert)."""
    # TODO: Mock API-Key Authentication
    # Aktuell wird dieser Test nur ausgeführt wenn API_KEY_ENABLED=false
    pass


def test_get_job_not_found(client):
    """Test: Job nicht gefunden."""
    from uuid import uuid4
    
    response = client.get(f"/v1/jobs/{uuid4()}")
    # Erwartet 401 (API-Key) oder 404 (Job nicht gefunden)
    assert response.status_code in [401, 404]

