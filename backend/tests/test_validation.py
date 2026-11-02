"""Unit tests for image validation and comparison endpoints."""

import io
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def create_test_image_bytes(width=200, height=200, fmt="JPEG", color=(120, 150, 180)):
    """Helper to synthesize valid in-memory image bytes for testing."""
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=color)
    img.save(buf, format=fmt)
    return buf.getvalue()


def test_validate_valid_jpeg():
    """Verify valid JPEG passes signature, dimensions, and generates diagnostics."""
    data = create_test_image_bytes(250, 250, "JPEG")
    files = {"file": ("probe.jpg", data, "image/jpeg")}
    response = client.post("/api/validate-image", files=files)
    assert response.status_code == 200
    res = response.json()
    assert res["is_valid"] is True
    assert res["error_message"] is None
    diag = res["diagnostics"]
    assert diag is not None
    assert diag["width"] == 250
    assert diag["height"] == 250
    assert diag["format"] == "JPEG"
    assert len(diag["sha256_hash"]) == 16


def test_validate_valid_png():
    """Verify valid PNG passes validation."""
    data = create_test_image_bytes(300, 300, "PNG")
    files = {"file": ("reference.png", data, "image/png")}
    response = client.post("/api/validate-image", files=files)
    assert response.status_code == 200
    res = response.json()
    assert res["is_valid"] is True
    assert res["diagnostics"]["format"] == "PNG"


def test_validate_invalid_signature():
    """Verify file disguised as image with invalid magic bytes is rejected."""
    fake_data = b"This is just plain text content pretending to be an image."
    files = {"file": ("fake.jpg", fake_data, "image/jpeg")}
    response = client.post("/api/validate-image", files=files)
    assert response.status_code == 200
    res = response.json()
    assert res["is_valid"] is False
    assert "Invalid or unsupported file signature" in res["error_message"]
    assert res["diagnostics"] is None


def test_validate_too_small_dimensions():
    """Verify images below 32x32 minimum dimension are rejected."""
    data = create_test_image_bytes(16, 16, "PNG")
    files = {"file": ("tiny.png", data, "image/png")}
    response = client.post("/api/validate-image", files=files)
    assert response.status_code == 200
    res = response.json()
    assert res["is_valid"] is False
    assert "Image resolution too low" in res["error_message"]


def test_validate_corrupt_payload():
    """Verify corrupted image payload (valid magic bytes but truncated/garbled) is rejected safely."""
    # JPEG magic bytes followed by garbage that fails Pillow decoding
    corrupt_data = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00GarbledTruncatedStream"
    files = {"file": ("corrupt.jpg", corrupt_data, "image/jpeg")}
    response = client.post("/api/validate-image", files=files)
    assert response.status_code == 200
    res = response.json()
    assert res["is_valid"] is False
    assert "Corrupt or unreadable image file" in res["error_message"]


def test_validate_oversized_payload():
    """Verify file exceeding size limit is rejected."""
    # Simulate oversized payload larger than 15MB (production limit)
    oversized = b"\xFF\xD8\xFF" + b"\x00" * (16 * 1024 * 1024)
    files = {"file": ("huge.jpg", oversized, "image/jpeg")}
    response = client.post("/api/validate-image", files=files)
    assert response.status_code == 200
    res = response.json()
    assert res["is_valid"] is False
    assert "exceeds maximum allowed limit" in res["error_message"]


def test_compare_endpoint_rejects_invalid_probe():
    """Verify comparison endpoint returns 422 if Image A is invalid."""
    invalid_data = b"Not an image"
    valid_data = create_test_image_bytes(200, 200, "JPEG")

    files = {
        "image_a": ("bad.jpg", invalid_data, "image/jpeg"),
        "image_b": ("good.jpg", valid_data, "image/jpeg"),
    }
    response = client.post("/api/compare", files=files)
    assert response.status_code == 422
    assert "Image A validation failed" in response.json()["detail"]


def test_compare_endpoint_rejects_when_no_face_detected():
    """Verify compare endpoint rejects blank images where no face is present."""
    blank_a = create_test_image_bytes(200, 200, "JPEG", color=(100, 110, 120))
    blank_b = create_test_image_bytes(220, 220, "PNG", color=(130, 140, 150))

    files = {
        "image_a": ("probe.jpg", blank_a, "image/jpeg"),
        "image_b": ("reference.png", blank_b, "image/png"),
    }
    response = client.post("/api/compare", files=files)
    assert response.status_code == 422
    assert "No face detected" in response.json()["detail"]


def test_compare_endpoint_with_single_face_images():
    """Verify compare endpoint extracts embeddings and computes real cosine similarity."""
    from tests.test_engine import create_single_face_image_bytes

    face_a = create_single_face_image_bytes(320, 320)
    face_b = create_single_face_image_bytes(320, 320)

    files = {
        "image_a": ("probe.jpg", face_a, "image/jpeg"),
        "image_b": ("reference.jpg", face_b, "image/jpeg"),
    }
    response = client.post("/api/compare", files=files)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "evaluation_completed"
    assert res["raw_cosine_similarity"] is not None
    assert -1.0 <= res["raw_cosine_similarity"] <= 1.0
    assert res["transformed_display_score"] is not None
    assert 0.0 <= res["transformed_display_score"] <= 100.0
    assert "SFace" in res["interpretation_notice"]
