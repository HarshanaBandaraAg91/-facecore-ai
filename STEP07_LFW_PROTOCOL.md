# FACECORE AI — STEP 07: Labeled Faces in the Wild (LFW) Evaluation Protocol Specification

**Document Version:** 1.0.0  
**Status:** Certified Specification  
**Date:** November 2026  
**Auditor / Researcher:** Senior Computer Vision Researcher & Machine-Learning Evaluation Engineer  

---

## 1. Introduction

The **Labeled Faces in the Wild (LFW)** dataset serves as the seminal benchmark for face verification under unconstrained real-world conditions (variations in pose, illumination, expression, occlusion, resolution, and age).

To ensure scientific validity and reproducibility, this document formally specifies the **View 2 10-Fold Evaluation Protocol** as implemented in FACECORE AI, distinguishes it from custom partitioning strategies, and establishes the mathematical rules for threshold calibration and face acquisition.

---

## 2. Official LFW View 2 Specification

The LFW benchmark comprises two distinct divisions:
* **View 1:** Development and hyperparameter exploration set (unused for final reporting).
* **View 2:** Official 10-fold cross-validation protocol (the authoritative scientific benchmark).

### 2.1 Pair List Architecture (`pairs.txt`)

The official `pairs.txt` defines an exact sequence of 6,000 image pairs distributed across 10 mutually exclusive testing folds:

```
[Header: 10 300]
├── Fold 1:  300 Genuine Pairs  +  300 Impostor Pairs  (600 pairs)
├── Fold 2:  300 Genuine Pairs  +  300 Impostor Pairs  (600 pairs)
├── Fold 3:  300 Genuine Pairs  +  300 Impostor Pairs  (600 pairs)
├── Fold 4:  300 Genuine Pairs  +  300 Impostor Pairs  (600 pairs)
├── Fold 5:  300 Genuine Pairs  +  300 Impostor Pairs  (600 pairs)
├── Fold 6:  300 Genuine Pairs  +  300 Impostor Pairs  (600 pairs)
├── Fold 7:  300 Genuine Pairs  +  300 Impostor Pairs  (600 pairs)
├── Fold 8:  300 Genuine Pairs  +  300 Impostor Pairs  (600 pairs)
├── Fold 9:  300 Genuine Pairs  +  300 Impostor Pairs  (600 pairs)
└── Fold 10: 300 Genuine Pairs  +  300 Impostor Pairs  (600 pairs)
Total: 3,000 Genuine Pairs + 3,000 Impostor Pairs = 6,000 Pairs
```

### 2.2 Record Parsing Rules

The file format is parsed deterministically using the following rules:

1. **Header Line:** Contains two integers: `num_folds` (10) and `pairs_per_type` (300).
2. **Genuine Pair Record (3 tokens):**
   ```
   <Identity_Name> <Image_Index_1> <Image_Index_2>
   ```
   * *Example:* `Abel_Pacheco 1 4`  
   * *Resolved Images:* `Abel_Pacheco/Abel_Pacheco_0001.jpg` and `Abel_Pacheco/Abel_Pacheco_0004.jpg`  
   * *Ground Truth Label:* Genuine ($y = 1$)

3. **Impostor Pair Record (4 tokens):**
   ```
   <Identity_Name_1> <Image_Index_1> <Identity_Name_2> <Image_Index_2>
   ```
   * *Example:* `Abel_Pacheco 1 Dean_Barker 1`  
   * *Resolved Images:* `Abel_Pacheco/Abel_Pacheco_0001.jpg` and `Dean_Barker/Dean_Barker_0001.jpg`  
   * *Ground Truth Label:* Impostor ($y = 0$)

4. **Zero-Padding Format:** Indices are zero-padded to 4 digits: `f"{name}_{int(idx):04d}.jpg"`.

---

## 3. Protocol Classification & Operating Paradigms

The literature defines several operational modes for LFW:

| Protocol Mode | Training Data Permitted | Pair Information Used | Production Pipeline Relevance |
| :--- | :--- | :--- | :--- |
| **Restricted** | LFW 9 training folds only | Binary same/different labels only | Academic algorithms training from scratch |
| **Unrestricted** | LFW 9 training folds only | Identity names and group associations | Metric learning algorithms training from scratch |
| **Unsupervised** | None | No labels used during training | Raw feature extractors |
| **Unrestricted With Outside Data** *(Standard)* | Outside datasets (e.g. CASIA-WebFace, MS-Celeb) | Pre-trained weights; LFW pairs used **only** for calibration & testing | **FACECORE AI (YuNet + SFace)** |

