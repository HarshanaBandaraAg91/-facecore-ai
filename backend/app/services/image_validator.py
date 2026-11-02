import io
import math
import hashlib
from typing import Tuple, Optional, List
import numpy as np
from PIL import Image

from app.config import settings
from app.models.schemas import ImageQualityDiagnostics, DetectedFaceSummary
from app.services.face_detector import (
    shared_face_detector,
    InvalidCropCoordinatesError,
    DetectionResult,
)


def detect_magic_signature(data: bytes) -> Optional[str]:
    """Inspect leading bytes to detect true file signature (magic numbers)."""
    if len(data) < 12:
        return None

    # JPEG: FF D8 FF
    if data.startswith(b"\xFF\xD8\xFF"):
        return "JPEG"

    # PNG: 89 50 4E 47 0D 0A 1A 0A
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "PNG"

    # WebP: RIFF .... WEBP
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "WEBP"

    return None


def calculate_aspect_ratio_str(width: int, height: int) -> str:
    """Return simplified aspect ratio string."""
    divisor = math.gcd(width, height)
    simplified_w = width // divisor
    simplified_h = height // divisor
    
    # Common standard ratios
    ratio = width / height
    if abs(ratio - 1.0) < 0.03:
        return "1:1 (Square)"
    if abs(ratio - 4/3) < 0.03:
        return "4:3 (Standard)"
    if abs(ratio - 3/4) < 0.03:
        return "3:4 (Portrait)"
    if abs(ratio - 16/9) < 0.04:
        return "16:9 (Widescreen)"
    if abs(ratio - 9/16) < 0.04:
        return "9:16 (Vertical)"
        
    if simplified_w < 50 and simplified_h < 50:
        return f"{simplified_w}:{simplified_h}"
    return f"{ratio:.2f}:1"


def compute_sharpness_estimate(arr: np.ndarray) -> float:
    """Estimate image sharpness using discrete Laplacian variance."""
    try:
        if arr.shape[0] < 5 or arr.shape[1] < 5:
            return 0.0
            
        # 3x3 discrete Laplacian kernel convolution
        # kernel: [[0, 1, 0], [1, -4, 1], [0, 1, 0]]
        top = arr[:-2, 1:-1]
        bottom = arr[2:, 1:-1]
        left = arr[1:-1, :-2]
        right = arr[1:-1, 2:]
        center = arr[1:-1, 1:-1]
        
        laplacian = top + bottom + left + right - (4.0 * center)
        variance = float(np.var(laplacian))
        return round(variance, 2)
    except Exception:
        return 0.0


