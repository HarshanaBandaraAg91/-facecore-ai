# FACECORE AI — STEP 09.1
## INDEPENDENT STATISTICAL FORENSIC AUDIT & CLAIM VERIFICATION REPORT

**Auditor Role:** Senior Computer Vision Researcher, Biometric Evaluation Auditor & Statistical Researcher  
**Audit Completion Timestamp:** 2026-11-02T15:36:00Z  
**Primary Target:** Independent statistical verification of all numerical claims, raw artifacts, and operational thresholds published in STEP 09.

---

### 1. Executive Summary & Audit Conclusions

An exhaustive statistical forensic audit of all benchmark artifacts, mathematical claims, and evaluation protocols in **FACECORE AI STEP 09** has been completed. 

The audit utilized an **entirely independent recalculation module** ([`backend/app/benchmarks/independent_audit.py`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/backend/app/benchmarks/independent_audit.py)) that computes exact count-based rational rates (`fractions.Fraction`), exact Wilcoxon-Mann-Whitney U statistics, linear crossover EER, and exact Clopper-Pearson binomial confidence intervals without importing or calling any production evaluation functions from `app.benchmarks.metrics`.

#### Core Audit Conclusions:
1. **LFW Canonical Protocol ($N = 6,000$):**
   * **Verification Accuracy:** Mathematically verified at **$99.350\%$** ($\pm 0.388\%$) under both Estimator A (mean per-fold) and Estimator B (pooled out-of-fold).
   * **ROC-AUC:** Mathematically verified at **$0.99877$** ($\approx 0.9988$).
   * **Equal Error Rate (EER):** Mathematically verified at **$0.800\%$** at crossover threshold $\tau = 0.29910$.
   * **Failure-to-Acquire (FTA):** Exactly **$0.00\%$** ($0 / 6,000$ failures).
2. **FAR / TAR Correction (LFW Operating Point):**
   * **Defect Identified:** STEP 09 reported $\text{TAR} = 98.80\%$ at target $\text{FAR} \le 0.1\%$ using threshold $\tau = 0.3423$. Forensic inspection revealed that at $\tau = 0.34231$, exactly $4$ impostors were accepted out of $3,000$, yielding an empirical $\text{FAR} = \frac{4}{3,000} = \mathbf{0.1333\%}$, which exceeds the $0.1000\%$ ceiling by $+33.3\%$.
   * **Mathematical Correction:** For strict $\text{FAR} \le 0.1000\%$ ($\le 3$ false accepts), the threshold must be set to $\tau = \mathbf{0.35916}$, yielding exactly $3 / 3,000$ false accepts ($\text{FAR} = \mathbf{0.1000\%}$, 95% Clopper-Pearson CI $[0.0206\%, 0.2920\%]$) and true $\text{TAR} = \frac{2,955}{3,000} = \mathbf{98.50\%}$.
3. **Threshold Divergence Root Cause Resolved:**
   * Step 08 reported a CALFW threshold of $\tau^* = 0.4907$ from an isolated 60-pair sample. Full-corpus 10-fold cross-validation on the 2,424 resolvable pairs establishes the true native threshold at $\tau^* = \mathbf{0.38725}$.
   * The upward shift from LFW ($\tau^* = 0.3132$) to CALFW ($\tau^* = 0.3872$) is empirically proven to result from demographic attribute matching in CALFW negative pairs, which inflates impostor similarity mean from $\mu = 0.0838$ to $\mu = 0.1703$.
4. **Sampling Bias in CALFW & CPLFW Subsets:**
   * Standard `lfw.tgz` contains $13,233$ images, leaving $2,640$ CALFW and $2,444$ CPLFW supplementary web images unmounted.
   * Consequently, exactly $2,424$ CALFW pairs ($40.40\%$) and $2,494$ CPLFW pairs ($41.57\%$) resolve on disk.
   * Unmounted images predominantly affected genuine pairs, shifting the class prior from $50:50$ to **$35.5\% : 64.5\%$** in CALFW and **$37.9\% : 62.1\%$** in CPLFW.
   * While ROC-AUC ($0.9981$ and $0.9985$) is invariant to class prior shifts, naive classification accuracy ($99.14\%$ and $98.81\%$) is influenced by the higher impostor proportion. **These subset accuracies must never be represented as full-benchmark results.**
5. **Robustness Reproduction & $32\times 32$ px Collapse:**
   * Severe downsampling ($32\times 32$ px) suffers a two-stage failure mode: Stage 1 detection failure ($\text{FTA} = \mathbf{54.00\%}$) followed by Stage 2 representation inversion on acquired faces ($\text{AUC} = \mathbf{0.4518}$, $\text{EER} = \mathbf{52.17\%}$ on $N=46$).
   * The reported AUC was verified to be calculated exclusively on the $46$ acquired pairs, strictly compliant with ISO/IEC 19795-1.

---

### 2. Comprehensive Forensic Reports Directory

This audit delivers seven exhaustive reference reports:

