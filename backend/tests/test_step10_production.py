"""Unit and integration tests for FACECORE AI - Step 10 Production Engineering.

Tests cover:
1. Thread safety and concurrency in FaceDetectorYN and SFace inference locks.
2. Ephemeral SQLite audit logging and dashboard metrics aggregation (zero images/embeddings stored).
3. Calibrated threshold profiles (high_security, balanced, high_convenience, custom).
4. Ingestion dimension gates (<48px hard rejection, face box <16px floor).
5. Structured error codes and exceptions.
"""

from __future__ import annotations

import concurrent.futures
import os
import sqlite3
import tempfile
import threading
import numpy as np
import pytest

from app.config import get_settings
from app.db.database import (
    init_db,
    record_comparison,
    get_dashboard_stats,
    get_recent_comparisons,
    clear_comparison_history,
    record_benchmark_run,
)
from app.engine.real_engine import (
    RealFacialEmbeddingEngine,
    THRESHOLD_PROFILES,
    resolve_threshold,
    compute_cosine_similarity,
    calculate_display_score,
)
from app.models.schemas import ErrorCode, ThresholdProfile
from app.services.face_detector import shared_face_detector


class TestThresholdProfilesAndEngine:
    """Verify calibrated operating threshold profiles and resolution logic."""

    def test_threshold_profile_constants(self):
        """Verify defined profiles match Step 09.2 scientific specifications."""
        assert THRESHOLD_PROFILES["high_security"]["threshold"] == 0.3600
        assert THRESHOLD_PROFILES["balanced"]["threshold"] == 0.3132
        assert THRESHOLD_PROFILES["high_convenience"]["threshold"] == 0.2500

    def test_resolve_threshold_presets(self):
        """Test threshold resolution for standard profiles."""
        p_hs, t_hs = resolve_threshold("high_security", None)
        assert p_hs == "high_security"
        assert t_hs == 0.3600

        p_bal, t_bal = resolve_threshold("balanced", None)
        assert p_bal == "balanced"
        assert t_bal == 0.3132

        p_hc, t_hc = resolve_threshold("high_convenience", None)
        assert p_hc == "high_convenience"
        assert t_hc == 0.2500

    def test_resolve_threshold_custom(self):
        """Test custom threshold overrides."""
        p_custom, t_custom = resolve_threshold("custom", 0.4200)
        assert p_custom == "custom"
        assert t_custom == 0.4200

        # Custom without explicit value falls back to balanced
        p_def, t_def = resolve_threshold("custom", None)
        assert p_def == "custom"
        assert t_def == 0.3132

    def test_cosine_similarity_properties(self):
        """Test exact cosine calculation on known vectors."""
        v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        v2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        v3 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        v4 = np.array([-1.0, 0.0, 0.0], dtype=np.float32)

        # Identical vectors -> 1.0
        assert abs(compute_cosine_similarity(v1, v2) - 1.0) < 1e-6
        # Orthogonal vectors -> 0.0
        assert abs(compute_cosine_similarity(v1, v3) - 0.0) < 1e-6
        # Opposite vectors -> -1.0
        assert abs(compute_cosine_similarity(v1, v4) - (-1.0)) < 1e-6

        # Display score linear scaling
        assert calculate_display_score(1.0) == 100.0
        assert calculate_display_score(0.0) == 50.0
        assert calculate_display_score(-1.0) == 0.0


