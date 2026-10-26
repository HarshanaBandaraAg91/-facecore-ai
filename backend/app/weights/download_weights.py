"""Automated downloader and checksum validator for FACECORE AI neural model weights."""

import hashlib
from pathlib import Path
import urllib.request

WEIGHTS_DIR = Path(__file__).resolve().parent

MODELS = {
    "face_detection_yunet_2023mar.onnx": {
        "url": "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
        "sha256": "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
        "license": "Apache-2.0",
        "size_expected": 232589,
    },
    "face_recognition_sface_2021dec.onnx": {
        "url": "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
        "sha256": "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79",
        "license": "Apache-2.0",
        "size_expected": 38696353,
    },
}


def download_and_verify():
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print("FACECORE AI — Model Weight Verification and Download Utility")
    print("=" * 70)

    for filename, meta in MODELS.items():
        dest = WEIGHTS_DIR / filename
        needs_download = True

        if dest.exists():
            computed_sha = hashlib.sha256(dest.read_bytes()).hexdigest()
            if computed_sha == meta["sha256"]:
                print(f"[OK] {filename} is present and verified (SHA256: {computed_sha[:12]}...).")
                needs_download = False
            else:
                print(f"[WARN] {filename} exists but checksum mismatch. Re-downloading...")

        if needs_download:
            print(f"Downloading {filename} from {meta['url']} ...")
            req = urllib.request.Request(
                meta["url"],
                headers={"User-Agent": "FACECORE-AI/0.2.0 (Model Evaluator)"},
            )
            with urllib.request.urlopen(req) as resp, open(dest, "wb") as f:
                while chunk := resp.read(1024 * 64):
                    f.write(chunk)

            computed_sha = hashlib.sha256(dest.read_bytes()).hexdigest()
            if computed_sha != meta["sha256"]:
                raise RuntimeError(
                    f"Checksum mismatch for {filename}! Expected {meta['sha256']}, got {computed_sha}"
                )
            print(f"[SUCCESS] Downloaded and verified {filename} ({dest.stat().st_size} bytes).")


if __name__ == "__main__":
    download_and_verify()
