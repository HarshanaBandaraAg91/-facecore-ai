# FACECORE AI — STEP 09.2: THRESHOLD SELECTION LEAKAGE AUDIT
**Phase:** Step 09.2 Independent Forensic Audit & Operating-Point Reliability  
**Date:** November 2026  
**Auditor:** Independent Machine-Learning Evaluation Auditor & Statistical Researcher  
**Status:** Completed & Forensically Proven  

---

## 1. Executive Summary & Forensic Verdict

During Step 09 and Step 09.1, the evaluation reports presented operational operating points for the unmodified YuNet + SFace pipeline on LFW:
- **Step 09 Claim:** Operating threshold $\tau = 0.3423$ achieves $\text{FAR} \le 0.10\%$ with $\text{TAR} = 98.90\%$.
- **Step 09.1 Claim:** Operating threshold $\tau = 0.35916$ achieves exactly 3 false acceptances out of 3,000 impostor comparisons ($\text{FAR} = 0.1000\%$) with $\text{TAR} = 98.60\%$.

### Forensic Audit Verdict: `THRESHOLD_SELECTION_LEAKAGE`
An independent forensic examination of the persisted raw score artifact `backend/data/step09_results/lfw_raw_scores.json` confirms that **both thresholds were derived in-sample from the pooled test-fold impostor scores across all 10 folds of LFW without test-fold isolation**.

Specifically:
- $\tau = 0.359156$ is exactly the **3rd highest score** among all 3,000 test impostor comparisons ($k = 3$, Rank 3). Setting the operating threshold at Rank 3 of the test data guarantees by construction that exactly 3 test impostors will meet or exceed the threshold ($3 / 3000 = 0.1000\%$).
- $\tau = 0.342305$ is exactly the **4th highest score** among all 3,000 test impostor comparisons ($k = 4$, Rank 4).
- Neither threshold was derived from an independent calibration dataset, nor from fold-isolated validation partitions.
- Deriving an operational decision threshold from the test set used to evaluate it constitutes **post-hoc in-sample threshold optimization (leakage)**.

---

## 2. Forensic Reconstruction & Evidence

### 2.1 The Top Impostor Scores in LFW
Across all 3,000 impostor comparisons in the canonical 10-fold View 2 evaluation of LFW, the top 10 cosine similarity scores and their assigned folds are:

| Rank | Impostor Pair ID | Cosine Similarity Score | Assigned Fold | Status Under Pooled $\tau=0.35916$ |
|:---:|:---|:---:|:---:|:---:|
| **1** | `imp_fold5_pair142` | **0.405145** | **Fold 5** | False Accept (1 / 3) |
| **2** | `imp_fold5_pair208` | **0.366252** | **Fold 5** | False Accept (2 / 3) |
| **3** | `imp_fold6_pair089` | **0.359156** | **Fold 6** | False Accept (3 / 3) [Threshold] |
| 4 | `imp_fold9_pair047` | 0.342305 | Fold 9 | True Reject (Step 09 Thresh) |
| 5 | `imp_fold2_pair112` | 0.338176 | Fold 2 | True Reject |
| 6 | `imp_fold6_pair214` | 0.330577 | Fold 6 | True Reject |
| 7 | `imp_fold2_pair198` | 0.330237 | Fold 2 | True Reject |
| 8 | `imp_fold9_pair165` | 0.328285 | Fold 9 | True Reject |
| 9 | `imp_fold8_pair073` | 0.325727 | Fold 8 | True Reject |
| 10 | `imp_fold9_pair281` | 0.316698 | Fold 9 | True Reject |

### 2.2 Proof of In-Sample Selection
1. **Mathematical Identity:** $\text{Rank}(0.359156) = 3$. Since there are $3,000$ impostor pairs, $\frac{3}{3000} = 0.00100 = 0.1000\%$. The threshold was chosen by sorting the 3,000 test scores and taking the score at index $3 - 1 = 2$.
2. **Fold Concentration:** Note that Rank 1 and Rank 2 both reside in Fold 5, while Rank 3 resides in Fold 6. The remaining 8 folds (Folds 0, 1, 2, 3, 4, 7, 8, 9) contain zero impostors with score $\ge 0.35916$.
3. **Absence of Partition Isolation:** At no point during the calculation of $\tau = 0.35916$ was any fold held out as untouched test data.

---

## 3. Strict 3-Way Partition Architecture

To maintain scientific integrity in biometric verification, three distinct data tiers must be strictly maintained:

```mermaid
flowchart LR
    Tier1["Tier 1: Model Development\n(Training Weights)\nCASIA-WebFace / MS-Celeb"] --> Tier2["Tier 2: Operational Calibration\n(Threshold Tuning)\nValidation Split / Folds j ≠ k"]
    Tier2 --> Tier3["Tier 3: Final Untouched Evaluation\n(Reported Performance)\nTest Fold k / Independent Set"]
```

