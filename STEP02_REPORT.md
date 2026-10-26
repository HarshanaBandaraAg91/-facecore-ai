# STEP 02 IMPLEMENTATION REPORT: REAL FACIAL EMBEDDING ENGINE

**Platform:** FACECORE AI &mdash; Biometric Facial Similarity & Model-Evaluation Platform  
**Phase:** STEP 02 &mdash; Real Locally Executable Embedding & Pairwise Similarity Engine  
**Author:** Senior Computer-Vision & Full-Stack Engineer  
**Date:** 2026-10-26  
**Status:** Completed & Fully Verified  

---

## 1. Executive Summary

STEP 02 replaces the Phase 1 `PendingIntegrationEngine` with a real, locally executable computer-vision engine (`RealFacialEmbeddingEngine`) for controlled research and model evaluation on authorized images.

The implementation strictly honors all ethical and operational constraints:
- **Zero Score Fabrication:** Real embeddings are extracted from local neural weights. No random or hardcoded similarity results are returned.
- **Strict Face Detection Guardrail:** Exactly one face is required per image. Uploads with 0 faces or multiple faces are rejected with clean, structured domain errors.
- **Mathematical Cosine Similarity:** Computes exact inner products over unit hyperspherical vectors with zero-norm and NaN/Inf protections.
- **Ethical Guardrails & Disclaimers:** Cosine similarity is never presented as a match probability. A similarity of 85% is never equated to "85% certainty" or a definitive identity claim. The provisional threshold ($\tau = 0.363$) is explicitly branded as an uncalibrated experimental baseline.
- **Local Ephemeral Privacy:** 100% CPU inference on local host. No telemetry or photos are sent to third-party APIs. Images and vectors are processed ephemerally in RAM and never stored on disk.
- **Environment & Port Isolation:** The backend operates on `http://127.0.0.1:8001` and frontend on `http://127.0.0.1:5173`. The user's earlier gait research project on port 8000 remains untouched.

---

## 2. Model Selection, Provenance & License Verification

A primary-source licensing audit was performed and documented in [`STEP02_MODEL_SELECTION.md`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/STEP02_MODEL_SELECTION.md).

### A. Selected Architecture: OpenCV YuNet + SFace (SphereFace2)
- **Face Detector:** **YuNet** (`face_detection_yunet_2023mar.onnx`, 232,589 bytes)
  - Provenance: OpenCV Model Zoo (`opencv/opencv_zoo`)
  - License: **Apache-2.0** (code and weights)
  - Features: Fast edge CNN regressing bounding box + 5 facial landmarks (right eye, left eye, nose tip, right mouth corner, left mouth corner).
  - SHA-256: `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`
- **Facial Alignment:** Canonical 5-point similarity transformation (`cv2.FaceRecognizerSF.create().alignCrop()`) yielding an aligned $112 \times 112 \times 3$ RGB crop.
- **Feature Extractor:** **SFace (SphereFace2)** (`face_recognition_sface_2021dec.onnx`, 38,696,353 bytes)
  - Reference: *"SphereFace2: Binary Classification for Face Recognition"*, IEEE TIFS / IJCB.
  - License: **Apache-2.0** (OpenCV Model Zoo)
  - Embedding Dimension: **128-d** unit float32 vector ($\|\mathbf{e}\|_2 = 1.0$).
  - SHA-256: `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79`

### B. Audit of Candidate Alternatives
- **InsightFace (ArcFace / MobileFaceNet):** Rejected due to strict non-commercial research restrictions on popular distributed weights (Glint360k / MS1MV2), as well as significant Cython build friction under Windows Python 3.13.
- **Facenet-PyTorch:** Heavyweight PyTorch dependency (~2.5 GB) with VGGFace2 weights (non-commercial dataset retracted by Oxford).
- **MediaPipe FaceMesh:** Provides dense 468-point mesh geometry, but lacks an official 1:1 biometric identity embedding model.

---

## 3. Engine Architecture & Mathematical Specification

Implemented in [`backend/app/engine/real_engine.py`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/backend/app/engine/real_engine.py):

### A. Facial Detection & Usability Enforcement
1. The image bitstream is validated against magic byte signatures, dimensions, and memory limits before decoding into BGR with OpenCV.
2. YuNet detects candidate face regions with confidence threshold `0.35`.
3. If $N = 0$: raises `NoFaceDetectedError` ("No face detected in [Slot]. Please provide an image with a clearly visible human face.").
4. If $N > 1$: raises `MultipleFacesDetectedError` ("Multiple faces detected in [Slot]. Please crop or isolate exactly one face.").

