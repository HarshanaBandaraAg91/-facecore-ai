"""Unit tests for health and engine endpoints."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify health endpoint reports status ok and version."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "FACECORE AI"
    assert data["version"] == "0.1.0-alpha"
    assert data["engine_status"] == "pending_integration"
    assert data["security_mode"] == "ephemeral_local_strict"


def test_engine_info_endpoint():
    """Verify modular engine metadata reports pending integration and zero mock score fabrication."""
    response = client.get("/api/engine-info")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending_integration"
    assert data["is_mock_data"] is False
    assert "ArcFace" in str(data["supported_models"])
