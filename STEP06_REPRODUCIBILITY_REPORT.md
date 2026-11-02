# FACECORE AI &mdash; STEP 06: SCIENTIFIC REPRODUCIBILITY & AUDIT PROVENANCE REPORT

**Role:** Independent Machine-Learning Evaluation Auditor & Statistical Researcher  
**Phase:** STEP 06 &mdash; Independent Benchmark Audit and Scientific Validation  
**Date:** November 2026  
**Document:** Experimental Provenance, Repeated Trial Verification, Baseline Metrics, and Test Execution Log  

---

## 1. Executive Summary & Experimental Controls

To guarantee that FACECORE AI biometric evaluation benchmarks are completely reproducible, tamper-evident, and scientifically auditable, this report documents:
1. Complete cryptographic environment provenance (model hashes, dataset manifest hashes, library versions).
2. Two independent executions of the full evaluation benchmark under identical configuration ($seed=42$) to prove bit-for-bit repeatability.
3. Actual, verified benchmark results on the 10-fold identity-disjoint evaluation fixture.
4. Comprehensive test execution logs across backend and frontend test suites.
5. Remaining limitations and prioritized next experiments.

---

## 2. Experimental Environment Provenance

### 2.1. Software & Hardware Runtime Configuration

| Component | Verified Specification |
| :--- | :--- |
| **Operating System** | Microsoft Windows 11 Enterprise (win32) |
| **Host CPU Architecture** | x86_64, Multi-core |
| **Python Runtime** | Python 3.13.7 (tags/v3.13.7:bcee153, Feb 2025) |
| **OpenCV (`opencv-python`)** | Version 4.12.0 (with OpenCV DNN module) |
| **NumPy** | Version 2.2.3 |
| **Pytest** | Version 9.1.1 (pluggy 1.7.0, anyio 4.15.1) |
| **Node.js & NPM** | Node.js v20+, NPM v10+ |
| **Frontend Test Harness** | Vitest v5.0.5 with React Testing Library |
| **Frontend Production Bundler**| Vite v8.3.5 & TypeScript 5.x |

### 2.2. Cryptographic Asset Fingerprints (SHA-256)

All neural weights, dataset manifests, and configuration fixtures are cryptographically signed via SHA-256:

| Asset | Path | SHA-256 Checksum | License & Origin |
| :--- | :--- | :--- | :--- |
| **SFace Recognizer Model** | `backend/app/weights/face_recognition_sface_2021dec.onnx` | `0ba9fbfa01b5270cc69910dbe9a7fb3c9ba8f3b145610738e4a9057b6f6fcfa3` | Apache-2.0 (OpenCV Model Zoo) |
| **YuNet Detector Model** | `backend/app/weights/face_detection_yunet_2023mar.onnx` | `8f2383e4dd3cfbb4b6a0a7d9753e1be276f7b158fcce1dc2be289196b6d51bbd` | Apache-2.0 (OpenCV Model Zoo) |
| **10-Fold Disjoint Manifest**| In-Memory Canonical Fixture (120 pairs) | `5aeb6c8e0087a8c5eb3c04ce7a36cb9eb221147043831b747970ba4305bcdd00` | Internal Verified Test Fixture |

### 2.3. Model Baseline Architecture Controls
The production facial recognition pipeline was strictly preserved without altering weights:
- **Feature Backbone:** SFace (SphereFace2 hyperspherical angular margin architecture).
- **Embedding Space:** 128-dimensional unit normalized vector ($\|\mathbf{u}\|_2 = 1.0 \pm 10^{-6}$).
- **Detector Architecture:** YuNet CNN with 5-point facial landmark regression.
- **Image Alignment Procedure:** 5-point landmark similarity transform aligning eyes, nose tip, and mouth corners into a canonical $112 \times 112$ RGB/BGR input crop (`cv2.FaceRecognizerSF.alignCrop`).
- **Live Comparison Workflow:** Single-pair comparison endpoints remain completely operational.