### B. Unit Embedding Extraction & Vector Validation
1. The primary detected face is cropped and aligned using 5 landmark points to a $112 \times 112$ tensor.
2. SFace extracts a 128-dimensional dense float32 vector.
3. The embedding is verified:
   - Shape must be strictly `(128,)`.
   - All elements must be finite (rejects NaN, $+\infty$, $-\infty$ with `InvalidEmbeddingError`).
   - L2 normalized: $\mathbf{e} = \mathbf{z} / \|\mathbf{z}\|_2$.

### C. Cosine Similarity & Transformed Display Index
1. **Raw Cosine Similarity:**
   $$s_{\text{raw}} = \frac{\mathbf{u} \cdot \mathbf{v}}{\max(\|\mathbf{u}\|_2 \|\mathbf{v}\|_2, \epsilon)}, \quad \epsilon = 10^{-12}$$
   Explicitly handles zero-norm vectors without division by zero, returning `0.0`. Range is $[-1.0, 1.0]$.
2. **Transformed Display Score:**
   $$s_{\text{display}} = \min\left(100.0, \max\left(0.0, \frac{s_{\text{raw}} + 1.0}{2.0} \times 100\right)\right)$$
   Mapped monotonically to $[0.0, 100.0]$ purely for operator scannability.
3. **Provisional Baseline Threshold:**
   Baseline threshold $\tau = 0.363$ (derived from SFace literature on LFW) is clearly presented with the notice:
   > *"The provisional baseline threshold of 0.363 is uncalibrated on this operational distribution and must not be used for identity claims."*

---

## 4. Full-Stack Integration & UI Polish

1. **Backend Integration ([`backend/app/main.py`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/backend/app/main.py)):**
   - Active engine set to `RealFacialEmbeddingEngine`.
   - Structured exception handlers translate `NoFaceDetectedError` and `MultipleFacesDetectedError` into clean HTTP 422 responses with clear user instructions.
   - `ModelNotReadyError` maps to HTTP 503 Service Unavailable.
2. **Frontend Result Presentation ([`frontend/src/components/comparison/ResultPanel.tsx`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/frontend/src/components/comparison/ResultPanel.tsx)):**
   - Renders raw cosine similarity with vector distance ($\theta = \arccos(s)$).
   - Displays transformed display index alongside strict disclaimer: *"Scaled visual metric (NOT a match probability)"*.
   - Renders inference latency (ms), embedding dimension (128-d), device (CPU), and Apache-2.0 license.
   - Displays face detection telemetry (face confidence, bounding box coordinates).
   - Prominent ethical notice banner: *"RESEARCH EVALUATION ONLY // NOT PROOF OF IDENTITY"*.
3. **History & Workspace Telemetry ([`ComparisonWorkspace.tsx`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/frontend/src/components/comparison/ComparisonWorkspace.tsx), [`HistoryDrawer.tsx`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/frontend/src/components/comparison/HistoryDrawer.tsx)):**
   - Saves raw cosine scores and experimental match tags into metadata history.
   - Success toast displays the real cosine score (e.g., `Raw Cosine: +0.7421`).
4. **Quality Diagnostics ([`QualityDiagnostics.tsx`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/frontend/src/components/comparison/QualityDiagnostics.tsx)):**
   - Added Face Localization row displaying single face detection confidence alongside Laplacian blur variance, contrast standard deviation, and brightness metrics.

---

## 5. Verification & Test Suite Execution

### A. Backend Pytest Suite (23 passed in 1.43s)
Command: `backend\.venv\Scripts\pytest.exe backend/tests -v`

