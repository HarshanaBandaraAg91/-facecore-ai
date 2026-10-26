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
    
    passes_quality_check: bool = Field(..., description="Whether image meets baseline comparison thresholds")
    warnings: List[str] = Field(default_factory=list, description="Quality or fidelity advisories")


class ImageValidationResponse(BaseModel):
    is_valid: bool = Field(..., description="True if image passed file signature, size, and decoding checks")
    error_message: Optional[str] = Field(None, description="Human-readable reason for rejection if invalid")
    diagnostics: Optional[ImageQualityDiagnostics] = Field(None, description="Technical diagnostics if valid")


class EngineMetadata(BaseModel):
    engine_id: str = Field("stub-modular-v1", description="Identifier for facial embedding engine")
    name: str = Field("Modular Stub Interface", description="Display name of verification backend")
    version: str = Field("0.1.0-alpha", description="Engine version")
    status: EngineStatus = Field(EngineStatus.PENDING_INTEGRATION, description="Operational status")
    is_mock_data: bool = Field(False, description="Explicit indicator that results are NOT fabricated mock scores")
    description: str = Field(
        "Modular inference engine placeholder awaiting embedding model integration in Phase 2.",
        description="Detailed engine status"
    )
    supported_models: List[str] = Field(
        default_factory=lambda: ["ArcFace (ResNet-100)", "AdaFace (IR-50)", "MagFace (ResNet-50)"],
        description="Planned facial recognition backbones"
    )


class ComparisonResponse(BaseModel):
    status: str = Field("engine_pending_integration", description="Workflow state")
    timestamp: str = Field(..., description="ISO 8601 evaluation timestamp")
    engine: EngineMetadata = Field(..., description="Engine metadata and readiness status")
    image_a_diagnostics: ImageQualityDiagnostics = Field(..., description="Diagnostics for Probe Image A")
    image_b_diagnostics: ImageQualityDiagnostics = Field(..., description="Diagnostics for Reference Image B")
    
    # Strict rule: No fabricated scores in Step 01!
    similarity_score: Optional[float] = Field(
        None,
        description="Normalized cosine similarity [0.0 - 1.0]. Null when engine is pending integration."
    )
    is_match: Optional[bool] = Field(
        None,
        description="Decision threshold verdict. Null when engine is pending integration."
    )
    interpretation_notice: str = Field(
        ...,
        description="Mandatory scientific interpretation notice and disclaimers."
    )


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "FACECORE AI"
    version: str = "0.1.0-alpha"
    timestamp: str
    engine_status: EngineStatus
    security_mode: str = "ephemeral_local_strict"
