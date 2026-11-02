# FACECORE AI — STEP 10: PRODUCTION DEPLOYMENT & SYSTEM MANUAL

**Document Version:** 1.0.0 (Production Release)  
**Date:** November 2026  
**Pipeline:** OpenCV YuNet (INT8/FP32) + SFace (SphereFace2, 128-d)  
**Operating Execution Mode:** 100% Local Multi-Threaded CPU (No Cloud Dependencies)  
**Persistence Layer:** SQLite (Write-Ahead Logging / WAL Mode)  
**Biometric Privacy Guarantee:** Strict Zero-Persistence of Facial Images or Vectors (Memory-Only Ephemeral Execution)

---

## 1. Executive Summary & Transition Status

FACECORE AI has transitioned from scientific research, empirical dataset evaluation, and statistical forensics (Steps 01 through 09.2) into a production-grade, hardened, and locally deployable biometric verification and evaluation software product.

### Core Transition Principles
1. **Model Pipeline Preservation:** The production model weights (YuNet face detector + SFace recognizer) remain unmodified from scientific validation phases.
2. **Scientific Metric Integrity:** Evaluated benchmark results, Clopper-Pearson confidence intervals, and Step 01–09.2 audit logs are preserved intact.
3. **Operational Hardening:** Thread safety locks protect OpenCV DNN C++ inference against reentrancy crashes under concurrent API traffic.
4. **Zero-Storage Privacy Architecture:** Uploaded image byte streams exist in RAM strictly for the duration of inference. Neither raw photograph pixels nor 128-dimensional neural vector embeddings are ever saved to disk or written to database records.
5. **Calibrated Threshold Profiles:** Operating points derived from empirical benchmark distributions replace uncalibrated placeholder thresholds across the entire user experience.

---

## 2. System Architecture & Components

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FACECORE AI APPLICATION                         │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  [ FRONTEND - REACT 18 + VITE ] (Port 5173)                            │
│  ├── Audit Dashboard (Live SQLite Telemetry & Throughput)              │
│  ├── Biometric Pair Inspection (Dual Upload, Face Overlays, Crop)      │
│  ├── Calibrated Threshold Profiles (High Security, Balanced, etc.)    │
│  ├── Scientific Test Lab & Standardized Benchmarks (LFW, CPLFW, etc.)  │
│  └── Settings & Biometric Privacy Manifesto                            │
│                                │                                       │
│                                ▼ HTTP / REST JSON                     │
│                                                                        │
│  [ BACKEND - FASTAPI + UVICORN ] (Port 8001)                           │
│  ├── App Config (.env / typed Settings / Security Limits)              │
│  ├── Ingestion Quality Gates (48px Hard Floor / 16px Face Box Floor)   │
│  ├── Thread-Safe FaceDetector (OpenCV FaceDetectorYN + Mutex)          │
│  ├── Thread-Safe SFace Engine (OpenCV FaceRecognizerSF + _INFERENCE_LOCK)
│  ├── Benchmarks Runner & Statistical Evaluation Engine                 │
│  └── SQLite Database Manager (WAL Mode, Schema Migrations)             │
│                                │                                       │
│                                ▼ SQLite (No Vectors / No Photos)       │
│                                                                        │
│  [ PERSISTENCE - SQLite (WAL MODE) ] (backend/data/facecore.db)        │
│  ├── comparison_audit_log (SHA-256 prefixes, scores, latencies)        │
│  ├── benchmark_runs (dataset IDs, accuracy, EER, AUC, execution times) │
│  └── schema_migrations (versioned database migrations)                 │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Hardware & Software Requirements

### Hardware Specifications
| Parameter | Minimum Requirements | Recommended Production |
| :--- | :--- | :--- |
| **Processor** | 2-Core x86_64 / ARM64 CPU | 4-Core or 8-Core modern CPU |
| **RAM** | 4 GB | 8 GB or 16 GB |
| **Disk Space** | 500 MB (application + models) | 2 GB (with benchmark corpora) |
| **Operating System** | Windows 10/11, Ubuntu 20.04+, macOS 12+ | Windows 11 / Ubuntu 22.04 LTS |
| **GPU Requirement** | None (100% CPU inference optimized) | None |

### Software Prerequisites
- **Python:** Version 3.10, 3.11, 3.12, or 3.13.
- **Node.js:** Version 18.0.0 or higher (v20+ LTS recommended).
- **Package Managers:** `pip` (Python) and `npm` (Node.js).

---

## 4. Cryptographic Model Weights Verification