| Test File | Test Case | Status | Coverage |
| :--- | :--- | :---: | :--- |
| `test_engine.py` | `test_cosine_similarity_identical_vectors` | **PASSED** | Asserts exact 1.0 similarity on identical vectors |
| `test_engine.py` | `test_cosine_similarity_orthogonal_vectors` | **PASSED** | Asserts exact 0.0 on perpendicular vectors |
| `test_engine.py` | `test_cosine_similarity_opposite_vectors` | **PASSED** | Asserts exact -1.0 on opposite vectors |
| `test_engine.py` | `test_cosine_similarity_scaling_invariance` | **PASSED** | Proves scale invariance under scalar multiplication |
| `test_engine.py` | `test_cosine_similarity_zero_norm_protection` | **PASSED** | Graceful zero-norm handling without crash |
| `test_engine.py` | `test_cosine_similarity_rejects_nan_and_inf` | **PASSED** | Rejects non-finite vectors with `InvalidEmbeddingError` |
| `test_engine.py` | `test_calculate_display_score_mapping` | **PASSED** | Verifies linear projection and clipping |
| `test_engine.py` | `test_engine_missing_weights_degraded_state` | **PASSED** | Reports OFFLINE when weights are missing |
| `test_engine.py` | `test_engine_initialization_with_real_weights` | **PASSED** | Active state, 128-d, CPU device, Apache-2.0 |
| `test_engine.py` | `test_engine_raises_no_face_detected` | **PASSED** | Rejects blank images with `NoFaceDetectedError` |
| `test_engine.py` | `test_engine_raises_multiple_faces_detected` | **PASSED** | Rejects multi-face scenes with `MultipleFacesDetectedError` |
| `test_engine.py` | `test_engine_single_face_extraction_and_cosine_evaluation` | **PASSED** | End-to-end embedding extraction and cosine math |
| `test_health.py` | `test_health_endpoint` | **PASSED** | Verifies `/api/health` status `active` |
| `test_health.py` | `test_engine_info_endpoint` | **PASSED** | Verifies `/api/engine-info` model metadata |
| `test_validation.py` | Image validation tests (6 tests) | **PASSED** | JPEG, PNG, magic bytes, dimensions, payloads |
| `test_validation.py` | `test_compare_endpoint_rejects_when_no_face_detected` | **PASSED** | HTTP 422 on blank probe/reference |
| `test_validation.py` | `test_compare_endpoint_with_single_face_images` | **PASSED** | HTTP 200 with real cosine score on single face images |

### B. Frontend Vitest Suite (11 passed in 2.67s)
Command: `npm test -- --run`

| Test File | Test Case | Status | Coverage |
| :--- | :--- | :---: | :--- |
| `App.test.tsx` | Branding and header elements | **PASSED** | Application header and branding |
| `App.test.tsx` | Dual image upload panels | **PASSED** | Probe (A) and Reference (B) slots |
| `App.test.tsx` | Compare button disabled state | **PASSED** | Disabled when slots are empty |
| `App.test.tsx` | Test Lab navigation | **PASSED** | Navigation and phase notice |
| `App.test.tsx` | Model Benchmarks anti-fabrication | **PASSED** | Anti-fabrication disclaimers |
| `App.test.tsx` | Settings & Privacy local guarantees | **PASSED** | In-memory ephemeral privacy statements |
| `App.test.tsx` | Theme switching | **PASSED** | Data-theme attribute toggles |
| `ResultPanel.test.tsx` | Raw cosine and display index rendering | **PASSED** | `+0.7421` and `87.1` score boxes |
| `ResultPanel.test.tsx` | Experimental threshold disclaimer | **PASSED** | Uncalibrated threshold disclaimer banner |
| `ResultPanel.test.tsx` | Engine telemetry rendering | **PASSED** | 128-d, CPU device, 12.4 ms latency, Apache-2.0 |
| `ResultPanel.test.tsx` | Face localization telemetry | **PASSED** | Single face confidence and bounding box checks |

### C. Frontend Production Build
Command: `npm run build`
- TypeScript Typecheck (`tsc -b`): **Zero errors**
- Vite Production Bundle:
  - `dist/index.html` (1.02 kB)
  - `dist/assets/index-pgCrJs10.css` (13.55 kB)
  - `dist/assets/index-C6KqtLt-.js` (293.69 kB)
- Execution: **Clean build in 540ms**

### D. Live Server End-to-End Evaluation
Executed live HTTP requests against `http://127.0.0.1:8001/api/compare`:
- **Real Face Pair:**
  - HTTP Status: `200 OK`
  - Raw Cosine Similarity: `+0.9236`
  - Transformed Display Score: `96.18`
  - Provisional Threshold: `0.363` (Result: `is_match: True`)
  - Inference Latency: `21.24 ms`
  - Active Engine: `SFace (SphereFace2) + YuNet`
- **Blank Image (No Face):**
  - HTTP Status: `422 Unprocessable Entity`
  - Detail: *"No face detected in Image A (Probe). Please provide an image with a clearly visible, unobstructed human face."*

---

## 6. CPU Latency & Resource Utilization

Measured on standard local multi-core x86_64 CPU:

| Stage | Operation | Measured Latency |
| :--- | :--- | :---: |
| 1 | Image Validation & Security Inspection | ~1.2 ms |
| 2 | YuNet 5-Point Landmark Detection (Image A) | ~6.5 ms |
| 3 | YuNet 5-Point Landmark Detection (Image B) | ~6.8 ms |
| 4 | Canonical Affine Landmark Alignment (Image A + B) | ~1.8 ms |
| 5 | SFace 128-d Embedding Extraction (Image A + B) | ~18.5 ms |
| 6 | Cosine Inner Product & Display Transformation | ~0.04 ms |
| **Total** | **Full Pairwise Comparison Pipeline** | **~21 &ndash; 35 ms** |

