# FACECORE AI — STEP 09.1
## MASTER CLAIM VERIFICATION REGISTER

**Audit Author:** Independent Machine-Learning Evaluation Auditor & Statistical Researcher  
**Execution Timestamp:** 2026-11-02T15:35:00Z  
**Scope:** Exhaustive claim-by-claim verification of all published numerical statements from STEP 09 across LFW, CALFW, CPLFW, Robustness, and Operating Thresholds.

---

### Standard Audit Classification Lexicon

* **`VERIFIED`:** Mathematically and empirically confirmed from raw persisted artifacts without methodological flaw.
* **`VERIFIED WITH LIMITATIONS`:** Confirmed on the specific evaluated sample or subset, but subject to documented sample size, corpus completeness, or prior-skew constraints that prevent unrestricted generalization.
* **`INCORRECT`:** The published numerical value or metric label contradicts mathematical fact or raw experimental data.
* **`NOT VERIFIED`:** Required raw artifacts or underlying records are absent or corrupt, preventing verification.
* **`NOT EVALUATED`:** Dataset or condition was not executed due to uninstalled or legally restricted access.

---

### Master Claim Verification Register

| Claim ID | Category | Target Statement / Numerical Claim | Source Artifact | Forensic Calculation Method | Raw Numerator / Denominator | Recalculated Value | Discrepancy Analysis | Forensic Audit Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CLM-01** | LFW | **6,000 official pairs evaluated across 10 folds** | `lfw_raw_scores.json` | Manifest parsing & unique ID tracking | $6,000 / 6,000$ | **$6,000$ pairs** | Zero missing images, exactly 300 gen + 300 imp per fold | `VERIFIED` |
| **CLM-02** | LFW | **Verification Accuracy = 99.35%** | `lfw_raw_scores.json` | 10-fold cross-validation with fold-specific $\tau_k^*$ | $\frac{5,961}{6,000}$ | **$99.350\%$** ($\pm 0.388\%$) | Identical under both Estimator A and Estimator B | `VERIFIED` |
| **CLM-03** | LFW | **ROC-AUC = 0.9988** | `lfw_raw_scores.json` | Exact Wilcoxon U with 0.5 tie weighting | $\frac{8,988,944.5}{3,000 \times 3,000}$ | **$0.99877$** | Published value is 4-decimal rounded representation | `VERIFIED` |
| **CLM-04** | LFW | **Equal Error Rate (EER) = 0.80%** | `lfw_raw_scores.json` | Linear interpolation between crossover thresholds | Interpolation at $\tau = 0.29910$ | **$0.800\%$** | Exact crossover at $\tau = 0.29910$ | `VERIFIED` |
| **CLM-05** | LFW | **Failure-to-Acquire (FTA) = 0.00%** | `lfw_full_result.json` | ISO/IEC 19795-1 pair failure tracking | $0 / 6,000$ | **$0.00\%$** | 100% face detection and alignment across 13,233 images | `VERIFIED` |
| **CLM-06** | LFW | **TAR @ FAR 0.1% = 98.80% at $\tau = 0.3423$** | `lfw_full_result.json` | Score thresholding on impostor distribution | $4 / 3,000$ (FA), $2,964 / 3,000$ (TA) | $\text{FAR} = \mathbf{0.1333\%}$, $\text{TAR} = \mathbf{98.80\%}$ | **Defect:** Observed FAR is $0.1333\% > 0.1000\%$. Strict TAR at FAR $\le 0.1000\%$ is **$98.50\%$** ($3 / 3000$ FA) at $\tau = 0.3592$. | `INCORRECT` |
| **CLM-07** | CALFW | **2,424 resolvable pairs evaluated across 10 folds** | `calfw_raw_scores.json` | Safe CSV parsing with image existence checks | $2,424 / 6,000$ | **$2,424$ pairs** | $3,576$ unmounted pairs explicitly tracked; 0.00% FTA on resolved | `VERIFIED WITH LIMITATIONS` (40.4% completeness) |
| **CLM-08** | CALFW | **Verification Accuracy = 99.14%** | `calfw_full_result.json` | Cross-validation threshold evaluation | Evaluated at $\bar{\tau} = 0.38725$ | **$99.139\%$** ($\approx 99.14\%$) | Corresponds to Estimator D. Estimator A is $99.095\% \pm 0.432\%$. | `VERIFIED WITH LIMITATIONS` (Subset prior: 35.5% gen) |
| **CLM-09** | CALFW | **ROC-AUC = 0.9981** | `calfw_raw_scores.json` | Exact Wilcoxon U with 0.5 tie weighting | $\frac{1,342,467.5}{860 \times 1,564}$ | **$0.99809$** | Published value is 4-decimal rounded representation | `VERIFIED WITH LIMITATIONS` (40.4% completeness) |
| **CLM-10** | CALFW | **Equal Error Rate (EER) = 1.05%** | `calfw_raw_scores.json` | Linear interpolation between crossover thresholds | Interpolation at $\tau = 0.36787$ | **$1.047\%$** ($\approx 1.05\%$) | Exact crossover at $\tau = 0.36787$ | `VERIFIED WITH LIMITATIONS` (40.4% completeness) |
| **CLM-11** | CALFW | **Transferred LFW threshold causes 2.77% drop** | `calfw_full_result.json` | Applying LFW $\tau=0.3132$ to CALFW | $\frac{2,336}{2,424}$ vs $\frac{2,403}{2,424}$ | **$\Delta = -2.77\%$** ($96.37\%$ vs $99.14\%$) | Impostor FAR surges to $5.18\%$ ($81 / 1,564$) | `VERIFIED` |
| **CLM-12** | CALFW | **Historical Step 08 Threshold $\tau^* = 0.4907$** | `STEP08_CROSS_DATASET_REPORT.md` | In-sample max accuracy on 60 sample pairs | 60 sample pairs | $\tau^* = 0.4907$ | Valid on isolated 60-pair sample; stabilizes to $0.3872$ on full corpus | `VERIFIED WITH LIMITATIONS` (Sample artifact) |
| **CLM-13** | CPLFW | **2,494 resolvable pairs evaluated across 10 folds** | `cplfw_raw_scores.json` | Safe CSV parsing with 4-digit zero padding | $2,494 / 6,000$ | **$2,494$ pairs** | $3,506$ unmounted pairs explicitly tracked; 0.00% FTA on resolved | `VERIFIED WITH LIMITATIONS` (41.6% completeness) |
| **CLM-14** | CPLFW | **Verification Accuracy = 98.81%** | `cplfw_raw_scores.json` | 10-fold cross-validation with fold-specific $\tau_k^*$ | $\frac{1}{10} \sum \text{Acc}_k$ | **$98.804\%$** ($\approx 98.81\%$) | Matches Estimator A rounded to 2 decimals | `VERIFIED WITH LIMITATIONS` (Subset prior: 37.9% gen) |
| **CLM-15** | CPLFW | **ROC-AUC = 0.9985** | `cplfw_raw_scores.json` | Exact Wilcoxon U with 0.5 tie weighting | $\frac{1,460,948.5}{944 \times 1,550}$ | **$0.99846$** | Published value is 4-decimal rounded representation | `VERIFIED WITH LIMITATIONS` (41.6% completeness) |
| **CLM-16** | CPLFW | **Equal Error Rate (EER) = 1.29%** | `cplfw_raw_scores.json` | Linear interpolation between crossover thresholds | Interpolation at $\tau = 0.38281$ | **$1.290\%$** | Exact crossover at $\tau = 0.38281$ | `VERIFIED WITH LIMITATIONS` (41.6% completeness) |
| **CLM-17** | CPLFW | **Transferred LFW threshold causes 2.26% drop** | `cplfw_full_result.json` | Applying LFW $\tau=0.3132$ to CPLFW | $\frac{2,408}{2,494}$ vs $\frac{2,464}{2,494}$ | **$\Delta = -2.26\%$** ($96.55\%$ vs $98.81\%$) | Impostor FAR surges to $5.03\%$ ($78 / 1,550$) | `VERIFIED` |
| **CLM-18** | Robustness | **32x32 Downsampling FTA = 54.0%** | `robustness_full_results.json` | ISO/IEC 19795-1 detection failure counting | $54 / 100$ failed pairs | **$54.00\%$** | $67 / 200$ images failed face detection | `VERIFIED` |
| **CLM-19** | Robustness | **32x32 Downsampling AUC = 0.4518** | `robustness_full_results.json` | Exact Wilcoxon U on acquired pairs | Acquired pairs ($N=46$) | **$0.4518$** | Computed exclusively on $46$ acquired pairs; complete discrimination collapse | `VERIFIED` |
| **CLM-20** | Robustness | **Sunglasses Occlusion Accuracy = 77.78%** | `robustness_full_results.json` | Classification at $\tau = 0.3132$ | Acquired pairs ($N=99$) | **$77.78\%$** | $1 / 100$ FTA; FAR surges to $18.00\%$ due to ocular alignment loss | `VERIFIED` |
| **CLM-21** | Robustness | **Mask Occlusion Accuracy = 99.00%** | `robustness_full_results.json` | Classification at $\tau = 0.3132$ | Acquired pairs ($N=100$) | **$99.00\%$** | Zero FTA; SFace features rely predominantly on ocular/upper face | `VERIFIED` |
| **CLM-22** | Robustness | **All perturbations are deterministic** | Code audit of `robustness.py` | AST and runtime seed inspection | 0 random calls | **Deterministic** | Fixed OpenCV flags, no stochastic operations | `VERIFIED` |
| **CLM-23** | Unmounted | **CFP-FP evaluated on real photographs** | Manifest & disk inspection | Path existence check | 0 pairs | **0 pairs evaluated** | Marked `NOT_INSTALLED`; unmounted archive | `NOT EVALUATED` |
| **CLM-24** | Unmounted | **AgeDB-30 evaluated on real photographs** | Manifest & disk inspection | Path existence check | 0 pairs | **0 pairs evaluated** | Marked `RESTRICTED_ACCESS`; requires authorization | `NOT EVALUATED` |

