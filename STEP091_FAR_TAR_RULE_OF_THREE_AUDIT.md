# FACECORE AI — STEP 09.1
## STATISTICAL AUDIT: FAR, TAR, AND RULE OF THREE EVALUATION

**Audit Author:** Independent Machine-Learning Evaluation Auditor & Statistical Researcher  
**Execution Timestamp:** 2026-11-02T15:31:00Z  
**Target Specifications:** ISO/IEC 19795-1 Biometric Performance Testing, NIST SP 800-244, Wayman (1999) Rule of Three, Exact Clopper-Pearson Binomial Confidence Intervals.

---

### 1. Mathematical Definitions & Operational Estimators

In biometric verification, error rates are calculated across strictly partitioned genuine and impostor comparison sets:

$$\text{FAR}(\tau) = \frac{\text{False Acceptances}(\tau)}{N_{\text{imp}}} = \frac{\sum_{j=1}^{N_{\text{imp}}} \mathbb{I}(s_j \ge \tau)}{N_{\text{imp}}}$$

$$\text{FRR}(\tau) = \frac{\text{False Rejections}(\tau)}{N_{\text{gen}}} = \frac{\sum_{i=1}^{N_{\text{gen}}} \mathbb{I}(s_i < \tau)}{N_{\text{gen}}}$$

$$\text{TAR}(\tau) = 1 - \text{FRR}(\tau) = \frac{\sum_{i=1}^{N_{\text{gen}}} \mathbb{I}(s_i \ge \tau)}{N_{\text{gen}}}$$

Every claim of an operating point must explicitly distinguish:
1. **Empirical Discrete Observed Rate:** Direct observed ratio of discrete counts $\frac{k}{N}$.
2. **ROC-Interpolated Rate:** Continuous linear or spline interpolation along the ROC curve between discrete operating points.
3. **Statistical Upper Confidence Bound:** The upper confidence limit of the true underlying operational error rate at a specified confidence level $(1 - \alpha)$.
4. **Rule of Three Boundary:** The sample size threshold required such that zero observed failures yields a 95% upper bound $\le p$.

---

### 2. Forensic Investigation of the Reported LFW Operating Point

