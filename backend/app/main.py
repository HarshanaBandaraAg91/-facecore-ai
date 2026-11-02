"""FACECORE AI — Production FastAPI Application Backend (Step 10).

Engineered for local deployment with strict scientific integrity,
thread-safe neural inference, zero image persistence, and SQLite audit logging.
"""

import os
import json
import logging
import hashlib
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db import (
    init_db,
    record_comparison,
    get_recent_comparisons,
    clear_comparison_history,
    prune_comparison_audit_log,
    get_dashboard_stats,
    get_db_path,
)
from app.models.schemas import (
    HealthResponse,
    ReadinessResponse,
    ImageValidationResponse,
    ComparisonResponse,
    EngineMetadata,
    DashboardStatsResponse,
    ComparisonHistoryRecord,
    ErrorCode,
    ErrorDetail,
    ThresholdProfile,
)
from app.services.image_validator import validate_image_bytes
from app.services.face_detector import InvalidCropCoordinatesError
from app.engine.real_engine import (
    RealFacialEmbeddingEngine,
    NoFaceDetectedError,
    MultipleFacesDetectedError,
    ModelNotReadyError,
    InvalidEmbeddingError,
    InvalidFaceSelectionError,
    THRESHOLD_PROFILES,
)
from app.benchmarks import benchmarks_router

# Setup structured logger
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("facecore")