FACECORE AI operates under the **Unrestricted with Outside Data** paradigm:
- YuNet and SFace model weights are **completely frozen** (trained outside LFW).
- No parameters are fine-tuned on LFW images.
- LFW folds are utilized strictly for threshold calibration and empirical performance evaluation.

---

## 4. Methodological Distinction: Official LFW vs. STEP 05 Custom Disjoint Protocol

| Feature | Official LFW View 2 Protocol | STEP 05 Custom Identity-Disjoint Protocol |
| :--- | :--- | :--- |
| **Pair Source** | Official fixed `pairs.txt` (6,000 pairs) | Synthetically sampled from identity pool |
| **Identity Overlap Across Folds** | **Permitted across folds.** Frequent subjects (e.g., George W. Bush) appear in multiple folds according to historical protocol design. | **Strictly prohibited.** Every identity exists in exactly one fold ($I_i \cap I_j = \emptyset$). |
| **Pair Counts** | Exactly 300 genuine + 300 impostor per fold (600 total). | Configurable (e.g., 6 genuine + 6 impostor per fold). |
| **Scientific Purpose** | Standardized international benchmark comparison against published state of the art. | Rigorous stress-testing of unseen identities to guarantee zero cross-fold identity contamination. |

> **Scientific Audit Note:** Results produced from the custom identity-disjoint protocol must never be presented as official LFW benchmark figures. The system strictly separates dataset IDs:
> - `lfw-canonical-v1`: The official 6,000-pair View 2 protocol.
> - `synthetic-fixture-v1`: The controlled identity-disjoint test fixture.

---

## 5. Threshold Calibration & Evaluation Math

To prevent data snooping and test contamination, the 10-fold evaluation adheres to strict cross-validation:

### 5.1 Cross-Validation Step
For each fold $k \in \{0, 1, \dots, 9\}$:
1. **Validation Partition:** Formed by the union of all 9 remaining folds:
   $$\mathcal{D}_{\text{val}}^{(k)} = \bigcup_{j \neq k} \mathcal{F}_j$$
   ($N_{\text{val}} = 5,400$ pairs under full protocol).
2. **Optimal Validation Threshold Determination:**
   $$\tau_k^* = \arg\max_{\tau} \text{Accuracy}(\mathcal{D}_{\text{val}}^{(k)}, \tau)$$
   Where ties occur, the midpoint of the maximum-accuracy interval is selected:
   $$\tau_k^* = \frac{\tau_{\min} + \tau_{\max}}{2}$$
3. **Test Partition Evaluation:**
   Fold $k$ is evaluated strictly using $\tau_k^*$:
   $$\hat{y}_i = \mathbb{I}(s_i \ge \tau_k^*), \quad \forall i \in \mathcal{F}_k$$
   $$\text{Accuracy}_k = \frac{1}{|\mathcal{F}_k|} \sum_{i \in \mathcal{F}_k} \mathbb{I}(\hat{y}_i = y_i)$$

### 5.2 Aggregation & Uncertainty
* **Mean Verification Accuracy:**
  $$\mu = \frac{1}{10} \sum_{k=0}^9 \text{Accuracy}_k$$
* **Standard Error of the Mean:**
  $$S_E = \frac{\sigma}{\sqrt{10}} = \sqrt{\frac{1}{10 \cdot 9} \sum_{k=0}^9 (\text{Accuracy}_k - \mu)^2}$$

---

## 6. Real-World Image Acquisition Policies

Because unconstrained press photographs frequently capture incidental bystanders or multiple subjects, the benchmark runner supports two rigorous face selection policies:

```
[Input Photograph (250x250)]
           │
      [YuNet 0.6]
           │
     ┌─────┴─────┐
[1 Face]     [>1 Faces]
     │           │
     │      ┌────┴────────────────────────┐
     │      │                             │
     │  (Policy: center_face)      (Policy: strict_single_face)
     │      │                             │
     │  Select face closest to     Raise MultipleFacesDetectedError
     │  image center (125, 125)    Flag as Failure-to-Acquire (FTA)
     │      │                             │
     └──────┬─────────────────────────────┘
            ▼
    [Landmark Alignment (112x112)]
            ▼
    [SFace Embedding (128-d)]
```

1. **`center_face` (Canonical LFW Protocol):**
   In alignment with the official LFW specification, when multiple faces are detected, the face whose bounding box center is closest to the image center $(125, 125)$ is selected as the designated subject. This eliminates false rejections caused by journalists or background spectators.
2. **`strict_single_face` (ISO/IEC 19795-1 Compliance Mode):**
   In strict operational security audits, any image containing more than one detectable face is rejected as a Failure-to-Acquire (FTA), testing whether uncontrolled capture environments compromise automated biometric ingestion.

