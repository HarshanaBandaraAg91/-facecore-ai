# FACECORE AI — STEP 09.1
## CROSS-VALIDATION INTEGRITY & SAMPLING BIAS AUDIT

**Audit Author:** Independent Machine-Learning Evaluation Auditor & Statistical Researcher  
**Execution Timestamp:** 2026-11-02T15:33:00Z  
**Primary Target:** 10-fold cross-validation partitioning, identity leakage verification, test-fold isolation invariance, and sampling bias analysis across LFW, CALFW, and CPLFW.

---

### 1. Official LFW View 2 Protocol Verification

The official LFW evaluation protocol defines a 10-fold cross-validation procedure designed to assess face verification performance under unconstrained natural variations without identity leakage.

#### 1.1 Structural Partitioning Verification
* **Total Pairs:** Exactly $6,000$ pairs parsed from `backend/data/lfw/pairs.txt`.
* **Folds:** Exactly $10$ folds numbered $0$ through $9$.
* **Per-Fold Count:** Exactly $600$ pairs per fold.
* **Per-Fold Label Balance:** Exactly $300$ genuine pairs and $300$ impostor pairs per fold.
* **Duplicate Detection:** Zero duplicate pairs detected across all folds ($0$ within-fold duplicates, $0$ across-fold duplicates).
* **Missing Images:** Exactly $0$ missing images out of $13,233$ source files.

