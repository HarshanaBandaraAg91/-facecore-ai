# FACECORE AI — STEP 11: THRESHOLD PROFILE SAFETY & DISCLOSURE AUDIT
**Document Reference:** `STEP11_THRESHOLD_POLICY_AUDIT.md`  
**Execution Date:** 2026-11-02  
**Auditor:** Senior Biometric Systems & Security Auditor / Release Engineer  
**Pipeline:** OpenCV YuNet + SFace (128-d) + Cosine Similarity  
**Components Audited:** `real_engine.py`, `ResultPanel.tsx`, `ComparisonWorkspace.tsx`, `schemas.py`  

---

## 1. Executive Summary

Phase 6 audits the scientific fidelity, safety boundaries, statistical transparency, and ethical disclosures surrounding biometric comparison scores and operating profiles in FACECORE AI. The audit verifies that cosine similarity scores are never misrepresented as probabilities or certainty ratings, operating profiles carry rigorous empirical disclosures, and users receive clear warnings regarding statistical ambiguity, demographic bias, and legal limitations.

### Safety & Disclosure Compliance Matrix

| Audit Criterion | Verification Standard | Implementation Status | Evidence / Location |
| :--- | :--- | :---: | :--- |
| **Probability Non-Equivalence** | Cosine score never called "confidence %" | **PASS** | Labeled "Normalized Display Index" with explicit note: *(NOT a match probability)*. |
| **Ambiguous Zone Alert** | Scores in $[0.28, 0.35]$ flagged | **PASS** | Prominent warning banner displayed when raw cosine falls within the critical distribution overlap. |
| **High Security Profile** | Disclosed as experimental research split | **PASS** | $\tau = 0.3600$: Explicitly noted as NOT certified for physical access control or legal identification. |
| **Balanced Profile** | LFW EER trade-off disclosed | **PASS** | $\tau = 0.3132$: Discloses Equal Error Rate crossover (FAR: 0.43%, FRR: 0.57%). |
| **High Convenience Profile** | Elevated FAR risk disclosed | **PASS** | $\tau = 0.2500$: Explicitly warns against security-sensitive use due to elevated false accept rate (~1.50%). |
| **Custom Threshold Range** | Range $[0.20, 0.45]$ boundaries guarded | **PASS** | Visual warning triggered whenever custom $\tau < 0.20$ or $\tau > 0.45$. |
| **Demographic Bias Notice** | Performance variance disclosed | **PASS** | Notice confirms potential error rate skew across skin tones, genders, and age groups. |
| **Human Review Mandate** | Anti-automated decision enforcement | **PASS** | System mandate states tool is an advisory aid; automated adverse decisions without human review prohibited. |

---

## 2. Mathematical Definition & Display Score Formulation

### 2.1 Raw Cosine Similarity
The fundamental comparison metric between two 128-dimensional unit embeddings $u, v \in \mathbb{R}^{128}$ is the inner dot product:
$$\cos(\theta) = \frac{u \cdot v}{\|u\|_2 \, \|v\|_2} \in [-1.0, 1.0]$$

> [!IMPORTANT]
> **Scientific Integrity Rule:**  
> The cosine similarity $\cos(\theta)$ is a continuous geometric angle metric on a hypersphere. It represents vector proximity, **NOT** an identity probability, posterior likelihood ratio, or Bayesian certainty percentage.

### 2.2 Normalized Display Index
To provide an intuitive visual scale without deceiving users into perceiving an odds ratio, the backend and UI apply a strictly documented linear affine transformation:
$$S_{\text{display}} = \left(\frac{\cos(\theta) + 1.0}{2.0}\right) \times 100.0$$

- An identical pair ($\cos = 1.0000$) maps to $100.0/100$.
- Orthogonal embeddings ($\cos = 0.0000$) map to $50.0/100$.
- Diametrically opposed embeddings ($\cos = -1.0000$) map to $0.0/100$.
- **Disclosure:** The frontend tag displays `Linear ((cos+1)/2)` and explicitly clarifies: *"Scaled visual metric (NOT a match probability)"*.

---

## 3. Ambiguous Zone Governance ($[0.28, 0.35]$)

Empirical score distributions on LFW, CALFW, and CPLFW establish that genuine pairs and impostor pairs overlap within the interval $\cos(\theta) \in [0.28, 0.35]$.

