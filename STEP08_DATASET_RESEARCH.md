# FACECORE AI — STEP 08: Cross-Dataset Research & Acquisition Specifications

**Document Version:** 1.0.0  
**Status:** Certified Academic & Empirical Research Document  
**Date:** November 2026  
**Role:** Senior Computer Vision Researcher & Biometric Evaluation Engineer  

---

## 1. Executive Summary & Objective

In **STEP 08**, FACECORE AI extends its evaluation framework beyond the canonical frontal baseline of **Labeled Faces in the Wild (LFW)** to investigate cross-dataset generalization and robustness under non-ideal, real-world covariates. 

Biometric verification pipelines trained on unconstrained web imagery often experience sharp performance drops when confronted with:
1. **Severe Yaw Rotation (Cross-Pose):** Large non-frontal angles ($\ge 45^\circ$, up to $90^\circ$ profile) disrupting landmark detection and distorting facial symmetry.
2. **Longitudinal Temporal Aging (Cross-Age):** Biological aging gaps spanning decades ($\Delta t \ge 10 - 30$ years), altering soft-tissue morphology and craniofacial metrics.
3. **Attribute Homogeneity (Demographic Matching):** Challenging negative (impostor) pairs sharing the same demographic traits (gender, race, approximate age) which confound feature representations that rely on high-level demographic cues.

This document formalizes the dataset provenance, academic citations, licensing terms, official protocols, corpus scales, and local staging specifications for the four primary evaluation datasets under investigation:
- **CFP-FP (Celebrities in Frontal-Profile)**
- **AgeDB-30 (Temporal Chronological Aging)**
- **CALFW (Cross-Age Labeled Faces in the Wild)**
- **CPLFW (Cross-Pose Labeled Faces in the Wild)**

---

## 2. Dataset Comparative Inventory

| Dataset | Primary Covariate | Corpus Scale (Identities / Images) | Evaluation Pairs & Protocols | Access Status & License | Source Institution |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LFW (Baseline)** | Unconstrained In-the-Wild Frontal | 5,749 identities / 13,233 images | 6,000 pairs (10 folds, 300 gen / 300 imp) | Non-Commercial Research (CC BY-NC 4.0 equiv) | University of Massachusetts Amherst |
| **CALFW** | Cross-Age Verification | 4,025 identities / 12,174 images | 6,000 pairs (10 folds, 300 gen / 300 imp) | Open Academic Research Use | Tsinghua University & BUPT |
| **CPLFW** | Cross-Pose Verification | 3,998 identities / 11,652 images | 6,000 pairs (10 folds, 300 gen / 300 imp) | Open Academic Research Use | Beijing University of Posts & Telecom (BUPT) |
| **CFP-FP** | Frontal vs. Profile ($90^\circ$ Yaw) | 500 identities / 7,000 images | 7,000 pairs (10 folds, 350 gen / 350 imp) | Non-Commercial Academic Agreement | University of Maryland (CFPDB) |
| **AgeDB-30** | Longitudinal Aging ($\Delta t \ge 30$ yrs) | 568 identities / 16,488 images | 6,000 pairs (10 folds, 300 gen / 300 imp) | Restricted Academic Agreement (iBUG) | Imperial College London |

---

## 3. Comprehensive Dataset Specifications

### 3.1 CALFW (Cross-Age Labeled Faces in the Wild)

* **Formal Citation:**  
  *Zheng, T., Deng, W., & Hu, J. (2017). Cross-Age LFW: A Database for Studying Face Recognition in Unconstrained Environments with Large Age Gaps. Neurocomputing, 2018.*
* **Primary Objective:**  
  Addresses the primary limitation of standard LFW, where many genuine pairs depict the same person photographed within weeks or months of each other. CALFW selects positive pairs with the largest chronological age gap available in the LFW corpus and constructs negative pairs by matching identities with identical gender and race to prevent demographic shortcutting.
* **Corpus & Protocol Geometry:**
  * Total Pairs: **6,000 pairs** partitioned into **10 distinct folds** (600 pairs per fold: 300 genuine, 300 impostor).
  * Pair Labeling: Standard binary (`1` = genuine, `0` = impostor).
  * Attribute Matching: Negative pairs are systematically paired with same-gender and same-ethnicity individuals.
* **Image Provenance & Resolution:**
  * CALFW pairs reference the underlying LFW image collection.
  * In the FACECORE AI environment, the verified LFW corpus installed on disk contains **2,424 valid pairs** (with $>220$ balanced pairs in every fold 1..10) directly resolvable without synthetic rendering.
* **Access & Licensing:**
  * Released publicly for non-commercial academic research.
  * Annotation file format: `pairs.csv` with schema `(pair_id, fold_id, fold_position, is_same, image_a, image_b)`.

---

### 3.2 CPLFW (Cross-Pose Labeled Faces in the Wild)

* **Formal Citation:**  
  *Zheng, T., & Deng, W. (2018). Cross-Pose LFW: A Database for Studying Face Recognition in Unconstrained Environments with Large Pose Variations. arXiv:1804.01022.*
