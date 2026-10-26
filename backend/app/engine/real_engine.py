"""Real facial embedding and pairwise similarity engine using YuNet and SFace.

Adheres strictly to biometric research integrity:
- Validates embedding shape, finitude, and norm.
- Computes exact cosine similarity with zero-norm protection.
- Requires exactly one usable face per image.
- Never claims cosine similarity is an absolute identity verdict.
- Employs Apache-2.0 licensed model weights from OpenCV Model Zoo.
"""

import os
import time
import math
from datetime import datetime, timezone
from typing import Optional, Tuple, List, Any
import numpy as np
import cv2

from app.models.schemas import (
    EngineStatus,
    EngineMetadata,
    ComparisonResponse,
    ImageQualityDiagnostics,
)
from app.engine.base import FacialEmbeddingEngine

# Default path constants for model weights
DEFAULT_WEIGHTS_DIR = os.path.join(os.path.dirname(__file__), "..", "weights")
DEFAULT_YUNET_PATH = os.path.join(DEFAULT_WEIGHTS_DIR, "face_detection_yunet_2023mar.onnx")
DEFAULT_SFACE_PATH = os.path.join(DEFAULT_WEIGHTS_DIR, "face_recognition_sface_2021dec.onnx")

# Published experimental baseline threshold for SFace (SphereFace2)
PROVISIONAL_COSINE_THRESHOLD = 0.363


class FaceEngineError(Exception):
    """Base exception for facial engine processing errors."""
    pass


class ModelNotReadyError(FaceEngineError):
    """Raised when model weights are not loaded or missing."""
    pass


class NoFaceDetectedError(FaceEngineError):
    """Raised when zero faces are located in the target image."""
    def __init__(self, slot_label: str = "Image"):
        super().__init__(
            f"No face detected in {slot_label}. Please provide an image with a clearly visible, "
            f"unobstructed human face."
        )
        self.slot_label = slot_label


class MultipleFacesDetectedError(FaceEngineError):
    """Raised when more than one face is located in the target image."""
    def __init__(self, count: int, slot_label: str = "Image"):
        super().__init__(
            f"Multiple faces ({count} detected) in {slot_label}. For controlled pairwise "
            f"evaluation, each image must contain exactly one primary face."
        )
        self.count = count
        self.slot_label = slot_label


class InvalidEmbeddingError(FaceEngineError):
    """Raised when extracted embedding contains NaN, Inf, or empty values."""
    pass


def compute_cosine_similarity(u: np.ndarray, v: np.ndarray) -> float:
    """Compute mathematical cosine similarity between two vectors with zero-norm protection.

    Formula: cos(theta) = (u . v) / (||u||_2 * ||v||_2)
    Returns: Float in range [-1.0, 1.0].
    """
    if u is None or v is None:
        raise ValueError("Cannot compute cosine similarity on None vectors.")

    u_flat = np.asarray(u, dtype=np.float32).flatten()
    v_flat = np.asarray(v, dtype=np.float32).flatten()

    if len(u_flat) != len(v_flat) or len(u_flat) == 0:
        raise ValueError(
            f"Vector dimension mismatch or empty: {len(u_flat)} vs {len(v_flat)}."
        )

    if not (np.isfinite(u_flat).all() and np.isfinite(v_flat).all()):
        raise InvalidEmbeddingError("Embedding vectors contain non-finite values (NaN/Inf).")

    norm_u = float(np.linalg.norm(u_flat))
    norm_v = float(np.linalg.norm(v_flat))

    # Explicit protection against zero-length vectors
    if norm_u < 1e-7 or norm_v < 1e-7:
        return 0.0

    u_unit = u_flat / norm_u
    v_unit = v_flat / norm_v

    cosine = float(np.dot(u_unit, v_unit))
    return float(np.clip(cosine, -1.0, 1.0))


def calculate_display_score(raw_cosine: float) -> float:
    """Linearly map raw cosine [-1.0, 1.0] to a normalized display index [0.0, 100.0].

    Formula: s_display = ((raw_cosine + 1.0) / 2.0) * 100.0
    """
    clipped = max(-1.0, min(1.0, raw_cosine))
    score = ((clipped + 1.0) / 2.0) * 100.0
    return round(float(score), 2)