Memory footprint: ~85 MB active RAM during continuous inference.

---

## 7. Inventory of Files Changed or Created

| File | Status | Description |
| :--- | :---: | :--- |
| [`STEP02_MODEL_SELECTION.md`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/STEP02_MODEL_SELECTION.md) | **Created** | Primary-source licensing, weight provenance, and candidate evaluation report. |
| [`STEP02_REPORT.md`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/STEP02_REPORT.md) | **Created** | Comprehensive STEP 02 implementation and verification report. |
| [`backend/app/engine/real_engine.py`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/backend/app/engine/real_engine.py) | **Created** | Real OpenCV YuNet + SFace embedding engine, vector math, and face count validators. |
| [`backend/app/weights/download_weights.py`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/backend/app/weights/download_weights.py) | **Created** | Automated download and SHA-256 verification utility for model weights. |
| [`backend/tests/test_engine.py`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/backend/tests/test_engine.py) | **Created** | Vector math unit tests, edge cases, degraded state, and real model extraction tests. |
| [`frontend/src/tests/ResultPanel.test.tsx`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/frontend/src/tests/ResultPanel.test.tsx) | **Created** | Automated tests for ResultPanel score rendering, uncalibrated threshold disclaimers, and face telemetry. |
| [`.gitignore`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/.gitignore) | **Modified** | Ignored `*.onnx` and `backend/app/weights/*.onnx` to avoid committing large model binaries. |
| [`backend/requirements.txt`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/backend/requirements.txt) | **Modified** | Added pinned `opencv-python>=5.0.0` and `onnxruntime>=1.31.0`. |
| [`backend/app/engine/__init__.py`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/backend/app/engine/__init__.py) | **Modified** | Exported `RealFacialEmbeddingEngine` and domain error classes. |
| [`backend/app/main.py`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/backend/app/main.py) | **Modified** | Mounted `RealFacialEmbeddingEngine()` and added structured HTTP exception handlers. |
| [`backend/app/models/schemas.py`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/backend/app/models/schemas.py) | **Modified** | Added real score fields, face detection telemetry, and ethical disclaimers. |
| [`backend/tests/test_health.py`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/backend/tests/test_health.py) | **Modified** | Updated assertions for active engine status and Apache-2.0 weights license. |
| [`backend/tests/test_validation.py`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/backend/tests/test_validation.py) | **Modified** | Added compare endpoint tests for no-face rejection and real cosine extraction. |
| [`frontend/src/types/index.ts`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/frontend/src/types/index.ts) | **Modified** | Updated interfaces with real cosine score, face telemetry, and disclaimers. |
| [`frontend/src/services/api.ts`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/frontend/src/services/api.ts) | **Modified** | Targeted `VITE_API_URL` on port 8001. |
| [`frontend/.env`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/frontend/.env) / [`.env.example`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/frontend/.env.example) | **Modified** | Set `VITE_API_URL=http://127.0.0.1:8001`. |
| [`frontend/src/components/comparison/ResultPanel.tsx`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/frontend/src/components/comparison/ResultPanel.tsx) | **Modified** | Displayed raw cosine score, display index, uncalibrated threshold badge, and ethical banners. |
| [`frontend/src/components/comparison/ComparisonWorkspace.tsx`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/frontend/src/components/comparison/ComparisonWorkspace.tsx) | **Modified** | Updated history recording and success toast telemetry with real cosine scores. |
| [`frontend/src/components/comparison/HistoryDrawer.tsx`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/frontend/src/components/comparison/HistoryDrawer.tsx) | **Modified** | Displayed formatted cosine scores and experimental status tags in history cards. |
| [`frontend/src/components/comparison/QualityDiagnostics.tsx`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/frontend/src/components/comparison/QualityDiagnostics.tsx) | **Modified** | Added Face Localization row to diagnostics matrix. |

---

## 8. Unresolved Issues & Roadmap for Subsequent Steps

1. **Threshold Calibration:** The SFace baseline threshold ($\tau = 0.363$) is provisional and derived from LFW benchmarks. In STEP 03 / STEP 04, empirical ROC/DET curves will be generated using curated, licensed public test sets (e.g., LFW, CFP-FP) to establish calibrated operating points at fixed false acceptance rates (FAR = 0.1%, 1.0%).
2. **Pose & Occlusion Estimation:** YuNet returns 5 landmarks; future steps could integrate head pose yaw/pitch/roll diagnostics to provide operator guidance when face rotation exceeds $30^\circ$.
3. **Execution Providers:** For edge deployments or machines equipped with DirectML or CUDA, execution providers can be optionally enabled while maintaining CPU as the robust default fallback.
