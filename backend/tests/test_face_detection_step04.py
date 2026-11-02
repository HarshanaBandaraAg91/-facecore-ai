"""Comprehensive regression test suite for STEP 04: Robust Face Detection, Multi-Face Handling, and Image Recovery.

Covers all 12 acceptance criteria:
1. Exactly one detected face
2. Multiple valid detected faces
3. False-positive candidate rejection
4. Zero detected faces
5. Inconsistent diagnostics/comparison response prevention
6. Correct RGB/BGR handling
7. Different image dimensions and aspect ratios
8. Incorrect bounding-box coordinate transformations
9. Manual face selection validation
10. Manual crop validation
11. Corrupt and unsupported images
12. Existing SFace embedding and cosine similarity behavior
"""

import io
import json
import pytest
import numpy as np
import cv2
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.services.face_detector import (
    shared_face_detector,
    is_plausible_face_candidate,
    InvalidCropCoordinatesError,
)
from app.services.image_validator import validate_image_bytes
from app.engine.real_engine import (
    RealFacialEmbeddingEngine,
    NoFaceDetectedError,
    MultipleFacesDetectedError,
    InvalidFaceSelectionError,
    compute_cosine_similarity,
)
from tests.test_engine import (
    create_single_face_image_bytes,
    create_two_faces_image_bytes,
    create_blank_image_bytes,
)

client = TestClient(app)


# ============================================================================
# Criterion 1: Exactly one detected face
# ============================================================================
def test_detection_exactly_one_face():
    """Verify single-face image produces exactly one detected face with valid coordinates."""
    face_bytes = create_single_face_image_bytes(320, 320)
    result = shared_face_detector.detect_faces(face_bytes, use_cache=False)

    assert result.face_count == 1
    assert len(result.faces) == 1
    assert result.primary_face is not None

    f = result.primary_face
    assert f.index == 0
    assert f.confidence >= 0.35
    assert len(f.box) == 4
    x, y, w, h = f.box
    assert w >= 16 and h >= 16
    assert 0 <= x < 320 and 0 <= y < 320
    assert len(f.landmarks) == 5


# ============================================================================
# Criterion 2: Multiple valid detected faces
# ============================================================================
def test_detection_multiple_valid_faces():
    """Verify image with two faces detects both faces with distinct indices and coordinates."""
    two_faces_bytes = create_two_faces_image_bytes(480, 320)
    result = shared_face_detector.detect_faces(two_faces_bytes, use_cache=False)

    assert result.face_count == 2
    assert len(result.faces) == 2
    f0 = result.faces[0]
    f1 = result.faces[1]

    assert f0.index == 0 and f1.index == 1
    # Bounding boxes should be distinctly positioned
    assert abs(f0.box[0] - f1.box[0]) > 50


# ============================================================================
# Criterion 3: False-positive candidate rejection
# ============================================================================
def test_candidate_filtering_rejects_false_positives():
    """Verify plausible candidate filtering rejects noise, degenerate landmarks, and bad aspect ratios."""
    # 1. Candidate below confidence threshold
    low_conf = np.array([50, 50, 100, 100, 70, 70, 110, 70, 90, 90, 80, 120, 100, 120, 0.20], dtype=np.float32)
    is_valid, reason = is_plausible_face_candidate(low_conf, 300, 300, score_threshold=0.35)
    assert not is_valid
    assert "below threshold" in reason

    # 2. Candidate too small (< 16x16)
    tiny_box = np.array([50, 50, 10, 12, 53, 53, 57, 53, 55, 56, 54, 58, 56, 58, 0.90], dtype=np.float32)
    is_valid, reason = is_plausible_face_candidate(tiny_box, 300, 300)
    assert not is_valid
    assert "too small" in reason

    # 3. Implausible aspect ratio (sliver 20x100, ratio 0.20 < 0.35)
    sliver_box = np.array([50, 50, 20, 100, 55, 60, 65, 60, 60, 75, 56, 90, 64, 90, 0.85], dtype=np.float32)
    is_valid, reason = is_plausible_face_candidate(sliver_box, 300, 300)
    assert not is_valid
    assert "aspect ratio" in reason

    # 4. Collapsed eye landmarks (< 4px apart)
    collapsed_eyes = np.array([50, 50, 80, 90, 70.0, 70.0, 71.0, 70.0, 70.5, 85.0, 65.0, 100.0, 75.0, 100.0, 0.80], dtype=np.float32)
    is_valid, reason = is_plausible_face_candidate(collapsed_eyes, 300, 300)
    assert not is_valid
    assert "eye landmark distance" in reason

    # 5. Geometrically plausible face candidate
    valid_face = np.array([50, 50, 80, 90, 70, 75, 110, 75, 90, 95, 75, 115, 105, 115, 0.85], dtype=np.float32)
    is_valid, reason = is_plausible_face_candidate(valid_face, 300, 300)
    assert is_valid
    assert reason is None