The system requires two official OpenCV Model Zoo ONNX model weight files located in `backend/app/weights/`:

| File Name | File Size | Role | SHA-256 Digest |
| :--- | :--- | :--- | :--- |
| `face_detection_yunet_2023mar.onnx` | 232,589 B | 5-point landmark face detector | `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4` |
| `face_recognition_sface_2021dec.onnx` | 38,696,353 B | 128-d hyperspherical embedder | `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79` |

### Automated Weight Verification Script
To verify the presence and cryptographic checksums of the weights:
```powershell
python backend/scripts/verify_weights.py
```

Expected output:
```
======================================================================
 ALL MODEL WEIGHTS VERIFIED SUCCESSFULLY (100% INTEGRITY CHECK PASSED)
======================================================================
```

---

## 5. Calibrated Operating Threshold Profiles (Step 09.2)

To avoid reliance on decorative or uncalibrated thresholds, FACECORE AI provides four named operating profiles calibrated during extensive 10-fold cross-validation on canonical benchmarks:

| Profile Key | Profile Name | Decision Threshold ($\tau$) | Target Performance | Population FAR Bound (95% CI) | Recommended Use Case |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `high_security` | **High Security** | **$0.3600$** | $\text{FAR} \le 0.1\%$ ($3 / 3,000$ impostor errors) | $\le 0.292\%$ (Clopper-Pearson) | Access control, identity gating, biometric authentication |
| `balanced` | **Balanced (LFW Native)** | **$0.3132$** | Equal Error Rate ($\text{EER} \approx 0.5\%$, $\text{Acc} = 99.50\%$) | $\le 0.725\%$ | General pairwise comparison, default workflow |
| `high_convenience` | **High Convenience** | **$0.2500$** | $\text{FRR} \le 0.1\%$ ($\text{TAR} > 99.90\%$) | $\le 1.98\%$ | Adverse lighting, profile pose, low user friction |
| `custom` | **Custom** | User Defined | Custom research evaluation | Uncalibrated outside standard benchmarks | Specialized academic experiments |

> **Scientific Disclosure:**  
> A facial similarity score represents continuous vector proximity in 128-dimensional hyperspherical space. It is **never** an absolute identity certainty percentage. The display index ($Linear: \frac{\cos + 1}{2} \times 100$) is a scaled visual indicator and must never be interpreted as an identity probability.

---

## 6. Image Ingestion Gates & Quality Advisories

To protect inference stability and biometric accuracy against low-resolution degradation, the platform enforces strict quality gates:

1. **Hard Floor Rejection Gate:**
   - Any uploaded image with canvas width or height $< 48$ px is rejected immediately with HTTP 422 (`IMAGE_BELOW_MIN_DIMENSION`).
2. **Face Box Floor (100% FTA Risk):**
   - If a detected face bounding box width or height is $< 16$ px, face alignment cannot be computed reliably, producing a 100% Failure to Acquire (FTA) rate.
3. **Soft Quality Advisory Gate:**
   - Detected face bounding boxes with width $< 48$ px trigger a visible quality advisory in the UI:
     > *"Advisory: Face width < 48px induces genuine score attenuation, elevating false rejection risks."*
4. **Safe Operational Region:**
   - Face bounding boxes $\ge 128$ px width operate within the nominal resolution envelope for YuNet and SFace.

---

## 7. Zero-Storage Ephemeral Privacy Architecture

FACECORE AI implements a strict local-first, zero-persistence policy:

| Telemetry / Data Item | In Memory (RAM) | Stored to Disk (SQLite) | Exported to External Services |
| :--- | :---: | :---: | :---: |
| **Uploaded Photograph Bytes** | Yes (Transient) | **NEVER** | **NEVER** |
| **Aligned Face Crop** | Yes (Transient) | **NEVER** | **NEVER** |
| **128-d Float Feature Vector** | Yes (Transient) | **NEVER** | **NEVER** |
| **Cryptographic SHA-256 Prefix** | Yes | Yes (First 8-16 chars) | **NEVER** |
| **Cosine Similarity Score** | Yes | Yes (Scalar float) | **NEVER** |
| **Latency & Quality Flags** | Yes | Yes (Metadata only) | **NEVER** |

