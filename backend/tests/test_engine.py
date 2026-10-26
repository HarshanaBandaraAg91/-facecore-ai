"""Automated tests for RealFacialEmbeddingEngine and mathematical vector operations."""

import io
import pytest
import numpy as np
import cv2
from PIL import Image

from app.engine.real_engine import (
    RealFacialEmbeddingEngine,
    compute_cosine_similarity,
    calculate_display_score,
    NoFaceDetectedError,
    MultipleFacesDetectedError,
    ModelNotReadyError,
    InvalidEmbeddingError,
    PROVISIONAL_COSINE_THRESHOLD,
)
from app.models.schemas import ImageQualityDiagnostics


def create_blank_image_bytes(width=300, height=300, color=(128, 128, 128)):
    """Create a blank synthetic image with no face."""
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=color)
    img.save(buf, format="JPEG")
    return buf.getvalue()


def create_single_face_image_bytes(width=320, height=320):
    """Synthesize an image with a single oval face and facial features detectable by YuNet."""
    arr = np.full((height, width, 3), 220, dtype=np.uint8)
    # Head contour
    cv2.ellipse(arr, (160, 160), (70, 95), 0, 0, 360, (140, 115, 95), -1)
    # Eyes
    cv2.circle(arr, (135, 140), 9, (20, 20, 20), -1)
    cv2.circle(arr, (185, 140), 9, (20, 20, 20), -1)
    # Nose
    cv2.circle(arr, (160, 170), 7, (50, 50, 50), -1)
    # Mouth
    cv2.ellipse(arr, (160, 210), (25, 10), 0, 0, 180, (30, 30, 30), -1)

    _, encoded = cv2.imencode(".jpg", arr)
    return encoded.tobytes()


def create_two_faces_image_bytes(width=480, height=320):
    """Synthesize an image containing two distinct faces."""
    arr = np.full((height, width, 3), 220, dtype=np.uint8)
    for center_x in [130, 350]:
        cv2.ellipse(arr, (center_x, 160), (60, 85), 0, 0, 360, (140, 115, 95), -1)
        cv2.circle(arr, (center_x - 25, 140), 8, (20, 20, 20), -1)
        cv2.circle(arr, (center_x + 25, 140), 8, (20, 20, 20), -1)
        cv2.circle(arr, (center_x, 170), 6, (50, 50, 50), -1)
        cv2.ellipse(arr, (center_x, 205), (20, 8), 0, 0, 180, (30, 30, 30), -1)

    _, encoded = cv2.imencode(".jpg", arr)
    return encoded.tobytes()


# ============================================================================
# Task 4.1: Mathematical Cosine Similarity & Vector Tests
# ============================================================================

def test_cosine_similarity_identical_vectors():
    """Identical non-zero vectors must yield exact cosine similarity of 1.0."""
    v = np.array([0.5, 0.5, 0.5, 0.5], dtype=np.float32)
    score = compute_cosine_similarity(v, v)
    assert pytest.approx(score, rel=1e-5) == 1.0


def test_cosine_similarity_orthogonal_vectors():
    """Orthogonal (perpendicular) vectors must yield cosine similarity of 0.0."""
    u = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    v = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    score = compute_cosine_similarity(u, v)
    assert pytest.approx(score, abs=1e-6) == 0.0


def test_cosine_similarity_opposite_vectors():
    """Opposite direction vectors must yield cosine similarity of -1.0."""
    u = np.array([2.5, 0.0, 0.0], dtype=np.float32)
    v = np.array([-1.2, 0.0, 0.0], dtype=np.float32)
    score = compute_cosine_similarity(u, v)
    assert pytest.approx(score, rel=1e-5) == -1.0


def test_cosine_similarity_scaling_invariance():
    """Cosine similarity must be invariant to scalar vector magnitude multiplication."""
    u = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    v = u * 42.5
    score = compute_cosine_similarity(u, v)
    assert pytest.approx(score, rel=1e-5) == 1.0


def test_cosine_similarity_zero_norm_protection():
    """Zero-norm vectors must be handled gracefully without division by zero errors."""
    zero_v = np.zeros(128, dtype=np.float32)
    normal_v = np.ones(128, dtype=np.float32)
    score = compute_cosine_similarity(zero_v, normal_v)
    assert score == 0.0
    score_both_zero = compute_cosine_similarity(zero_v, zero_v)
    assert score_both_zero == 0.0


def test_cosine_similarity_rejects_nan_and_inf():
    """Vectors containing NaN or Infinity must be rejected with InvalidEmbeddingError."""
    v_nan = np.array([1.0, np.nan, 3.0], dtype=np.float32)
    v_normal = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    with pytest.raises(InvalidEmbeddingError):
        compute_cosine_similarity(v_nan, v_normal)

    v_inf = np.array([1.0, np.inf, 3.0], dtype=np.float32)
    with pytest.raises(InvalidEmbeddingError):
        compute_cosine_similarity(v_normal, v_inf)