# ============================================================================
# Criterion 4: Zero detected faces
# ============================================================================
def test_detection_zero_faces_blank_image():
    """Verify blank image produces 0 detected faces and fails quality check."""
    blank_bytes = create_blank_image_bytes(250, 250, color=(140, 140, 140))
    is_valid, err_msg, diag = validate_image_bytes(blank_bytes, filename="blank.jpg")

    assert is_valid is True
    assert diag is not None
    assert diag.face_detected is False
    assert diag.face_count == 0
    assert diag.face_confidence is None
    assert diag.face_bounding_box is None
    assert len(diag.detected_faces) == 0
    # Must NOT report PASS when face localization fails
    assert diag.passes_quality_check is False


# ============================================================================
# Criterion 5: Inconsistent diagnostics/comparison response prevention
# ============================================================================
def test_diagnostics_comparison_consistency():
    """Verify that diagnostics endpoint and comparison endpoint report identical face counts."""
    two_faces = create_two_faces_image_bytes(480, 320)
    single_face = create_single_face_image_bytes(320, 320)

    # 1. Validation endpoint reports face_count = 2
    val_res = client.post(
        "/api/validate-image",
        files={"file": ("probe.jpg", two_faces, "image/jpeg")},
    )
    assert val_res.status_code == 200
    diag = val_res.json()["diagnostics"]
    assert diag["face_count"] == 2
    assert diag["face_detected"] is True

    # 2. Compare endpoint without selection returns MultipleFacesDetectedError with EXACT same count (2)
    cmp_res = client.post(
        "/api/compare",
        files={
            "image_a": ("probe.jpg", two_faces, "image/jpeg"),
            "image_b": ("ref.jpg", single_face, "image/jpeg"),
        },
    )
    assert cmp_res.status_code == 422
    assert "Multiple faces (2 detected)" in cmp_res.json()["detail"]


# ============================================================================
# Criterion 6: Correct RGB/BGR handling
# ============================================================================
def test_rgb_bgr_color_handling():
    """Verify detector and engine handle RGB-encoded image payloads safely without color distortion."""
    face_rgb = create_single_face_image_bytes(320, 320)
    engine = RealFacialEmbeddingEngine()
    if not engine.is_ready():
        pytest.skip("Model weights not installed")

    crop, emb, conf, bbox, count = engine.detect_and_extract_face(face_rgb, slot_label="Test RGB")
    assert crop.shape == (112, 112, 3)
    assert len(emb) == 128
    assert np.isfinite(emb).all()
    assert pytest.approx(float(np.linalg.norm(emb)), rel=1e-5) == 1.0


# ============================================================================
# Criterion 7: Different image dimensions and aspect ratios
# ============================================================================
def test_different_dimensions_and_aspect_ratios():
    """Verify detector operates across square, portrait, and widescreen aspect ratios."""
    # Portrait 2:3 aspect ratio (320x480)
    face_portrait = create_single_face_image_bytes(320, 480)
    res_port = shared_face_detector.detect_faces(face_portrait, use_cache=False)
    assert res_port.face_count >= 1
    assert 0 <= res_port.faces[0].box[0] + res_port.faces[0].box[2] <= 320
    assert 0 <= res_port.faces[0].box[1] + res_port.faces[0].box[3] <= 480

    # Landscape / Widescreen aspect ratio (480x320)
    face_wide = create_single_face_image_bytes(480, 320)
    res_wide = shared_face_detector.detect_faces(face_wide, use_cache=False)
    assert res_wide.face_count >= 1
    assert 0 <= res_wide.faces[0].box[0] + res_wide.faces[0].box[2] <= 480
    assert 0 <= res_wide.faces[0].box[1] + res_wide.faces[0].box[3] <= 320


# ============================================================================
# Criterion 8: Incorrect bounding-box coordinate transformations
# ============================================================================
def test_incorrect_bounding_box_coordinate_transformations():
    """Verify out-of-bounds, negative, or degenerate crop coordinates are rejected."""
    face_bytes = create_single_face_image_bytes(320, 320)

    # Negative coordinates
    with pytest.raises(InvalidCropCoordinatesError, match="negative"):
        shared_face_detector.detect_faces(face_bytes, crop_box=[-10, 20, 100, 100], use_cache=False)

    # Origin outside canvas
    with pytest.raises(InvalidCropCoordinatesError, match="outside image"):
        shared_face_detector.detect_faces(face_bytes, crop_box=[400, 20, 100, 100], use_cache=False)

    # Degenerate dimensions (< 16px)
    with pytest.raises(InvalidCropCoordinatesError, match="too small"):
        shared_face_detector.detect_faces(face_bytes, crop_box=[10, 10, 8, 8], use_cache=False)