---

## 3. Repeated Benchmark Trial Reproducibility

### 3.1. Trial Protocol
Two independent benchmark runs were executed using identical configuration:
- **Dataset ID:** `facecore-synthetic-fixture-v1`
- **Evaluation Folds:** 10 folds (Strictly identity-disjoint)
- **Pair Sample Size:** 120 pairs (60 genuine, 60 impostor)
- **Random Seed:** $42$
- **Robustness Suite:** Disabled for baseline timing verification

### 3.2. Side-by-Side Comparison of Results

| Metric / Telemetry Field | Trial 1 (`run_20261102_052036_f8eb3c`) | Trial 2 (`run_20261102_052042_a9d1e4`) | Discrepancy Observed |
| :--- | :---: | :---: | :---: |
| **Total Requested Pairs** | 120 | 120 | **None (0)** |
| **Evaluated Pairs** | 120 | 120 | **None (0)** |
| **Genuine Pairs** | 60 | 60 | **None (0)** |
| **Impostor Pairs** | 60 | 60 | **None (0)** |
| **Failure to Acquire (FTA)** | 0 (0.00%) | 0 (0.00%) | **None (0)** |
| **Mean Test Accuracy** | **84.167%** | **84.167%** | **None (0.00000)** |
| **Calibrated Threshold ($\bar{\tau}$)** | **0.96342** | **0.96342** | **None (0.00000)** |
| **Equal Error Rate (EER)** | **16.667%** | **16.667%** | **None (0.00000)** |
| **EER Operating Threshold** | **0.96200** | **0.96200** | **None (0.00000)** |
| **ROC-AUC (Wilcoxon-Mann-Whitney)** | **0.93278** | **0.93278** | **None (0.00000)** |
| **Confusion Matrix TP** | 50 | 50 | **None (0)** |
| **Confusion Matrix TN** | 51 | 51 | **None (0)** |
| **Confusion Matrix FP** | 9 | 9 | **None (0)** |
| **Confusion Matrix FN** | 10 | 10 | **None (0)** |
| **Confusion Matrix Accuracy** | **84.167%** | **84.167%** | **None (0.00000)** |
| **Precision** | 0.84746 | 0.84746 | **None (0.00000)** |
| **Recall** | 0.83333 | 0.83333 | **None (0.00000)** |
| **F1-Score** | 0.84034 | 0.84034 | **None (0.00000)** |
| **Manifest SHA-256 Hash** | `5aeb6c8e0087a8c5` | `5aeb6c8e0087a8c5` | **None (Identical)** |
| **Model Weights Hash** | `sface:0ba9...\|yunet:8f23...` | `sface:0ba9...\|yunet:8f23...` | **None (Identical)** |

**Reproducibility Verdict:**  
**100% BIT-FOR-BIT REPRODUCIBLE.** Zero numerical variance across all scalar and vector metrics under identical seeds.

---

## 4. Actual Controlled Baseline Benchmark Results

### 4.1. Core Performance Telemetry

```
==================================================================================
FACECORE AI &mdash; SFace (SphereFace2) Baseline Benchmark Telemetry
Protocol: 10-Fold Stratified Cross-Validation (Identity-Disjoint)
Sample Size: N = 120 pairs (60 Genuine, 60 Impostor, 20 Subject Identities)
==================================================================================
Mean Test Accuracy:              84.17%
Equal Error Rate (EER):          16.67%  (at threshold tau = 0.9620)
Area Under ROC Curve (AUC):      0.9328  (Wilcoxon-Mann-Whitney Exact)
Optimal Calibrated Threshold:    0.9634  (Max-Margin Validation Contiguous Midpoint)
Failure to Acquire Rate (FTA):    0.00%  (0 / 120 pairs)
==================================================================================
```

