"""Configuration settings for FACECORE AI production backend."""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env file if present
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.is_file():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()


def _safe_int(val: str | None, default: int) -> int:
    """Parse integer from environment string with graceful default fallback."""
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _safe_bool(val: str | None, default: bool) -> bool:
    """Parse boolean from environment string with graceful default fallback."""
    if val is None:
        return default
    v = str(val).strip().lower()
    if v in ("true", "1", "yes", "on"):
        return True
    if v in ("false", "0", "no", "off"):
        return False
    return default


class Settings(BaseModel):
    app_name: str = Field(default_factory=lambda: os.getenv("APP_NAME", "FACECORE AI"))
    app_version: str = Field(default_factory=lambda: os.getenv("APP_VERSION", "1.0.0-prod"))
    environment: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "production"))
    debug: bool = Field(default_factory=lambda: _safe_bool(os.getenv("DEBUG"), False))

    # Security & CORS
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
            ).split(",")
            if origin.strip()
        ]
    )

    # File Upload & Ingestion Safeguards (Step 09.2 Evidence-Based Gates)
    max_upload_size_bytes: int = Field(
        default_factory=lambda: _safe_int(os.getenv("MAX_UPLOAD_SIZE_BYTES"), 15 * 1024 * 1024)  # 15 MB
    )
    min_image_dimension: int = Field(
        default_factory=lambda: _safe_int(os.getenv("MIN_IMAGE_DIMENSION"), 48)  # 48x48 px hard failure gate
    )
    max_image_dimension: int = Field(
        default_factory=lambda: _safe_int(os.getenv("MAX_IMAGE_DIMENSION"), 4096)  # 4096 px max width/height
    )
    max_total_pixels: int = Field(
        default_factory=lambda: _safe_int(os.getenv("MAX_TOTAL_PIXELS"), 16777216)  # 16 MP decompression bomb cap
    )

    # Supported MIME types
    allowed_mime_types: List[str] = [
        "image/jpeg",
        "image/png",
        "image/webp",
    ]

    # Database & Storage
    database_path: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_PATH",
            str(BASE_DIR / "data" / "facecore.db")
        )
    )

    # Comparison Audit Log Policy & Retention (Step 11 Security & Privacy Controls)
    audit_logging_enabled: bool = Field(
        default_factory=lambda: _safe_bool(os.getenv("AUDIT_LOGGING_ENABLED"), True)
    )
    audit_retention_days: int = Field(
        default_factory=lambda: _safe_int(os.getenv("AUDIT_RETENTION_DAYS"), 30)
    )

    # Model Weights Directory
    weights_dir: str = Field(
        default_factory=lambda: os.getenv(
            "WEIGHTS_DIR",
            str(Path(__file__).resolve().parent / "weights")
        )
    )

    # Default Operating Threshold Profile
    default_threshold_profile: str = Field(
        default_factory=lambda: os.getenv("DEFAULT_THRESHOLD_PROFILE", "balanced")
    )

    # Quality Advisory Thresholds
    advisory_min_face_width: int = Field(
        default_factory=lambda: _safe_int(os.getenv("ADVISORY_MIN_FACE_WIDTH"), 48)
    )

    # Privacy & Ephemeral Execution Policies
    ephemeral_processing: bool = True  # Strict memory-only image decoding; zero disk persistence
    telemetry_enabled: bool = False   # Strict zero phone-home; 100% offline local inference


settings = Settings()


def get_settings() -> Settings:
    """Return the global application settings instance."""
    return settings

