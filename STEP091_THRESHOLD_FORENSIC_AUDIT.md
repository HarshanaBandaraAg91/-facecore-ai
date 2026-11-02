# FACECORE AI — STEP 09.1
## THRESHOLD FORENSIC AUDIT & PROVENANCE REGISTER

**Audit Author:** Independent Machine-Learning Evaluation Auditor & Statistical Researcher  
**Execution Timestamp:** 2026-11-02T15:30:00Z  
**Primary Target:** Threshold origins, objective functions, optimization criteria, and cross-dataset transfer boundaries across STEP 05, STEP 06, STEP 07, STEP 08, and STEP 09.

---

### 1. Executive Summary

A forensic investigation was conducted to resolve inconsistencies among published decision thresholds:
1. **LFW Native Accuracy Threshold ($\tau^* \approx 0.3132$):** Cross-validation accuracy-maximizing threshold on LFW 10-fold View 2 protocol.
2. **LFW Operational Low-FAR Threshold ($\tau \approx 0.3423$ vs $0.3592$):** Operational threshold targeting False Acceptance Rate (FAR) $\le 10^{-3}$ ($0.1\%$).
3. **CALFW Native Threshold ($\tau^* \approx 0.3872$):** Cross-validation accuracy-maximizing threshold on the 2,424 resolvable CALFW pairs.
4. **Historical STEP 08 CALFW Threshold ($\tau^* = 0.4907$):** Derived from an isolated 60-pair demonstration sample with dense demographic clustering.

This audit establishes that these values represent **fundamentally different objective functions and sample scales** that were historically conflated in reporting.

---

### 2. Threshold Provenance & Mathematical Derivation Register

| Threshold Identifier | Numerical Value | Optimization Objective | Dataset & Corpus Scope | Validation Partitions Used | Test Scores Leaked? | Historical Source Artifact | Forensic Audit Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **$\tau_{\text{LFW-CV}}^*$** | `0.31318` ($\approx 0.3132$) | $\arg\max_\tau \text{Acc}_{\text{val}}(\tau)$ | LFW Canonical ($N=6,000$) | 10 folds ($9/10$ train per split) | **NO (Strict)** | `lfw_full_result.json`, `STEP09_FULL_DATASET_EVALUATION.md` | `VERIFIED` |
| **$\tau_{\text{LFW-EER}}$** | `0.29910` ($\approx 0.2991$) | $\text{FAR}(\tau) = \text{FRR}(\tau)$ (Interpolated) | LFW Canonical ($N=6,000$) | Full corpus pooled | N/A (Analytical) | `lfw_raw_scores.json`, `STEP09_METRIC_RECALCULATION.md` | `VERIFIED` |
| **$\tau_{\text{LFW-FAR0.1\%}}^{\text{STEP09}}$** | `0.34231` ($\approx 0.3423$) | Discrete cutoff targeting $\text{FAR} \le 0.001$ | LFW Canonical ($N=6,000$) | Full impostor array ($N_{\text{imp}}=3,000$) | N/A (Operational) | `lfw_full_result.json` | `INCORRECT` (Yielded 4 FA, FAR=0.1333% > 0.1000%) |
| **$\tau_{\text{LFW-FAR0.1\%}}^{\text{STRICT}}$** | `0.35916` ($\approx 0.3592$) | Exact discrete $\text{FAR} \le 0.00100$ | LFW Canonical ($N=6,000$) | Full impostor array ($N_{\text{imp}}=3,000$) | N/A (Operational) | Forensic recalculation | `VERIFIED` (Yields 3 FA, FAR=0.1000% exactly) |
| **$\tau_{\text{CALFW-CV}}^*$** | `0.38725` ($\approx 0.3872$) | $\arg\max_\tau \text{Acc}_{\text{val}}(\tau)$ | CALFW Resolvable ($N=2,424$) | 10 folds ($9/10$ train per split) | **NO (Strict)** | `calfw_full_result.json`, `STEP09_FULL_DATASET_EVALUATION.md` | `VERIFIED` |
| **$\tau_{\text{CALFW-EER}}$** | `0.36787` ($\approx 0.3679$) | $\text{FAR}(\tau) = \text{FRR}(\tau)$ (Interpolated) | CALFW Resolvable ($N=2,424$) | Full corpus pooled | N/A (Analytical) | `calfw_raw_scores.json` | `VERIFIED` |
| **$\tau_{\text{CALFW-SAMPLE60}}^*$** | `0.49070` ($\approx 0.4907$) | $\arg\max_\tau \text{Acc}_{\text{sample}}(\tau)$ | CALFW Sample ($N=60$) | 60 sample pairs (no 10-fold split) | **YES (In-Sample)** | `STEP08_CROSS_DATASET_REPORT.md` | `VERIFIED WITH LIMITATIONS` (Sample artifact) |
| **$\tau_{\text{CPLFW-CV}}^*$** | `0.40836` ($\approx 0.4084$) | $\arg\max_\tau \text{Acc}_{\text{val}}(\tau)$ | CPLFW Resolvable ($N=2,494$) | 10 folds ($9/10$ train per split) | **NO (Strict)** | `cplfw_full_result.json`, `STEP09_FULL_DATASET_EVALUATION.md` | `VERIFIED` |
| **$\tau_{\text{CPLFW-EER}}$** | `0.38281` ($\approx 0.3828$) | $\text{FAR}(\tau) = \text{FRR}(\tau)$ (Interpolated) | CPLFW Resolvable ($N=2,494$) | Full corpus pooled | N/A (Analytical) | `cplfw_raw_scores.json` | `VERIFIED` |

