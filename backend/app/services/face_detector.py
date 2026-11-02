"""Shared facial detection service for FACECORE AI.

Provides a unified YuNet detector shared by both image validation (/api/validate-image)
and neural embedding evaluation (/api/compare). Ensures consistent BGR color decoding,
dynamic input-size configuration, candidate filtering for implausible false positives,
face-specific quality telemetry, and ephemeral per-request caching.
"""

import os
import math
import hashlib
import threading
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import cv2

# Path to YuNet ONNX weights
DEFAULT_WEIGHTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "weights")
)
DEFAULT_YUNET_PATH = os.path.join(
    DEFAULT_WEIGHTS_DIR, "face_detection_yunet_2023mar.onnx"
)


class FaceDetectionError(Exception):
    """Exception raised for facial detection errors."""
    pass


class InvalidCropCoordinatesError(FaceDetectionError):
    """Raised when provided manual crop coordinates violate image boundaries."""
    pass


@dataclass
class DetectedFace:
    """Structured representation of a validated, plausible face detection."""
    index: int
    box: List[int]  # [x, y, w, h] integer pixel bounding box
    confidence: float
    landmarks: List[List[float]]  # 5 landmarks: [re, le, nt, rc, lc]
    raw_face: np.ndarray  # Full 15-float YuNet vector for recognizer.alignCrop
    quality_advisories: List[str] = field(default_factory=list)


@dataclass
class DetectionResult:
    """Complete structured detection result for an image."""
    image_width: int
    image_height: int
    face_count: int
    faces: List[DetectedFace]
    filtered_false_positives: int
    primary_face: Optional[DetectedFace]
    is_cropped: bool = False
    crop_box: Optional[List[int]] = None
    warnings: List[str] = field(default_factory=list)


def is_plausible_face_candidate(
    face: np.ndarray,
    img_width: int,
    img_height: int,
    score_threshold: float = 0.35,
) -> Tuple[bool, Optional[str]]:
    """Determine whether a raw YuNet candidate is a geometrically plausible face.

    Filters out tiny noise artifacts, sliver aspect ratios, and geometrically
    degenerate landmarks without discarding genuine human faces.
    """
    x, y, w, h = float(face[0]), float(face[1]), float(face[2]), float(face[3])
    score = float(face[14])

    if score < score_threshold:
        return False, f"Score ({score:.3f}) below threshold ({score_threshold:.3f})"

    # Minimum dimension checks: human face must be at least 16x16 pixels
    if w < 16.0 or h < 16.0:
        return False, f"Candidate box too small ({w:.0f}x{h:.0f} px, minimum 16x16)"

    # Aspect ratio check: Face boxes typically range 0.45 to 1.4; allow 0.35 to 2.5 for angles
    aspect_ratio = w / max(h, 1.0)
    if aspect_ratio < 0.35 or aspect_ratio > 2.5:
        return False, f"Implausible face aspect ratio ({aspect_ratio:.2f})"

    # Bounding box center must be within image canvas
    center_x = x + (w / 2.0)
    center_y = y + (h / 2.0)
    if not (0.0 <= center_x <= float(img_width) and 0.0 <= center_y <= float(img_height)):
        return False, f"Candidate center ({center_x:.0f}, {center_y:.0f}) outside image"

    # Area check
    if (w * h) < 256.0:
        return False, f"Candidate area ({w * h:.0f} px) below threshold"

    # Landmarks geometry check
    # 5 landmarks: right eye, left eye, nose tip, right mouth corner, left mouth corner
    re_x, re_y = float(face[4]), float(face[5])
    le_x, le_y = float(face[6]), float(face[7])

    eye_distance = math.sqrt((le_x - re_x) ** 2 + (le_y - re_y) ** 2)
    if eye_distance < 4.0:
        return False, f"Degenerate eye landmark distance ({eye_distance:.1f} px)"

    # Eye distance relative to box width
    if (eye_distance / max(w, 1.0)) < 0.08:
        return False, "Eye distance abnormally small relative to candidate box"

    # Ensure landmarks are not wildly displaced from bounding box margin
    margin_w = w * 0.8
    margin_h = h * 0.8
    for idx, (lm_x, lm_y) in enumerate([
        (re_x, re_y),
        (le_x, le_y),
        (float(face[8]), float(face[9])),
        (float(face[10]), float(face[11])),
        (float(face[12]), float(face[13])),
    ]):
        if not (
            (x - margin_w) <= lm_x <= (x + w + margin_w)
            and (y - margin_h) <= lm_y <= (y + h + margin_h)
        ):
            return False, f"Landmark {idx} displaced outside candidate margin"

    return True, None


