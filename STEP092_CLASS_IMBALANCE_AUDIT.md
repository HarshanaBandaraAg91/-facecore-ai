# FACECORE AI — STEP 09.2: CLASS IMBALANCE & SAMPLING BIAS AUDIT
**Phase:** Step 09.2 Independent Forensic Audit & Operating-Point Reliability  
**Date:** November 2026  
**Auditor:** Independent Machine-Learning Evaluation Auditor & Statistical Researcher  
**Status:** Completed & Forensically Quantified  

---

## 1. Executive Summary & Forensic Discovery

The official evaluation protocols for both **CALFW** (Cross-Age LFW) and **CPLFW** (Cross-Pose LFW) were designed with a perfectly balanced $1:1$ class distribution:
- **Official Specification:** 3,000 genuine pairs and 3,000 impostor pairs ($N = 6,000$, $50.0\%$ genuine prevalence).

However, an independent audit of the locally evaluated corpora revealed substantial **class prevalence distortion**:
- **CALFW Evaluated Corpus:** 860 Genuine ($35.48\%$) vs. 1,564 Impostor ($64.52\%$). Imbalance Ratio = **$1.82 : 1$**.
- **CPLFW Evaluated Corpus:** 944 Genuine ($37.85\%$) vs. 1,550 Impostor ($62.15\%$). Imbalance Ratio = **$1.64 : 1$**.

### Why This Matters Scientifically
Because SFace exhibits higher specificity on impostors ($\text{TNR} > 99.3\%$) than sensitivity on challenging cross-age/cross-pose genuine pairs ($\text{TPR} \approx 98.1\% - 98.6\%$), weighting the evaluation corpus toward the impostor class **biases ordinary accuracy upward**.

Reporting ordinary accuracy on an imbalanced subset without disclosure creates a false impression of higher verification capability.

---

## 2. Root Cause Analysis: Web Scraping Attrition

The discrepancy between the official 6,000-pair protocols and the locally resolvable subsets ($2,424$ for CALFW, $2,494$ for CPLFW) stems from the dataset construction methodology:
1. **Supplementary Web Crawling:** CALFW and CPLFW researchers collected additional images beyond base LFW to find celebrities at different ages (CALFW) or extreme yaw angles (CPLFW).
2. **Broken Link Attrition:** Over time, URLs hosting the supplementary images rotted or became inaccessible.
3. **Asymmetric Impact on Classes:**
   - **Genuine pairs** required finding the *exact same identity* in both the base set and supplementary set. If a supplementary image failed to download, the entire genuine pair became unresolvable.
   - **Impostor pairs** could frequently be formed using pairs of existing, readily available base LFW images.
4. **Result:** Genuine pairs suffered a **$71.3\%$ attrition rate** (only $860 / 3,000$ resolved in CALFW), whereas impostor pairs suffered only a **$47.9\%$ attrition rate** ($1,564 / 3,000$ resolved).

---

## 3. Ordinary vs. Balanced Metric Dissection

When class prevalence deviates from $50\%$, ordinary accuracy is a weighted average:
$$\text{Accuracy}_{\text{ordinary}} = p_{\text{gen}} \cdot \text{TPR} + (1 - p_{\text{gen}}) \cdot \text{TNR}$$
where $p_{\text{gen}}$ is the genuine prevalence.

To eliminate prevalence bias, the biometric evaluation standard requires **Balanced Accuracy**:
$$\text{Accuracy}_{\text{balanced}} = \frac{\text{TPR} + \text{TNR}}{2} = \frac{\text{Recall} + \text{Specificity}}{2}$$

### Comparative Forensic Evaluation Table:

| Metric | CALFW ($N = 2,424$) | CPLFW ($N = 2,494$) | Reference LFW ($N = 6,000$) |
|:---|:---:|:---:|:---:|
| **Total Evaluated Pairs** | 2,424 | 2,494 | 6,000 |
| Genuine Pairs ($N_{\text{gen}}$) | 860 ($35.48\%$) | 944 ($37.85\%$) | 3,000 ($50.00\%$) |
| Impostor Pairs ($N_{\text{imp}}$) | 1,564 ($64.52\%$) | 1,550 ($62.15\%$) | 3,000 ($50.00\%$) |
| Class Imbalance Ratio ($N_{\text{imp}} : N_{\text{gen}}$) | **$1.82 : 1$** | **$1.64 : 1$** | **$1.00 : 1$** |
| True Positives ($\text{TP}$) | 848 | 926 | 2,983 |
| False Negatives ($\text{FN}$) | 12 | 18 | 17 |
| True Negatives ($\text{TN}$) | 1,554 | 1,539 | 2,987 |
| False Positives ($\text{FP}$) | 10 | 11 | 13 |
| **Genuine Recall / TPR** | **$98.605\%$** | **$98.093\%$** | **$99.433\%$** |
| False Rejection Rate ($\text{FRR}$) | $1.395\%$ | $1.907\%$ | $0.567\%$ |
| **Impostor Rejection / TNR** | **$99.361\%$** | **$99.290\%$** | **$99.567\%$** |
| False Acceptance Rate ($\text{FAR}$) | $0.639\%$ | $0.710\%$ | $0.433\%$ |
| **Precision / PPV** | **$98.834\%$** | **$98.826\%$** | **$99.566\%$** |
| **F1 Score** | **$0.98719$** | **$0.98458$** | **$0.99500$** |
| **Ordinary Accuracy** | **$99.092\%$** | **$98.837\%$** | **$99.500\%$** |
| **Balanced Accuracy** | **$98.983\%$** | **$98.692\%$** | **$99.500\%$** |
| **Upward Skew Bias ($\Delta$)** | **$+0.109\%$** | **$+0.145\%$** | **$0.000\%$** |

### Key Forensic Takeaways:
1. **Upward Skew in Ordinary Accuracy:** Ordinary accuracy overstates actual balanced performance by $+0.109\%$ on CALFW and $+0.145\%$ on CPLFW.
2. **True Aging Penalty:** At the native threshold ($\tau = 0.3872$), true genuine recall on CALFW is **$98.605\%$** (compared to $99.433\%$ on frontal LFW), reflecting an aging-induced false rejection rate of $1.395\%$ ($2.46\times$ higher than frontal).
3. **True Pose Penalty:** On CPLFW, true genuine recall is **$98.093\%$**, reflecting a pose-induced false rejection rate of $1.907\%$ ($3.36\times$ higher than frontal).

---

## 4. Per-Fold Class Distribution Forensic Check

An audit of the 10 cross-validation folds in both datasets confirms that the class imbalance was distributed across all 10 folds:

### CALFW Per-Fold Distribution:
- Genuine pairs per fold: range $[68, 101]$, mean $= 86.0 \pm 10.4$.
- Impostor pairs per fold: range $[139, 172]$, mean $= 156.4 \pm 9.8$.
- Impostor proportion per fold: range $[60.2\%, 70.8\%]$.

### CPLFW Per-Fold Distribution:
- Genuine pairs per fold: range $[79, 109]$, mean $= 94.4 \pm 9.1$.
- Impostor pairs per fold: range $[139, 169]$, mean $= 155.0 \pm 8.7$.
- Impostor proportion per fold: range $[58.1\%, 66.8\%]$.

Because every single fold exhibited an impostor majority of $\approx 60\% - 70\%$, standard cross-validation averages without sample weighting were consistently skewed.

---

## 5. Audit Recommendations & Reporting Policy

1. **Mandatory Balanced Accuracy Reporting:** In all future benchmark summaries, dashboards, and API endpoints, **Balanced Accuracy** must be displayed alongside ordinary accuracy whenever class prevalence is not exactly $50.0\%$.
2. **Explicit Sample Size and Prevalence Disclosure:** Every evaluation report must clearly state:
   - Evaluated genuine pair count and prevalence.
   - Evaluated impostor pair count and prevalence.
   - Genuine Recall ($\text{TPR}$) and Impostor Specificity ($\text{TNR}$) independently.
3. **No Generalization Claims from Unbalanced Subsets:** Claims regarding cross-age and cross-pose generalization must be explicitly qualified as evaluated on the local resolvable subsets ($N=2,424$ and $N=2,494$), not the complete 6,000-pair official corpus.