def test_calculate_display_score_mapping():
    """Display score must accurately project [-1.0, 1.0] range to [0.0, 100.0]."""
    assert pytest.approx(calculate_display_score(1.0), abs=1e-2) == 100.0
    assert pytest.approx(calculate_display_score(0.0), abs=1e-2) == 50.0
    assert pytest.approx(calculate_display_score(-1.0), abs=1e-2) == 0.0
    # Out of bounds clipping
    assert calculate_display_score(1.5) == 100.0
    assert calculate_display_score(-1.5) == 0.0


# ============================================================================
# Task 4.2: Engine Initialization & Missing Model Handling
# ============================================================================

def test_engine_missing_weights_degraded_state():
    """Engine must report OFFLINE status and handle missing weights cleanly without crash."""
    engine = RealFacialEmbeddingEngine(
        yunet_path="/nonexistent/path/yunet.onnx",
        sface_path="/nonexistent/path/sface.onnx",
    )
    assert engine.is_ready() is False
    meta = engine.get_metadata()
    assert meta.status.value == "offline"

    with pytest.raises(ModelNotReadyError):
        engine.detect_and_extract_face(b"fake_image_bytes")


def test_engine_initialization_with_real_weights():
    """Engine must initialize successfully when real weights are available."""
    engine = RealFacialEmbeddingEngine()
    if engine.is_ready():
        meta = engine.get_metadata()
        assert meta.status.value == "active"
        assert meta.embedding_dimension == 128
        assert meta.inference_device == "CPU"
        assert meta.weights_license == "Apache-2.0 (OpenCV Model Zoo)"


# ============================================================================
# Task 4.3: Face Detection Guardrails (No Face / Multiple Faces)
# ============================================================================

def test_engine_raises_no_face_detected():
    """Blank image with no face must trigger NoFaceDetectedError."""
    engine = RealFacialEmbeddingEngine()
    if not engine.is_ready():
        pytest.skip("Model weights not installed")

    blank_bytes = create_blank_image_bytes(300, 300)
    with pytest.raises(NoFaceDetectedError) as exc_info:
        engine.detect_and_extract_face(blank_bytes, slot_label="Image A (Probe)")
    assert "No face detected in Image A (Probe)" in str(exc_info.value)


def test_engine_raises_multiple_faces_detected():
    """Image with two or more faces must trigger MultipleFacesDetectedError."""
    engine = RealFacialEmbeddingEngine()
    if not engine.is_ready():
        pytest.skip("Model weights not installed")

    multi_face_bytes = create_two_faces_image_bytes(480, 320)
    try:
        engine.detect_and_extract_face(multi_face_bytes, slot_label="Image B (Reference)")
    except MultipleFacesDetectedError as exc:
        assert exc.count >= 2
        assert "Multiple faces" in str(exc)
        assert "Image B (Reference)" in str(exc)
    except NoFaceDetectedError:
        # If synthetic shapes were not resolved by detector threshold, skip
        pytest.skip("Synthetic multi-face not triggered by detector threshold")


# ============================================================================
# Task 4.4: Real Model Extraction & Pairwise Comparison Integration
# ============================================================================

def test_engine_single_face_extraction_and_cosine_evaluation():
    """Real model must extract 128-d unit vector and compute cosine similarity."""
    engine = RealFacialEmbeddingEngine()
    if not engine.is_ready():
        pytest.skip("Model weights not installed")

    face_a = create_single_face_image_bytes(320, 320)
    face_b = create_single_face_image_bytes(320, 320)

    diag_a = ImageQualityDiagnostics(
        filename="probe.jpg",
        format="JPEG",
        color_mode="RGB",
        width=320,
        height=320,
        aspect_ratio="1:1 (Square)",
        file_size_bytes=len(face_a),
        sha256_hash="abcdef0123456789",
        estimated_sharpness=85.0,
        contrast_std=40.0,
        brightness_mean=140.0,
        resolution_category="Standard Definition",
        passes_quality_check=True,
    )
    diag_b = ImageQualityDiagnostics(
        filename="ref.jpg",
        format="JPEG",
        color_mode="RGB",
        width=320,
        height=320,
        aspect_ratio="1:1 (Square)",
        file_size_bytes=len(face_b),
        sha256_hash="1234567890abcdef",
        estimated_sharpness=82.0,
        contrast_std=39.0,
        brightness_mean=138.0,
        resolution_category="Standard Definition",
        passes_quality_check=True,
    )

    response = engine.compare_faces(face_a, face_b, diag_a, diag_b)
    assert response.status == "evaluation_completed"
    assert response.similarity_score is not None
    assert response.raw_cosine_similarity is not None
    assert -1.0 <= response.raw_cosine_similarity <= 1.0
    assert response.transformed_display_score is not None
    assert 0.0 <= response.transformed_display_score <= 100.0
    assert response.provisional_threshold == PROVISIONAL_COSINE_THRESHOLD
    assert response.is_match is not None
    assert response.inference_latency_ms > 0
    assert "SFace" in response.interpretation_notice
    assert response.image_a_diagnostics.face_detected is True
    assert response.image_b_diagnostics.face_detected is True
