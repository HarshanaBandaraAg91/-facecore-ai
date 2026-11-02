# FACECORE AI &mdash; STEP 06: INDEPENDENT BENCHMARK AUDIT REPORT

**Role:** Independent Machine-Learning Evaluation Auditor & Statistical Researcher  
**Phase:** STEP 06 &mdash; Independent Benchmark Audit and Scientific Validation  
**Date:** November 2026  
**Audit Scope:** Complete audit of backend/app/benchmarks, dataset manifests, fold construction, metrics calculations, threshold calibration, runner pipeline, and frontend telemetry.  
**Auditor Verdict:** **AUDIT COMPLETED & VERIFIED.** Critical methodological defects, data leakages, and ungrounded metric claims identified, mathematically corrected, and locked with 59 passing backend tests, 36 frontend tests, and clean production build.

---

## 1. Executive Summary

As an independent machine-learning evaluation auditor, I conducted a rigorous, adversarial source-code audit and statistical validation of the facial benchmarking framework implemented in STEP 05.

The core objective was to establish whether the reported experimental methodology and results are statistically and scientifically reliable. **No code, docstring, or prior report (including [STEP05_REPORT.md](file:///c:/Projects/project%207%20-%20face%20checking%20tool/STEP05_REPORT.md)) was accepted on trust without independent verification.**

### Critical Audit Findings Overview:
1. **100% Cross-Fold Identity Leakage in Synthetic Fixture (Confirmed Defect):**  
   In `manifest.py`, impostor pairs were formed by pairing an identity in the target fold with identities from other folds (`other_ids`). Consequently, **all 10 evaluation folds leaked 8 identities between training/validation and testing**. The Step 05 test suite missed this because it tested a dummy three-name list (`Alice`, `Bob`, `Charlie`) and never asserted anti-leakage on its own fixture.
2. **Phantom Evaluation & Silent Dataset Substitution (Confirmed Defect):**  
   `runner.py`'s `_load_dataset_pairs_and_images` completely ignored `config.dataset_id`. If a researcher selected `lfw-canonical-v1`, the engine substituted synthetic fixture images, labeled the output "Labeled Faces in the Wild (LFW)", and marked LFW as `COMPLETED`. No LFW image files were present locally.
3. **Silent Omission of Face Detection Failures (Confirmed Defect):**  
   Pairs where YuNet failed to detect a face were silently dropped in `_compute_pair_similarity` (`except: return None`). Out of 120 pairs in Step 05, 11 pairs were dropped (a 9.17% Failure to Acquire rate) without reporting FTA or FTE, biasing verification accuracy claims.
4. **EER Linear Interpolation Was Never Implemented (Methodological Discrepancy):**  
   While `STEP05_REPORT.md` claimed "fine-grid threshold scanning ($\Delta \tau = 0.001$) and linear interpolation between adjacent crossover intervals", `compute_eer` actually performed a discrete grid argmin of `abs(far - frr)` and took `(far + frr)/2.0` at that single point without interpolation.
5. **Statistical Violations at Low FAR Operating Points (Statistical Flaw):**  
   `compute_tar_at_far` reported operating points at $FAR = 0.1\%$ ($10^{-3}$) and $FAR = 1.0\%$ ($10^{-2}$) on samples with only 50&ndash;60 impostor pairs, directly violating the **Rule of Three** ($N_{imp} \ge 3 / \alpha \implies 3,000$ impostors for $FAR=0.1\%$).
6. **Cross-Validation Confusion Matrix Disconnect (Confirmed Defect):**  
   `runner.py` calculated fold test accuracies using fold-specific thresholds $\tau_k$, but constructed the final confusion matrix by re-thresholding the pooled scores with `mean_tau`. As a result, `confusion_mat.accuracy` did not match `accuracy` (the cross-validation mean test accuracy).
7. **Pair-Level vs. Identity-Clustered Bootstrap (Statistical Flaw):**  
   Resampling pairs with replacement assumed observations were i.i.d., ignoring subject-level correlations when identities appear in multiple pairs.
8. **OpenCV Engine Re-Instantiation Handle Crash on Windows (Runtime Bug):**  
   Instantiating `RealFacialEmbeddingEngine()` on every benchmark execution triggered Windows fatal exception `0xc0000008` (`STATUS_INVALID_HANDLE`) during OpenCV C++ model deallocation.

All confirmed defects have been remediated, verified mathematically, and anchored with 11 new regression and audit tests in [backend/tests/test_benchmarks_step06_audit.py](file:///c:/Projects/project%207%20-%20face%20checking%20tool/backend/tests/test_benchmarks_step06_audit.py).

---

## 2. Task 1: Complete Source Code Audit & Data Flow Trace

I traced the end-to-end data pipeline from raw annotations to reported metrics:

```
[ Dataset Manifest / Fixture Generator ]
                 |
                 v
   [ Pair Subsampling: max_pairs ]  <-- AUDIT FLAW: Previously broke 10-fold balance;
                 |                                  Now stratified across folds.
                 v
[ In-Memory Byte Decoding & YuNet Face Detection ]
                 |
                 v  <-- AUDIT FLAW: Detection failures were silently dropped;
                 |                  Now tracked as Failure to Acquire (FTA/FTE).
[ SFace 128-d Hyperspherical Embedding Extraction ]
                 |
                 v
[ Cosine Similarity Computation Sim(u, v) ]
                 |
                 v
[ 10-Fold Stratified Cross-Validation ]
  - Fold k Validation Set (9 folds): Calibrate tau_k (Max-Margin Contiguous Midpoint)
  - Fold k Test Set (1 fold): Out-of-Fold Predictions y_hat_k = Sim >= tau_k
                 |
                 v
[ Statistical Metric Engine ]
  - Exact Wilcoxon-Mann-Whitney ROC-AUC
  - EER with True Linear Crossover Interpolation
  - TAR@FAR with Rule-of-Three Sample Size Validation
  - Out-of-Fold Cross-Validation Confusion Matrix
  - Identity-Clustered Non-Parametric Bootstrap CIs (B=500)
                 |
                 v
[ REST API & Cryptographic Provenance Serialization ]
  - Manifest SHA-256 Hash
  - Model Weights SHA-256 Fingerprint
  - System Environment Telemetry (Python, OpenCV, NumPy, OS)
```

---

## 3. Task 2: LFW Protocol Verification & Scientific Protocol Audit

### 3.1. Official LFW Protocol Analysis (Huang et al., 2007)
The official LFW evaluation protocol defines two experimental views:
- **View 1 (Development View):** Intended strictly for algorithm exploration, training, and parameter tuning. Contains two subsets (training and testing).
- **View 2 (10-Fold Cross-Validation View):** The official benchmark protocol. Contains 6,000 fixed pairs partitioned into 10 mutually disjoint subsets of 600 pairs each (300 genuine and 300 impostor pairs per fold).

### 3.2. Standard LFW Evaluation Paradigms
The literature defines four distinct training paradigms on View 2:
1. **Image-Restricted, No Outside Data:** Only equivalence labels (same/different) on the 9 training folds are permitted.
2. **Unrestricted, No Outside Data:** Identity names within the 9 training folds can be leveraged to form additional intra-subject pairs.
3. **Image-Restricted, With Outside Data:** Commercial or public pre-training sets permitted, but tuning on LFW restricted to pair equivalence.
4. **Unrestricted, With Outside Data:** The standard regime for modern deep neural networks (SFace, ArcFace, SphereFace), where models are pre-trained on external datasets and evaluated on LFW View 2 without fine-tuning weights.

### 3.3. Methodological Discrepancy: Official LFW vs. Identity-Disjoint Protocols
In [STEP05_REPORT.md](file:///c:/Projects/project%207%20-%20face%20checking%20tool/STEP05_REPORT.md) Section 2, the following claim was made:
> *"Identity-Disjoint Guarantee: Each fold contains mutually exclusive identities, strictly isolating training, validation, and test sets."*

**Auditor Finding: THIS CLAIM WAS FALSE REGARDING OFFICIAL LFW.**  
In official LFW View 2 (`pairs.txt`), while the *image pairs* are mutually disjoint across the 10 folds, **the subjects are not mutually exclusive across folds**. Celebrities with numerous images (e.g., George W. Bush with 530 images, Colin Powell with 236 images) appear in genuine and impostor pairs across multiple folds.

This methodological characteristic of LFW motivated subsequent benchmarks (such as CPLFW and CALFW) to create strictly subject-disjoint partitions. **Describing official LFW View 2 as "identity-disjoint" is scientifically inaccurate.**

### 3.4. Elimination of Phantom LFW Evaluation
In STEP 05, selecting LFW in the UI executed synthetic fixture images while generating results stamped "Labeled Faces in the Wild (LFW)".

**Resolution:**  
In [backend/app/benchmarks/manifest.py](file:///c:/Projects/project%207%20-%20face%20checking%20tool/backend/app/benchmarks/manifest.py), `lfw-canonical-v1` is now marked `is_available = False` with `local_path = None`. When invoked without mounted image archives, `BenchmarkRunner` raises a clear, descriptive `ValueError`:
```
Dataset 'lfw-canonical-v1' images are not locally mounted at 'None'.
Please select 'facecore-synthetic-fixture-v1' for verified offline evaluation
or mount authorized dataset images at the specified local_path.
```
Phantom evaluations and dataset substitutions are strictly prohibited.

---

## 4. Task 3: Data Leakage Audit & Graph Verification

### 4.1. The 100% Identity Leakage Defect in Synthetic Fixture
In `manifest.py`, lines 318&ndash;324 originally read:
```python
# DEFECTIVE STEP 05 CODE:
other_ids = [ident for ident in identities_list if ident not in fold_ids]
for g in range(len(fold_ids) * 3):
    sub_a = fold_ids[g % len(fold_ids)]
    sub_b = other_ids[(fold * 3 + g) % len(other_ids)]  # <-- LEAKAGE: sub_b belongs to another fold!
```
Because `sub_b` was chosen from `other_ids` (identities allocated to other folds), when fold $k$ was designated as the test fold:
- `IdentitySet(Test Fold k)` contained `sub_a` and `sub_b`.
- `IdentitySet(Train Folds)` (all folds $j \neq k$) also contained `sub_b` (since `sub_b` was an assigned identity of fold $j$).
- Result: **10 out of 10 folds violated identity disjointness**, leaking 8 subject identities per fold.

### 4.2. Mathematical Correction & Anti-Leakage Verification
To achieve a mathematically provable identity-disjoint 10-fold benchmark:
- Given 20 identities $\{I_0, I_1, \dots, I_{19}\}$, fold $k \in \{0, \dots, 9\}$ is assigned exactly two identities:
  $$\text{FoldIdentities}(k) = \{I_{2k}, I_{2k+1}\}$$
- **Genuine Pairs:** Formed exclusively between distinct photos of $I_{2k}$ and distinct photos of $I_{2k+1}$.
- **Impostor Pairs:** Formed strictly cross-pairing $I_{2k}$ against $I_{2k+1}$.
- **Mathematical Guarantee:**
  $$\text{Identities}(\text{Fold}_k) \cap \text{Identities}(\text{Fold}_j) = \emptyset \quad \forall k \neq j$$
  $$\text{Identities}(\text{Test Fold}_k) \cap \bigcup_{j \neq k} \text{Identities}(\text{Train Fold}_j) = \emptyset$$

The new function `validate_manifest_splits(pairs)` and regression test `test_strict_identity_leakage_across_all_folds` audit all 10 folds, confirming **0 leaking identities (100% clean isolation)**.

---

## 5. Task 4: Statistical Metrics Audit

Full derivations and numerical proofs are detailed in **[STEP06_METRIC_VERIFICATION.md](file:///c:/Projects/project%207%20-%20face%20checking%20tool/STEP06_METRIC_VERIFICATION.md)**.

### Summary of Corrected Calculations:
1. **Exact ROC-AUC:** Replaced discrete trapezoidal upper-envelope approximation with the analytical Wilcoxon-Mann-Whitney U statistic:
   $$\text{AUC} = \frac{\sum_{i \in \mathcal{G}} \sum_{j \in \mathcal{I}} \left( \mathbb{I}(s_i > s_j) + 0.5 \cdot \mathbb{I}(s_i = s_j) \right)}{|\mathcal{G}| \cdot |\mathcal{I}|}$$
   Eliminates discretization artifacts and properly weights score ties at 0.5.
2. **EER with Linear Crossover Interpolation:** Replaced nearest-neighbor discrete argmin with exact adjacent linear interpolation:
   $$\alpha = \frac{\text{FAR}_1 - \text{FRR}_1}{(\text{FRR}_2 - \text{FRR}_1) - (\text{FAR}_2 - \text{FAR}_1)}, \quad \text{EER}^* = \text{FAR}_1 + \alpha (\text{FAR}_2 - \text{FAR}_1)$$
3. **Rule of Three Enforcement at Low FAR:** Implemented Wayman (1999) sample size validation ($N_{imp} \ge 3 / \alpha$) and Doddington (1998) significance checks. Any operating point evaluated on insufficient sample sizes surfaces `rule_of_three_valid: false` and a human-readable uncertainty advisory.
4. **Identity-Clustered Bootstrap:** Implemented clustered resampling by subject identity to account for intra-subject score dependencies, preventing artificially narrow confidence intervals.
5. **Out-of-Fold Confusion Matrix Alignment:** Confusion matrix now aggregates true out-of-fold test predictions across the $K$ cross-validation iterations, guaranteeing that:
   $$\text{ConfusionMatrix.accuracy} \equiv \text{Mean Cross-Validation Test Accuracy}$$

---

## 6. Task 5: Threshold Calibration Audit

### 6.1. Validation-Only Protocol Verification
Audited `calibrate_threshold_cross_validation`:
- For each fold $k \in \{0, \dots, K-1\}$:
  - Validation set = all samples where $\text{fold} \neq k$.
  - Threshold $\tau_k$ calibrated solely on validation set via `_find_optimal_threshold`.
  - Fold $k$ test set scored using $\tau_k$.
- Tested with adversarial test fold containing inverted score labels; confirmed test accuracy drops to 0.0% while validation threshold remains isolated.

### 6.2. Max-Margin Midpoint Search Improvement
In Step 05, taking `(best_thresholds[0] + best_thresholds[-1]) / 2.0` across 400 linear steps risked landing in an accuracy dip if optimal thresholds were multimodal.

**Improvement:**
`_find_optimal_threshold` now evaluates candidate thresholds placed at the midpoints of sorted unique validation scores, detects contiguous optimal intervals, selects the midpoint of the largest contiguous optimal segment, and verifies that the midpoint achieves the optimal validation accuracy.

---

## 7. Task 6: Reproducibility & Cryptographic Provenance

Repeated executions under identical seeds ($seed=42$) confirm bit-for-bit repeatability across all scalar metrics. Full provenance telemetry is now bound to every `BenchmarkResult`:
- `dataset_manifest_hash`: SHA-256 fingerprint of all pair annotations (`5aeb6c8e0087a8c5`).
- `model_weights_hash`: Combined SHA-256 fingerprints of SFace (`0ba9fbfa01b5270c`) and YuNet (`8f2383e4dd3cfbb4`).
- `system_environment`: Python 3.13.7, OpenCV 4.12.0, NumPy 2.x, Windows 11.
- `failure_to_acquire_count`: 0 (0.0% FTA on verified fixture).

Full experimental logs are detailed in **[STEP06_REPRODUCIBILITY_REPORT.md](file:///c:/Projects/project%207%20-%20face%20checking%20tool/STEP06_REPRODUCIBILITY_REPORT.md)**.

---

## 8. Task 7: Controlled Model Baseline

The production model stack is strictly preserved:
- **Embedding Model:** SFace (SphereFace2 backbone, 128-dimensional unit normalized hyperspherical embeddings, Apache-2.0 license).
- **Face Detector:** YuNet (5-point landmark detector, 14-dimensional detection vector, Apache-2.0 license).
- **Face Alignment:** Canonical $112 \times 112$ similarity transform via `recognizer.alignCrop`.
- **Live Comparison API:** Operational endpoints (`/api/compare`, `/api/validate-image`, `/api/health`, `/api/engine-info`) remain fully functional and uncompromised.
- **Engine Architecture:** Refactored `BenchmarkRunner` to use a shared singleton engine, eliminating the Windows `0xc0000008` invalid handle crash.

---

## 9. Comprehensive Defect Matrix

| Defect ID | Severity | Component | Description | Remediation | Verification Test |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **DEF-01** | **CRITICAL** | `manifest.py` | 100% of synthetic fixture folds leaked 8 identities between train and test. | Implemented strict intra-fold impostor pairing with mutually exclusive fold identities. | `test_strict_identity_leakage_across_all_folds` |
| **DEF-02** | **HIGH** | `runner.py` | Phantom evaluation: Selecting LFW ran synthetic images and claimed LFW completed. | Enforced real file presence check; unmounted datasets raise explicit `ValueError`. | `test_official_protocol_consistency` |
| **DEF-03** | **HIGH** | `runner.py` | Detection failures silently dropped (9.17% FTA omitted in Step 05). | Canonical face proportions ensure 0% FTA; added ISO/IEC 19795-1 FTA tracking. | `test_repeated_experiment_provenance` |
| **DEF-04** | **MEDIUM** | `metrics.py` | EER calculation used nearest discrete grid point without linear interpolation. | Implemented analytical linear interpolation between crossover intervals. | `test_eer_linear_interpolation` |
| **DEF-05** | **HIGH** | `metrics.py` | TAR@FAR reported at $FAR \le 0.1\%$ on $N=60$ impostors (violating Rule of Three). | Populated `TARAtFAR` with Rule of Three validity flag and sample size advisory. | `test_low_sample_far_limitations` |
| **DEF-06** | **MEDIUM** | `metrics.py` | Confusion matrix accuracy did not match CV test accuracy due to global pooled thresholding. | Confusion matrix now aggregates out-of-fold test predictions across CV folds. | `test_repeated_experiment_provenance` |
| **DEF-07** | **MEDIUM** | `metrics.py` | Naive pair-level bootstrap underestimated variance on correlated identities. | Implemented identity-clustered non-parametric bootstrap resampling. | `test_identity_clustered_bootstrap_reproducibility` |
| **DEF-08** | **MEDIUM** | `metrics.py` | Midpoint threshold selection vulnerable to accuracy dips on multi-modal boundaries. | Evaluates sorted candidate midpoints and verifies largest contiguous segment. | `test_threshold_selection_max_margin` |
| **DEF-09** | **LOW** | `metrics.py` | Trapezoidal ROC-AUC upper-envelope heuristic differed from exact analytical AUC. | Implemented exact Wilcoxon-Mann-Whitney U statistic with tie handling. | `test_exact_roc_auc_calculation` |
| **DEF-10** | **HIGH** | `runner.py` | Repeated engine re-instantiation caused Windows `0xc0000008` STATUS_INVALID_HANDLE crash. | Refactored to reuse shared engine singleton across benchmark executions. | All 59 backend tests pass cleanly. |
| **DEF-11** | **LOW** | `schemas.py` | Missing cryptographic hashes (manifest and model weights) in `BenchmarkResult`. | Added manifest SHA-256, model weights SHA-256, and runtime environment fields. | `test_export_audit_contracts` |
| **DEF-12** | **MEDIUM** | `runner.py` | Subsampling with `max_pairs` globally broke 10-fold cross-validation balance. | Implemented stratified fold-aware subsampling preserving genuine/impostor ratio. | `test_experiment_reproducibility` |

---

## 10. Audit Conclusion

The FACECORE AI benchmarking framework has been subjected to a complete, independent evaluation audit. All identified data leakages, protocol misrepresentations, and metric approximation errors have been resolved. The framework now provides a scientifically rigorous, mathematically verified, and reproducible foundation for biometric evaluation.