In STEP 09 reporting, an operating point was cited as:
$$\text{"TAR @ FAR = 0.1\%: 98.80\% at threshold } \tau = 0.3423"$$

#### 2.1 Forensic Verification of Stored Telemetry
Inspection of `backend/data/step09_results/lfw_raw_scores.json` ($N_{\text{imp}} = 3,000$, $N_{\text{gen}} = 3,000$) reveals:

```python
# Impostor scores sitting at or above candidate thresholds:
Rank 1: 0.40514  (Pair: fold_7_imp_Jean-David_Levitte_0001_Kofi_Annan_0001)
Rank 2: 0.36625  (Pair: fold_2_imp_Jacques_Chirac_0028_John_Howard_0010)
Rank 3: 0.35916  (Pair: fold_0_imp_Tony_Blair_0099_Bill_Simon_0001)
Rank 4: 0.34231  (Pair: fold_9_imp_George_W_Bush_0428_Colin_Powell_0072)
```

At threshold $\tau = 0.34231$:
* **False Acceptances (Numerator):** $4$
* **Total Impostor Trials (Denominator):** $3,000$
* **Observed Empirical FAR:**
  $$\text{FAR} = \frac{4}{3,000} = 0.001333 \quad (\mathbf{0.1333\%})$$
* **True Acceptances (Numerator):** $2,964$
* **Total Genuine Trials (Denominator):** $3,000$
* **Observed Empirical TAR:**
  $$\text{TAR} = \frac{2,964}{3,000} = 0.988000 \quad (\mathbf{98.80\%})$$

#### 2.2 Audit Finding & Violation Classification
* **Defect:** Labeling an operating point as **"TAR @ FAR = 0.1%"** when the measured empirical FAR is **$0.1333\%$** is mathematically inaccurate. $0.1333\%$ exceeds the target ceiling by **$+33.3\%$ relative error**.
* **Audit Verdict:** The claim *"TAR @ FAR=0.1% is 98.80% at $\tau=0.3423$"* is classified as **`INCORRECT`**.

#### 2.3 Mathematical Correction for Strict FAR $\le 0.1000\%$
To guarantee that the empirical FAR does not exceed the target ceiling of $\alpha = 0.001000$ ($0.1000\%$):
$$\text{False Acceptances} \le \lfloor \alpha \cdot N_{\text{imp}} \rfloor = \lfloor 0.001000 \times 3,000 \rfloor = 3$$

The 3rd highest impostor score is **$0.35916$**. Setting the threshold at $\tau = 0.35916$:
* **False Acceptances:** $3 / 3,000$
* **Observed Empirical FAR:** $\mathbf{0.1000\%}$ ($0.001000 \le 0.001000$)
* **False Rejections:** $45 / 3,000$
* **Observed Empirical FRR:** $\mathbf{1.5000\%}$ ($0.015000$)
* **True Empirical TAR:**
  $$\text{TAR} = \frac{2,955}{3,000} = \mathbf{98.50\%} \quad (0.985000)$$

---

### 3. Exact Clopper-Pearson Binomial Confidence Intervals

Because biometric errors follow a Binomial distribution $\text{Binomial}(N, p)$, normal Gaussian approximations are invalid at low event counts. We compute exact Clopper-Pearson intervals by inverting the binomial CDF:

$$\sum_{i=k}^N \binom{N}{i} p_{\text{lower}}^i (1 - p_{\text{lower}})^{N-i} = \frac{\alpha}{2}$$

$$\sum_{i=0}^k \binom{N}{i} p_{\text{upper}}^i (1 - p_{\text{upper}})^{N-i} = \frac{\alpha}{2}$$

#### 3.1 Empirical Confidence Intervals on LFW Impostor Comparisons ($N = 3,000$)

| Operating Condition | Threshold ($\tau$) | Observed False Accepts | Observed Empirical FAR | Exact 95% Clopper-Pearson CI (FAR) | True Acceptances | Observed Empirical TAR | Exact 95% Clopper-Pearson CI (TAR) | Verification Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Strict Target $\text{FAR} \le 0.10\%$** | $0.35916$ | **$3 / 3,000$** | **$0.1000\%$** | **$[0.0206\%, 0.2920\%]$** | $2,955 / 3,000$ | **$98.50\%$** | $[98.01\%, 98.90\%]$ | `VERIFIED` |
| **STEP 09 Point ($\tau = 0.3423$)** | $0.34231$ | **$4 / 3,000$** | **$0.1333\%$** | **$[0.0363\%, 0.3410\%]$** | $2,964 / 3,000$ | **$98.80\%$** | $[98.35\%, 99.16\%]$ | `VERIFIED WITH LIMITATIONS` (FAR > 0.1%) |
| **Target $\text{FAR} \le 1.00\%$** | $0.29309$ | **$30 / 3,000$** | **$1.0000\%$** | **$[0.6757\%, 1.4245\%]$** | $2,978 / 3,000$ | **$99.27\%$** | $[98.90\%, 99.54\%]$ | `VERIFIED` |
| **Target $\text{FAR} \le 5.00\%$** | $0.22770$ | **$150 / 3,000$** | **$5.0000\%$** | **$[4.2477\%, 5.8416\%]$** | $2,988 / 3,000$ | **$99.60\%$** | $[99.31\%, 99.79\%]$ | `VERIFIED` |
| **Target $\text{FAR} \le 10.00\%$** | $0.20134$ | **$300 / 3,000$** | **$10.0000\%$** | **$[8.9492\%, 11.1295\%]$** | $2,990 / 3,000$ | **$99.67\%$** | $[99.39\%, 99.84\%]$ | `VERIFIED` |

---

### 4. Mathematical Origin of the Rule of Three

The **Rule of Three** (Wayman, 1999; NIST SP 800-244) states that if zero errors occur in $N$ independent trials, the 95% upper confidence bound on the true error rate is approximately:

$$p_{\text{upper}} \approx \frac{3}{N}$$

#### 4.1 Rigorous Mathematical Derivation
Let $X \sim \text{Binomial}(N, p)$ be the number of false acceptances. If $X = 0$:
$$P(X = 0) = (1 - p)^N$$

To establish a one-sided $95\%$ upper confidence bound $p_{\text{upper}}$:
$$(1 - p_{\text{upper}})^N = \alpha = 0.05$$
Taking natural logarithms:
$$N \ln(1 - p_{\text{upper}}) = \ln(0.05)$$

Using the first-order Taylor series approximation $\ln(1 - p) \approx -p$ (valid for small $p \ll 1$):
$$-N p_{\text{upper}} \approx \ln(0.05) \approx -2.995732$$
$$p_{\text{upper}} \approx \frac{2.995732}{N} \approx \frac{3}{N}$$

For exact calculation without Taylor approximation:
$$p_{\text{upper}}^{\text{exact}} = 1 - (0.05)^{1/N}$$

#### 4.2 Application to Corpus Scales
* For **LFW Canonical** ($N_{\text{imp}} = 3,000$):
  $$p_{\text{upper}}^{\text{approx}} = \frac{3}{3,000} = 0.001000 \quad (0.1000\%)$$
  $$p_{\text{upper}}^{\text{exact}} = 1 - (0.05)^{1/3000} = 0.0009981 \quad (0.0998\%)$$
  **Conclusion:** LFW with $3,000$ impostor pairs satisfies the sample size requirement to validate $\text{FAR} \le 0.10\%$ with 95% confidence.

* For **CALFW Resolvable Subset** ($N_{\text{imp}} = 1,564$):
  $$p_{\text{upper}}^{\text{approx}} = \frac{3}{1,564} = 0.001918 \quad (0.1918\%)$$
  $$p_{\text{upper}}^{\text{exact}} = 1 - (0.05)^{1/1564} = 0.001913 \quad (0.1913\%)$$
  **Conclusion:** Because $1,564 < 3,000$, zero false accepts on CALFW only establishes an upper bound of $\approx 0.19\%$, which is mathematically insufficient to validate target $\text{FAR} = 0.10\%$.

* For **CPLFW Resolvable Subset** ($N_{\text{imp}} = 1,550$):
  $$p_{\text{upper}}^{\text{approx}} = \frac{3}{1,550} = 0.001935 \quad (0.1935\%)$$
  **Conclusion:** Sample size is mathematically underpowered for $\text{FAR} \le 0.10\%$.

---

### 5. Summary of Corrected Claims

| Original STEP 09 Claim | Numerator / Denominator | Historical Claimed Value | Recalculated Exact Value | Exact 95% Binomial CI | Audit Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LFW TAR @ FAR 0.1%** | $4 / 3,000$ (FA), $2,964 / 3,000$ (TA) | $98.80\%$ at FAR $\le 0.1\%$ | $\text{FAR} = \mathbf{0.1333\%}$ (Exceeds 0.1%) | FAR: $[0.0363\%, 0.3410\%]$ | `INCORRECT` |
| **LFW Strict TAR @ FAR 0.1%** | $3 / 3,000$ (FA), $2,955 / 3,000$ (TA) | Not reported | $\text{TAR} = \mathbf{98.50\%}$ at $\text{FAR} = \mathbf{0.1000\%}$ | TAR: $[98.01\%, 98.90\%]$ | `VERIFIED` |
| **CALFW TAR @ FAR 0.1%** | $1 / 1,564$ (FA), $810 / 860$ (TA) | $94.54\%$ | $\text{TAR} = \mathbf{94.19\%}$ ($\tau = 0.4830$) | TAR: $[92.39\%, 95.66\%]$ | `VERIFIED WITH LIMITATIONS` (Underpowered N=1,564) |
| **CPLFW TAR @ FAR 0.1%** | $1 / 1,550$ (FA), $903 / 944$ (TA) | $96.08\%$ | $\text{TAR} = \mathbf{95.66\%}$ ($\tau = 0.4581$) | TAR: $[94.17\%, 96.86\%]$ | `VERIFIED WITH LIMITATIONS` (Underpowered N=1,550) |

