"""Pydantic schemas for request/response serialization."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class EngineStatus(str, Enum):
    PENDING_INTEGRATION = "pending_integration"
    ACTIVE = "active"
    DEGRADED = "degraded"
    OFFLINE = "offline"


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
    face_count: int = Field(0, description="Total number of detected faces")
    face_confidence: Optional[float] = Field(None, description="Detector confidence score")
    face_bounding_box: Optional[List[int]] = Field(None, description="[x, y, w, h] bounding box")
    
    passes_quality_check: bool = Field(..., description="Whether image meets baseline comparison thresholds")
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
        description="Detailed engine description"
    )
    supported_models: List[str] = Field(
        default_factory=lambda: [
            "YuNet (Face Detection & 5-point alignment)",
            "SFace (128-d Spherical Margin Embedding)",
        ],
        description="Active model backbones"
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
        None,
        description="Raw cosine similarity [-1.0, 1.0]. None if engine unavailable or face error."
    )
    raw_cosine_similarity: Optional[float] = Field(
        None,
        description="Mathematically exact dot product of unit-normalized embeddings [-1.0, 1.0]"
    )
    transformed_display_score: Optional[float] = Field(
        None,
        description="Linearly scaled display index [0.0 - 100.0] derived as ((cosine + 1) / 2) * 100"
    )
    provisional_threshold: Optional[float] = Field(
        0.363,
        description="Provisional experimental cosine threshold for SFace (uncalibrated on custom operational data)"
    )
    is_match: Optional[bool] = Field(
        None,
        description="Provisional threshold verdict. Strictly experimental and not a definitive identity confirmation."
    )
    threshold_notice: Optional[str] = Field(
        None,
        description="Notice stating that match threshold is experimental and provisional."
    )
    inference_latency_ms: Optional[float] = Field(
        None,
        description="Total CPU execution latency in milliseconds"
    )
    interpretation_notice: str = Field(
        ...,
        description="Mandatory scientific interpretation notice and disclaimers."
    )


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "FACECORE AI"
    version: str = "0.2.0-alpha"
    timestamp: str
    engine_status: EngineStatus
    security_mode: str = "ephemeral_local_strict"