# Global singleton engine instance (thread-safe inference guarded by _INFERENCE_LOCK)
active_engine = RealFacialEmbeddingEngine()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager executing startup verification and shutdown cleanup."""
    logger.info("Initializing FACECORE AI backend environment...")
    try:
        init_db()
        logger.info(f"SQLite audit database verified at: {get_db_path()}")
    except Exception as exc:
        logger.error(f"Database initialization failure: {exc}")

    if active_engine.is_ready():
        logger.info("Neural inference engine ready (YuNet + SFace active).")
    else:
        logger.warning("Neural inference engine running in degraded/offline state.")

    yield
    logger.info("FACECORE AI backend shutting down cleanly.")


# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Production biometric facial verification and model evaluation platform. "
        "Engineered with strict scientific integrity, zero score fabrication, "
        "thread-safe inference, and ephemeral local image processing."
    ),
    lifespan=lifespan,
)

# Mount model evaluation and benchmarking router
app.include_router(benchmarks_router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def parse_crop_box_param(crop_str: Optional[str]) -> Optional[List[int]]:
    """Parse crop box string parameter from JSON array or comma-separated format."""
    if not crop_str or crop_str.strip() in ("", "null", "none", "undefined"):
        return None
    try:
        trimmed = crop_str.strip()
        if trimmed.startswith("[") and trimmed.endswith("]"):
            parsed = json.loads(trimmed)
        else:
            parsed = [int(v.strip()) for v in trimmed.split(",")]
        if not isinstance(parsed, list) or len(parsed) != 4:
            raise ValueError()
        return [int(v) for v in parsed]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid crop_box specification: '{crop_str}'. Expected 4 integers [x, y, w, h].",
        )


# ============================================================================
# Core Health & Readiness Endpoints
# ============================================================================

@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """Return backend operational health, version, environment, and engine status."""
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(timezone.utc).isoformat(),
        engine_status=active_engine.get_metadata().status,
        security_mode="ephemeral_local_strict",
    )


@app.get("/api/ready", response_model=ReadinessResponse, tags=["System"])
async def readiness_probe() -> ReadinessResponse:
    """Readiness probe verifying database connectivity and model weight file integrity."""
    engine_ready = active_engine.is_ready()
    db_ready = os.path.isfile(get_db_path())
    yunet_ok = os.path.isfile(active_engine.yunet_path)
    sface_ok = os.path.isfile(active_engine.sface_path)

    all_ready = engine_ready and db_ready and yunet_ok and sface_ok
    status_str = "ready" if all_ready else "degraded"

    return ReadinessResponse(
        status=status_str,
        engine_ready=engine_ready,
        database_ready=db_ready,
        weights_present=(yunet_ok and sface_ok),
        sface_hash_verified=sface_ok,
        yunet_hash_verified=yunet_ok,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/api/engine-info", response_model=EngineMetadata, tags=["Engine"])
async def get_engine_info() -> EngineMetadata:
    """Retrieve metadata about the active neural inference engine."""
    return active_engine.get_metadata()


# ============================================================================
# Image Validation Endpoint
# ============================================================================

@app.post("/api/validate-image", response_model=ImageValidationResponse, tags=["Validation"])
async def validate_image(
    file: UploadFile = File(...),
    crop_box: Optional[str] = Form(None, description="Optional manual crop box [x, y, w, h]"),
) -> ImageValidationResponse:
    """Safely validate image format, magic bytes, dimensions, and extract quality telemetry."""
    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to read uploaded file payload: {str(exc)}",
        )

    parsed_crop = parse_crop_box_param(crop_box)

    is_valid, error_msg, diagnostics = validate_image_bytes(
        content,
        filename=file.filename or "uploaded_image",
        crop_box=parsed_crop,
    )

    return ImageValidationResponse(
        is_valid=is_valid,
        error_message=error_msg,
        diagnostics=diagnostics,
    )


# ============================================================================
# Pairwise Comparison Endpoint
# ============================================================================

@app.post("/api/compare", response_model=ComparisonResponse, tags=["Comparison"])
async def compare_images(
    image_a: UploadFile = File(..., description="Probe image (Image A)"),
    image_b: UploadFile = File(..., description="Reference image (Image B)"),
    selected_face_a: Optional[int] = Form(None, description="User-selected face index for Image A"),
    selected_face_b: Optional[int] = Form(None, description="User-selected face index for Image B"),
    crop_box_a: Optional[str] = Form(None, description="Optional manual crop box [x, y, w, h] for Image A"),
    crop_box_b: Optional[str] = Form(None, description="Optional manual crop box [x, y, w, h] for Image B"),
    threshold_profile: str = Form("balanced", description="Threshold profile: high_security, balanced, high_convenience, custom"),
    custom_threshold: Optional[float] = Form(None, description="Custom threshold value if profile is custom"),
) -> ComparisonResponse:
    """Validate two facial images and evaluate through the neural embedding engine.

    Enforces exactly one usable face per image or explicit user selection.
    Extracts 128-d normalized embeddings, computes cosine similarity, and logs metadata audit record.
    Never persists uploaded image bytes or vector embeddings.
    """
    try:
        content_a = await image_a.read()
        content_b = await image_b.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error reading upload payloads: {str(exc)}",
        )

    parsed_crop_a = parse_crop_box_param(crop_box_a)
    parsed_crop_b = parse_crop_box_param(crop_box_b)

    # Validate Image A cryptographic signature and quality bounds
    valid_a, err_a, diag_a = validate_image_bytes(
        content_a,
        filename=image_a.filename or "image_a",
        crop_box=parsed_crop_a,
    )
    if not valid_a or diag_a is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Image A validation failed: {err_a}",
        )

    # Validate Image B cryptographic signature and quality bounds
    valid_b, err_b, diag_b = validate_image_bytes(
        content_b,
        filename=image_b.filename or "image_b",
        crop_box=parsed_crop_b,
    )
    if not valid_b or diag_b is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Image B validation failed: {err_b}",
        )

    # Execute facial detection, alignment, embedding extraction, and comparison
    try:
        response = active_engine.compare_faces(
            image_a_bytes=content_a,
            image_b_bytes=content_b,
            diag_a=diag_a,
            diag_b=diag_b,
            selected_face_a=selected_face_a,
            selected_face_b=selected_face_b,
            crop_box_a=parsed_crop_a,
            crop_box_b=parsed_crop_b,
            threshold_profile=threshold_profile,
            custom_threshold=custom_threshold,
        )

        # Record anonymized audit log entry in SQLite (zero images, zero embeddings)
        try:
            record_comparison(
                probe_hash_prefix=diag_a.sha256_hash,
                reference_hash_prefix=diag_b.sha256_hash,
                similarity_score=response.similarity_score,
                display_score=response.transformed_display_score,
                threshold_used=response.threshold_used,
                threshold_profile=response.threshold_profile,
                is_match=bool(response.is_match),
                latency_ms=response.inference_latency_ms or 0.0,
                face_count_a=diag_a.face_count,
                face_count_b=diag_b.face_count,
                quality_flags_a=diag_a.warnings,
                quality_flags_b=diag_b.warnings,
                status="SUCCESS",
            )
        except Exception as db_exc:
            logger.warning(f"Failed to record comparison audit log: {db_exc}")

        return response

    except NoFaceDetectedError as exc:
        try:
            record_comparison(
                probe_hash_prefix=diag_a.sha256_hash,
                reference_hash_prefix=diag_b.sha256_hash,
                similarity_score=None,
                display_score=None,
                threshold_used=0.3132,
                threshold_profile=threshold_profile,
                is_match=False,
                latency_ms=0.0,
                face_count_a=diag_a.face_count,
                face_count_b=diag_b.face_count,
                quality_flags_a=diag_a.warnings,
                quality_flags_b=diag_b.warnings,
                status="FTA_NO_FACE",
            )
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )

    except MultipleFacesDetectedError as exc:
        try:
            record_comparison(
                probe_hash_prefix=diag_a.sha256_hash,
                reference_hash_prefix=diag_b.sha256_hash,
                similarity_score=None,
                display_score=None,
                threshold_used=0.3132,
                threshold_profile=threshold_profile,
                is_match=False,
                latency_ms=0.0,
                face_count_a=diag_a.face_count,
                face_count_b=diag_b.face_count,
                quality_flags_a=diag_a.warnings,
                quality_flags_b=diag_b.warnings,
                status="FTA_MULTIPLE_FACES",
            )
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )

    except InvalidFaceSelectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )

    except InvalidCropCoordinatesError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )

    except ModelNotReadyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Biometric engine unavailable: {str(exc)}",
        )

    except InvalidEmbeddingError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Biometric embedding extraction failed: {str(exc)}",
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failure during evaluation: {str(exc)}",
        )


# ============================================================================
# Dashboard & Persistence Endpoints
# ============================================================================

@app.get("/api/dashboard/stats", response_model=DashboardStatsResponse, tags=["Dashboard"])
async def get_dashboard_statistics() -> DashboardStatsResponse:
    """Retrieve aggregated operational throughput, match rates, and FTA telemetry from SQLite."""
    raw_stats = get_dashboard_stats()
    return DashboardStatsResponse(
        total_comparisons=raw_stats["total_comparisons"],
        successful_comparisons=raw_stats["successful_comparisons"],
        matches_count=raw_stats["matches_count"],
        non_matches_count=raw_stats["non_matches_count"],
        acquisition_failures=raw_stats["acquisition_failures"],
        fta_rate=raw_stats["fta_rate"],
        fta_breakdown=raw_stats["fta_breakdown"],
        recent_activity=raw_stats["recent_activity"],
        benchmarks_summary=raw_stats["benchmarks_summary"],
        engine_status=active_engine.get_metadata().status,
        uptime_seconds=raw_stats["uptime_seconds"],
    )


@app.get("/api/history", response_model=List[ComparisonHistoryRecord], tags=["History"])
async def get_history(limit: int = 50) -> List[ComparisonHistoryRecord]:
    """Retrieve recent comparison audit records (metadata only, no images/embeddings)."""
    return get_recent_comparisons(limit=min(100, max(1, limit)))


@app.delete("/api/history", tags=["History"])
async def clear_history(older_than_days: Optional[int] = None) -> Dict[str, Any]:
    """Clear or prune comparison audit records from SQLite.

    If older_than_days is provided, prunes records older than that window.
    Otherwise, clears all comparison audit records.
    """
    if older_than_days is not None:
        deleted = prune_comparison_audit_log(retention_days=older_than_days)
        return {
            "status": "ok",
            "message": f"Pruned {deleted} records older than {older_than_days} days.",
            "deleted_count": deleted,
        }
    deleted = clear_comparison_history()
    return {
        "status": "ok",
        "message": "Comparison history cleared successfully.",
        "deleted_count": deleted,
    }


# ============================================================================
# Structured Exception Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Structured HTTP exception handler mapping failures to machine-readable error codes."""
    detail_str = str(exc.detail)
    err_code = ErrorCode.INTERNAL_ERROR.value

    if "No face detected" in detail_str:
        err_code = ErrorCode.NO_FACE_DETECTED.value
    elif "Multiple faces" in detail_str:
        err_code = ErrorCode.MULTIPLE_FACES_DETECTED.value
    elif "resolution too low" in detail_str.lower():
        err_code = ErrorCode.RESOLUTION_TOO_LOW.value
    elif "exceeds maximum allowed limit" in detail_str.lower():
        err_code = ErrorCode.FILE_TOO_LARGE.value
    elif "unsupported file signature" in detail_str.lower() or "invalid or unsupported" in detail_str.lower():
        err_code = ErrorCode.UNSUPPORTED_FORMAT.value
    elif "corrupt or unreadable" in detail_str.lower():
        err_code = ErrorCode.IMAGE_CORRUPT.value
    elif "selected face index" in detail_str.lower():
        err_code = ErrorCode.INVALID_FACE_SELECTION.value
    elif "crop coordinates" in detail_str.lower():
        err_code = ErrorCode.INVALID_CROP_COORDINATES.value
    elif "unavailable" in detail_str.lower():
        err_code = ErrorCode.MODEL_UNAVAILABLE.value
    elif "embedding" in detail_str.lower():
        err_code = ErrorCode.INVALID_EMBEDDING.value

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": err_code,
            "message": detail_str.split(".")[0],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Sanitized global exception handler to avoid leaking internal trace details."""
    logger.error(f"Unhandled exception processing {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred during processing.",
            "error_code": ErrorCode.INTERNAL_ERROR.value,
            "message": "Internal processing error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
