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
    assert "1.0.0" in data["version"] or "0.2.0" in data["version"]
    assert data["engine_status"] in ["active", "pending_integration"]
    assert data["security_mode"] == "ephemeral_local_strict"


def test_engine_info_endpoint():
    """Verify active engine metadata reports active status and zero mock score fabrication."""
    response = client.get("/api/engine-info")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["active", "pending_integration"]
    assert data["is_mock_data"] is False
    assert "SFace" in str(data["supported_models"]) or "ArcFace" in str(data["supported_models"])