### SQLite Schema Guarantee
The `comparison_audit_log` table contains **zero** BLOB, image, or vector columns:
```sql
CREATE TABLE comparison_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    probe_hash_prefix TEXT NOT NULL,
    reference_hash_prefix TEXT NOT NULL,
    similarity_score REAL,
    display_score REAL,
    threshold_used REAL NOT NULL,
    threshold_profile TEXT NOT NULL,
    is_match INTEGER NOT NULL,
    latency_ms REAL NOT NULL,
    face_count_a INTEGER NOT NULL,
    face_count_b INTEGER NOT NULL,
    quality_flags_a TEXT,
    quality_flags_b TEXT,
    status TEXT NOT NULL
);
```

---

## 8. Deployment & Execution Instructions

### Step 1: Environment Setup
Clone the repository and initialize the virtual environments:
```powershell
# 1. Initialize Python virtual environment
cd "C:\Projects\project 7 - face checking tool"
python -m venv backend\.venv
backend\.venv\Scripts\pip install -r backend\requirements.txt

# 2. Install Frontend dependencies
npm --prefix frontend install
```

### Step 2: Environment Configuration
Copy the production environment template:
```powershell
copy backend\.env.example backend\.env
```
Default `.env` configuration:
```ini
APP_NAME=FACECORE AI
APP_VERSION=1.0.0-prod
ENVIRONMENT=production
DEBUG=false
DEFAULT_THRESHOLD_PROFILE=balanced
MIN_IMAGE_DIMENSION=48
MAX_UPLOAD_SIZE_BYTES=15728640
DATABASE_PATH=backend/data/facecore.db
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### Step 3: Launch Services

#### Option A: One-Click Startup Script (PowerShell — Recommended)
```powershell
.\start.ps1
```
This script:
1. Verifies the Python venv and Node.js installation.
2. Validates SHA-256 checksums of the ONNX models.
3. Checks for port conflicts.
4. Starts FastAPI on port 8001 and Vite on port 5173.
5. Monitors both processes and cleans them up on `Ctrl+C`.

#### Option B: One-Click Batch Script (Windows CMD)
```cmd
start.bat
```

#### Option C: Manual Multi-Terminal Startup
**Terminal 1 (Backend):**
```powershell
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001
```

**Terminal 2 (Frontend):**
```powershell
npm --prefix frontend run dev
```

---

## 9. Verification & Test Suite Execution

All test suites across backend and frontend must achieve a 100% pass rate:

### Frontend Unit & Component Tests (Vitest)
```powershell
npm --prefix frontend test -- --run
```
Output:
```
Test Files  10 passed (10)
     Tests  54 passed (54)
```

### Frontend Production Bundle Build (Vite)
```powershell
npm --prefix frontend run build
```
Output:
```
✓ built in 1.04s
```

### Backend Production & Forensic Audit Tests (Pytest)
```powershell
backend\.venv\Scripts\pytest.exe backend\tests\test_step10_production.py backend\tests\test_benchmarks_step092_audit.py backend\tests\test_benchmarks_step091_audit.py backend\tests\test_benchmarks_step08_cross_dataset.py -v
```
Output:
```
============================= 35 passed in 12.4s =============================
```

---

## 10. Operational Troubleshooting

### Issue 1: OpenCV DNN Graph Engine Warnings
**Symptom:**
```
[ WARN:0@0.053] cv::dnn::Net::Impl::setPreferableTarget Targets are not supported by the new graph engine for now
```
**Cause & Impact:** OpenCV 4.10+ outputs an informational warning on Windows when CPU execution target is assigned.  
**Resolution:** This is standard OpenCV diagnostic logging. CPU inference is fully functional, thread-safe, and accelerated via AVX2/FMA SIMD intrinsics.

### Issue 2: Port 8001 or 5173 Already Bound
**Symptom:** `Error: listen EADDRINUSE: address already in use 127.0.0.1:8001`  
**Resolution:**
```powershell
# Identify and terminate stale process
Get-NetTCPConnection -LocalPort 8001 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
Get-NetTCPConnection -LocalPort 5173 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

### Issue 3: SQLite Database Locked
**Symptom:** `sqlite3.OperationalError: database is locked`  
**Resolution:** The backend uses SQLite in Write-Ahead Logging (WAL) mode with a 5000ms busy timeout and Python process-level threading locks (`_DB_LOCK`). If a lock persists due to an unhandled OS crash:
```powershell
Remove-Item backend\data\facecore.db-wal, backend\data\facecore.db-shm -ErrorAction SilentlyContinue
```

---

## 11. Maintenance & Database Archival

To inspect SQLite database health or vacuum storage:
```powershell
# Check database size
(Get-Item backend\data\facecore.db).Length / 1KB

# Clear comparison audit history via API
Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/history" -Method Delete
```

---

**FACECORE AI Engineering Team — Step 10 Complete**