def analyze_face_quality(
    face_box: List[int],
    landmarks: List[List[float]],
    bgr_image: np.ndarray,
) -> List[str]:
    """Inspect facial region for low resolution, blur, boundary clipping, or excessive tilt."""
    img_h, img_w = bgr_image.shape[:2]
    x, y, w, h = face_box
    advisories: List[str] = []

    # 1. Face resolution
    if w < 48 or h < 48:
        advisories.append(
            f"Low face resolution: Face region is {w}x{h} px. Embedding fidelity may be reduced."
        )

    # 2. Boundary clipping (partial face visibility)
    margin = min(x, y, img_w - (x + w), img_h - (y + h))
    if margin <= 3:
        advisories.append(
            "Partial face visibility: Face bounding box touches or borders the image boundary."
        )

    # 3. Head tilt / facial rotation angle between eyes
    if len(landmarks) >= 2:
        re_x, re_y = landmarks[0]
        le_x, le_y = landmarks[1]
        delta_x = le_x - re_x
        delta_y = le_y - re_y
        angle_rad = math.atan2(delta_y, delta_x)
        angle_deg = abs(math.degrees(angle_rad))
        if angle_deg > 30.0:
            advisories.append(
                f"Excessive facial rotation: Estimated head tilt ({angle_deg:.1f}°) may affect alignment."
            )

    # 4. Face crop blur / sharpness estimate
    crop_x1 = max(0, x)
    crop_y1 = max(0, y)
    crop_x2 = min(img_w, x + w)
    crop_y2 = min(img_h, y + h)

    if (crop_x2 - crop_x1) >= 16 and (crop_y2 - crop_y1) >= 16:
        face_crop = bgr_image[crop_y1:crop_y2, crop_x1:crop_x2]
        gray_face = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        laplacian_var = float(cv2.Laplacian(gray_face, cv2.CV_64F).var())
        if laplacian_var < 20.0:
            advisories.append(
                f"Face region exhibits soft focus / blur (sharpness: {laplacian_var:.1f})."
            )

    return advisories