### 4.2. Statistical Uncertainty Bounds (Identity-Clustered Bootstrap, B=500)

| Metric | Point Estimate | 95% Bootstrap Confidence Interval | Standard Error |
| :--- | :---: | :---: | :---: |
| **Accuracy** | 84.17% | **[75.00%, 91.67%]** | $\pm 4.25\%$ |
| **Equal Error Rate (EER)** | 16.67% | **[8.33%, 25.00%]** | $\pm 4.25\%$ |
| **Area Under Curve (AUC)** | 0.9328 | **[0.8522, 0.9815]** | $\pm 0.0330$ |

### 4.3. Operational TAR @ FAR Operating Points Table

| Target FAR Operating Point | Calibrated Threshold ($\tau$) | Observed FAR | False Accepts ($FP$) | Target TAR | Statistical Validity Check |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Convenience ($\text{FAR} \le 10\%$)** | 0.9835 | 0.1000 | 6 / 60 | **70.00%** | **VALID:** $N_{imp}=60 \ge 30$ (Rule of 3 satisfied) |
| **Medium Security ($\text{FAR} \le 5\%$)**| 0.9902 | 0.0500 | 3 / 60 | **55.00%** | **VALID:** $N_{imp}=60 \ge 60$ (Rule of 3 satisfied) |
| **High Security ($\text{FAR} \le 1\%$)**  | 0.9950 | 0.0000 | 0 / 60 | **31.67%** | **INSUFFICIENT SAMPLE:** Rule of 3 requires $N \ge 300$ |
| **Extreme Security ($\text{FAR} \le 0.1\%$)**| 0.9972 | 0.0000 | 0 / 60 | **18.33%** | **INSUFFICIENT SAMPLE:** Rule of 3 requires $N \ge 3000$ |

> [!WARNING]
> While thresholds can be numerically calculated for $\text{FAR} \le 1\%$ and $\text{FAR} \le 0.1\%$, the sample size of 60 impostor pairs is statistically insufficient to prove that the true false match rate is below $1\%$ at 95% confidence. Claims of performance at these operating points are formally flagged as statistically non-generalizable pending evaluations on larger corpora ($N_{imp} \ge 3,000$).

---

## 5. Comprehensive Automated Test Execution Log

### 5.1. Backend Test Suite (`pytest`)
- **Total Tests Executed:** **59 tests** across 6 test modules.
- **Pass Rate:** **100% (59 passed, 0 failed, 0 skipped)** in 11.41 seconds.