#### 1.2 Mathematical Invariance of Test-Fold Isolation
To mathematically prove zero test leakage during threshold selection:
1. For each test fold $k \in \{0, \dots, 9\}$, the validation partition is strictly defined as $\mathcal{F}_{\text{val}} = \bigcup_{j \neq k} \text{Fold}_j$ ($5,400$ pairs).
2. The optimal decision threshold $\tau_k^*$ is selected exclusively to maximize accuracy on $\mathcal{F}_{\text{val}}$.
3. **Invariance Test:** In regression test [`test_fold_specific_threshold_isolation`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/backend/tests/test_benchmarks_step091_audit.py#L110-L135), the test fold scores and labels were completely altered to an adversarial state. The validation-selected threshold for fold $k$ remained identical to floating-point precision ($|\Delta \tau_k^*| < 10^{-12}$).
* **Audit Verdict:** Test-fold isolation on LFW Canonical is **`VERIFIED`**.

---

### 2. CALFW and CPLFW Fold Accounting & Sampling Bias Audit

Both CALFW (Cross-Age LFW) and CPLFW (Cross-Pose LFW) were constructed by BUPT/Tsinghua researchers using the identities of LFW, organized into 10 official folds of 600 pairs each ($3,000$ genuine and $3,000$ impostor pairs).

#### 2.1 Per-Fold Accounting Matrix (CALFW Resolvable Subset)

| Fold Index | Official Pairs | Local Resolved Pairs | Missing Pairs | Resolved Genuine | Resolved Impostor | Resolved Genuine % | Resolved Impostor % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Fold 0** | 600 | **234** | 366 | 79 | 155 | 33.8% | 66.2% |
| **Fold 1** | 600 | **234** | 366 | 83 | 151 | 35.5% | 64.5% |
| **Fold 2** | 600 | **232** | 368 | 85 | 147 | 36.6% | 63.4% |
| **Fold 3** | 600 | **238** | 362 | 84 | 154 | 35.3% | 64.7% |
| **Fold 4** | 600 | **244** | 356 | 81 | 163 | 33.2% | 66.8% |
| **Fold 5** | 600 | **250** | 350 | 93 | 157 | 37.2% | 62.8% |
| **Fold 6** | 600 | **281** | 319 | 110 | 171 | 39.1% | 60.9% |
| **Fold 7** | 600 | **234** | 366 | 79 | 155 | 33.8% | 66.2% |
| **Fold 8** | 600 | **252** | 348 | 87 | 165 | 34.5% | 65.5% |
| **Fold 9** | 600 | **225** | 375 | 79 | 146 | 35.1% | 64.9% |
| **TOTAL** | **6,000** | **2,424 (40.4%)** | **3,576 (59.6%)** | **860** | **1,564** | **35.5%** | **64.5%** |

#### 2.2 Per-Fold Accounting Matrix (CPLFW Resolvable Subset)

| Fold Index | Official Pairs | Local Resolved Pairs | Missing Pairs | Resolved Genuine | Resolved Impostor | Resolved Genuine % | Resolved Impostor % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Fold 0** | 600 | **244** | 356 | 89 | 155 | 36.5% | 63.5% |
| **Fold 1** | 600 | **260** | 340 | 98 | 162 | 37.7% | 62.3% |
| **Fold 2** | 600 | **222** | 378 | 88 | 134 | 39.6% | 60.4% |
| **Fold 3** | 600 | **264** | 336 | 98 | 166 | 37.1% | 62.9% |
| **Fold 4** | 600 | **238** | 362 | 88 | 150 | 37.0% | 63.0% |
| **Fold 5** | 600 | **255** | 345 | 106 | 149 | 41.6% | 58.4% |
| **Fold 6** | 600 | **248** | 352 | 101 | 147 | 40.7% | 59.3% |
| **Fold 7** | 600 | **232** | 368 | 76 | 156 | 32.8% | 67.2% |
| **Fold 8** | 600 | **277** | 323 | 103 | 174 | 37.2% | 62.8% |
| **Fold 9** | 600 | **254** | 346 | 97 | 157 | 38.2% | 61.8% |
| **TOTAL** | **6,000** | **2,494 (41.6%)** | **3,506 (58.4%)** | **944** | **1,550** | **37.9%** | **62.1%** |

---

### 3. Forensic Identification of Sampling Bias

1. **Class Imbalance Induced by Missing Web Images:**
   * In standard LFW, pairs are 50% genuine and 50% impostor.
   * To maximize age gaps and head yaw, CALFW and CPLFW creators searched the web for supplementary images of individuals who only had 1 or 2 photos in standard LFW.
   * Because those supplementary crawled images ($2,640$ for CALFW, $2,444$ for CPLFW) were never bundled into standard `lfw.tgz`, significantly more genuine pairs failed local resolution than impostor pairs.
   * Consequently, the resolved corpus shifted from a balanced **$50:50$** split to an impostor-heavy **$35.5 : 64.5$** split in CALFW and **$37.9 : 62.1$** split in CPLFW.

2. **Scientific Implications for Metric Reliability:**
   * **ROC-AUC & EER:** Because ROC-AUC and EER evaluate the false positive rate against the true positive rate across rank-ordered thresholds, they are mathematically invariant to class prior shifts. The reported **$\text{AUC} = 0.9981$** and **$\text{EER} = 1.05\%$** remain statistically robust descriptors of discrimination on the available photos.
   * **Naive Classification Accuracy:** Because accuracy $= (\text{TP} + \text{TN}) / N$, shifting the prior to $65\%$ impostors rewards models with lower false acceptance rates and penalizes models with higher false rejection rates.
   * **Generalizability Boundary:** **Under no circumstances should the 99.14% (CALFW) or 98.81% (CPLFW) subset accuracy figures be cited as the official full-benchmark accuracy.** They must be explicitly qualified as performance on the **verified 40.4% / 41.6% local subsets**.

---

### 4. Cross-Validation Audit Summary

| Benchmark Corpus | Total Folds | Folds Evaluated | Pairs / Fold Range | Genuine / Fold Range | Impostor / Fold Range | Cross-Validation Isolation | Audit Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **LFW Canonical** | 10 | 10 | Exactly 600 | Exactly 300 | Exactly 300 | Zero Leakage Invariant Confirmed | `VERIFIED` |
| **CALFW Resolvable** | 10 | 10 | 225 – 281 | 79 – 110 | 146 – 171 | Zero Leakage Invariant Confirmed | `VERIFIED WITH LIMITATIONS` (Class skew: 35.5% gen) |
| **CPLFW Resolvable** | 10 | 10 | 222 – 277 | 76 – 106 | 134 – 174 | Zero Leakage Invariant Confirmed | `VERIFIED WITH LIMITATIONS` (Class skew: 37.9% gen) |

