#!/usr/bin/env python3
"""FACECORE AI — Model Weights Verification Utility (Step 10).

Verifies the cryptographic integrity and presence of the required OpenCV Model Zoo
ONNX neural weights before launching local CPU inference.
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

# Reference hashes and official OpenCV Zoo download locations for Apache-2.0 licensed models
OFFICIAL_WEIGHTS = {
    "face_detection_yunet_2023mar.onnx": {
        "expected_sha256": "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
        "min_size_bytes": 200_000,
        "role": "YuNet 5-point facial landmark detector (INT8/FP32)",
        "download_url": "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    },
    "face_recognition_sface_2021dec.onnx": {
        "expected_sha256": "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79",
        "min_size_bytes": 30_000_000,
        "role": "SFace 128-dimensional hyperspherical feature extractor",
        "download_url": "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
    },
}


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 digest of a binary file in 64KB chunks."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def verify_weights(weights_dir: Path | None = None) -> bool:
    """Verify all required neural network weight files."""
    if weights_dir is None:
        base_dir = Path(__file__).resolve().parent.parent
        weights_dir = base_dir / "app" / "weights"

    print("=" * 70)
    print(" FACECORE AI — Model Weight Verification (OpenCV YuNet + SFace)")
    print("=" * 70)
    print(f"Weights Directory: {weights_dir}")

    if not weights_dir.is_dir():
        print(f"\n[FAIL] Weights directory does not exist: {weights_dir}")
        print("Please create the directory and place the official ONNX model files inside.")
        return False

    all_passed = True

    for filename, spec in OFFICIAL_WEIGHTS.items():
        file_path = weights_dir / filename
        print(f"\nVerifying: {filename}")
        print(f"Role:      {spec['role']}")

        if not file_path.is_file():
            print(f"  [MISSING] File not found: {file_path}")
            all_passed = False
            continue

        size = file_path.stat().st_size
        print(f"  File size: {size:,} bytes")
        if size < spec["min_size_bytes"]:
            print(f"  [CORRUPT] File size is smaller than expected minimum ({spec['min_size_bytes']:,} bytes)")
            all_passed = False
            continue

        actual_hash = compute_sha256(file_path)
        expected_hash = spec["expected_sha256"].lower()

        if actual_hash == expected_hash:
            print(f"  SHA-256:   {actual_hash}")
            print("  Status:    [PASSED] Cryptographic checksum verified.")
        else:
            print(f"  Expected:  {expected_hash}")
            print(f"  Actual:    {actual_hash}")
            print("  Status:    [CHECKSUM MISMATCH] File may be corrupt or tampered with.")
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print(" ALL MODEL WEIGHTS VERIFIED SUCCESSFULLY (100% INTEGRITY CHECK PASSED)")
        print("=" * 70)
        return True
    else:
        print(" WEIGHT VERIFICATION FAILED: ONE OR MORE FILES ARE MISSING OR CORRUPTED")
        print("=" * 70)
        print("\nACTIONABLE REMEDIATION INSTRUCTIONS:")
        print("To download the official OpenCV Model Zoo ONNX weights, run the following commands:")
        print(f"  mkdir -p \"{weights_dir}\"")
        for fn, sp in OFFICIAL_WEIGHTS.items():
            dst = weights_dir / fn
            if not dst.is_file():
                print(f"  curl -L -o \"{dst}\" \"{sp['download_url']}\"")
        print("\nOr download them manually from your browser and place them in the directory above.")
        return False
        return False


if __name__ == "__main__":
    target_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    success = verify_weights(target_dir)
    sys.exit(0 if success else 1)