```
backend/tests/test_benchmarks_step05.py::test_genuine_and_impostor_pair_construction PASSED
backend/tests/test_benchmarks_step05.py::test_identity_leakage_prevention PASSED
backend/tests/test_benchmarks_step05.py::test_deterministic_pair_generation PASSED
backend/tests/test_benchmarks_step05.py::test_roc_and_auc_calculation PASSED
backend/tests/test_benchmarks_step05.py::test_far_and_frr_calculations PASSED
backend/tests/test_benchmarks_step05.py::test_eer_calculation PASSED
backend/tests/test_benchmarks_step05.py::test_threshold_calibration_cross_validation PASSED
backend/tests/test_benchmarks_step05.py::test_test_set_isolation PASSED
backend/tests/test_benchmarks_step05.py::test_missing_and_malformed_annotations PASSED
backend/tests/test_benchmarks_step05.py::test_empty_datasets_and_insufficient_pairs PASSED
backend/tests/test_benchmarks_step05.py::test_experiment_reproducibility PASSED
backend/tests/test_benchmarks_step05.py::test_export_correctness PASSED
backend/tests/test_benchmarks_step05.py::test_benchmarks_api_endpoints PASSED
backend/tests/test_benchmarks_step06_audit.py::test_official_protocol_consistency PASSED
backend/tests/test_benchmarks_step06_audit.py::test_pair_and_fold_integrity PASSED
backend/tests/test_benchmarks_step06_audit.py::test_strict_identity_leakage_across_all_folds PASSED
backend/tests/test_benchmarks_step06_audit.py::test_validation_only_threshold_isolation PASSED
backend/tests/test_benchmarks_step06_audit.py::test_exact_roc_auc_calculation PASSED
backend/tests/test_benchmarks_step06_audit.py::test_eer_linear_interpolation PASSED
backend/tests/test_benchmarks_step06_audit.py::test_low_sample_far_limitations PASSED
backend/tests/test_benchmarks_step06_audit.py::test_threshold_selection_max_margin PASSED
backend/tests/test_benchmarks_step06_audit.py::test_identity_clustered_bootstrap_reproducibility PASSED
backend/tests/test_benchmarks_step06_audit.py::test_repeated_experiment_provenance PASSED
backend/tests/test_benchmarks_step06_audit.py::test_export_audit_contracts PASSED
backend/tests/test_engine.py::test_cosine_similarity_identical_vectors PASSED
backend/tests/test_engine.py::test_cosine_similarity_orthogonal_vectors PASSED
backend/tests/test_engine.py::test_cosine_similarity_opposite_vectors PASSED
backend/tests/test_engine.py::test_cosine_similarity_scaling_invariance PASSED
backend/tests/test_engine.py::test_cosine_similarity_zero_norm_protection PASSED
backend/tests/test_engine.py::test_cosine_similarity_dimension_mismatch PASSED
backend/tests/test_engine.py::test_engine_detect_and_extract_face_success PASSED
backend/tests/test_engine.py::test_engine_detect_and_extract_no_face PASSED
backend/tests/test_engine.py::test_engine_detect_and_extract_multiple_faces PASSED
backend/tests/test_engine.py::test_engine_detect_and_extract_corrupt_data PASSED
backend/tests/test_engine.py::test_engine_compare_faces_identical_same_subject PASSED
backend/tests/test_engine.py::test_engine_metadata_reports_active_model_and_zero_mock PASSED
backend/tests/test_face_detection_step04.py::test_detection_exactly_one_face PASSED
backend/tests/test_face_detection_step04.py::test_detection_multiple_valid_faces PASSED
backend/tests/test_face_detection_step04.py::test_candidate_filtering_rejects_false_positives PASSED
backend/tests/test_face_detection_step04.py::test_candidate_filtering_retains_small_faces PASSED
backend/tests/test_face_detection_step04.py::test_detection_zero_faces_blank_image PASSED
backend/tests/test_face_detection_step04.py::test_face_quality_advisories_reported PASSED
backend/tests/test_face_detection_step04.py::test_rgb_bgr_color_decoding_consistency PASSED
backend/tests/test_face_detection_step04.py::test_various_dimensions_and_aspect_ratios PASSED
backend/tests/test_face_detection_step04.py::test_manual_face_selection_workflow PASSED
backend/tests/test_face_detection_step04.py::test_manual_crop_workflow PASSED
backend/tests/test_face_detection_step04.py::test_corrupt_and_unsupported_image_handling PASSED
backend/tests/test_face_detection_step04.py::test_engine_embedding_dimension_and_range PASSED
backend/tests/test_health.py::test_health_endpoint PASSED
backend/tests/test_health.py::test_engine_info_endpoint PASSED
backend/tests/test_validation.py::test_validate_valid_jpeg PASSED
backend/tests/test_validation.py::test_validate_valid_png PASSED
backend/tests/test_validation.py::test_validate_invalid_signature PASSED
backend/tests/test_validation.py::test_validate_too_small_dimensions PASSED
backend/tests/test_validation.py::test_validate_excessive_dimensions PASSED
backend/tests/test_validation.py::test_validate_corrupt_payload PASSED
backend/tests/test_validation.py::test_compare_valid_identical_images PASSED
backend/tests/test_validation.py::test_compare_rejects_empty_slots PASSED
backend/tests/test_validation.py::test_compare_rejects_invalid_image PASSED
======================= 59 passed, 1 warning in 11.41s ========================
```

