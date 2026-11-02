# FACECORE AI — STEP 09.1
## ROBUSTNESS EVALUATION REPRODUCTION & PERTURBATION AUDIT

**Audit Author:** Independent Machine-Learning Evaluation Auditor & Statistical Researcher  
**Execution Timestamp:** 2026-11-02T15:34:00Z  
**Primary Target:** Independent forensic audit of the 100-pair (200 images) symmetric robustness evaluation stored in `backend/data/step09_results/robustness_full_results.json`.

---

### 1. Executive Summary

A comprehensive forensic audit of the 8 controlled environmental, optical, and transmission stress conditions was executed. All perturbations were evaluated on **100 authentic research photograph pairs (200 distinct image files)** with identical symmetric perturbations applied to both images in each pair.

#### Key Audit Discoveries:
1. **Separation of Detection Failures vs. Discrimination Loss:**
   * In severe downsampling ($32\times 32$ px), **54.0% of pairs suffered complete Failure-to-Acquire (FTA)** because OpenCV YuNet failed to detect one or both faces.
   * On the remaining **46 successfully acquired pairs**, SFace suffered complete discrimination inversion ($\text{AUC} = \mathbf{0.4518}$, $\text{EER} = \mathbf{52.17\%}$), where impostors scored slightly higher ($\mu_{\text{imp}} = 0.3992$) than genuine matches ($\mu_{\text{gen}} = 0.3809$).
   * The reported AUC of $0.4518$ was computed **exclusively on the 46 acquired pairs**, in accordance with ISO/IEC 19795-1.
2. **Determinism Verification:**
   * Resizing, interpolation algorithms (`INTER_LINEAR` and `INTER_NEAREST`), gamma look-up tables, synthetic occlusion bounding boxes, and JPEG compression quantization factors are **100% deterministic** with zero random state dependencies.
3. **Upper-Face vs. Lower-Face Occlusion Asymmetry:**
   * Lower-face masks degrade accuracy negligibly ($\Delta \text{Acc} = -1.0\%$, $\text{Acc} = 99.00\%$, $\text{FTA} = 0.0\%$).
   * Upper-face sunglasses degrade accuracy severely ($\text{Acc} = 77.78\%$, $\text{AUC} = 0.8543$, $\text{EER} = 22.00\%$, $\text{FAR}$ surges to $18.00\%$), caused by ocular landmark degradation preventing accurate affine alignment to $112\times 112$.

---

### 2. Full Robustness Condition Forensic Matrix

Every condition evaluated on 100 pairs (200 authentic images) is detailed below:

| Condition Identifier | Physical Perturbation Description | Source Images | Image Detections | Pair FTA Count | Failure-to-Acquire (FTA Rate) | Acquired Pairs ($N_{\text{eval}}$) | Verification Accuracy ($\tau=0.3132$) | Observed FAR | Observed FRR | ROC-AUC | Equal Error Rate (EER) | Audit Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`baseline`** | Unmodified source photographs | 200 | 200 / 200 (100%) | 0 / 100 | **0.00%** $[0.0\%, 3.6\%]$ | **100** (50G, 50I) | **100.00%** | 0.00% | 0.00% | **1.0000** | **0.00%** | `VERIFIED` |
| **`gaussian_blur`** | Defocus blur ($\sigma=3.0, k=13$) | 200 | 200 / 200 (100%) | 0 / 100 | **0.00%** $[0.0\%, 3.6\%]$ | **100** (50G, 50I) | **95.00%** | 2.00% | 8.00% | **0.9532** | **6.00%** | `VERIFIED` |
| **`severe_downsampling`** | Downsample to $32\times 32$ px | 200 | 133 / 200 (66.5%) | 54 / 100 | **54.00%** $[43.7\%, 64.0\%]$ | **46** (23G, 23I) | **41.30%** | 78.26% | 39.13% | **0.4518** | **52.17%** | `VERIFIED` |
| **`underexposure`** | Non-linear gamma $\gamma = 1.8$ | 200 | 200 / 200 (100%) | 0 / 100 | **0.00%** $[0.0\%, 3.6\%]$ | **100** (50G, 50I) | **100.00%** | 0.00% | 0.00% | **1.0000** | **0.00%** | `VERIFIED` |
| **`overexposure`** | Direct flash saturation $\gamma = 0.4$ | 200 | 200 / 200 (100%) | 0 / 100 | **0.00%** $[0.0\%, 3.6\%]$ | **100** (50G, 50I) | **99.00%** | 2.00% | 0.00% | **1.0000** | **0.00%** | `VERIFIED` |
| **`jpeg_compression`** | Heavy lossy compression $Q = 10$ | 200 | 200 / 200 (100%) | 0 / 100 | **0.00%** $[0.0\%, 3.6\%]$ | **100** (50G, 50I) | **98.00%** | 0.00% | 4.00% | **0.9876** | **4.00%** | `VERIFIED` |
| **`partial_occlusion_mask`** | Lower 35% face block (mask) | 200 | 200 / 200 (100%) | 0 / 100 | **0.00%** $[0.0\%, 3.6\%]$ | **100** (50G, 50I) | **99.00%** | 0.00% | 2.00% | **0.9896** | **2.00%** | `VERIFIED` |
| **`partial_occlusion_sunglasses`** | Upper 28%-52% eye block | 200 | 199 / 200 (99.5%) | 1 / 100 | **1.00%** $[0.03\%, 5.4\%]$ | **99** (49G, 50I) | **77.78%** | 18.00% | 26.53% | **0.8543** | **22.00%** | `VERIFIED` |

