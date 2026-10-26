"""Configuration settings for FACECORE AI backend."""

import os
from typing import List
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "FACECORE AI"
    app_version: str = "0.1.0-alpha"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Security & CORS
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # File Upload Limits
    max_upload_size_bytes: int = 10 * 1024 * 1024  # 10 MB strict limit
    min_image_dimension: int = 32                  # Min 32x32 px
    max_image_dimension: int = 4096                # Max 4096x4096 px
    max_total_pixels: int = 16_777_216             # 16 Megapixels safeguard

    # Supported MIME types and magic byte headers
    allowed_mime_types: List[str] = [
        "image/jpeg",
        "image/png",
        "image/webp"
    ]

    # Privacy & Storage Policy
    ephemeral_processing: bool = True              # Never persist images to disk
    telemetry_enabled: bool = False               # Zero external tracking or phone-home


settings = Settings()