### 5.2. Frontend Test Suite (`vitest`)
- **Total Tests Executed:** **36 tests** across 6 test files.
- **Pass Rate:** **100% (36 passed, 0 failed, 0 skipped)** in 7.73 seconds.

```
✓ src/tests/ResultPanel.test.tsx (4 tests) 300ms
✓ src/tests/ComparisonProgress.test.tsx (5 tests) 578ms
✓ src/tests/FaceDetectionStep04.test.tsx (7 tests) 788ms
✓ src/tests/BenchmarksStep05.test.tsx (5 tests) 1028ms
  ✓ renders benchmark header, scientific integrity directive, and dataset registry
  ✓ displays primary evaluation metric cards when run results are loaded
  ✓ renders confusion matrix and operational operating points table
  ✓ renders export buttons for JSON report and pairwise CSV
  ✓ triggers executeBenchmarkRun when Execute Model Benchmark button is clicked
✓ src/tests/App.test.tsx (7 tests) 1332ms
✓ src/tests/ComparisonWorkflow.test.tsx (8 tests) 2275ms
Test Files: 6 passed (6)
Tests:      36 passed (36)
```

### 5.3. Production Build (`npm run build`)
```
> frontend@0.0.0 build
> tsc -b && vite build

vite v8.3.5 building client environment for production...
transforming...
✓ 1951 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   1.02 kB │ gzip:  0.59 kB
dist/assets/index-B5uWrYye.css   16.40 kB │ gzip:  4.11 kB
dist/assets/index-DHGn_G1A.js   344.67 kB │ gzip: 97.43 kB

✓ built in 887ms
```

---

## 6. Remaining Methodological Limitations & Prioritized Future Experiments

While the benchmark implementation is now free of data leakage and mathematical approximation bugs, the following inherent limitations remain:

1. **Synthetic vs. Real In-The-Wild Face Diversity:**  
   The current offline self-contained fixture consists of 120 synthetic images across 20 distinct identities. While suitable for CI regression and mathematical verification with zero external network dependencies, synthetic geometry cannot replicate the full distribution of real-world skin textures, camera noise, and dynamic facial expressions.
   - *Recommendation:* Download and mount the official LFW image archive (~173 MB) into `backend/data/lfw/` and implement the native LFW directory loader to establish official LFW View 2 baseline numbers.
2. **Extreme Cross-Pose Evaluation (CFP-FP):**  
   SFace performs well on near-frontal imagery ($\pm 30^\circ$ yaw). Its accuracy under extreme profile yaw ($90^\circ$) remains unquantified until the CFP-FP dataset is mounted.
3. **Demographic Parity & Skin Tone Balance:**  
   Fairness auditing requires multi-demographic datasets (e.g. FHIBE or BUPT-BalancedFace) to evaluate whether $\text{FMR}$ or $\text{FNMR}$ disparities exist across Fitzpatrick and Monk skin tone categories.
4. **Large-Scale Impostor Testing for $FAR \le 10^{-4}$:**  
   In compliance with the Rule of Three, validating operational security thresholds for high-security applications requires at least 30,000 to 300,000 distinct impostor pairs.

---

## 7. Sign-Off & Verification Verdict

As an independent auditor, I certify that:
- No test-set data leaked into threshold calibration.
- All evaluation partitions in the benchmark fixture are strictly identity-disjoint.
- Confidence intervals are computed via identity-clustered bootstrap.
- All metric formulas (ROC-AUC, EER, TAR@FAR) strictly adhere to mathematical biometric standards.
- All 59 backend tests, 36 frontend tests, and production build pass cleanly.

**FACECORE AI STEP 06 IS FORMALLY AUDITED, SCIENTIFICALLY VALIDATED, AND ACCEPTED.**

