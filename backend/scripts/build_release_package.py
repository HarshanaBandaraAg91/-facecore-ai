#!/usr/bin/env python3
"""FACECORE AI — Production Release Packager & Manifest Generator (Step 11).

Assembles the clean distributable directory structure in release/facecore-ai/,
enforces strict exclusions (no venvs, node_modules, pycache, or database blobs),
and computes SHA-256 checksums for every packaged asset.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
RELEASE_DIR = WORKSPACE_ROOT / "release" / "facecore-ai"

# Patterns to strictly exclude from the release
EXCLUDE_DIRS = {
    ".venv", "venv", "env", "node_modules", "__pycache__", ".pytest_cache",
    ".vite", ".git", ".gemini", "step09_results"
}
EXCLUDE_EXTS = {".pyc", ".pyo", ".db", ".db-wal", ".db-shm", ".log", ".tmp"}


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def copy_file_safe(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_tree_filtered(src_dir: Path, dst_dir: Path, ignore_names: set[str] | None = None):
    dst_dir.mkdir(parents=True, exist_ok=True)
    for root, dirs, files in os.walk(src_dir):
        # Modify dirs in-place to avoid descending into excluded directories
        dirs[:] = [
            d for d in dirs
            if d not in EXCLUDE_DIRS and not d.startswith(".") and (ignore_names is None or d not in ignore_names)
        ]
        rel_path = Path(root).relative_to(src_dir)
        target_sub = dst_dir / rel_path
        target_sub.mkdir(parents=True, exist_ok=True)
        for f in files:
            p = Path(root) / f
            if p.suffix in EXCLUDE_EXTS or (ignore_names and f in ignore_names):
                continue
            copy_file_safe(p, target_sub / f)


def build_release():
    print("=" * 70)
    print(" FACECORE AI — Packaging Distributable Release v1.0.0")
    print(f" Source:      {WORKSPACE_ROOT}")
    print(f" Destination: {RELEASE_DIR}")
    print("=" * 70)

    if RELEASE_DIR.exists():
        shutil.rmtree(RELEASE_DIR)
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Copy Backend Core
    print("\n[1/5] Packaging Backend Core & Weights...")
    backend_dst = RELEASE_DIR / "backend"
    copy_tree_filtered(WORKSPACE_ROOT / "backend" / "app", backend_dst / "app")
    copy_file_safe(WORKSPACE_ROOT / "backend" / "requirements.txt", backend_dst / "requirements.txt")
    copy_file_safe(WORKSPACE_ROOT / "backend" / "scripts" / "verify_weights.py", backend_dst / "scripts" / "verify_weights.py")

    # Ensure backend data directory template exists with .gitkeep
    (backend_dst / "data").mkdir(parents=True, exist_ok=True)
    (backend_dst / "data" / ".gitkeep").write_text("# SQLite storage directory\n", encoding="utf-8")

    # Create backend .env.example
    env_example_content = """# FACECORE AI — Backend Environment Configuration Template
APP_NAME=FACECORE AI
APP_VERSION=1.0.0-prod
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000
MAX_UPLOAD_SIZE_BYTES=15728640
MIN_IMAGE_DIMENSION=48
MAX_IMAGE_DIMENSION=4096
MAX_TOTAL_PIXELS=16777216
AUDIT_LOGGING_ENABLED=true
AUDIT_RETENTION_DAYS=30
DEFAULT_THRESHOLD_PROFILE=balanced
"""
    (backend_dst / ".env.example").write_text(env_example_content, encoding="utf-8")
    (RELEASE_DIR / ".env.example").write_text(env_example_content, encoding="utf-8")

    # 2. Copy Frontend Core & Pre-built Dist
    print("\n[2/5] Packaging Frontend Source & Production Dist Assets...")
    frontend_dst = RELEASE_DIR / "frontend"
    copy_tree_filtered(WORKSPACE_ROOT / "frontend" / "dist", frontend_dst / "dist")
    copy_tree_filtered(WORKSPACE_ROOT / "frontend" / "src", frontend_dst / "src")
    copy_file_safe(WORKSPACE_ROOT / "frontend" / "package.json", frontend_dst / "package.json")
    copy_file_safe(WORKSPACE_ROOT / "frontend" / "package-lock.json", frontend_dst / "package-lock.json")
    copy_file_safe(WORKSPACE_ROOT / "frontend" / "vite.config.ts", frontend_dst / "vite.config.ts")
    copy_file_safe(WORKSPACE_ROOT / "frontend" / "tsconfig.json", frontend_dst / "tsconfig.json")
    copy_file_safe(WORKSPACE_ROOT / "frontend" / "tsconfig.app.json", frontend_dst / "tsconfig.app.json")
    copy_file_safe(WORKSPACE_ROOT / "frontend" / "tsconfig.node.json", frontend_dst / "tsconfig.node.json")
    copy_file_safe(WORKSPACE_ROOT / "frontend" / "index.html", frontend_dst / "index.html")
    copy_file_safe(WORKSPACE_ROOT / "frontend" / ".env.example", frontend_dst / ".env.example")

    # 3. Create Documentation
    print("\n[3/5] Authoring Release Documentation...")
    docs_dst = RELEASE_DIR / "docs"
    docs_dst.mkdir(parents=True, exist_ok=True)

    (docs_dst / "INSTALLATION.md").write_text("""# FACECORE AI — Local Installation Guide