* **Primary Objective:**  
  Measures the vulnerability of 2D face recognition models to out-of-plane yaw rotations. While standard LFW is predominantly near-frontal, CPLFW selects positive pairs with maximal yaw angular divergence (one near-frontal and one profile or near-profile photograph) and pairs impostors with matching demographic attributes.
* **Corpus & Protocol Geometry:**
  * Total Pairs: **6,000 pairs** partitioned into **10 distinct folds** (600 pairs per fold: 300 genuine, 300 impostor).
  * Pair Selection: Pose estimators were utilized to quantify yaw angles, ensuring genuine pairs possess significant angular divergence ($\Delta \theta_{\text{yaw}} \ge 30^\circ - 60^\circ$).
* **Image Provenance & Zero-Padding Resolution:**
  * CPLFW annotations reference filenames using a 4-digit zero-padded index (e.g., `Aaron_Peirsol_0001.jpg` vs `Aaron_Peirsol_1.jpg`).
  * The FACECORE AI adapter (`parse_cplfw_pairs_csv`) includes deterministic filename resolution that transparently maps non-padded and padded variants to the verified on-disk LFW repository.
  * Verified pairs resolvable on local disk: **2,494 pairs** (yielding $220 - 280$ balanced pairs in every fold 1..10).
* **Access & Licensing:**
  * Publicly available for non-commercial academic research.

---

### 3.3 CFP-FP (Celebrities in Frontal-Profile)

* **Formal Citation:**  
  *Sengupta, S., Chen, J. C., Castillo, C., Patel, V. M., Chellappa, R., & Jacobs, D. W. (2016). Frontal to Profile Face Verification in the Wild. IEEE Winter Conference on Applications of Computer Vision (WACV).*
* **Primary Objective:**  
  Evaluates extreme frontal-to-profile verification ($0^\circ$ frontal vs $\approx 90^\circ$ profile). For each of 500 public figures, the dataset provides 10 frontal images and 4 extreme profile images collected in wild conditions.
* **Corpus & Protocol Geometry:**
  * Total Identities: 500 individuals.
  * Total Images: 7,000 images (5,000 frontal, 2,000 profile).
  * Official Protocols:
    - **CFP-FF (Frontal-Frontal):** 7,000 pairs across 10 folds (350 gen / 350 imp per fold).
    - **CFP-FP (Frontal-Profile):** 7,000 pairs across 10 folds (350 gen / 350 imp per fold), where every genuine pair contains one frontal and one profile image.
* **Access & Licensing:**
  * Hosted at `http://www.cfpdb.org/` by the University of Maryland.
  * Distribution requires researchers to request direct archive download links.
  * System Status: Designated as `NOT_INSTALLED`. FACECORE AI implements a strict archive verification module (`verify_cfp_installation`) ready to digest `Pair_list_P.txt` upon archive deposition in `backend/data/cfp`.

---

### 3.4 AgeDB-30 (Temporal 30-Year Age Gap)

* **Formal Citation:**  
  *Moschoglou, S., Papaioannou, A., Sagonas, C., Deng, J., & Zafeiriou, S. (2017). AgeDB: The First Manually Collected, In-the-Wild Age Database with Accurate Ground Truth. IEEE CVPR Workshop.*
* **Primary Objective:**  
  Provides gold-standard ground-truth chronological age annotations for in-the-wild photographs. The benchmark protocol isolates pairs with a strict 30-year chronological gap ($\Delta t \ge 30$ years) to evaluate recognition resistance to biological human aging.
* **Corpus & Protocol Geometry:**
  * Total Images: 16,488 images of 568 distinct subjects.
  * Age Range: 1 to 101 years old.
  * Official Metric Protocol: 6,000 pairs across 10 folds with 300 genuine and 300 impostor pairs per fold, strictly enforcing a 30-year age gap on genuine pairs.
* **Access & Licensing:**
  * Hosted by Imperial College London (iBUG group) at `https://ibug.doc.ic.ac.uk/resources/agedb/`.
  * **Restricted Access Policy:** Requires formal academic user agreement, signed institutional end-user licensing, and forbids redistribution.
  * System Status: Designated as `RESTRICTED_ACCESS`. Runner rejects execution attempts cleanly with explicit institutional licensing instructions.

---

## 4. Architectural Integration & Adapter Design

### 4.1 Parser Normalization & Integrity Checks
To ensure scientific consistency without mutating original source data:
- `parse_calfw_pairs_csv()`: Parses comma-delimited 6-column records, validates fold indexing (`1..10`), verifies file presence, and constructs immutable `PairAnnotation` structures.
- `parse_cplfw_pairs_csv()`: Handles 4-digit zero-padding format discrepancies and links pairs to verified local LFW photography.
- `parse_cfp_fp_pairs_txt()`: Parses CFP-FP 10-fold colon/space-delimited protocols, maps fold labels, and checks frontal/profile relative image paths.
- `parse_agedb_pairs_txt()`: Parses AgeDB 10-fold pair definitions, ensuring chronological metadata integrity.

### 4.2 Rejection of Synthetic Fallbacks
In accordance with FACECORE AI's strict scientific directive, if a requested dataset archive is missing, unmounted, or incomplete, the framework raises a deterministic `ValueError` explaining the exact file requirements. The engine **never** silently falls back to synthetic fixtures or procedural faces when executing an empirical benchmark run.

