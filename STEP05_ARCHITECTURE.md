# FACECORE AI &mdash; STEP 05 ARCHITECTURAL SPECIFICATION

**Title:** Reproducible Facial Model Benchmarking Framework Architecture & Evaluation Protocol  
**Author:** Senior Machine-Learning Evaluation Engineer & Full-Stack Biometric Architect  
**Status:** Approved for Implementation  
**Phase:** STEP 05 &mdash; Dataset Discovery and Facial Model Benchmarking Framework  

---

## 1. System Overview & Isolation Boundary

The Benchmarking Framework is designed as a standalone, modular evaluation subsystem located in [`backend/app/benchmarks/`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/backend/app/benchmarks/). 

### Core Architectural Guarantees:
1. **Zero Impact on Production Pipeline:** The operational pairwise comparison engine (`RealFacialEmbeddingEngine` in `real_engine.py`) and standard endpoints (`/api/validate-image`, `/api/compare`) remain completely untouched and unmodified.
2. **Model Weight Invariance:** SFace (SphereFace2) model weights and the 128-dimensional unit hyperspherical vector representation are strictly preserved.
3. **Identity-Disjoint Isolation:** Training, validation, and test splits are strictly separated by subject identity. No individual's images can span both validation and test sets.
4. **Validation-Only Threshold Calibration:** Thresholds are optimized exclusively on validation folds. The test partition remains locked and untouched until the calibrated threshold is evaluated.
5. **Anti-Fabrication & Scientific Honesty:**
   - Similarity scores represent latent vector distances, never identity probabilities. An 85% similarity score must **never** be presented as an "85% identity probability."
   - When benchmarks are unrun, interfaces show `UNRUN` with zero fabricated percentages.
6. **Ephemeral Privacy:** Biometric images and raw embeddings are processed ephemerally in RAM and immediately released. Only statistical aggregates (ROC points, FAR/FRR distributions, confusion matrices, and run configurations) are persisted.

---