## System Prerequisites
- **Operating System:** Windows 10/11 x64, Linux (Ubuntu 20.04+), or macOS.
- **Python:** Version 3.10 to 3.13 (64-bit).
- **Node.js:** Version 18.0 or higher.
- **Hardware:** Modern x86_64 CPU with AVX2 instruction support. Minimum 4 GB RAM.

## Quick-Start Setup

### 1. Backend Virtual Environment
```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
# Linux / macOS:
# source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Verify Neural Network Weights
```bash
python scripts/verify_weights.py
```
If weights are missing, the verification script will print the direct download URLs.

### 3. Frontend Installation
```bash
cd ../frontend
npm install
npm run build
```

### 4. Launch Application
In the project root directory, run:
```powershell
# Windows PowerShell:
.\\start.ps1
# Windows Command Prompt:
start.bat
```
Open your browser at `http://localhost:5173`.
""", encoding="utf-8")

    (docs_dst / "MODEL_PROVENANCE.md").write_text("""# Neural Model Provenance & Checksums

FACECORE AI utilizes two lightweight, high-performance neural network backbones from the official OpenCV Model Zoo:

## 1. YuNet (Facial Landmark Detector)
- **File:** `face_detection_yunet_2023mar.onnx`
- **Architecture:** Fast depthwise separable convolution network with feature pyramids.
- **Output:** Bounding box $[x, y, w, h]$, confidence score, and 5 facial landmarks (right eye, left eye, nose tip, right mouth corner, left mouth corner).
- **Official SHA-256:** `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`
- **License:** Apache-2.0

## 2. SFace / SphereFace2 (Hyperspherical Feature Extractor)
- **File:** `face_recognition_sface_2021dec.onnx`
- **Architecture:** Deep convolutional neural network trained with hyperspherical margin loss.
- **Input:** $112 \\times 112$ 5-point affine aligned facial crop.
- **Output:** 128-dimensional unit normalized feature vector.
- **Similarity Metric:** Cosine similarity (inner dot product) bounded in $[-1.0, 1.0]$.
- **Official SHA-256:** `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79`
- **License:** Apache-2.0
""", encoding="utf-8")

    (docs_dst / "API_DOCUMENTATION.md").write_text("""# FACECORE AI — API Reference

All requests are serviced locally on `http://127.0.0.1:8001`. Interactive Swagger documentation is available at `/docs`.

## Key Endpoints