---

### 3. Detailed Forensic Root-Cause Analysis

#### 3.1 Origin of $\tau^* = 0.4907$ (CALFW Step 08)
* **Forensic Finding:** In STEP 08, an initial demonstration run was executed with `--max-pairs 60`. 
* **Mechanism:** In that specific 60-pair subsample, the impostor similarity distribution contained extreme demographic pairings whose similarity scores reached up to $0.4830$. The in-sample accuracy optimizer set the boundary above all impostors at $\tau^* = 0.4907$.
* **Audit Verdict:** $\tau^* = 0.4907$ is an authentic result of an isolated 60-pair sample optimization, but was improperly reported as the characteristic native threshold of CALFW. When evaluated on the full 2,424 resolvable pairs across 10 folds, the true cross-validation threshold stabilizes at **$\tau^* = 0.38725$**.

#### 3.2 Origin of $\tau = 0.3423$ vs $0.3592$ (LFW Operational Threshold)
* **Forensic Finding:** In Step 09 result JSON (`tar_at_far_table`), the row targeting $\text{FAR} = 0.001$ reported threshold $0.34231$ with $\text{TAR} = 98.80\%$.
* **Algorithmic Defect:** `compute_tar_at_far` computed `cutoff_idx = int(np.floor(alpha * n_imp)) = int(np.floor(0.001 * 3000)) = 3`. In Python's 0-indexed array, `imp_scores[3]` is the **4th highest** impostor score ($0.342305$). Evaluating `scores >= 0.342305` yielded $4$ false acceptances:
  $$\text{Observed FAR} = \frac{4}{3,000} = 0.001333 \quad (0.1333\%)$$
* **Audit Correction:** $0.1333\%$ strictly exceeds the target constraint $\text{FAR} \le 0.00100$. To achieve $\text{FAR} \le 0.00100$, false acceptances must be $\le 3$. The 3rd highest impostor score is **$0.35916$**. Setting $\tau = 0.35916$ produces exactly 3 false accepts ($\text{FAR} = 3 / 3,000 = 0.001000$ exactly) and achieves a true $\text{TAR} = 2,955 / 3,000 = \mathbf{98.50\%}$.

#### 3.3 Objective Function Incompatibility
* Conflating **accuracy-maximizing thresholds** ($\tau^*$) with **Equal Error Rate thresholds** ($\tau_{\text{EER}}$) or **fixed-FAR thresholds** ($\tau_{\text{FAR}}$) is scientifically invalid:
  * On LFW: $\tau_{\text{EER}} = 0.2991$, $\tau^* = 0.3132$, $\tau_{\text{FAR}=0.1\%} = 0.3592$.
  * Across these three operating points, True Acceptance Rate shifts from $99.20\%$ down to $98.50\%$, and False Acceptance Rate shifts from $0.80\%$ down to $0.10\%$.

---

### 4. Threshold Transfer Vulnerability Matrix

When LFW's validation-calibrated threshold ($\tau^* = 0.31318$) is transferred without recalibration:

| Target Corpus | Native Threshold ($\tau^*$) | Transferred Threshold ($\tau_{\text{LFW}}$) | Native Accuracy | Transferred Accuracy | Transfer Gap ($\Delta \text{Acc}$) | Native FAR | Transferred FAR | Relative FAR Surge |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CALFW** | $0.38725$ | $0.31318$ | **99.14%** | **96.37%** | **$-2.77\%$** | $0.58\%$ ($9 / 1,564$) | **$5.18\%$** ($81 / 1,564$) | **$+793\%$** (8.9x) |
| **CPLFW** | $0.40836$ | $0.31318$ | **98.81%** | **96.55%** | **$-2.26\%$** | $0.65\%$ ($10 / 1,550$) | **$5.03\%$** ($78 / 1,550$) | **$+674\%$** (7.7x) |

**Conclusion:** A single static threshold calibrated on unconstrained frontal data must never be transferred to demographically balanced or cross-pose verification deployments without rigorous operational recalibration.