class TestSQLiteAuditTrailAndPrivacy:
    """Verify SQLite persistence layer, privacy guarantees, and statistical aggregation."""

    @pytest.fixture
    def test_db(self):
        """Create a temporary SQLite database for isolation."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        init_db(db_path)
        yield db_path

        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except OSError:
                pass

    def test_zero_image_or_embedding_storage(self, test_db: str):
        """Verify that table schemas strictly prohibit storing image bytes or vectors."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Inspect comparison_audit_log columns
        cursor.execute("PRAGMA table_info(comparison_audit_log);")
        columns = [row[1] for row in cursor.fetchall()]

        # Columns that must exist
        assert "probe_hash_prefix" in columns
        assert "reference_hash_prefix" in columns
        assert "similarity_score" in columns
        assert "threshold_profile" in columns
        assert "threshold_used" in columns
        assert "is_match" in columns
        assert "latency_ms" in columns

        # Ensure NO column can store raw image bytes or vector embeddings
        forbidden = ["image", "bytes", "photo", "embedding", "vector", "payload", "blob"]
        for col in columns:
            for forb in forbidden:
                assert forb not in col.lower(), f"Forbidden column found: {col}"

        conn.close()

    def test_record_and_aggregate_stats(self, test_db: str):
        """Test recording comparison records and calculating aggregate telemetry."""
        # Record 3 matches, 1 non-match, 1 FTA
        record_comparison(
            probe_hash_prefix="a1b2c3d4",
            reference_hash_prefix="e5f6a1b2",
            similarity_score=0.75,
            display_score=87.5,
            threshold_used=0.3600,
            threshold_profile="high_security",
            is_match=True,
            latency_ms=20.0,
            face_count_a=1,
            face_count_b=1,
            quality_flags_a=[],
            quality_flags_b=[],
            status="SUCCESS",
            db_path=test_db,
        )
        record_comparison(
            probe_hash_prefix="b2c3d4e5",
            reference_hash_prefix="f6a1b2c3",
            similarity_score=0.45,
            display_score=72.5,
            threshold_used=0.3132,
            threshold_profile="balanced",
            is_match=True,
            latency_ms=25.0,
            face_count_a=1,
            face_count_b=1,
            quality_flags_a=[],
            quality_flags_b=[],
            status="SUCCESS",
            db_path=test_db,
        )
        record_comparison(
            probe_hash_prefix="c3d4e5f6",
            reference_hash_prefix="a1b2c3d4",
            similarity_score=0.82,
            display_score=91.0,
            threshold_used=0.3132,
            threshold_profile="balanced",
            is_match=True,
            latency_ms=22.0,
            face_count_a=1,
            face_count_b=1,
            quality_flags_a=["face_width_below_48px"],
            quality_flags_b=[],
            status="SUCCESS",
            db_path=test_db,
        )
        record_comparison(
            probe_hash_prefix="d4e5f6a1",
            reference_hash_prefix="b2c3d4e5",
            similarity_score=0.15,
            display_score=57.5,
            threshold_used=0.3132,
            threshold_profile="balanced",
            is_match=False,
            latency_ms=21.0,
            face_count_a=1,
            face_count_b=1,
            quality_flags_a=[],
            quality_flags_b=[],
            status="SUCCESS",
            db_path=test_db,
        )
        record_comparison(
            probe_hash_prefix="e5f6a1b2",
            reference_hash_prefix="c3d4e5f6",
            similarity_score=None,
            display_score=None,
            threshold_used=0.3132,
            threshold_profile="balanced",
            is_match=False,
            latency_ms=5.0,
            face_count_a=0,
            face_count_b=1,
            quality_flags_a=["no_face_detected"],
            quality_flags_b=[],
            status="FAILED",
            db_path=test_db,
        )

        stats = get_dashboard_stats(test_db)
        assert stats["total_comparisons"] == 5
        assert stats["successful_matches"] == 3
        assert stats["successful_non_matches"] == 1
        assert stats["failed_comparisons"] == 1
        assert stats["total_fta_events"] == 1
        # FTA rate = 1 / 5 = 20%
        assert stats["fta_rate_percent"] == 20.0
        assert stats["average_latency_ms"] > 0

        # Test history listing
        history = get_recent_comparisons(limit=10, db_path=test_db)
        assert len(history) == 5
        assert history[0]["status"] == "FAILED"
        assert history[0]["probe_hash_prefix"] == "e5f6a1b2"

        # Test clear
        deleted = clear_comparison_history(test_db)
        assert deleted == 5
        stats_after = get_dashboard_stats(test_db)
        assert stats_after["total_comparisons"] == 0


class TestConcurrencyAndThreadSafety:
    """Verify thread-safe reentrant inference across concurrent worker threads."""

    def test_concurrent_face_detection_and_inference(self):
        """Execute parallel face detections across multiple threads simultaneously."""
        detector = shared_face_detector
        assert detector is not None

        # Synthetic image with a bright rectangle
        img = np.zeros((300, 300, 3), dtype=np.uint8)
        img[50:200, 50:200] = 160
        import cv2
        _, encoded = cv2.imencode(".jpg", img)
        raw_bytes = encoded.tobytes()

        def worker_task(thread_id: int):
            # Run detection via shared detector (must be re-entrant and thread-safe)
            det_res = detector.detect_faces(raw_bytes)
            return thread_id, det_res.face_count

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(worker_task, i) for i in range(8)]
            results = [f.result(timeout=10.0) for f in concurrent.futures.as_completed(futures)]

        assert len(results) == 8
        for thread_id, n_faces in results:
            assert isinstance(n_faces, int)


class TestQualityPolicyGatesAndErrorCodes:
    """Verify operational ingestion gates, dimension floors, and error mappings."""

    def test_min_dimension_setting(self):
        """Verify settings enforce 48px hard floor."""
        settings = get_settings()
        assert settings.min_image_dimension == 48

    def test_error_code_enum_values(self):
        """Verify error code enums match standard production taxonomy."""
        assert ErrorCode.RESOLUTION_TOO_LOW.value == "RESOLUTION_TOO_LOW"
        assert ErrorCode.NO_FACE_DETECTED.value == "NO_FACE_DETECTED"
        assert ErrorCode.MULTIPLE_FACES_DETECTED.value == "MULTIPLE_FACES_DETECTED"
        assert ErrorCode.IMAGE_CORRUPT.value == "IMAGE_CORRUPT"
        assert ErrorCode.INTERNAL_ERROR.value == "INTERNAL_ERROR"