- `GET /api/health`: System health, version, engine operational state.
- `GET /api/ready`: Readiness probe verifying weights and SQLite DB presence.
- `GET /api/engine-info`: Detailed metadata on YuNet + SFace pipeline.
- `POST /api/validate-image`: Multipart upload validating file signatures, dimensions, and sharpness.
- `POST /api/compare`: Multipart upload comparing Probe Image A against Reference Image B with selected threshold profile.
- `GET /api/dashboard/stats`: Aggregated operational throughput, FTA rates, and telemetry.
- `GET /api/history`: Recent pairwise audit logs (metadata only, zero images/embeddings).
- `DELETE /api/history`: Clear or prune historical comparison logs.
- `GET /api/benchmarks/datasets`: List of registered evaluation datasets.
""", encoding="utf-8")

    # 4. Copy Root Launchers & Readme
    print("\n[4/5] Packaging Root Launchers & README...")
    copy_file_safe(WORKSPACE_ROOT / "start.ps1", RELEASE_DIR / "start.ps1")
    copy_file_safe(WORKSPACE_ROOT / "start.bat", RELEASE_DIR / "start.bat")
    copy_file_safe(WORKSPACE_ROOT / "README.md", RELEASE_DIR / "README.md")

    # 5. Inventory and Hash Computation
    print("\n[5/5] Generating Cryptographic Release Manifest...")
    manifest_entries = []
    total_files = 0
    total_bytes = 0

    for root, _, files in os.walk(RELEASE_DIR):
        for f in files:
            file_path = Path(root) / f
            rel_path = file_path.relative_to(RELEASE_DIR).as_posix()
            size = file_path.stat().st_size
            sha256 = compute_sha256(file_path)
            manifest_entries.append({
                "path": rel_path,
                "size_bytes": size,
                "sha256": sha256,
            })
            total_files += 1
            total_bytes += size

    manifest_entries.sort(key=lambda x: x["path"])

    print(f"Total packaged files: {total_files}")
    print(f"Total package size:   {total_bytes / (1024 * 1024):.2f} MB")

    # Generate STEP11_RELEASE_MANIFEST.md in workspace root
    manifest_md_path = WORKSPACE_ROOT / "STEP11_RELEASE_MANIFEST.md"
    with open(manifest_md_path, "w", encoding="utf-8") as md:
        md.write("# FACECORE AI — STEP 11: PRODUCTION RELEASE MANIFEST\n")
        md.write("**Release Version:** `1.0.0-prod`  \n")
        md.write("**Release Date:** 2026-11-02  \n")
        md.write("**Package Root:** `release/facecore-ai/`  \n")
        md.write(f"**Total Files Packaged:** {total_files}  \n")
        md.write(f"**Total Package Footprint:** {total_bytes / (1024 * 1024):.2f} MB  \n\n")

        md.write("---\n\n")
        md.write("## 1. Release Specification & Environment\n\n")
        md.write("- **Operating Systems:** Windows 10/11 x64 (Native), Linux x86_64, macOS 12+\n")
        md.write("- **Python Version:** 3.10, 3.11, 3.12, 3.13\n")
        md.write("- **Node.js Version:** v18.0.0+\n")
        md.write("- **Neural Execution:** Local CPU via OpenCV DNN (INT8/FP32)\n")
        md.write("- **Network Dependency:** ZERO (100% Offline Local Operation)\n")
        md.write("- **Biometric Privacy:** ZERO image persistence, ZERO embedding persistence\n\n")

        md.write("## 2. Neural Network Model Weights Provenance\n\n")
        md.write("| Model File | Role | Expected SHA-256 | License |\n")
        md.write("| :--- | :--- | :--- | :---: |\n")
        md.write("| `face_detection_yunet_2023mar.onnx` | 5-point facial landmark detector | `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4` | Apache-2.0 |\n")
        md.write("| `face_recognition_sface_2021dec.onnx` | 128-d hyperspherical feature extractor | `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79` | Apache-2.0 |\n\n")

        md.write("## 3. Package File Inventory & SHA-256 Checksums\n\n")
        md.write("| File Relative Path | Size (Bytes) | SHA-256 Checksum |\n")
        md.write("| :--- | :---: | :--- |\n")
        for e in manifest_entries:
            md.write(f"| `{e['path']}` | {e['size_bytes']:,} | `{e['sha256']}` |\n")

        md.write("\n---\n\n")
        md.write("## 4. Verification & Installation\n\n")
        md.write("Operators can verify release package integrity by running:\n")
        md.write("```powershell\n")
        md.write("cd release\\facecore-ai\n")
        md.write("python backend\\scripts\\verify_weights.py\n")
        md.write(".\\start.ps1\n")
        md.write("```\n")

    print(f"Wrote release manifest to: {manifest_md_path}")
    print("\n" + "=" * 70)
    print(" RELEASE PACKAGE & MANIFEST GENERATED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    build_release()
