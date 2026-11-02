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
import threading
from datetime import datetime, timezone
from typing import Optional, Tuple, List, Any, Dict
import numpy as np
import cv2

from app.models.schemas import (
    EngineStatus,
    EngineMetadata,
    ComparisonResponse,
    ImageQualityDiagnostics,
    DetectedFaceSummary,
)
from app.engine.base import FacialEmbeddingEngine
from app.services.face_detector import (
    shared_face_detector,
    InvalidCropCoordinatesError,
    DetectedFace,
)

# Default path constants for model weights
DEFAULT_WEIGHTS_DIR = os.path.join(os.path.dirname(__file__), "..", "weights")
DEFAULT_YUNET_PATH = os.path.join(DEFAULT_WEIGHTS_DIR, "face_detection_yunet_2023mar.onnx")
DEFAULT_SFACE_PATH = os.path.join(DEFAULT_WEIGHTS_DIR, "face_recognition_sface_2021dec.onnx")

# Thread safety lock protecting C++ forward pass of OpenCV FaceRecognizerSF & FaceDetectorYN
_INFERENCE_LOCK = threading.Lock()

# Named operating threshold profiles from Step 09.2 audit
THRESHOLD_PROFILES: Dict[str, Dict[str, Any]] = {
    "high_security": {
        "threshold": 0.3600,
        "name": "High Security Profile",
        "description": "Calibrated for high security environments (Target FAR <= 0.10%). Out-of-fold TAR: 98.47%.",
        "target_far": 0.001,
        "tar_estimate": 0.9847,
        "confidence_upper_bound_far": 0.00292,
    },
    "balanced": {
        "threshold": 0.3132,
        "name": "Balanced Profile",
        "description": "Equal Error Rate (EER) crossover on canonical LFW. Accuracy: 99.50%, FAR: 0.43%, FRR: 0.57%.",
        "target_far": 0.0043,
        "tar_estimate": 0.9943,
        "confidence_upper_bound_far": 0.00725,
    },
    "high_convenience": {
        "threshold": 0.2500,
        "name": "High Convenience Profile",
        "description": "Optimized to minimize false rejections (Target FRR <= 0.10%). TAR > 99.90%.",
        "target_far": 0.015,
        "tar_estimate": 0.9990,
        "confidence_upper_bound_far": 0.0198,
    },
}

# Baseline reference threshold
PROVISIONAL_COSINE_THRESHOLD = 0.3132


def resolve_threshold(profile: str = "balanced", custom_threshold: Optional[float] = None) -> tuple[str, float]:
    """Resolve threshold profile name and numerical float value."""
    key = (profile or "balanced").lower()
    if key == "custom" and custom_threshold is not None:
        return ("custom", float(custom_threshold))
    elif key in THRESHOLD_PROFILES:
        return (key, THRESHOLD_PROFILES[key]["threshold"])
    elif key == "custom":
        return ("custom", THRESHOLD_PROFILES["balanced"]["threshold"])
    return ("balanced", THRESHOLD_PROFILES["balanced"]["threshold"])



class FaceEngineError(Exception):
    """Base exception for facial engine processing errors."""
    pass


class ModelNotReadyError(FaceEngineError):
    """Raised when model weights are not loaded or missing."""
    pass


