# FACECORE AI &mdash; Biometric Facial Verification & Evaluation Platform

[![Release](https://img.shields.io/badge/release-v1.0.0--prod-emerald?style=flat-square)](STEP11_FINAL_RELEASE_AUDIT.md)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue?style=flat-square)](backend/requirements.txt)
[![Frontend](https://img.shields.io/badge/frontend-React%2018%20%2B%20Vite%205-purple?style=flat-square)](frontend/package.json)
[![Tests](https://img.shields.io/badge/tests-166%2F166%20passed%20(100%25)-brightgreen?style=flat-square)](STEP11_REGRESSION_AUDIT.md)
[![Biometrics](https://img.shields.io/badge/biometrics-OpenCV%20YuNet%20%2B%20SFace%20(128--d)-crimson?style=flat-square)](docs/MODEL_PROVENANCE.md)
[![Privacy](https://img.shields.io/badge/privacy-100%25%20Ephemeral%20RAM-success?style=flat-square)](STEP11_SECURITY_PRIVACY_AUDIT.md)
[![License](https://img.shields.io/badge/license-Apache--2.0-lightgrey?style=flat-square)](LICENSE)

**FACECORE AI** is a production-engineered, locally deployable biometric facial verification and evaluation platform. Built with strict mathematical discipline, scientific transparency, and zero score fabrication, it provides high-precision pairwise facial image comparison, automated quality diagnostics, and reproducible benchmark auditing.

---

## Key Capabilities & Architectural Principles

- **Dual-Model Local Neural Pipeline:**
  - **Detector:** OpenCV YuNet (depthwise separable convolution with 5-point landmark localization).
  - **Recognizer:** OpenCV SFace / SphereFace2 (128-dimensional hyperspherical margin feature extraction).
  - **Metric:** Exact inner dot-product cosine similarity bounded in $[-1.0, 1.0]$.
- **Ephemeral In-Memory Privacy (Zero Persistence):**
  - Image payloads are decoded directly in RAM (`cv2.imdecode`) and discarded post-comparison.
  - Zero raw images, facial crops, or 128-dimensional embedding vectors are ever saved to disk or external services.
  - Strictly 100% offline local inference; zero telemetry or phone-home calls.
- **Calibrated Operating Profiles:**
  - `High Security` ($\tau = 0.3600$): Target FAR $\le 0.10\%$, out-of-fold TAR $98.47\%$ (LFW calibrated).
  - `Balanced` ($\tau = 0.3132$): Canonical LFW Equal Error Rate (EER) crossover point ($99.50\%$ accuracy).
  - `High Convenience` ($\tau = 0.2500$): Low false-rejection operating point.
  - `Custom`: User-defined operating threshold with out-of-bounds safety warnings.
- **Ambiguous Zone Protection:**
  - Automatically flags scores falling in the statistical distribution overlap zone $[0.28, 0.35]$ with mandatory human-review advisories.
- **Scientific Humility & Probability Non-Equivalence:**
  - Cosine similarity reflects geometric vector proximity on a hypersphere&mdash;it is never misrepresented as an identity probability, confidence percentage, or proof of identity.

---

## Repository Structure

```text
facecore-ai/
├── backend/
│   ├── app/
│   │   ├── benchmarks/         # Standardized evaluation runners (LFW, CALFW, CPLFW)
│   │   ├── config.py           # Ingestion ceilings, CORS, audit retention policies
│   │   ├── db/                 # SQLite WAL audit service & schema migrations
│   │   ├── engine/             # RealFacialEmbeddingEngine (YuNet + SFace CPU execution)
│   │   ├── models/             # Pydantic schemas, error codes, and telemetry models
│   │   ├── services/           # Magic byte validator, face detector, crop handlers
│   │   ├── weights/            # Official OpenCV ONNX neural network model files
│   │   └── main.py             # FastAPI backend with structured error masking
│   ├── data/                   # SQLite database storage directory (.gitkeep)
│   ├── scripts/                # Verification, load benchmarks, and security scanners
│   ├── tests/                  # 112 pytest automated regression test cases
│   ├── requirements.txt        # Pinned Python dependencies
│   └── .env.example            # Backend configuration template
│
├── frontend/
│   ├── src/
│   │   ├── components/         # Comparison, Dashboard, Benchmarks, TestLab views
│   │   ├── services/           # Typed REST client with VITE_API_BASE_URL resolution
│   │   ├── types/              # Strict TypeScript interface contracts
│   │   └── tests/              # 54 vitest component & workflow test cases
│   ├── package.json            # Vite + React 18 frontend configuration
│   ├── vite.config.ts          # Vite build and test orchestration
│   └── .env.example            # Frontend environment template
│
├── docs/                       # Architecture, deployment, environment & setup guides
├── start.ps1                   # One-click Windows PowerShell deployment launcher
├── start.bat                   # One-click Windows Command Prompt deployment launcher
├── .gitignore                  # Production exclusion rules (caches, venvs, DBs)
├── .env.example                # Unified root environment template
└── STEP11_FINAL_RELEASE_AUDIT.md # Release qualification certification & gate matrix
```

---

## Quick-Start Setup (Local Desktop)

### Prerequisites
- **Python:** 3.10 to 3.13 (64-bit).
- **Node.js:** v18.0.0 or higher with `npm`.
- **Operating System:** Windows 10/11 x64, Linux (Ubuntu 20.04+), or macOS.

### One-Click Launchers (Windows)

In the repository root:
```powershell
# PowerShell (Recommended):
.\start.ps1

# Or Windows Command Prompt / Double-Click:
start.bat
```

The script automatically validates Python, Node, model checksums, and network ports before launching:
- **Frontend Web UI:** `http://localhost:5173`
- **Backend REST API:** `http://127.0.0.1:8001`
- **Interactive Swagger Docs:** `http://127.0.0.1:8001/docs`

---

## Manual Step-by-Step Setup

### 1. Backend Service
```bash
cd backend
python -m venv .venv

# Activate virtual environment:
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux / macOS:
# source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# Verify model weights integrity
python scripts/verify_weights.py

# Launch FastAPI backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

### 2. Frontend Client
```bash
cd frontend
npm install
npm run dev
```

---

## Independent Cloud Deployment

The backend and frontend can be deployed together or completely decoupled across different hosting providers:

### Frontend (Static Edge Hosting: Vercel / Netlify / Cloudflare Pages)
- **Root Directory:** `frontend/`
- **Build Command:** `npm run build`
- **Publish Directory:** `dist`
- **Environment Variable:** `VITE_API_BASE_URL=https://your-api.domain.com`

### Backend (Containers / PaaS: Docker, Render, Railway, AWS ECS)
- Build the container using `backend/Dockerfile` (see [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)).
- Set Environment Variables:
  - `ENVIRONMENT=production`
  - `CORS_ORIGINS=https://your-frontend.domain.com`
  - `AUDIT_LOGGING_ENABLED=true`
  - `AUDIT_RETENTION_DAYS=30`

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for full container manifests and Nginx reverse proxy configurations.

---

## Neural Model Provenance & Verification

FACECORE AI relies on two official, open-source model files under the Apache-2.0 license:

| Model File | Architecture / Role | Input / Output | Expected SHA-256 |
| :--- | :--- | :--- | :--- |
| `face_detection_yunet_2023mar.onnx` | YuNet 5-point landmark detector | $320 \times 320 \to$ BBox + 5 Landmarks | `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4` |
| `face_recognition_sface_2021dec.onnx` | SFace (SphereFace2) feature extractor | $112 \times 112 \to$ 128-d Hyperspherical Vector | `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79` |

To verify bitwise cryptographic integrity at any time:
```bash
python backend/scripts/verify_weights.py
```

---

## Quality Assurance & Automated Testing

The codebase maintains a 100% pass rate across 166 automated regression tests:

```bash
# Run backend pytest suite (112 tests)
pytest backend/tests -v

# Run frontend Vitest suite (54 tests)
npm --prefix frontend test -- --run

# Compile production TypeScript build
npm --prefix frontend run build
```

---

## Documentation Index

- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md): Container, PaaS, and static edge deployment guides.
- [`docs/ENV_VARS.md`](docs/ENV_VARS.md): Complete environment variable reference.
- [`docs/GITHUB_SETUP.md`](docs/GITHUB_SETUP.md): GitHub setup, Git LFS notes, and CI workflows.
- [`docs/MODEL_PROVENANCE.md`](docs/MODEL_PROVENANCE.md): Neural network architecture and license details.
- [`STEP11_FINAL_RELEASE_AUDIT.md`](STEP11_FINAL_RELEASE_AUDIT.md): Comprehensive production acceptance audit report.

---

## License

This software and its official model weights are distributed under the [Apache-2.0 License](LICENSE).