---

### 3. Forensic Analysis: The $32\times 32$ Downsampling Collapse

The severe downsampling condition presents the most critical vulnerability in the production pipeline:

#### 3.1 Two-Stage Failure Mode
1. **Stage 1 (Detection Failure):**
   * YuNet operates on feature maps with stride 8, 16, and 32. In a $32\times 32$ image, an entire face spans only $16\times 16$ to $24\times 24$ pixels.
   * YuNet failed to detect any face in **$67$ out of $200$ source images** (Image Detection Failure Rate: $33.5\%$).
   * Because biometric verification requires two valid faces, **$54$ out of $100$ pairs** failed acquisition ($\text{FTA} = \mathbf{54.00\%}$).
2. **Stage 2 (Representation Collapse on Acquired Faces):**
   * On the remaining $46$ pairs where both faces were detected, the $5$ facial landmarks (two eyes, nose tip, two mouth corners) were severely misaligned due to sub-pixel coordinate discretization.
   * After bilinear resizing and nearest restoration, high-frequency identity features were eradicated.
   * **Score Distributions ($N=46$):**
     * Genuine similarity: $\mu_{\text{gen}} = 0.3809 \pm 0.1718$
     * Impostor similarity: $\mu_{\text{imp}} = 0.3992 \pm 0.1487$
     * Because $\mu_{\text{imp}} > \mu_{\text{gen}}$, impostors scored higher on average than genuine pairs, resulting in $\text{AUC} = \mathbf{0.4518}$ and $\text{EER} = \mathbf{52.17\%}$.

#### 3.2 ISO/IEC 19795-1 Compliance Audit
* Per ISO/IEC 19795-1 Section 5.3, **Failure-to-Acquire must never be conflated with False Match Rate or False Non-Match Rate.**
* The reporting in STEP 09 correctly segregated FTA ($54.0\%$) and computed AUC ($0.4518$) conditional on successful acquisition ($N=46$).
* **Operational Directive:** System integrators must enforce a strict input resolution gate ($H \ge 80, W \ge 80$ px) at the ingestion boundary to reject low-resolution probe images before comparison.

---

### 4. Determinism & Pipeline Provenance Audit

1. **Random Number Generator Inspection:**
   * Grepping `random`, `np.random`, `torch.manual_seed` across `robustness.py` confirmed **zero stochastic components**.
   * Resizing uses explicit deterministic OpenCV flags:
     ```python
     small = cv2.resize(bgr_img, (target_dim, target_dim), interpolation=cv2.INTER_LINEAR)
     restored = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
     ```
2. **Order Invariance:**
   * The 100 pairs are loaded in deterministic order from `backend/data/lfw/pairs.txt` (pairs 0 to 99).
   * Symmetric perturbation applies the exact same transformation function with identical parameters to both `image_a` and `image_b`.
3. **Audit Verdict:** The robustness evaluation methodology and numerical outputs are **`VERIFIED`**.