### Protocol Rules:
1. **Tier 1 (Model Development Data):** Closed-set training images used to learn YuNet detector weights and SFace feature embedding projections. Under no circumstances should test identities or test images appear in Tier 1.
2. **Tier 2 (Calibration Data):** A sequestered partition used exclusively to tune operating thresholds for target FAR levels ($\tau_{\alpha}$ such that $\text{FAR}_{\text{val}} \le \alpha$).
3. **Tier 3 (Final Untouched Evaluation Data):** Benchmark pairs evaluated *only once* using thresholds fixed during Tier 2. Scores from Tier 3 must **never** be used to adjust, select, or search for thresholds.

When standard benchmarks (like LFW View 2) provide only a 10-fold structure without a separate calibration partition, **fold-isolated cross-validation** must be employed: for each fold $k$, the threshold $\tau_k$ is calibrated on the 9 validation folds ($j \neq k$) and applied to test fold $k$.

---

## 4. Leak-Free Fold-Isolated Cross-Validation Results

We executed the strict fold-isolated cross-validation protocol on LFW ($N = 6,000$ pairs):
- For each fold $k \in \{0, \dots, 9\}$:
  - Calibration impostor pool: $N_{\text{imp,val}} = 2,700$ pairs from the other 9 folds.
  - Allowed validation false acceptances: $\text{FA}_{\text{val}} \le \lfloor 0.001 \times 2,700 \rfloor = 2$.
  - Threshold $\tau_k$: The 3rd highest score among the 2,700 validation impostors.
  - Test fold $k$: 300 genuine and 300 impostor pairs evaluated using $\tau_k$.

### Per-Fold Calibration and Test Results:

| Test Fold $k$ | Calibration Impostors | Allowed $\text{FA}_{\text{val}}$ | Calibrated $\tau_k$ | Test Gen Acc ($\text{TP}_k$) | Test Imp Rej ($\text{TN}_k$) | Test False Accepts ($\text{FP}_k$) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Fold 0 | 2,700 | 2 | 0.359156 | 296 / 300 | 300 / 300 | 0 |
| Fold 1 | 2,700 | 2 | 0.359156 | 296 / 300 | 300 / 300 | 0 |
| Fold 2 | 2,700 | 2 | 0.359156 | 296 / 300 | 300 / 300 | 0 |
| Fold 3 | 2,700 | 2 | 0.359156 | 298 / 300 | 300 / 300 | 0 |
| Fold 4 | 2,700 | 2 | 0.359156 | 294 / 300 | 300 / 300 | 0 |
| Fold 5 | 2,700 | 2 | **0.338176** | 298 / 300 | 298 / 300 | **2** |
| Fold 6 | 2,700 | 2 | **0.342305** | 297 / 300 | 299 / 300 | **1** |
| Fold 7 | 2,700 | 2 | 0.359156 | 296 / 300 | 300 / 300 | 0 |
| Fold 8 | 2,700 | 2 | 0.359156 | 294 / 300 | 300 / 300 | 0 |
| Fold 9 | 2,700 | 2 | 0.359156 | 293 / 300 | 300 / 300 | 0 |
| **Pooled Out-of-Fold** | **—** | **—** | **Mean = 0.35537** | **2,958 / 3,000 (98.60%)** | **2,997 / 3,000 (99.90%)** | **3 / 3,000 (0.1000%)** |

### Observations:
1. **Dynamic Threshold Response:** When evaluating Fold 5 (which contains the top 2 global impostors), those impostors are excluded from calibration, causing the validation threshold to settle at $\tau_5 = 0.33818$. When applied to Fold 5, exactly 2 false acceptances occur.
2. **Conservative Variant:** If calibration enforces strict $\text{FA}_{\text{val}} \le 1$ ($< 0.074\%$), $\tau_k \in [0.35916, 0.40515]$ with mean $\bar{\tau} = 0.36386$. This yields **2 false acceptances** ($\text{FAR} = 0.0667\%$) and **$\text{TAR} = 98.47\%$** ($2,954 / 3,000$).
3. **True Out-of-Fold Performance:** The true out-of-fold TAR for SFace on LFW at $\text{FAR} \le 0.10\%$ is **$98.47\%$ to $98.60\%$**.
4. **Correction of Record:** The result $\text{TAR} = 98.60\%$ at $\text{FAR} = 0.1000\%$ is scientifically valid under out-of-fold cross-validation, but the claim of a single global fixed threshold $\tau = 0.35916$ without fold variance is corrected.

---

## 5. Audit Compliance Checklist

- [x] Independent verification of all 3,000 impostor scores.
- [x] Forensic identification of $\tau = 0.35916$ as order statistic Rank 3.
- [x] Forensic identification of $\tau = 0.3423$ as order statistic Rank 4.
- [x] Implementation of strict fold-isolated cross-validation for operating points.
- [x] Reporting of per-fold calibration thresholds ($\min = 0.33818, \max = 0.35916$).
- [x] Reporting of true out-of-fold TAR ($98.60\%$) and FAR ($0.1000\%$).
- [x] Documented 3-tier data separation architecture.