class SharedFaceDetector:
    """Singleton-ready shared face detector service wrapping OpenCV YuNet."""

    def __init__(
        self,
        weights_path: Optional[str] = None,
        score_threshold: float = 0.35,
        nms_threshold: float = 0.3,
        cache_size: int = 32,
    ) -> None:
        self.weights_path = os.path.abspath(weights_path or DEFAULT_YUNET_PATH)
        self.score_threshold = score_threshold
        self.nms_threshold = nms_threshold
        self.cache_size = cache_size
        self._cache: OrderedDict[str, DetectionResult] = OrderedDict()
        self._lock = threading.Lock()

        self._detector = None
        self._is_ready = False
        self._init_error = None
        self._init_detector()

    def _init_detector(self) -> None:
        """Initialize the underlying cv2.FaceDetectorYN model."""
        try:
            if not os.path.isfile(self.weights_path):
                raise FileNotFoundError(
                    f"YuNet ONNX model weights not found at: {self.weights_path}"
                )

            self._detector = cv2.FaceDetectorYN.create(
                model=self.weights_path,
                config="",
                input_size=(320, 320),
                score_threshold=self.score_threshold,
                nms_threshold=self.nms_threshold,
                top_k=5000,
            )
            self._is_ready = True
            self._init_error = None
        except Exception as exc:
            self._detector = None
            self._is_ready = False
            self._init_error = str(exc)

    @property
    def is_ready(self) -> bool:
        return self._is_ready and self._detector is not None

    def clear_cache(self) -> None:
        """Flush the ephemeral in-memory cache."""
        self._cache.clear()

    def validate_and_clip_crop(
        self,
        crop_box: List[int],
        img_width: int,
        img_height: int,
    ) -> List[int]:
        """Validate that manual crop coordinates are within image boundaries and satisfy minimum size."""
        if len(crop_box) != 4:
            raise InvalidCropCoordinatesError(
                f"Crop coordinates must contain exactly 4 integers [x, y, w, h], got {crop_box}."
            )

        x, y, w, h = crop_box
        if w < 16 or h < 16:
            raise InvalidCropCoordinatesError(
                f"Crop region dimensions ({w}x{h} px) too small. Minimum required is 16x16 px."
            )

        if x < 0 or y < 0:
            raise InvalidCropCoordinatesError(
                f"Crop origin ({x}, {y}) cannot be negative."
            )

        if x >= img_width or y >= img_height:
            raise InvalidCropCoordinatesError(
                f"Crop origin ({x}, {y}) is outside image dimensions ({img_width}x{img_height} px)."
            )

        # Ensure crop does not exceed image boundaries
        clipped_w = min(w, img_width - x)
        clipped_h = min(h, img_height - y)

        if clipped_w < 16 or clipped_h < 16:
            raise InvalidCropCoordinatesError(
                f"Clipped crop region ({clipped_w}x{clipped_h} px) is smaller than minimum 16x16 px."
            )

        return [int(x), int(y), int(clipped_w), int(clipped_h)]

    def detect_faces(
        self,
        image_bytes: bytes,
        crop_box: Optional[List[int]] = None,
        use_cache: bool = True,
    ) -> DetectionResult:
        """Execute face detection on image bytes or designated crop region.

        Args:
            image_bytes: Raw JPEG/PNG/WebP image payload.
            crop_box: Optional [x, y, w, h] region to restrict detection.
            use_cache: If True, consults the ephemeral in-memory cache.

        Returns:
            Structured DetectionResult with plausible faces, landmarks, and advisories.
        """
        if not self.is_ready:
            raise FaceDetectionError(
                f"Face detector model is unavailable: {self._init_error or 'Weights missing'}"
            )

        if not image_bytes or len(image_bytes) == 0:
            raise FaceDetectionError("Cannot run face detection on empty image payload.")

        # Cache key based on SHA-256 and crop box
        cache_key = None
        if use_cache:
            sha256 = hashlib.sha256(image_bytes).hexdigest()
            crop_str = f"{crop_box[0]}_{crop_box[1]}_{crop_box[2]}_{crop_box[3]}" if crop_box else "full"
            cache_key = f"{sha256}_{crop_str}"
            with self._lock:
                if cache_key in self._cache:
                    # Move to end (LRU)
                    result = self._cache[cache_key]
                    self._cache.move_to_end(cache_key)
                    return result

        # Decode image using OpenCV
        np_arr = np.frombuffer(image_bytes, np.uint8)
        bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise FaceDetectionError("Failed to decode image data into OpenCV BGR matrix.")

        img_h, img_w = bgr.shape[:2]

        # Handle optional manual crop
        valid_crop_box: Optional[List[int]] = None
        if crop_box is not None:
            valid_crop_box = self.validate_and_clip_crop(crop_box, img_w, img_h)
        is_cropped = valid_crop_box is not None


        # Stage 1: Detect on full canvas (thread-safe DNN execution)
        with self._lock:
            self._detector.setInputSize((img_w, img_h))
            _, full_raw_faces = self._detector.detect(bgr)

        plausible_faces: List[DetectedFace] = []
        filtered_count = 0
        warnings: List[str] = []

        if full_raw_faces is not None and len(full_raw_faces) > 0:
            for raw_face in full_raw_faces:
                is_valid, _ = is_plausible_face_candidate(
                    raw_face,
                    img_w,
                    img_h,
                    score_threshold=self.score_threshold,
                )
                if not is_valid:
                    filtered_count += 1
                    continue

                x = max(0, int(raw_face[0]))
                y = max(0, int(raw_face[1]))
                w = min(int(raw_face[2]), img_w - x)
                h = min(int(raw_face[3]), img_h - y)
                box = [x, y, w, h]
                conf = float(raw_face[14])

                # If crop_box is specified, check if face center or overlap falls within crop
                if valid_crop_box is not None:
                    cx, cy, cw, ch = valid_crop_box
                    face_center_x = x + (w / 2.0)
                    face_center_y = y + (h / 2.0)
                    if not (cx <= face_center_x <= (cx + cw) and cy <= face_center_y <= (cy + ch)):
                        # Face is outside user crop region
                        continue

                landmarks = [
                    [round(float(raw_face[4]), 2), round(float(raw_face[5]), 2)],
                    [round(float(raw_face[6]), 2), round(float(raw_face[7]), 2)],
                    [round(float(raw_face[8]), 2), round(float(raw_face[9]), 2)],
                    [round(float(raw_face[10]), 2), round(float(raw_face[11]), 2)],
                    [round(float(raw_face[12]), 2), round(float(raw_face[13]), 2)],
                ]

                advisories = analyze_face_quality(box, landmarks, bgr)

                face_obj = DetectedFace(
                    index=len(plausible_faces),
                    box=box,
                    confidence=round(conf, 4),
                    landmarks=landmarks,
                    raw_face=raw_face.copy(),
                    quality_advisories=advisories,
                )
                plausible_faces.append(face_obj)

        # Stage 2: If crop_box was provided and no full-canvas face matched, run dedicated detector on sub-image
        if valid_crop_box is not None and len(plausible_faces) == 0:
            cx, cy, cw, ch = valid_crop_box
            sub_bgr = bgr[cy:cy + ch, cx:cx + cw]
            sub_h, sub_w = sub_bgr.shape[:2]
            if sub_w >= 16 and sub_h >= 16:
                self._detector.setInputSize((sub_w, sub_h))
                _, sub_raw_faces = self._detector.detect(sub_bgr)
                if sub_raw_faces is not None and len(sub_raw_faces) > 0:
                    for raw_face in sub_raw_faces:
                        is_valid, _ = is_plausible_face_candidate(
                            raw_face,
                            sub_w,
                            sub_h,
                            score_threshold=self.score_threshold,
                        )
                        if not is_valid:
                            filtered_count += 1
                            continue

                        adjusted_raw = raw_face.copy()
                        adjusted_raw[0] += cx
                        adjusted_raw[1] += cy
                        for lm_idx in range(4, 14, 2):
                            adjusted_raw[lm_idx] += cx
                            adjusted_raw[lm_idx + 1] += cy

                        x = max(0, int(adjusted_raw[0]))
                        y = max(0, int(adjusted_raw[1]))
                        w = min(int(adjusted_raw[2]), img_w - x)
                        h = min(int(adjusted_raw[3]), img_h - y)
                        box = [x, y, w, h]
                        conf = float(adjusted_raw[14])

                        landmarks = [
                            [round(float(adjusted_raw[4]), 2), round(float(adjusted_raw[5]), 2)],
                            [round(float(adjusted_raw[6]), 2), round(float(adjusted_raw[7]), 2)],
                            [round(float(adjusted_raw[8]), 2), round(float(adjusted_raw[9]), 2)],
                            [round(float(adjusted_raw[10]), 2), round(float(adjusted_raw[11]), 2)],
                            [round(float(adjusted_raw[12]), 2), round(float(adjusted_raw[13]), 2)],
                        ]

                        advisories = analyze_face_quality(box, landmarks, bgr)

                        face_obj = DetectedFace(
                            index=len(plausible_faces),
                            box=box,
                            confidence=round(conf, 4),
                            landmarks=landmarks,
                            raw_face=adjusted_raw,
                            quality_advisories=advisories,
                        )
                        plausible_faces.append(face_obj)


        # Order faces deterministically: primary face has highest confidence
        plausible_faces.sort(key=lambda f: f.confidence, reverse=True)
        # Re-index
        for idx, f in enumerate(plausible_faces):
            f.index = idx

        face_count = len(plausible_faces)
        primary_face = plausible_faces[0] if face_count > 0 else None

        if face_count == 0:
            if is_cropped:
                warnings.append(
                    "No human face verified within the selected crop region. "
                    "Please adjust the crop or upload a clearer portrait."
                )
            else:
                warnings.append(
                    "No human face detected. Use the Manual Face Crop tool "
                    "or upload a clearer, well-lit image."
                )
        elif face_count > 1:
            warnings.append(
                f"Multiple faces detected ({face_count} found). "
                "Select the intended face before proceeding with comparison."
            )

        is_cropped = valid_crop_box is not None
        result = DetectionResult(
            image_width=img_w,
            image_height=img_h,
            face_count=face_count,
            faces=plausible_faces,
            filtered_false_positives=filtered_count,
            primary_face=primary_face,
            is_cropped=is_cropped,
            crop_box=valid_crop_box,
            warnings=warnings,
        )


        # Store in LRU cache
        if use_cache and cache_key:
            with self._lock:
                if len(self._cache) >= self.cache_size:
                    self._cache.popitem(last=False)
                self._cache[cache_key] = result

        return result


# Global singleton shared face detector
shared_face_detector = SharedFaceDetector()
