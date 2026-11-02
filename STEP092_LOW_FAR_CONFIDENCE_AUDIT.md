# FACECORE AI — STEP 09.2: LOW-FAR STATISTICAL CONFIDENCE AUDIT
**Phase:** Step 09.2 Independent Forensic Audit & Operating-Point Reliability  
**Date:** November 2026  
**Auditor:** Independent Machine-Learning Evaluation Auditor & Statistical Researcher  
**Status:** Completed & Statistically Proven  

---

## 1. Executive Summary & Critical Distinction

In Step 09 and Step 09.1, the evaluation reported an operational operating point of:
$$\text{FAR} = 0.1000\% \quad (3 \text{ false acceptances out of } 3,000 \text{ impostor comparisons})$$
Accompanying this was an exact 95% Clopper-Pearson confidence interval of:
$$[0.0206\%, 0.2920\%]$$

### The Critical Statistical Fallacy
A common but dangerous error in biometric reporting is conflating the **observed sample rate** with a **statistically verified population bound**. Observing $3 / 3,000$ false acceptances in a finite test corpus **does NOT establish that the population $\text{FAR} \le 0.1000\%$**.

In fact, because the 95% confidence upper bound is **$0.2920\%$**, the empirical evidence only proves with 95% confidence that the true operational false acceptance rate is **less than $\approx 0.30\%$**—nearly **THREE TIMES HIGHER** than the claimed $0.10\%$ operating point.

---

## 2. Theoretical Framework: Four Levels of Statistical Statements

To prevent misleading claims in deployment documentation, biometric evaluations must rigorously distinguish between four distinct statistical concepts:

| Level | Concept | Definition | LFW Value ($k=3, n=3000$) | Operational Interpretation |
|:---:|:---|:---|:---:|:---|
| **1** | **Observed Empirical FAR** ($\hat{p}$) | The sample proportion $\hat{p} = \frac{k}{n}$ observed in this specific benchmark run. | **$0.1000\%$** ($3 / 3,000$) | Descriptive statistic of the test corpus only. |
| **2** | **Estimated Population FAR** ($p$) | The unknown true probability parameter of the data-generating distribution. | Unknown ($p \approx 0.10\%$) | Point estimate, but carries sampling uncertainty. |
| **3** | **95% Confidence Interval** | The set of population rates $p$ for which the observed $k=3$ is not rejected at $\alpha=0.05$. | **$[0.0206\%, 0.2920\%]$** | Range of plausible true population rates. |
| **4** | **Statistically Supported Upper Bound** | The highest rate consistent with the data at the stated confidence level ($p_{\text{upper}}$). | **$0.2920\%$** | The **only** mathematically defensible guarantee for risk analysis. |

> [!CAUTION]
> **Biometric Risk Rule:** If an operational specification mandates $\text{FAR} \le 0.1000\%$ with 95% statistical confidence, a benchmark with $3 / 3,000$ false accepts **fails to qualify**, because the upper bound ($0.2920\%$) exceeds the specification by $192\%$.

---

## 3. Sample Size Requirements for Low-FAR Verification

### 3.1 The Rule of Three (Zero Observed Errors)
When testing a system where **zero** errors are observed ($k = 0$) in $n$ independent trials:
$$(1 - p)^n = 1 - (1 - \alpha) = \alpha$$
Taking natural logarithms:
$$n \ln(1 - p) = \ln(\alpha)$$
Using the first-order Taylor expansion $\ln(1 - p) \approx -p$ for small $p$:
$$-n p \approx \ln(\alpha) \implies p_{\text{upper}} \approx \frac{-\ln(\alpha)}{n}$$
For a standard 95% confidence level ($\alpha = 0.05$):
$$-\ln(0.05) \approx 2.99573 \approx 3.0 \implies p_{\text{upper}} \approx \frac{3}{n}$$
Conversely, to prove with 95% confidence that population $\text{FAR} \le p_{\text{target}}$ when **zero** errors occur, the required sample size is:
$$n \ge \frac{-\ln(0.05)}{p_{\text{target}}} \approx \frac{2.99573}{p_{\text{target}}}$$

### 3.2 Non-Zero Error Rates (Binomial Inversion)
If the system operates with a realistic non-zero error rate $r = \frac{k}{n} > 0$, to ensure that the 95% upper bound satisfies $p_{\text{upper}} \le p_{\text{target}}$, the required sample size increases substantially:
$$p_{\text{upper}} \approx r + z_{1 - \alpha/2} \sqrt{\frac{r(1 - r)}{n}} \le p_{\text{target}}$$
$$n \ge \frac{z_{1 - \alpha/2}^2 \cdot r(1 - r)}{(p_{\text{target}} - r)^2}$$
where $z_{0.975} = 1.95996$.

### Required Sample Size Table:

| Target FAR Claim ($p_{\text{target}}$) | Expected System Rate ($r$) | Required Impostor Comparisons ($n$) | Supported by LFW ($N_{\text{imp}} = 3,000$)? | Status |
|:---|:---:|:---:|:---:|:---:|
| **$\text{FAR} \le 1.00\%$** ($0.01$) | 0.0% (0 errors) | **300** | Yes ($10\times$ headroom) | `STATISTICALLY VALIDATED` |
| $\text{FAR} \le 1.00\%$ ($0.01$) | 0.5% ($k = 0.005n$) | **768** | Yes ($3.9\times$ headroom) | `STATISTICALLY VALIDATED` |
| **$\text{FAR} \le 0.10\%$** ($0.001$) | 0.0% (0 errors) | **2,996** | Borderline ($N=3,000$ requires 0 errors) | `CONDITIONAL (0 Errors Required)` |
| $\text{FAR} \le 0.10\%$ ($0.001$) | 0.05% ($k = 0.0005n$) | **7,679** | **No** (Deficit of 4,679 pairs) | `NOT SUPPORTED AT r=0.05%` |
| $\text{FAR} \le 0.10\%$ ($0.001$) | 0.07% ($k = 0.0007n$) | **29,858** | **No** (Deficit of 26,858 pairs) | `NOT SUPPORTED AT r=0.07%` |
| **$\text{FAR} \le 0.01\%$** ($0.0001$) | 0.0% (0 errors) | **29,958** | **No** ($10\times$ sample deficit) | **`NOT STATISTICALLY SUPPORTED`** |
| $\text{FAR} \le 0.01\%$ ($0.0001$) | 0.005% | **76,798** | **No** ($25\times$ sample deficit) | **`NOT STATISTICALLY SUPPORTED`** |

---

## 4. Formal Classification of Unsupported Claims

### Claim 1: "TAR at FAR = 0.01% on LFW is XX%"
- **Mathematical Fact:** In LFW View 2, there are exactly $3,000$ impostor pairs.
- **Granularity Limit:** A single false acceptance ($k = 1$) represents an empirical rate of:
  $$\frac{1}{3,000} = 0.000333 = 0.0333\%$$
  which is **$3.33\times$ larger** than the target rate of $0.01\%$.
- **Audit Verdict:** **`NOT STATISTICALLY SUPPORTED`**. It is mathematically impossible to calibrate or evaluate a $0.01\%$ FAR operating point on a corpus of 3,000 impostor pairs. Any reported TAR at $\text{FAR} \le 0.01\%$ is an unverified extrapolation.

### Claim 2: "FAR is 0.1% at threshold 0.35916"
- **Audit Verdict:** The observed sample rate on LFW was $0.1000\%$ ($3 / 3,000$). However, the 95% confidence upper bound is **$0.2920\%$**.
- **Corrected Claim:** *"On the 3,000 LFW impostor pairs, SFace achieved 3 false acceptances ($\text{FAR} = 0.1000\%$). The 95% Clopper-Pearson confidence interval is $[0.0206\%, 0.2920\%]$. The population FAR is supported only to an upper bound of $0.2920\%$."*

---

## 5. Paired Comparison Correlation and Effective Degrees of Freedom

In standard LFW View 2 evaluation, $3,000$ impostor pairs are generated from several hundred unique identities. As a consequence:
1. **Identity Re-Use:** Multiple impostor pairs involve images from the same underlying individual (e.g., George W. Bush appears in numerous pairs).
2. **Correlation of Errors:** If a particular individual's facial morphology happens to yield elevated cosine similarity against another subject, all pairs containing those images are statistically correlated.
3. **Reduction of Effective Sample Size:** The assumption of independent Bernoulli trials in the Clopper-Pearson interval is strictly an upper bound on statistical power. The **effective degrees of freedom ($N_{\text{eff}}$)** is smaller than $3,000$:
   $$N_{\text{eff}} = \frac{N}{1 + (m - 1) \rho}$$
   where $m$ is the average number of pairs per identity and $\rho$ is the intra-identity correlation coefficient.
4. **Impact:** Paired comparison correlation **widens** the true confidence interval even further beyond $[0.0206\%, 0.2920\%]$, reinforcing the imperative that low-FAR claims require much larger, diverse corpora.

---

## 6. Audit Conclusion & Recommendations

1. **Mandatory Reporting of Upper Bounds:** Every reported FAR must be accompanied by its 95% confidence upper bound.
2. **De-listing of $\text{FAR} \le 0.01\%$ from LFW Reports:** Remove all operational claims for $\text{FAR} \le 0.01\%$ on LFW and mark them as `NOT STATISTICALLY SUPPORTED (Requires N >= 30,000)`.
3. **Conservative Operating Margin:** For production deployment targeting $\text{FAR} \le 0.10\%$, calibrate the operational threshold using the upper confidence bound or enforce $\text{FA}_{\text{val}} \le 1$ to guarantee real-world safety.

