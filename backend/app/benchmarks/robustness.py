"""Controlled image perturbations for scientific robustness benchmarking.

Simulates optical, transmission, sensor, and environmental degradation under
strictly labeled, reproducible parameters.

IMPORTANT SCIENTIFIC NOTICE:
These transformations simulate synthetic sensor, optical, and transmission noise.
They do NOT represent physical 3D masks, adversarial disguise prosthetics,
or forensic alterations.
"""

from typing import Dict, Any, Callable, List
import numpy as np
import cv2


def apply_gaussian_blur(bgr_img: np.ndarray, sigma: float = 1.5) -> np.ndarray:
    """Apply controlled Gaussian blur simulating optical defocus or motion."""
    k_size = int(2 * np.ceil(2 * sigma) + 1)
    if k_size % 2 == 0:
        k_size += 1
    return cv2.GaussianBlur(bgr_img, (k_size, k_size), sigmaX=sigma, sigmaY=sigma)


def apply_resolution_degradation(bgr_img: np.ndarray, target_dim: int = 64) -> np.ndarray:
    """Downsample image to low pixel density (simulating surveillance CCTV) then restore scale."""
    h, w = bgr_img.shape[:2]
    if h <= target_dim or w <= target_dim:
        return bgr_img.copy()

    # Downsample
    small = cv2.resize(bgr_img, (target_dim, target_dim), interpolation=cv2.INTER_LINEAR)
    # Upsample back to preserve downstream model input tensor dimensions
    restored = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
    return restored


def apply_illumination_scaling(bgr_img: np.ndarray, gamma: float = 0.4) -> np.ndarray:
    """Apply non-linear gamma scaling simulating harsh lighting or severe underexposure."""
    inv_gamma = 1.0 / max(0.01, gamma)
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype("uint8")
    return cv2.LUT(bgr_img, table)


def apply_partial_occlusion(bgr_img: np.ndarray, region: str = "lower") -> np.ndarray:
    """Apply synthetic occlusion bar simulating face mask (lower) or sunglasses/visor (upper)."""
    out = bgr_img.copy()
    h, w = out.shape[:2]

    if region == "lower":
        # Lower 35% of face height (simulating health mask or scarf)
        y_start = int(h * 0.65)
        out[y_start:h, :] = (180, 150, 130)  # Neutral medical blue-gray
    elif region == "upper":
        # Eye region (25% to 50% height, simulating sunglasses or visor)
        y_start = int(h * 0.28)
        y_end = int(h * 0.52)
        out[y_start:y_end, :] = (25, 25, 25)  # Dark polarized sunglasses band

    return out


def apply_jpeg_compression(bgr_img: np.ndarray, quality: int = 25) -> np.ndarray:
    """Apply lossy JPEG compression artifacts at specified quality factor."""
    quality = max(1, min(100, quality))
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    success, enc = cv2.imencode(".jpg", bgr_img, encode_param)
    if not success:
        return bgr_img.copy()
    return cv2.imdecode(enc, cv2.IMREAD_COLOR)


# Registry of standard controlled robustness conditions
ROBUSTNESS_CONDITIONS = [
    {
        "id": "blur_light",
        "name": "Gaussian Blur (Light)",
        "description": "5x5 Gaussian blur with sigma=1.5 simulating minor camera shake",
        "fn": lambda img: apply_gaussian_blur(img, sigma=1.5),
    },
    {
        "id": "blur_heavy",
        "name": "Gaussian Blur (Heavy)",
        "description": "13x13 Gaussian blur with sigma=3.0 simulating severe defocus",
        "fn": lambda img: apply_gaussian_blur(img, sigma=3.0),
    },
    {
        "id": "low_res_64p",
        "name": "Resolution Degradation (64px)",
        "description": "Downsampled to 64x64 px simulating distant CCTV capture",
        "fn": lambda img: apply_resolution_degradation(img, target_dim=64),
    },
    {
        "id": "low_res_32p",
        "name": "Resolution Degradation (32px)",
        "description": "Extreme downsampling to 32x32 px (sub-baseline pixel density)",
        "fn": lambda img: apply_resolution_degradation(img, target_dim=32),
    },
    {
        "id": "low_light",
        "name": "Low Illumination / Shadow",
        "description": "Gamma scaling gamma=1.8 simulating nighttime/dim capture",
        "fn": lambda img: apply_illumination_scaling(img, gamma=1.8),
    },
    {
        "id": "high_glare",
        "name": "Overexposure / High Glare",
        "description": "Gamma scaling gamma=0.4 simulating direct flash or intense solar wash",
        "fn": lambda img: apply_illumination_scaling(img, gamma=0.4),
    },
    {
        "id": "occlusion_lower",
        "name": "Synthetic Lower Occlusion",
        "description": "Lower 35% facial occlusion simulating health mask or scarf",
        "fn": lambda img: apply_partial_occlusion(img, region="lower"),
    },
    {
        "id": "occlusion_upper",
        "name": "Synthetic Upper Occlusion",
        "description": "Eye band occlusion (28%-52% height) simulating dark sunglasses",
        "fn": lambda img: apply_partial_occlusion(img, region="upper"),
    },
    {
        "id": "compression_q25",
        "name": "JPEG Compression (Q25)",
        "description": "Lossy JPEG compression with Quality Factor=25",
        "fn": lambda img: apply_jpeg_compression(img, quality=25),
    },
    {
        "id": "compression_q10",
        "name": "JPEG Compression (Q10)",
        "description": "Extreme JPEG compression with Quality Factor=10",
        "fn": lambda img: apply_jpeg_compression(img, quality=10),
    },
]
