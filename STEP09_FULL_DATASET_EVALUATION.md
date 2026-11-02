# FACECORE AI — STEP 09: Full-Scale Empirical Dataset Evaluation Report

**Document Version:** 1.0.0  
**Status:** Independent Scientific Verification Document  
**Date:** November 2026  
**Auditor:** Senior Computer Vision Researcher, Biometric Evaluation Auditor & Machine-Learning Scientist  
**Production Pipeline Under Audit:** OpenCV YuNet Detector (2023mar) $\rightarrow$ 5-Point Affine Alignment to $112 \times 112$ $\rightarrow$ OpenCV SFace (SphereFace2 2021dec) 128-d Unit Embeddings $\rightarrow$ Cosine Similarity  

---

## 1. Executive Summary & Objective

In **STEP 09**, FACECORE AI transitioned from preliminary demonstration subsets (60–200 pairs) to a **full-scale empirical evaluation** utilizing all locally installed, legally accessible, authentic photographic pairs.

Previous phases demonstrated the functionality of the 10-fold cross-validation framework, but their reported metrics were limited to small sample slices. This evaluation establishes the full-corpus baseline on authentic photographs, auditing data provenance, image resolution, and Failure-to-Acquire (FTA) tracking across:
1. **LFW (Labeled Faces in the Wild):** The complete official 6,000-pair 10-fold View 2 protocol.
2. **CALFW (Cross-Age LFW):** All 2,424 pairs resolvable from verified local disk imagery.
3. **CPLFW (Cross-Pose LFW):** All 2,494 pairs resolvable from verified local disk imagery.
4. **CFP-FP & AgeDB-30:** Cataloged and verified as `NOT_INSTALLED` and `RESTRICTED_ACCESS` respectively.

---

## 2. Dataset Completeness & Accounting Matrix

| Metric / Dimension | LFW Canonical (`lfw-canonical-v1`) | Cross-Age LFW (`calfw-v1`) | Cross-Pose LFW (`cplfw-v1`) | CFP-FP (`cfp-fp-v1`) | AgeDB-30 (`agedb-30-v1`) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Official Protocol Pairs** | 6,000 pairs | 6,000 pairs | 6,000 pairs | 7,000 pairs | 6,000 pairs |
| **Official Protocol Folds** | 10 folds (300 gen / 300 imp) | 10 folds (300 gen / 300 imp) | 10 folds (300 gen / 300 imp) | 10 folds (350 gen / 350 imp) | 10 folds (300 gen / 300 imp) |
| **Total Images in Corpus** | 13,233 images (5,749 identities) | 12,174 images (4,025 identities) | 11,652 images (3,998 identities) | 7,000 images (500 identities) | 16,488 images (568 identities) |
| **Locally Installed Images** | 13,233 images (100.0%) | 13,233 (shared LFW store) | 13,233 (shared LFW store) | 0 images (Not mounted) | 0 images (Restricted iBUG) |
| **Locally Resolved Pairs** | **6,000 pairs (100.0%)** | **2,424 pairs (40.40%)** | **2,494 pairs (41.57%)** | 0 pairs (0.0%) | 0 pairs (0.0%) |
| **Unresolved Missing Pairs** | 0 pairs (0.0%) | 3,576 pairs (59.60%) | 3,506 pairs (58.43%) | 7,000 pairs (100.0%) | 6,000 pairs (100.0%) |
| **Unique Missing Image Files** | 0 images | 2,640 supplementary images | 2,444 supplementary images | Unmounted archive | Restricted agreement |
| **Attempted Pairs** | 6,000 pairs | 2,424 pairs | 2,494 pairs | 0 pairs | 0 pairs |
| **Successful Acquired Pairs** | 6,000 pairs | 2,424 pairs | 2,494 pairs | 0 pairs | 0 pairs |
| **Failure-to-Acquire (FTA)** | **0 (0.00%)** | **0 (0.00%)** | **0 (0.00%)** | N/A | N/A |
| **Completeness Classification** | **COMPLETE_OFFICIAL_CORPUS** | **VERIFIED_LOCAL_SUBSET** | **VERIFIED_LOCAL_SUBSET** | **NOT_INSTALLED** | **RESTRICTED_ACCESS** |

---

## 3. Full-Scale Empirical Results

All evaluations were executed on authentic source photographs using `face_selection_policy="center_face"` under 10-fold cross-validation. Thresholds were calibrated strictly on validation folds and evaluated on test folds.

### 3.1 Primary Metric Comparison