class InvalidFaceSelectionError(FaceEngineError):
    """Raised when selected face index is invalid or out of range."""
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
        selected_face_index: Optional[int] = None,
        crop_box: Optional[List[int]] = None,
    ) -> Tuple[np.ndarray, np.ndarray, float, List[int], int]:
        """Decode image, enforce face constraint / selection, crop/align, and extract embedding.

        Returns: (aligned_crop, embedding, confidence, bbox, face_count)
        Raises:
            ModelNotReadyError: If models are not loaded.
            NoFaceDetectedError: If 0 faces found.
            MultipleFacesDetectedError: If >1 faces found and none selected.
            InvalidFaceSelectionError: If selected face index is out of bounds.
            FaceEngineError: If image cannot be decoded.
        """
        if not self.is_ready():
            raise ModelNotReadyError(
                f"Facial embedding engine is offline: {self._init_error or 'Weights missing'}"
            )

        det_result = shared_face_detector.detect_faces(image_bytes, crop_box=crop_box)
        face_count = det_result.face_count

        if face_count == 0:
            raise NoFaceDetectedError(slot_label=slot_label)

        if face_count > 1:
            if selected_face_index is None:
                raise MultipleFacesDetectedError(count=face_count, slot_label=slot_label)
            if selected_face_index < 0 or selected_face_index >= face_count:
                raise InvalidFaceSelectionError(
                    f"Selected face index {selected_face_index} is invalid for {slot_label}. "
                    f"Must be between 0 and {face_count - 1}."
                )
            face = det_result.faces[selected_face_index]
        else:
            face = det_result.faces[0]

        # Safe decode image bytes using OpenCV
        np_arr = np.frombuffer(image_bytes, np.uint8)
        bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise FaceEngineError(f"Failed to decode image data for {slot_label}.")

        # Align crop to canonical 112x112 via 5-point landmark similarity transform & extract embedding
        with _INFERENCE_LOCK:
            aligned_crop = self.recognizer.alignCrop(bgr, face.raw_face)
            raw_feat = self.recognizer.feature(aligned_crop)

        emb = raw_feat.flatten().astype(np.float32)

        # Free temporary decoded raw image array and raw features
        del bgr
        del raw_feat

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

        return aligned_crop, unit_emb, face.confidence, face.box, face_count

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
        selected_face_a: Optional[int] = None,
        selected_face_b: Optional[int] = None,
        crop_box_a: Optional[List[int]] = None,
        crop_box_b: Optional[List[int]] = None,
        threshold_profile: str = "balanced",
        custom_threshold: Optional[float] = None,
    ) -> ComparisonResponse:
        """Run complete pairwise biometric evaluation with single-face enforcement or explicit user selection.

        Computes genuine mathematical cosine similarity, resolves operational threshold profile,
        and populates structured telemetry without persisting images or embeddings.
        """
        if not self.is_ready():
            raise ModelNotReadyError(
                f"Facial embedding engine is offline: {self._init_error or 'Weights missing'}"
            )

        start_time = time.perf_counter()

        # Process Probe (Image A)
        t_a0 = time.perf_counter()
        _, emb_a, conf_a, bbox_a, count_a = self.detect_and_extract_face(
            image_a_bytes,
            slot_label="Image A (Probe)",
            selected_face_index=selected_face_a,
            crop_box=crop_box_a,
        )
        t_a_ms = (time.perf_counter() - t_a0) * 1000.0

        diag_a.face_detected = True
        diag_a.face_count = count_a
        diag_a.face_confidence = round(conf_a, 4)
        diag_a.face_bounding_box = bbox_a
        diag_a.selected_face_index = selected_face_a if count_a > 1 else (0 if count_a == 1 else None)
        diag_a.crop_bounding_box = crop_box_a

        # Process Reference (Image B)
        t_b0 = time.perf_counter()
        _, emb_b, conf_b, bbox_b, count_b = self.detect_and_extract_face(
            image_b_bytes,
            slot_label="Image B (Reference)",
            selected_face_index=selected_face_b,
            crop_box=crop_box_b,
        )
        t_b_ms = (time.perf_counter() - t_b0) * 1000.0

        diag_b.face_detected = True
        diag_b.face_count = count_b
        diag_b.face_confidence = round(conf_b, 4)
        diag_b.face_bounding_box = bbox_b
        diag_b.selected_face_index = selected_face_b if count_b > 1 else (0 if count_b == 1 else None)
        diag_b.crop_bounding_box = crop_box_b

        # Compute exact cosine similarity between normalized 128-d unit vectors
        raw_cosine = compute_cosine_similarity(emb_a, emb_b)
        display_score = calculate_display_score(raw_cosine)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Resolve operational threshold profile
        profile_key = threshold_profile.lower()
        if profile_key == "custom" and custom_threshold is not None:
            threshold_used = float(custom_threshold)
            profile_name = "Custom Threshold"
            tar_est = None
            upper_far = None
            threshold_desc = f"User-configured custom threshold (tau = {threshold_used:.4f})."
        elif profile_key in THRESHOLD_PROFILES:
            prof = THRESHOLD_PROFILES[profile_key]
            threshold_used = prof["threshold"]
            profile_name = prof["name"]
            tar_est = prof["tar_estimate"]
            upper_far = prof["confidence_upper_bound_far"]
            threshold_desc = prof["description"]
        else:
            prof = THRESHOLD_PROFILES["balanced"]
            threshold_used = prof["threshold"]
            profile_name = prof["name"]
            profile_key = "balanced"
            tar_est = prof["tar_estimate"]
            upper_far = prof["confidence_upper_bound_far"]
            threshold_desc = prof["description"]

        # Final decision
        is_match = bool(raw_cosine >= threshold_used)
        decision_str = "MATCH" if is_match else "NO_MATCH"

        threshold_notice = (
            f"OPERATIONAL THRESHOLD PROFILE [{profile_name}]: Applied decision threshold "
            f"tau = {threshold_used:.4f}. {threshold_desc} "
            "A similarity score is continuous vector proximity in 128-d hyperspherical space, "
            "never an absolute identity verdict."
        )

        stat_notice = (
            f"STATISTICAL CONFIDENCE: At threshold tau = {threshold_used:.4f}, the empirical out-of-fold "
            f"true acceptance rate is estimated at {tar_est * 100:.2f}% (on canonical LFW). "
            f"The 95% Clopper-Pearson upper confidence bound on population FAR is <= {upper_far * 100:.3f}%."
            if (tar_est is not None and upper_far is not None)
            else "STATISTICAL CONFIDENCE: Custom threshold operates outside standardized calibrated benchmarks."
        )

        interpretation_notice = (
            f"EVALUATION COMPLETE (SFace + YuNet): Extracted 128-dimensional hyperspherical "
            f"embeddings. Raw cosine similarity: {raw_cosine:.4f} (Display Index: {display_score:.1f}/100). "
            f"Decision: {decision_str} (Threshold tau = {threshold_used:.4f}). "
            f"Total execution latency: {elapsed_ms:.1f}ms on CPU. "
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
            threshold_profile=profile_key,
            threshold_used=round(threshold_used, 4),
            decision=decision_str,
            is_match=is_match,
            provisional_threshold=round(threshold_used, 4),
            threshold_notice=threshold_notice,
            statistical_confidence_notice=stat_notice,
            inference_latency_ms=round(elapsed_ms, 2),
            detection_latency_ms=round((t_a_ms + t_b_ms) / 2.0, 2),
            embedding_latency_ms=round(elapsed_ms - ((t_a_ms + t_b_ms) / 2.0), 2),
            interpretation_notice=interpretation_notice,
        )