1. [STEP091_THRESHOLD_FORENSIC_AUDIT.md](file:///c:/Projects/project%207%20-%20face%20checking%20tool/STEP091_THRESHOLD_FORENSIC_AUDIT.md)
   *Complete threshold provenance register; origin of 0.3132, 0.3423, 0.3592, 0.3872, and 0.4907; objective function differentiation ($\arg\max \text{Acc}$ vs EER vs fixed FAR); transfer vulnerability matrix.*
2. [STEP091_FAR_TAR_RULE_OF_THREE_AUDIT.md](file:///c:/Projects/project%207%20-%20face%20checking%20tool/STEP091_FAR_TAR_RULE_OF_THREE_AUDIT.md)
   *Detailed forensic analysis of FAR/TAR estimators; mathematical investigation of the 4/3000 false accept defect; strict correction to $\tau=0.35916$; exact Clopper-Pearson 95% binomial confidence intervals; rigorous mathematical proof of Rule of Three ($p_{\text{upper}} \approx -\ln(0.05)/N \approx 3/N$).*
3. [STEP091_METRIC_RECALCULATION.md](file:///c:/Projects/project%207%20-%20face%20checking%20tool/STEP091_METRIC_RECALCULATION.md)
   *Independent recalculation across four distinct estimators (Estimators A, B, C, D); exact rational arithmetic confusion matrices (`Fraction`); precision, recall, F1, FAR, and FRR.*
4. [STEP091_CROSS_VALIDATION_AUDIT.md](file:///c:/Projects/project%207%20-%20face%20checking%20tool/STEP091_CROSS_VALIDATION_AUDIT.md)
   *10-fold View 2 protocol integrity; mathematical proof of test-fold isolation invariance; fold-by-fold accounting for CALFW and CPLFW; forensic identification of class prior skew ($35.5:64.5$).*
5. [STEP091_ROBUSTNESS_AUDIT.md](file:///c:/Projects/project%207%20-%20face%20checking%20tool/STEP091_ROBUSTNESS_AUDIT.md)
   *Forensic audit of 8 stress conditions on 100 pairs; separation of detection failure (54.0% FTA) vs. representation collapse (AUC 0.4518 on $N=46$); proof of 100% deterministic OpenCV execution.*
6. [STEP091_CLAIM_VERIFICATION_REGISTER.md](file:///c:/Projects/project%207%20-%20face%20checking%20tool/STEP091_CLAIM_VERIFICATION_REGISTER.md)
   *Item-by-item verification table of 24 distinct numerical claims from STEP 09 with source artifacts, raw numerators/denominators, recalculated values, and standard verdicts.*
7. [STEP091_REPORT.md](file:///c:/Projects/project%207%20-%20face%20checking%20tool/STEP091_REPORT.md)
   *Master synthesis report, regulatory compliance checklist, commands executed, and operational deployment rules.*

---

### 3. Master Metric Recalculation Synthesis Table

| Benchmark Corpus | Evaluated Pairs | Estimator A (Mean Per-Fold) | Estimator B (Pooled OOF) | Estimator C (In-Sample Global) | Estimator D (At Mean $\bar{\tau}$) | Exact Analytical ROC-AUC | Exact Crossover EER | Baseline FTA Rate | Audit Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **LFW Canonical** | **6,000** (3,000G, 3,000I) | **99.350%** ($\pm 0.388\%$) | **99.350%** ($5,961 / 6,000$) | 99.417% ($\tau=0.3081$) | 99.383% ($\bar{\tau}=0.3126$) | **0.99877** | **0.800%** ($\tau=0.2991$) | **0.00%** ($0 / 6,000$) | `VERIFIED` |
| **CALFW Cross-Age** | **2,424** (860G, 1,564I) | **99.095%** ($\pm 0.432\%$) | **99.092%** ($2,402 / 2,424$) | 99.175% ($\tau=0.3857$) | **99.182%** ($\bar{\tau}=0.3865$) | **0.99809** | **1.047%** ($\tau=0.3679$) | **0.00%** ($0 / 2,424$) | `VERIFIED WITH LIMITATIONS` (40.4% completeness) |
| **CPLFW Cross-Pose** | **2,494** (944G, 1,550I) | **98.804%** ($\pm 1.258\%$) | **98.837%** ($2,465 / 2,494$) | 98.957% ($\tau=0.4069$) | **98.929%** ($\bar{\tau}=0.4069$) | **0.99846** | **1.290%** ($\tau=0.3828$) | **0.00%** ($0 / 2,494$) | `VERIFIED WITH LIMITATIONS` (41.6% completeness) |
| **CFP-FP** | 0 (Unmounted) | N/A | N/A | N/A | N/A | N/A | N/A | N/A | `NOT EVALUATED` (`NOT_INSTALLED`) |
| **AgeDB-30** | 0 (Restricted) | N/A | N/A | N/A | N/A | N/A | N/A | N/A | `NOT EVALUATED` (`RESTRICTED_ACCESS`) |

---

### 4. Implementation & Test Suite Verification

#### 4.1 Independent Audit Module
Created [`backend/app/benchmarks/independent_audit.py`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/backend/app/benchmarks/independent_audit.py) featuring:
* `calculate_rational_metrics`: Exact rational arithmetic (`fractions.Fraction`) for counts and rates.
* `calculate_exact_wilcoxon_auc`: Analytical Mann-Whitney U computation with strict 0.5 tie-weighting.
* `calculate_independent_eer`: Linear crossover interpolation between discrete threshold crossings.
* `calculate_clopper_pearson_ci`: Exact binomial confidence interval inversion via CDF bisection.
* `calculate_rule_of_three_bound`: Exact one-sided $1 - 0.05^{1/N}$ and heuristic $3/N$ bounds.
* `evaluate_four_accuracy_estimators`: Side-by-side computation of Estimators A, B, C, and D.

#### 4.2 Automated Regression Suites
* **New STEP 09.1 Audit Suite:** [`backend/tests/test_benchmarks_step091_audit.py`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/backend/tests/test_benchmarks_step091_audit.py) (**9 tests, 100% passing**).
* **Full Backend Pytest Suite:** **96 / 96 tests passing (100%)**
  ```powershell
  backend\.venv\Scripts\python.exe -m pytest backend/tests -v
  # 96 passed in 28.14s
  ```
* **Full Frontend Vitest Suite:** **50 / 50 tests passing (100%)**
  ```powershell
  npm --prefix frontend test -- --run
  # 50 passed across all 9 test suites in 11.2s
  ```
* **Production Frontend Build:** **100% Clean**
  ```powershell
  npm --prefix frontend run build
  # tsc -b && vite build -> built in 1.02s with zero errors
  ```

---

### 5. Verified Raw Artifacts Provenance

| Artifact Filename | Absolute File Path | File Size | SHA-256 Checksum | Purpose / Description |
| :--- | :--- | :--- | :--- | :--- |
| `lfw_raw_scores.json` | `backend/data/step09_results/lfw_raw_scores.json` | 630.4 KB | `0d8b44ff9ee1188d3e23005cf46ab9b94ce5ba857321586940a45ea983412aa8` | Pair-level raw scores, folds, and labels for all 6,000 LFW pairs |
| `calfw_raw_scores.json` | `backend/data/step09_results/calfw_raw_scores.json` | 203.8 KB | `9eb3b7a5e8e8ea6f88837e3d17dbb18c5e6da805cf14e7a8e7e163b2f5670fc6` | Pair-level raw scores, folds, and labels for all 2,424 CALFW pairs |
| `cplfw_raw_scores.json` | `backend/data/step09_results/cplfw_raw_scores.json` | 209.8 KB | `82f9d6efb433cfb3952a265d1dcf50fa3aeb482a0b1cb3b6f00db14ad47f8ba7` | Pair-level raw scores, folds, and labels for all 2,494 CPLFW pairs |
| `robustness_full_results.json` | `backend/data/step09_results/robustness_full_results.json` | 5.5 KB | `a147e45e99493f0b2f5b5fba45ba6d1490dc61bc03a9f074d2fc00aa7ef31e9c` | Condition telemetry for 100 pairs across 8 symmetric stress conditions |
| `lfw_full_result.json` | `backend/data/step09_results/lfw_full_result.json` | 67.4 KB | `b305c21ce4f526ebc8bb02c38865e99bc150ebce5b3b06e8979354464c58f01b` | Aggregated BenchmarkResult schema for LFW Canonical |
| `calfw_full_result.json` | `backend/data/step09_results/calfw_full_result.json` | 68.4 KB | `a9cbf5607b36f54db1262d1c68f95c47fbbe833dbd3f44c688d08ea39c7163c4` | Aggregated BenchmarkResult schema for CALFW Cross-Age |
| `cplfw_full_result.json` | `backend/data/step09_results/cplfw_full_result.json` | 68.7 KB | `cc5f6d70d9709d436a56c4d7ec5b084926dc2145e546199042b4bfa2cbaf5513` | Aggregated BenchmarkResult schema for CPLFW Cross-Pose |

---

### 6. Remaining Scientific Limitations & Operational Directives

1. **Rule of Three Sample Size Limitation:**
   * Operating points at $\text{FAR} \le 10^{-3}$ ($0.1\%$) are mathematically valid only on corpora with $N_{\text{imp}} \ge 3,000$ (LFW). On CALFW ($N_{\text{imp}} = 1,564$) and CPLFW ($N_{\text{imp}} = 1,550$), sample size is mathematically insufficient for high-assurance $10^{-3}$ claims.
2. **Resolution Ingestion Barrier:**
   * Severe downsampling ($32\times 32$ px) induces a $54.0\%$ FTA rate and discrimination inversion ($\text{AUC} = 0.4518$). Applications must enforce an ingestion gate rejecting probe faces below $80\times 80$ px.
3. **Threshold Recalibration Requirement:**
   * A threshold calibrated on unconstrained frontal data ($\tau \approx 0.3132$) must never be transferred to demographically matched deployments without native recalibration to prevent an $8.9\times$ surge in False Acceptance Rate.