| Benchmark Dataset | Evaluated Pairs | Optimal $\tau^*$ | Cross-Val Accuracy | ROC-AUC | Equal Error Rate (EER) | TAR @ FAR=1.0% | TAR @ FAR=0.1% | Evaluation Duration |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **LFW (Full Official)** | **6,000** | $0.3132$ | **$99.35\% \pm 0.22\%$** | **$0.9988$** | **$0.80\%$** | **$99.27\%$** | **$98.80\%$** | $349.1\text{ s}$ |
| **CALFW (Local Subset)** | **2,424** | $0.3872$ | **$99.14\% \pm 0.20\%$** | **$0.9981$** | **$1.05\%$** | **$98.95\%$** | Insufficient $N$ | $72.2\text{ s}$ |
| **CPLFW (Local Subset)** | **2,494** | $0.4084$ | **$98.81\% \pm 0.58\%$** | **$0.9985$** | **$1.29\%$** | **$98.20\%$** | Insufficient $N$ | $64.7\text{ s}$ |

### 3.2 Full Confusion Matrices (Out-of-Fold Predictions)

- **LFW Canonical ($N=6,000$):**
  - $\text{True Positives (TP)} = 2,973$
  - $\text{True Negatives (TN)} = 2,988$
  - $\text{False Positives (FP)} = 12$
  - $\text{False Negatives (FN)} = 27$
  - $\text{False Acceptance Rate (FAR)} = 12 / 3,000 = \mathbf{0.40\%}$
  - $\text{False Rejection Rate (FRR)} = 27 / 3,000 = \mathbf{0.90\%}$
  - Overall Test Accuracy: **$99.35\%$**

- **CALFW Cross-Age ($N=2,424$):**
  - $\text{True Positives (TP)} = 848$
  - $\text{True Negatives (TN)} = 1,555$
  - $\text{False Positives (FP)} = 9$
  - $\text{False Negatives (FN)} = 12$
  - $\text{FAR} = 9 / 1,564 = \mathbf{0.58\%}$
  - $\text{FRR} = 12 / 860 = \mathbf{1.40\%}$
  - Overall Test Accuracy: **$99.14\%$**

- **CPLFW Cross-Pose ($N=2,494$):**
  - $\text{True Positives (TP)} = 927$
  - $\text{True Negatives (TN)} = 1,537$
  - $\text{False Positives (FP)} = 13$
  - $\text{False Negatives (FN)} = 17$
  - $\text{FAR} = 13 / 1,550 = \mathbf{0.84\%}$
  - $\text{FRR} = 17 / 944 = \mathbf{1.80\%}$
  - Overall Test Accuracy: **$98.81\%$**

---

## 4. Analysis of Unresolved Sample Pairs

### 4.1 Provenance of Supplementary Images in CALFW & CPLFW
The official protocols for CALFW (Zheng et al., 2017) and CPLFW (Zheng & Deng, 2018) were designed to modify LFW by:
1. Re-pairing existing LFW images to maximize age gaps and pose angles.
2. Collecting additional supplementary images from Google Images for subjects with only 1 or 2 photos in LFW.

Because the local research environment currently mounts the official baseline LFW archive (`lfw.tgz`, 13,233 images), all pairs requiring supplementary web-crawled photos could not be resolved from local disk.

### 4.2 Handling of Missing Pairs per Scientific Directive
1. **Zero Synthetic Substitution:** The benchmark runner **strictly refused** to generate procedural faces, interpolate missing embeddings, or duplicate existing images.
2. **Deterministic Accounting:** All 3,576 unresolvable CALFW pairs and 3,506 unresolvable CPLFW pairs were recorded in the audit logs with full image filenames and fold locations.
3. **Preservation of Fold Balance:** In both CALFW and CPLFW, every fold $1..10$ retained over 220 genuine and impostor pairs on disk, allowing standard 10-fold cross-validation to proceed without structural partition collapse.
4. **Honest Labeling:** The run metadata explicitly categorizes LFW as `COMPLETE_OFFICIAL_CORPUS` and CALFW/CPLFW as `VERIFIED_LOCAL_SUBSET`.

---

## 5. Audit Classification

- **LFW 6,000 Official Protocol:** **VERIFIED** (100% evaluated on authentic source photographs).
- **CALFW 2,424 Local Subset Protocol:** **VERIFIED WITH LIMITATIONS** (Evaluated on authentic photographs; limited to local LFW corpus; supplementary web photos unmounted).
- **CPLFW 2,494 Local Subset Protocol:** **VERIFIED WITH LIMITATIONS** (Evaluated on authentic photographs; limited to local LFW corpus; supplementary web photos unmounted).
- **CFP-FP & AgeDB-30:** **NOT EVALUATED** (Unmounted archives; access restrictions correctly enforced).

