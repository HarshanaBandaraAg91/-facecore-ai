"""Pydantic schemas for request/response serialization (Production Step 10)."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EngineStatus(str, Enum):
    PENDING_INTEGRATION = "pending_integration"
    ACTIVE = "active"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class ThresholdProfile(str, Enum):
    HIGH_SECURITY = "high_security"       # Target FAR <= 0.10% (tau = 0.3600)
    BALANCED = "balanced"                 # Equal Error Rate Crossover (tau = 0.3132)
    HIGH_CONVENIENCE = "high_convenience" # Target FRR <= 0.10% (tau = 0.2500)
    CUSTOM = "custom"                     # User-specified threshold


class ErrorCode(str, Enum):
    NO_FACE_DETECTED = "NO_FACE_DETECTED"
    MULTIPLE_FACES_DETECTED = "MULTIPLE_FACES_DETECTED"
    INVALID_FACE_SELECTION = "INVALID_FACE_SELECTION"
    INVALID_CROP_COORDINATES = "INVALID_CROP_COORDINATES"
    IMAGE_CORRUPT = "IMAGE_CORRUPT"
    RESOLUTION_TOO_LOW = "RESOLUTION_TOO_LOW"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    INVALID_EMBEDDING = "INVALID_EMBEDDING"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorDetail(BaseModel):
    error_code: ErrorCode = Field(..., description="Machine-readable error enumeration code")
    message: str = Field(..., description="Concise human-readable description of error")
    detail: str = Field(..., description="Diagnostic detail or failure remediation advice")
    timestamp: str = Field(..., description="ISO 8601 error generation timestamp")
    request_id: Optional[str] = Field(None, description="Correlation identifier for request tracing")


class DetectedFaceSummary(BaseModel):
    index: int = Field(..., description="0-based face index ordered by confidence")
    box: List[int] = Field(..., description="[x, y, w, h] bounding box in image coordinates")
    confidence: float = Field(..., description="Detector confidence score [0.0 - 1.0]")
    landmarks: List[List[float]] = Field(default_factory=list, description="5 facial landmarks [[x, y], ...]")
    quality_advisories: List[str] = Field(default_factory=list, description="Face-specific quality advisories")


class ImageQualityDiagnostics(BaseModel):
    filename: str = Field(..., description="Original client filename")
    format: str = Field(..., description="Detected image format (JPEG, PNG, WEBP)")
    color_mode: str = Field(..., description="Color space/mode (RGB, RGBA, L)")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    aspect_ratio: str = Field(..., description="Calculated aspect ratio string")
    file_size_bytes: int = Field(..., description="File size in bytes")
    sha256_hash: str = Field(..., description="Cryptographic SHA-256 fingerprint (prefix)")

    # Technical quality diagnostics
    estimated_sharpness: float = Field(..., description="Laplacian gradient variance measure")
    contrast_std: float = Field(..., description="Luminance standard deviation")
    brightness_mean: float = Field(..., description="Mean luma intensity (0-255)")
    resolution_category: str = Field(..., description="Fidelity tier: Low (<120p), Standard, High (>1080p)")

    # Face detection telemetry
    face_detected: bool = Field(False, description="Whether a face was located by the detector")
    face_count: int = Field(0, description="Total number of detected plausible faces")
    face_confidence: Optional[float] = Field(None, description="Detector confidence score of primary/selected face")
    face_bounding_box: Optional[List[int]] = Field(None, description="[x, y, w, h] bounding box of primary/selected face")
    detected_faces: List[DetectedFaceSummary] = Field(default_factory=list, description="List of all detected plausible faces")
    selected_face_index: Optional[int] = Field(None, description="Selected face index for multi-face comparison")
    crop_bounding_box: Optional[List[int]] = Field(None, description="Applied manual crop box [x, y, w, h] if any")

    passes_quality_check: bool = Field(..., description="Whether image meets baseline comparison thresholds and contains a valid face")
    warnings: List[str] = Field(default_factory=list, description="Quality or fidelity advisories")


class ImageValidationResponse(BaseModel):
    is_valid: bool = Field(..., description="True if image passed file signature, size, and decoding checks")
    error_message: Optional[str] = Field(None, description="Human-readable reason for rejection if invalid")
    diagnostics: Optional[ImageQualityDiagnostics] = Field(None, description="Technical diagnostics if valid")


class EngineMetadata(BaseModel):
    engine_id: str = Field("facecore-sface-yunet-v2", description="Identifier for facial embedding engine")
    name: str = Field("SFace + YuNet (OpenCV Model Zoo)", description="Display name of verification backend")
    version: str = Field("2021dec-2023mar", description="Engine version")
    status: EngineStatus = Field(EngineStatus.ACTIVE, description="Operational status")
    is_mock_data: bool = Field(False, description="Explicit indicator that results are NOT fabricated mock scores")
    description: str = Field(
        "Real local neural inference engine using YuNet 5-point landmark detector and SFace 128-d cosine embedding model.",
        description="Detailed engine description",
    )
    supported_models: List[str] = Field(
        default_factory=lambda: [
            "YuNet (Face Detection & 5-point alignment)",
            "SFace (128-d Spherical Margin Embedding)",
        ],
        description="Active model backbones",
    )
    embedding_dimension: int = Field(128, description="Verified vector dimension of feature embeddings")
    inference_device: str = Field("CPU", description="Inference compute device")
    weights_license: str = Field("Apache-2.0", description="Primary-source license for model weights")


class ComparisonResponse(BaseModel):
    status: str = Field("evaluation_completed", description="Workflow state")
    timestamp: str = Field(..., description="ISO 8601 evaluation timestamp")
    engine: EngineMetadata = Field(..., description="Engine metadata and readiness status")
    image_a_diagnostics: ImageQualityDiagnostics = Field(..., description="Diagnostics for Probe Image A")
    image_b_diagnostics: ImageQualityDiagnostics = Field(..., description="Diagnostics for Reference Image B")

    # Real mathematical scores
    similarity_score: Optional[float] = Field(
        None, description="Raw cosine similarity [-1.0, 1.0]. None if engine unavailable or face error."
    )
    raw_cosine_similarity: Optional[float] = Field(
        None, description="Mathematically exact dot product of unit-normalized embeddings [-1.0, 1.0]"
    )
    transformed_display_score: Optional[float] = Field(
        None, description="Linearly scaled display index [0.0 - 100.0] derived as ((cosine + 1) / 2) * 100"
    )

    # Threshold & Decision Telemetry (Step 09.2 Profiles)
    threshold_profile: str = Field("balanced", description="Named decision threshold profile used")
    threshold_used: float = Field(0.3132, description="Applied cosine decision threshold value")
    decision: str = Field("NO_MATCH", description="'MATCH' if raw_cosine >= threshold_used else 'NO_MATCH'")
    is_match: Optional[bool] = Field(None, description="Boolean decision flag")
    provisional_threshold: Optional[float] = Field(0.3132, description="Reference threshold (for backward compatibility)")

    # Latency Telemetry Breakdown
    inference_latency_ms: Optional[float] = Field(None, description="Total CPU execution latency in milliseconds")
    detection_latency_ms: Optional[float] = Field(None, description="Face detection latency in milliseconds")
    embedding_latency_ms: Optional[float] = Field(None, description="Recognition embedding latency in milliseconds")

    # Notices & Disclaimers
    threshold_notice: Optional[str] = Field(None, description="Context on threshold provenance and validation split")
    statistical_confidence_notice: Optional[str] = Field(
        None, description="Statistical uncertainty statement and Clopper-Pearson bound disclosure"
    )
    interpretation_notice: str = Field(..., description="Mandatory scientific interpretation notice and disclaimers.")


class ComparisonHistoryRecord(BaseModel):
    id: int = Field(..., description="Unique record identifier")
    timestamp: str = Field(..., description="ISO 8601 evaluation timestamp")
    probe_hash_prefix: str = Field(..., description="SHA-256 fingerprint prefix of Image A")
    reference_hash_prefix: str = Field(..., description="SHA-256 fingerprint prefix of Image B")
    similarity_score: Optional[float] = Field(None, description="Raw cosine similarity [-1.0, 1.0]")
    display_score: Optional[float] = Field(None, description="Transformed display index [0 - 100]")
    threshold_used: float = Field(..., description="Operating threshold used")
    threshold_profile: str = Field(..., description="Named profile used")
    is_match: bool = Field(..., description="Decision verdict")
    latency_ms: float = Field(..., description="Execution latency in milliseconds")
    face_count_a: int = Field(..., description="Detected faces in Image A")
    face_count_b: int = Field(..., description="Detected faces in Image B")
    quality_flags_a: List[str] = Field(default_factory=list, description="Advisory flags for Image A")
    quality_flags_b: List[str] = Field(default_factory=list, description="Advisory flags for Image B")
    status: str = Field(..., description="Comparison outcome: SUCCESS, FTA_NO_FACE, FTA_MULTIPLE_FACES, ERROR")


class DashboardStatsResponse(BaseModel):
    total_comparisons: int = Field(..., description="Total comparison evaluations recorded")
    successful_comparisons: int = Field(..., description="Total completed comparisons yielding valid similarity")
    matches_count: int = Field(..., description="Total comparisons classified as MATCH")
    non_matches_count: int = Field(..., description="Total comparisons classified as NO_MATCH")
    acquisition_failures: int = Field(..., description="Total pairs failing face acquisition (FTA)")
    fta_rate: float = Field(..., description="ISO/IEC 19795-1 Failure to Acquire rate [0.0 - 1.0]")
    fta_breakdown: Dict[str, int] = Field(default_factory=dict, description="FTA counts by failure category")
    recent_activity: List[ComparisonHistoryRecord] = Field(default_factory=list, description="Latest comparison records")
    benchmarks_summary: List[Dict[str, Any]] = Field(default_factory=list, description="Summary of verified benchmark datasets")
    engine_status: EngineStatus = Field(..., description="Operational status of backend engine")
    uptime_seconds: float = Field(..., description="Backend process uptime in seconds")


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "FACECORE AI"
    version: str = "1.0.0-prod"
    environment: str = "production"
    timestamp: str
    engine_status: EngineStatus
    security_mode: str = "ephemeral_local_strict"


class ReadinessResponse(BaseModel):
    status: str = Field(..., description="'ready' if all subsystems operational, else 'degraded'/'unavailable'")
    engine_ready: bool = Field(..., description="YuNet and SFace ONNX models loaded and verified")
    database_ready: bool = Field(..., description="SQLite connection open and migrations applied")
    weights_present: bool = Field(..., description="Model ONNX weight files verified on disk")
    sface_hash_verified: bool = Field(..., description="SFace weight checksum verified")
    yunet_hash_verified: bool = Field(..., description="YuNet weight checksum verified")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