## 2. Component Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │          FRONTEND (REACT + TS)               │
                    │   BenchmarksView (Cyber-Intelligence UI)     │
                    │  - Dataset Registry & Verification Status    │
                    │  - Interactive SVG ROC & FAR/FRR Charts      │
                    │  - Confusion Matrix & Performance Metrics    │
                    │  - Controlled Robustness Comparison Matrix   │
                    │  - JSON & CSV Export Generators              │
                    └──────────────────────┬───────────────────────┘
                                           │ HTTP REST API
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │      FASTAPI BENCHMARK ROUTER                │
                    │     /api/benchmarks/datasets                 │
                    │     /api/benchmarks/run                      │
                    │     /api/benchmarks/history                  │
                    │     /api/benchmarks/runs/{id}                │
                    │     /api/benchmarks/runs/{id}/export/{fmt}   │
                    └──────┬───────────────────────┬───────────────┘
                           │                       │
                           ▼                       ▼
            ┌────────────────────────────┐  ┌────────────────────────────┐
            │   DATASET MANIFEST ENGINE   │  │   BENCHMARK RUNNER CORE    │
            │   (manifest.py)            │  │   (runner.py)              │
            │ - Manifest parsers         │  │ - Execution lifecycle      │
            │ - Identity-disjoint split  │  │ - Real SFace engine caller │
            │ - Leakage & duplicate check│  │ - 10-fold cross-validation │
            │ - Fixture pair generators  │  │ - In-memory history cache  │
            └────────────────────────────┘  └──────────────┬─────────────┘
                                                           │
                                   ┌───────────────────────┴───────────────────────┐
                                   ▼                                               ▼
                    ┌────────────────────────────┐                  ┌────────────────────────────┐
                    │    EVALUATION METRICS      │                  │    ROBUSTNESS SUITE        │
                    │    (metrics.py)            │                  │    (robustness.py)         │
                    │ - ROC & Trapezoidal AUC    │                  │ - Controlled Perturbations:│
                    │ - EER & Intersection Point │                  │   * Gaussian Blur (1.5, 3) │
                    │ - FAR, FRR, TAR@FAR points │                  │   * Downsampling (64p, 32p)│
                    │ - Confusion Matrix         │                  │   * Extreme Light (0.4,1.8)│
                    │ - 95% Bootstrap CI         │                  │   * Synthetic Occlusion    │
                    │ - JSON & CSV Exporters     │                  │   * JPEG Compression (25,10│
                    └────────────────────────────┘                  └────────────────────────────┘
```

---

## 3. Mathematical Specifications & Metric Formulations

### 3.1. Pairwise Similarity Calculation
Given a pair of facial images $(I_a, I_b)$, the engine extracts 128-dimensional unit embeddings $\mathbf{u}, \mathbf{v} \in \mathbb{R}^{128}$ where $\|\mathbf{u}\|_2 = 1.0$ and $\|\mathbf{v}\|_2 = 1.0$.

Cosine similarity is computed as:
$$s(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2} = \mathbf{u} \cdot \mathbf{v} \in [-1.0, 1.0]$$

Given a decision threshold $\tau \in [-1.0, 1.0]$:
$$\hat{y}(s, \tau) = \begin{cases} 1 & \text{if } s \ge \tau \quad (\text{Classified as Genuine / Match}) \\ 0 & \text{if } s < \tau \quad (\text{Classified as Impostor / Non-Match}) \end{cases}$$

### 3.2. Error Rates & Operating Points
Let $N_{\text{gen}}$ be the number of genuine pairs ($y = 1$) and $N_{\text{imp}}$ be the number of impostor pairs ($y = 0$).

1. **False Acceptance Rate (FAR):** The proportion of impostor pairs incorrectly classified as genuine:
   $$\text{FAR}(\tau) = \frac{\sum_{i \in \text{Imp}} \mathbb{I}(s_i \ge \tau)}{N_{\text{imp}}} = \frac{\text{FP}}{\text{FP} + \text{TN}}$$
2. **False Rejection Rate (FRR):** The proportion of genuine pairs incorrectly classified as impostors:
   $$\text{FRR}(\tau) = \frac{\sum_{i \in \text{Gen}} \mathbb{I}(s_i < \tau)}{N_{\text{gen}}} = \frac{\text{FN}}{\text{TP} + \text{FN}}$$
3. **True Acceptance Rate (TAR):**
   $$\text{TAR}(\tau) = 1 - \text{FRR}(\tau) = \frac{\text{TP}}{\text{TP} + \text{FN}}$$
4. **Equal Error Rate (EER):** The threshold $\tau^*$ at which the False Acceptance Rate equals the False Rejection Rate:
   $$\tau^* = \arg\min_\tau |\text{FAR}(\tau) - \text{FRR}(\tau)|, \quad \text{EER} = \frac{\text{FAR}(\tau^*) + \text{FRR}(\tau^*)}{2}$$
5. **TAR at Predefined FAR Operating Points:** Standard biometrics evaluation requires measuring TAR at fixed operational FAR thresholds (e.g., $\text{FAR} \le 0.1, 0.01, 0.001$). For a given target $\alpha$:
   $$\tau_\alpha = \min \{ \tau : \text{FAR}(\tau) \le \alpha \}, \quad \text{TAR}@\text{FAR}=\alpha = \text{TAR}(\tau_\alpha)$$

### 3.3. Receiver Operating Characteristic (ROC) & AUC
The ROC curve plots $\text{TAR}(\tau)$ (vertical axis) versus $\text{FAR}(\tau)$ (horizontal axis) as threshold $\tau$ varies from $+1.0$ down to $-1.0$.

The Area Under the ROC Curve (ROC-AUC) is calculated using numerical trapezoidal integration across $M$ sorted operational thresholds:
$$\text{AUC} = \sum_{k=1}^{M-1} \frac{\text{TAR}_{k+1} + \text{TAR}_k}{2} \cdot (\text{FAR}_{k+1} - \text{FAR}_k)$$

### 3.4. Statistically Valid Confidence Intervals
To report uncertainty without making unwarranted Gaussian assumptions, the framework implements **non-parametric Bootstrap Resampling**:
- $B = 1,000$ bootstrap iterations.
- In each iteration $b \in \{1, \dots, B\}$, sample with replacement $N$ pairs, compute metric $\hat{\theta}^{*b}$ (e.g. $\text{EER}^{*b}$, $\text{AUC}^{*b}$).
- The 95% Confidence Interval is determined by the empirical percentiles:
  $$\text{CI}_{95\%} = \left[ \hat{\theta}^*_{(0.025)}, \, \hat{\theta}^*_{(0.975)} \right]$$

---

## 4. Cross-Validation & Anti-Leakage Protocol

### 4.1. 10-Fold Identity-Disjoint Partitioning
Following the canonical LFW evaluation protocol:
1. The dataset pairs are partitioned into $K = 10$ distinct folds.
2. **Leakage Verification:** For any pair $(I_a, I_b)$ belonging to subject identities $(\text{ID}_a, \text{ID}_b)$ assigned to Fold $k$, no pair in any other Fold $j \neq k$ may share either $\text{ID}_a$ or $\text{ID}_b$.
3. **Threshold Calibration:**
   - In fold round $k \in \{1, \dots, 10\}$:
   - Combine the other 9 folds as the **Validation Set** ($D_{\text{val}} = \bigcup_{j \ne k} D_j$).
   - Determine optimal threshold $\tau_k^*$ that maximizes classification accuracy on $D_{\text{val}}$:
     $$\tau_k^* = \arg\max_\tau \frac{\text{TP}_{\text{val}}(\tau) + \text{TN}_{\text{val}}(\tau)}{|D_{\text{val}}|}$$
   - Apply threshold $\tau_k^*$ to the strictly held-out **Test Fold** $D_k$ to record test accuracy $A_k$.
4. **Final Unbiased Score:** The overall cross-validated accuracy is:
   $$\bar{A} = \frac{1}{K} \sum_{k=1}^K A_k, \quad \sigma_A = \sqrt{\frac{1}{K-1} \sum_{k=1}^K (A_k - \bar{A})^2}$$

---

## 5. Controlled Robustness Evaluation Framework

Biometric accuracy reported solely on high-resolution, centered, well-lit images gives a misleading perception of real-world capability. The robustness framework subjects the model to six controlled, reproducible perturbations:

| Condition Name | Perturbation Description | Mathematical Implementation | Purpose |
| :--- | :--- | :--- | :--- |
| **Baseline (Reference)** | Unaltered image pair | Native image dimensions and color | Reference operating point |
| **Gaussian Blur (Light)** | Moderate sensor/optical blur | $5\times 5$ Gaussian kernel, $\sigma = 1.5$ | Simulated slight motion/focus error |
| **Gaussian Blur (Heavy)** | Severe defocus blur | $9\times 9$ Gaussian kernel, $\sigma = 3.0$ | Out-of-focus capture evaluation |
| **Low Resolution (64p)** | CCTV downsampling | Bilinear downsample to $64\times 64$, upsample | Sensor distance/low pixel density |
| **Low Resolution (32p)** | Extreme surveillance crop | Bilinear downsample to $32\times 32$, upsample | Extreme low-resolution threshold |
| **Low Illumination** | Dark environment underexposure | Gamma scale $I' = 255 \cdot (I / 255)^{1.8}$ | Night/shadowed environment |
| **High Glare / Overexposure**| Specular wash / direct flash | Gamma scale $I' = 255 \cdot (I / 255)^{0.4}$ | Harsh solar or direct flash wash |
| **Partial Occlusion (Lower)**| Lower face surgical mask simulation| Solid neutral band covering lower 35% of face | Mask / scarf tolerance |
| **Partial Occlusion (Upper)**| Eye/brow visor simulation | Dark band across eyes (25% to 50% height) | Sunglasses / visor tolerance |
| **JPEG Compression (Q25)** | Moderate lossy network encoding | JPEG encode with quality factor $Q = 25$ | Bandwidth-limited transfer |
| **JPEG Compression (Q10)** | Severe compression artifacts | JPEG encode with quality factor $Q = 10$ | Low-fidelity streaming artifacts |

> **Scientific Disclosure:** These controlled transformations simulate optical, sensor, and transmission artifacts. They do **not** represent physical 3D disguise materials, adversarial makeup, or surgical alterations.

---

## 6. API Specifications

### Endpoint Specifications

#### 1. `GET /api/benchmarks/datasets`
Returns all registered evaluation datasets and their availability/verification status.
```json
[
  {
    "dataset_id": "lfw-canonical-v1",
    "name": "Labeled Faces in the Wild (LFW)",
    "description": "Unconstrained facial verification across standard 10-fold pairs",
    "total_images": 13233,
    "total_identities": 5749,
    "total_pairs": 6000,
    "verification_status": "DATASET_VERIFIED",
    "is_available": true,
    "license": "Non-Commercial Academic Research"
  }
]
```

#### 2. `POST /api/benchmarks/run`
Executes an evaluation run using the specified configuration.
```json
{
  "dataset_id": "lfw-canonical-v1",
  "evaluate_robustness": true,
  "max_pairs": 600,
  "random_seed": 42
}
```

#### 3. `GET /api/benchmarks/history`
Returns list of completed or in-progress benchmark executions.

#### 4. `GET /api/benchmarks/runs/{run_id}`
Returns full detailed evaluation telemetry including ROC points, FAR/FRR distributions, confusion matrix, and robustness results.

#### 5. `GET /api/benchmarks/runs/{run_id}/export/{format}`
Exports the experiment report as structured JSON or pairwise evaluation CSV (`format = json | csv`).