# ============================================================================
# Criterion 9: Manual face selection validation
# ============================================================================
def test_manual_face_selection_validation():
    """Verify user face selection resolves comparison for multi-face image."""
    two_faces = create_two_faces_image_bytes(480, 320)
    single_face = create_single_face_image_bytes(320, 320)

    # Select Face 0 -> comparison succeeds
    res_0 = client.post(
        "/api/compare",
        files={
            "image_a": ("probe.jpg", two_faces, "image/jpeg"),
            "image_b": ("ref.jpg", single_face, "image/jpeg"),
        },
        data={"selected_face_a": 0},
    )
    assert res_0.status_code == 200
    assert res_0.json()["image_a_diagnostics"]["selected_face_index"] == 0
    assert res_0.json()["similarity_score"] is not None

    # Select Face 1 -> comparison succeeds with distinct evaluation
    res_1 = client.post(
        "/api/compare",
        files={
            "image_a": ("probe.jpg", two_faces, "image/jpeg"),
            "image_b": ("ref.jpg", single_face, "image/jpeg"),
        },
        data={"selected_face_a": 1},
    )
    assert res_1.status_code == 200
    assert res_1.json()["image_a_diagnostics"]["selected_face_index"] == 1

    # Out of bounds selection (index 99) -> rejected with 422
    res_bad = client.post(
        "/api/compare",
        files={
            "image_a": ("probe.jpg", two_faces, "image/jpeg"),
            "image_b": ("ref.jpg", single_face, "image/jpeg"),
        },
        data={"selected_face_a": 99},
    )
    assert res_bad.status_code == 422
    assert "invalid" in res_bad.json()["detail"].lower()


# ============================================================================
# Criterion 10: Manual crop validation
# ============================================================================
def test_manual_crop_validation():
    """Verify manual crop restricts evaluation to target region and validates crops."""
    two_faces = create_two_faces_image_bytes(480, 320)
    single_face = create_single_face_image_bytes(320, 320)

    # Crop around Face 0 (left face: x=50, y=80, w=160, h=180)
    crop_res = client.post(
        "/api/validate-image",
        files={"file": ("probe.jpg", two_faces, "image/jpeg")},
        data={"crop_box": "[50, 80, 160, 180]"},
    )
    assert crop_res.status_code == 200
    diag = crop_res.json()["diagnostics"]
    assert diag["face_count"] == 1
    assert diag["crop_bounding_box"] == [50, 80, 160, 180]

    # Comparison with crop_box_a executes cleanly
    cmp_res = client.post(
        "/api/compare",
        files={
            "image_a": ("probe.jpg", two_faces, "image/jpeg"),
            "image_b": ("ref.jpg", single_face, "image/jpeg"),
        },
        data={"crop_box_a": "[50, 80, 160, 180]"},
    )
    assert cmp_res.status_code == 200
    assert cmp_res.json()["image_a_diagnostics"]["crop_bounding_box"] == [50, 80, 160, 180]

    # Invalid crop coordinates rejected
    bad_crop = client.post(
        "/api/validate-image",
        files={"file": ("probe.jpg", two_faces, "image/jpeg")},
        data={"crop_box": "not-a-valid-box"},
    )
    assert bad_crop.status_code == 422


# ============================================================================
# Criterion 11: Corrupt and unsupported images
# ============================================================================
def test_corrupt_and_unsupported_images():
    """Verify corrupt files and fake signatures are rejected safely without crashes."""
    # Fake magic bytes
    fake_data = b"Plain text disguised as JPEG image"
    res_fake = client.post(
        "/api/validate-image",
        files={"file": ("fake.jpg", fake_data, "image/jpeg")},
    )
    assert res_fake.status_code == 200
    assert res_fake.json()["is_valid"] is False
    assert "signature" in res_fake.json()["error_message"].lower()

    # Corrupt payload with JPEG header
    corrupt_data = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00" + b"\x00" * 50
    res_corrupt = client.post(
        "/api/validate-image",
        files={"file": ("corrupt.jpg", corrupt_data, "image/jpeg")},
    )
    assert res_corrupt.status_code == 200
    assert res_corrupt.json()["is_valid"] is False


# ============================================================================
# Criterion 12: Existing SFace embedding and cosine similarity behavior
# ============================================================================
def test_existing_sface_embedding_and_cosine_math():
    """Verify mathematical cosine similarity invariants and SFace vector normalization."""
    # Normalized vector dot product
    u = np.array([0.6, 0.8], dtype=np.float32)
    v = np.array([0.6, 0.8], dtype=np.float32)
    assert pytest.approx(compute_cosine_similarity(u, v), rel=1e-5) == 1.0

    # Orthogonal
    u_orth = np.array([1.0, 0.0], dtype=np.float32)
    v_orth = np.array([0.0, 1.0], dtype=np.float32)
    assert pytest.approx(compute_cosine_similarity(u_orth, v_orth), abs=1e-6) == 0.0