def validate_image_bytes(
    data: bytes,
    filename: str = "upload.img",
    crop_box: Optional[List[int]] = None,
) -> Tuple[bool, Optional[str], Optional[ImageQualityDiagnostics]]:
    """Strictly validate image data, magic bytes, dimensions, and extract diagnostics."""
    if not data or len(data) == 0:
        return False, "Uploaded file is empty (0 bytes).", None

    # Check file size limit
    if len(data) > settings.max_upload_size_bytes:
        size_mb = len(data) / (1024 * 1024)
        max_mb = settings.max_upload_size_bytes / (1024 * 1024)
        return (
            False,
            f"File size ({size_mb:.2f} MB) exceeds maximum allowed limit of {max_mb:.0f} MB.",
            None,
        )

    # Magic signature verification
    detected_signature = detect_magic_signature(data)
    if not detected_signature:
        return (
            False,
            "Invalid or unsupported file signature. Only authentic JPEG, PNG, and WebP files are accepted.",
            None,
        )

    # Cryptographic hash prefix
    sha256_full = hashlib.sha256(data).hexdigest()
    sha256_prefix = sha256_full[:16]

    # Safe Pillow decoding with decompression bomb protection
    Image.MAX_IMAGE_PIXELS = settings.max_total_pixels
    try:
        # First verification pass: check for corrupt headers/chunks
        with Image.open(io.BytesIO(data)) as test_img:
            test_img.verify()
    except Exception as exc:
        return (
            False,
            f"Corrupt or unreadable image file: {str(exc)}",
            None,
        )

    # Second pass: read metadata and compute quality diagnostics
    try:
        with Image.open(io.BytesIO(data)) as img:
            width, height = img.size
            format_name = img.format or detected_signature
            color_mode = img.mode

            # Validate dimensions
            if width < settings.min_image_dimension or height < settings.min_image_dimension:
                return (
                    False,
                    f"Image resolution too low ({width}x{height} px). Minimum required dimension is {settings.min_image_dimension}x{settings.min_image_dimension} px.",
                    None,
                )

            if width > settings.max_image_dimension or height > settings.max_image_dimension:
                return (
                    False,
                    f"Image resolution ({width}x{height} px) exceeds maximum allowed dimension of {settings.max_image_dimension} px.",
                    None,
                )

            total_pixels = width * height
            if total_pixels > settings.max_total_pixels:
                return (
                    False,
                    f"Total pixel count ({total_pixels:,} px) exceeds maximum threshold ({settings.max_total_pixels:,} px).",
                    None,
                )

            # Convert to Grayscale (L) for brightness, contrast, and sharpness metrics
            gray = img.convert("L")
            gray_arr = np.asarray(gray, dtype=np.float32)
            
            mean_brightness = float(np.mean(gray_arr))
            contrast_std = float(np.std(gray_arr))
            sharpness_score = compute_sharpness_estimate(gray_arr)

            # Determine resolution category
            min_dim = min(width, height)
            if min_dim < 120:
                res_cat = "Low Fidelity (<120px)"
            elif min_dim < 720:
                res_cat = "Standard Definition"
            elif min_dim < 1440:
                res_cat = "High Definition (1080p tier)"
            else:
                res_cat = "Ultra High Definition"

            # Aspect ratio
            aspect_ratio_str = calculate_aspect_ratio_str(width, height)

            # Quality warnings
            warnings: List[str] = []
            if min_dim < 160:
                warnings.append("Low resolution: Facial landmark localization and embedding fidelity may be reduced.")
            if contrast_std < 18.0:
                warnings.append("Low contrast: Low dynamic range may obscure facial contour definition.")
            if mean_brightness < 35.0:
                warnings.append("Underexposed: Subject appears dark or poorly illuminated.")
            elif mean_brightness > 225.0:
                warnings.append("Overexposed: Highlights may be clipped or washed out.")
            
            ratio_val = width / max(height, 1)
            if ratio_val > 2.5 or ratio_val < 0.4:
                warnings.append("Extreme aspect ratio: Verify whether face framing is cropped appropriately.")
            if sharpness_score > 0 and sharpness_score < 25.0:
                warnings.append("Soft focus: Estimated sharpness is below typical verification baseline.")

            # Run unified face detection via shared detector service
            face_detected = False
            face_count = 0
            face_confidence: Optional[float] = None
            face_bounding_box: Optional[List[int]] = None
            detected_faces: List[DetectedFaceSummary] = []
            applied_crop: Optional[List[int]] = None

            if shared_face_detector.is_ready:
                try:
                    det_result = shared_face_detector.detect_faces(data, crop_box=crop_box)
                    face_count = det_result.face_count
                    face_detected = face_count > 0
                    applied_crop = det_result.crop_box
                    if det_result.primary_face:
                        face_confidence = det_result.primary_face.confidence
                        face_bounding_box = det_result.primary_face.box

                    detected_faces = [
                        DetectedFaceSummary(
                            index=f.index,
                            box=f.box,
                            confidence=f.confidence,
                            landmarks=f.landmarks,
                            quality_advisories=f.quality_advisories,
                        )
                        for f in det_result.faces
                    ]

                    for w in det_result.warnings:
                        if w not in warnings:
                            warnings.append(w)
                    if det_result.primary_face:
                        for adv in det_result.primary_face.quality_advisories:
                            if adv not in warnings:
                                warnings.append(adv)
                except InvalidCropCoordinatesError as exc:
                    return False, f"Invalid crop coordinates: {str(exc)}", None
                except Exception as exc:
                    warnings.append(f"Face detector warning: {str(exc)}")
            else:
                warnings.append("Face detection service is currently offline or weights unmounted.")

            # Do not report PASS if face localization has failed or 0 faces were located
            passes_quality = (
                face_detected
                and (min_dim >= 120 or crop_box is not None)
                and (contrast_std >= 15.0)
            )

            diagnostics = ImageQualityDiagnostics(
                filename=filename,
                format=format_name,
                color_mode=color_mode,
                width=width,
                height=height,
                aspect_ratio=aspect_ratio_str,
                file_size_bytes=len(data),
                sha256_hash=sha256_prefix,
                estimated_sharpness=sharpness_score,
                contrast_std=round(contrast_std, 2),
                brightness_mean=round(mean_brightness, 2),
                resolution_category=res_cat,
                face_detected=face_detected,
                face_count=face_count,
                face_confidence=face_confidence,
                face_bounding_box=face_bounding_box,
                detected_faces=detected_faces,
                crop_bounding_box=applied_crop,
                passes_quality_check=passes_quality,
                warnings=warnings,
            )

            return True, None, diagnostics

    except Exception as exc:
        return False, f"Image processing failed: {str(exc)}", None