class RealFacialEmbeddingEngine(FacialEmbeddingEngine):
    """Production facial embedding and comparison engine backed by YuNet and SFace."""

    def __init__(
        self,
        yunet_path: Optional[str] = None,
        sface_path: Optional[str] = None,
        score_threshold: float = 0.35,
        nms_threshold: float = 0.3,
    ) -> None:
        self.yunet_path = os.path.abspath(yunet_path or DEFAULT_YUNET_PATH)
        self.sface_path = os.path.abspath(sface_path or DEFAULT_SFACE_PATH)
        self.score_threshold = score_threshold
        self.nms_threshold = nms_threshold

        self.detector = None
        self.recognizer = None
        self._init_error = None
        self._model_ready = False

        self._init_models()

    def _init_models(self) -> None:
        """Attempt to load and initialize YuNet detector and SFace recognizer."""
        try:
            if not os.path.isfile(self.yunet_path):
                raise FileNotFoundError(
                    f"YuNet detector weights not found at: {self.yunet_path}"
                )
            if not os.path.isfile(self.sface_path):
                raise FileNotFoundError(
                    f"SFace recognizer weights not found at: {self.sface_path}"
                )

            # Initialize detector with default canvas size (updated per image)
            self.detector = cv2.FaceDetectorYN.create(
                model=self.yunet_path,
                config="",
                input_size=(320, 320),
                score_threshold=self.score_threshold,
                nms_threshold=self.nms_threshold,
                top_k=5000,
            )

            # Initialize SFace recognizer
            self.recognizer = cv2.FaceRecognizerSF.create(
                model=self.sface_path,
                config="",
            )

            self._model_ready = True
            self._init_error = None
        except Exception as exc:
            self.detector = None
            self.recognizer = None
            self._model_ready = False
            self._init_error = str(exc)

    def is_ready(self) -> bool:
        """Return True if both detector and embedding models are active and loaded."""
        return self._model_ready and self.detector is not None and self.recognizer is not None

    def get_metadata(self) -> EngineMetadata:
        """Return comprehensive engine metadata and operational state."""
        status = EngineStatus.ACTIVE if self.is_ready() else EngineStatus.OFFLINE
        desc = (
            "Local neural inference engine using YuNet 5-point landmark detector and SFace "
            "128-d hyperspherical cosine embedding backbone. Licensed under Apache 2.0."
            if self.is_ready()
            else f"Engine unavailable: {self._init_error or 'Weights unmounted'}"
        )

        return EngineMetadata(
            engine_id="facecore-sface-yunet-v2",
            name="SFace (SphereFace2) + YuNet",
            version="2021dec-2023mar",
            status=status,
            is_mock_data=False,
            description=desc,
            supported_models=[
                "YuNet (Fast 5-point facial landmark detector)",
                "SFace (128-d hyperspherical margin embedding)",
            ],
            embedding_dimension=128,
            inference_device="CPU",
            weights_license="Apache-2.0 (OpenCV Model Zoo)",
        )

    def detect_and_extract_face(
        self,
        image_bytes: bytes,
        slot_label: str = "Image",
    ) -> Tuple[np.ndarray, np.ndarray, float, List[int], int]:
        """Decode image, enforce single face constraint, crop/align, and extract embedding.

        Returns: (aligned_crop, embedding, confidence, bbox, face_count)
        Raises:
            ModelNotReadyError: If models are not loaded.
            NoFaceDetectedError: If 0 faces found.
            MultipleFacesDetectedError: If >1 faces found.
            FaceEngineError: If image cannot be decoded.
        """
        if not self.is_ready():
            raise ModelNotReadyError(
                f"Facial embedding engine is offline: {self._init_error or 'Weights missing'}"
            )

        # Safe decode image bytes using OpenCV
        np_arr = np.frombuffer(image_bytes, np.uint8)
        bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise FaceEngineError(f"Failed to decode image data for {slot_label}.")

        height, width = bgr.shape[:2]
        self.detector.setInputSize((width, height))
        _, raw_faces = self.detector.detect(bgr)

        face_count = 0 if raw_faces is None else len(raw_faces)

        if face_count == 0:
            raise NoFaceDetectedError(slot_label=slot_label)

        if face_count > 1:
            raise MultipleFacesDetectedError(count=face_count, slot_label=slot_label)

        face = raw_faces[0]
        confidence = float(face[-1])
        bbox = [int(face[0]), int(face[1]), int(face[2]), int(face[3])]

        # Align crop to canonical 112x112 via 5-point landmark similarity transform
        aligned_crop = self.recognizer.alignCrop(bgr, face)

        # Extract 128-d embedding
        raw_feat = self.recognizer.feature(aligned_crop)
        emb = raw_feat.flatten().astype(np.float32)

        # Strict validation
        if len(emb) != 128:
            raise InvalidEmbeddingError(f"Unexpected embedding dimension: {len(emb)} != 128")

        if not np.isfinite(emb).all():
            raise InvalidEmbeddingError("Embedding vector contains NaN or Infinite values.")

        norm = float(np.linalg.norm(emb))
        if norm < 1e-7:
            raise InvalidEmbeddingError("Degenerate near-zero embedding vector produced.")

        # Unit normalize embedding
        unit_emb = emb / norm

        return aligned_crop, unit_emb, confidence, bbox, face_count

    def extract_features(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """Extract a 128-d normalized embedding vector. Returns None if face is absent or multiple."""
        try:
            _, unit_emb, _, _, _ = self.detect_and_extract_face(image_bytes)
            return unit_emb
        except Exception:
            return None

    def compare_faces(
        self,
        image_a_bytes: bytes,
        image_b_bytes: bytes,
        diag_a: ImageQualityDiagnostics,
        diag_b: ImageQualityDiagnostics,
    ) -> ComparisonResponse:
        """Run complete pairwise biometric evaluation with single-face enforcement.

        Computes genuine mathematical cosine similarity and populates telemetry.
        """
        if not self.is_ready():
            raise ModelNotReadyError(
                f"Facial embedding engine is offline: {self._init_error or 'Weights missing'}"
            )

        start_time = time.perf_counter()

        # Process Probe (Image A)
        _, emb_a, conf_a, bbox_a, count_a = self.detect_and_extract_face(
            image_a_bytes,
            slot_label="Image A (Probe)"
        )
        diag_a.face_detected = True
        diag_a.face_count = count_a
        diag_a.face_confidence = round(conf_a, 4)
        diag_a.face_bounding_box = bbox_a

        # Process Reference (Image B)
        _, emb_b, conf_b, bbox_b, count_b = self.detect_and_extract_face(
            image_b_bytes,
            slot_label="Image B (Reference)"
        )
        diag_b.face_detected = True
        diag_b.face_count = count_b
        diag_b.face_confidence = round(conf_b, 4)
        diag_b.face_bounding_box = bbox_b

        # Compute exact cosine similarity between normalized 128-d unit vectors
        raw_cosine = compute_cosine_similarity(emb_a, emb_b)
        display_score = calculate_display_score(raw_cosine)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Provisional experimental decision
        is_match = bool(raw_cosine >= PROVISIONAL_COSINE_THRESHOLD)

        threshold_notice = (
            "EXPERIMENTAL / PROVISIONAL THRESHOLD: The decision threshold (0.363 cosine similarity) "
            "is derived from published SFace literature on standardized benchmark datasets. It has NOT "
            "been calibrated on your operational test distribution. A similarity score is continuous "
            "vector proximity in hyperspherical space, never 100% proof of identity."
        )

        interpretation_notice = (
            f"EVALUATION COMPLETE (SFace + YuNet): Extracted 128-dimensional hyperspherical "
            f"embeddings. Raw cosine similarity: {raw_cosine:.4f} (Transformed display index: {display_score:.1f}/100). "
            f"Processing completed in {elapsed_ms:.1f}ms on CPU. "
            "NOTE: High similarity indicates facial feature proximity, but does NOT constitute "
            "absolute proof that both images depict the same person."
        )

        now_iso = datetime.now(timezone.utc).isoformat()

        return ComparisonResponse(
            status="evaluation_completed",
            timestamp=now_iso,
            engine=self.get_metadata(),
            image_a_diagnostics=diag_a,
            image_b_diagnostics=diag_b,
            similarity_score=round(raw_cosine, 4),
            raw_cosine_similarity=round(raw_cosine, 4),
            transformed_display_score=display_score,
            provisional_threshold=PROVISIONAL_COSINE_THRESHOLD,
            is_match=is_match,
            threshold_notice=threshold_notice,
            inference_latency_ms=round(elapsed_ms, 2),
            interpretation_notice=interpretation_notice,
        )