### UI Warning Banner
When an evaluation produces a score within this window, the UI injects a dedicated cautionary card:
```text
AMBIGUOUS SIMILARITY ZONE [0.28 – 0.35]
The raw cosine similarity falls directly within the critical margin of statistical overlap where
genuine and impostor score distributions intersect. Manual human review is strongly advised
before relying on this classification.
```

This prevents operators from treating borderline classifications near the decision threshold as conclusive facts.

---

## 4. Operating Threshold Profiles & Scientific Disclosures

FACECORE AI defines three calibrated presets alongside a fully customizable operating point:

```
+-------------------------------------------------------------------------------------------------------+
| Profile Name       | Threshold | Target FAR | Empirical TAR | 95% CI FAR Upper | Primary Risk Profile |
+-------------------------------------------------------------------------------------------------------+
| High Security      |   0.3600  |  <= 0.10%  |     98.47%    |      0.292%      | Elevated FRR (1.53%) |
| Balanced (Native)  |   0.3132  |   0.43%    |     99.43%    |      0.725%      | Equal Error (0.50%)  |
| High Convenience   |   0.2500  |  ~ 1.50%   |    > 99.90%   |      1.980%      | Elevated FAR (1.50%) |
| Custom Threshold   | [-1.0, 1] | User Def.  |   Variable    |     Variable     | Uncalibrated Risk    |
+-------------------------------------------------------------------------------------------------------+
```

### 4.1 High Security Profile ($\tau = 0.3600$)
- **Empirical Basis:** Calibrated on out-of-fold LFW View 2 splits to push false accept counts to $\le 3$ per 3,000 impostor trials.
- **Mandatory Disclosure:**
  > *"High Security profile is an experimental operating point calibrated on research datasets. It is NOT externally certified under NIST FPVTE, iBeta ISO/IEC 30107-3, or EN 50133 standards, and MUST NOT be used for unattended high-security access control, border screening, or legal identity determinations."*

### 4.2 Balanced Profile ($\tau = 0.3132$)
- **Empirical Basis:** Equal Error Rate (EER) crossover point on canonical LFW View 2.
- **Trade-off:** Minimizes total classification error on standardized benchmark photographs, with balanced False Accept Rate ($0.43\%$) and False Reject Rate ($0.57\%$).

### 4.3 High Convenience Profile ($\tau = 0.2500$)
- **Empirical Basis:** Designed for low-friction verification where rejecting a legitimate user causes unacceptable inconvenience (Target FRR $\le 0.10\%$).
- **Mandatory Disclosure:**
  > *"High Convenience profile tolerates a significantly elevated False Accept Rate (~1.50%). Roughly 1 in every 67 impostor pairs may be erroneously classified as a match. Do NOT utilize this profile in security-sensitive contexts."*

### 4.4 Custom Threshold Controls
- Accepts any floating-point threshold $\tau \in [-1.0, 1.0]$.
- **Out-of-Bounds Guard:** If $\tau < 0.20$ or $\tau > 0.45$, the UI displays a warning alerting the operator that the threshold operates outside standard benchmark ranges and induces severe error rate asymmetry.

---

## 5. Regulatory & Ethical Compliance Declarations

To adhere to emerging artificial intelligence and biometric governance frameworks (including EU AI Act high-risk biometric transparency guidelines):

1. **Demographic Bias Disclosure:**
   - The SFace and YuNet neural networks were trained on academic corpora (such as CASIA-WebFace and WiderFace).
   - Accuracy and false match rates are documented to exhibit variance across phenotypic categories, gender presentations, age brackets, and skin reflectivity (Fitzpatrick scales). Operators must not assume universal parity across all user demographics.
2. **Prohibition of Fully Automated Adverse Decisions:**
   - FACECORE AI is an analytical pair-comparison decision-support tool. It must **not** be deployed to make unilateral, fully automated adverse determinations affecting individuals' legal rights, employment, or physical freedom without qualified human verification.
3. **No External Certification Claim:**
   - The platform clearly avoids claims of governmental or third-party laboratory certification.

---

## 6. Threshold Policy Audit Verdict

### Gate Status: **PASS**
- Cosine scores are rigorously distinguished from probability values.
- Ambiguous zones ($[0.28, 0.35]$) are visually flagged.
- Operating profile trade-offs and sample-size bounds are transparently disclosed.
- Ethical and demographic bias notices are embedded across both backend API responses and frontend views.

