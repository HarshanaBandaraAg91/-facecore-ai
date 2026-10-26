"""FastAPI main application entrypoint for FACECORE AI."""

from datetime import datetime, timezone
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.schemas import (
    HealthResponse,
    ImageValidationResponse,
    ComparisonResponse,
    EngineMetadata,
)
from app.services.image_validator import validate_image_bytes
from app.engine.real_engine import (
    RealFacialEmbeddingEngine,
    NoFaceDetectedError,
    MultipleFacesDetectedError,
    ModelNotReadyError,
    InvalidEmbeddingError,
)

# Initialize application
app = FastAPI(
    title=settings.app_name,
    version="0.2.0-alpha",
    description=(
        "Biometric facial image evaluation & similarity analysis platform. "
        "Engineered with strict scientific integrity, zero score fabrication, "
        "and real local neural embedding extraction via YuNet and SFace."
    ),
)

# Configure CORS for local development and designated frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active facial embedding engine instance (Production SFace + YuNet engine)
active_engine = RealFacialEmbeddingEngine()


@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """Return backend operational health, version, and engine status."""
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version="0.2.0-alpha",
        timestamp=datetime.now(timezone.utc).isoformat(),
        engine_status=active_engine.get_metadata().status,
        security_mode="ephemeral_local_strict",
    )


@app.get("/api/engine-info", response_model=EngineMetadata, tags=["Engine"])
async def get_engine_info() -> EngineMetadata:
    """Retrieve metadata about the currently active inference engine."""
    return active_engine.get_metadata()


@app.post("/api/validate-image", response_model=ImageValidationResponse, tags=["Validation"])
async def validate_image(file: UploadFile = File(...)) -> ImageValidationResponse:
    """Safely validate image format, magic bytes, dimensions, and extract quality telemetry.

    Does not persist image data to disk. Processing occurs ephemerally in-memory.
    """
    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to read uploaded file payload: {str(exc)}",
        )

    is_valid, error_msg, diagnostics = validate_image_bytes(
        content,
        filename=file.filename or "uploaded_image"
    )

    return ImageValidationResponse(
        is_valid=is_valid,
        error_message=error_msg,
        diagnostics=diagnostics,
    )


@app.post("/api/compare", response_model=ComparisonResponse, tags=["Comparison"])
async def compare_images(
    image_a: UploadFile = File(..., description="Probe image (Image A)"),
    image_b: UploadFile = File(..., description="Reference image (Image B)"),
) -> ComparisonResponse:
    """Validate two facial images and evaluate through the real neural embedding engine.

    Enforces exactly one usable face per image. Extracts 128-d normalized embeddings
    and computes verified cosine similarity.
    """
    try:
        content_a = await image_a.read()
        content_b = await image_b.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error reading upload payloads: {str(exc)}",
        )

    # Validate Image A cryptographic signature and quality bounds
    valid_a, err_a, diag_a = validate_image_bytes(
        content_a,
        filename=image_a.filename or "image_a"
    )
    if not valid_a or diag_a is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Image A validation failed: {err_a}",
        )

    # Validate Image B cryptographic signature and quality bounds
    valid_b, err_b, diag_b = validate_image_bytes(
        content_b,
        filename=image_b.filename or "image_b"
    )
    if not valid_b or diag_b is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Image B validation failed: {err_b}",
        )

    # Execute facial detection, alignment, and embedding extraction
    try:
        response = active_engine.compare_faces(
            image_a_bytes=content_a,
            image_b_bytes=content_b,
            diag_a=diag_a,
            diag_b=diag_b,
        )
        return response
    except NoFaceDetectedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )
    except MultipleFacesDetectedError as exc:
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


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Pass through structured HTTP exceptions with clean JSON bodies."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Sanitized global exception handler to avoid leaking internal trace details."""
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred during processing."},
    )
