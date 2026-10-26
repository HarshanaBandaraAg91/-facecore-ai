# FACECORE AI &mdash; Biometric Facial Evaluation Platform (Step 01)

FACECORE AI is a standalone facial-image similarity and model-evaluation platform engineered with strict scientific integrity, cryptographic validation, and modular biometric neural architectures.

---

## Key Principles & Design Philosophy

- **Zero Score Fabrication:** In Phase 1, inference models are pending integration. The platform explicitly withholds synthetic, random, or fake similarity percentages.
- **Scientific Humility:** A facial similarity score reflects continuous vector distance in a latent hypersphere&mdash;it is never proof of 100% identity.
- **Ephemeral In-Memory Privacy:** Image payloads exist only in RAM during validation and comparison. Zero biometric photos, vectors, or face crops are saved to disk or external cloud servers.
- **No Surveillance / Scraping:** No social-media scraping, external identity lookups, or global face search routines exist within this codebase.
- **Cyber-Intelligence Aesthetic:** Obsidian and charcoal surfaces, tactical crimson-red accents, emerald validation indicators, and high-precision monospace telemetry.

---

## Repository Architecture

```
project 7 - face checking tool/
├── backend/
│   ├── app/
│   │   ├── config.py              # Upload limits (10MB, 4096px), MIME & magic headers
│   │   ├── main.py                # FastAPI endpoints: /health, /validate-image, /compare
│   │   ├── models/
│   │   │   └── schemas.py         # Pydantic telemetry models & diagnostics schemas
│   │   ├── services/
│   │   │   └── image_validator.py # Safe Pillow decoding, magic bytes, Laplacian sharpness
│   │   └── engine/
│   │       ├── base.py            # Abstract FacialEmbeddingEngine interface
│   │       └── stub_engine.py     # Step 01 modular pending-integration baseline
│   ├── tests/
│   │   ├── test_health.py         # Health & engine metadata test suite
│   │   └── test_validation.py     # Signature, corrupt, oversized, and pair tests
│   ├── requirements.txt           # fastapi, uvicorn, pillow, numpy, pytest, httpx
│   └── .venv/                     # Python 3.13 virtual environment
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/            # AppShell, Sidebar, Header
│   │   │   ├── comparison/        # ComparisonWorkspace, UploadCard, Preview, ResultPanel, Diagnostics, HistoryDrawer
│   │   │   ├── testlab/           # TestLabView (Planned batch evaluation)
│   │   │   ├── benchmarks/        # BenchmarksView (Standardized protocols: LFW, CFP-FP, AgeDB)
│   │   │   ├── settings/          # SettingsView (Theme selector, API status, Privacy manifesto)
│   │   │   └── common/            # Badge, EmptyState, Toast
│   │   ├── services/
│   │   │   └── api.ts             # Typed REST client reading VITE_API_BASE_URL
│   │   ├── types/
│   │   │   └── index.ts           # Strict TypeScript contracts
│   │   ├── tests/
│   │   │   ├── setup.ts           # Vitest setup
│   │   │   └── App.test.tsx       # UI navigation and validation unit tests
│   │   ├── index.css              # Cyber-intelligence design system in Vanilla CSS
│   │   └── App.tsx                # Root state router and tab orchestration
│   ├── .env                       # VITE_API_BASE_URL=http://localhost:8000
│   ├── .env.example
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── README.md                      # Platform documentation & Windows PowerShell guide
└── STEP01_REPORT.md               # Phase 1 verification report & audit
```

---

## Windows PowerShell Setup Instructions

### Prerequisites
- **Python 3.11+ / 3.13** (accessible via `py -3` launcher or `python`)
- **Node.js v18+ / v22+** and `npm`

---

### 1. Backend Setup & Startup

Open a PowerShell terminal in the project root:

```powershell
# Navigate to backend directory
cd "c:\Projects\project 7 - face checking tool\backend"

# Create virtual environment (if not already created)
py -3 -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt

# Run backend unit tests (10 tests)
pytest tests -v

# Start FastAPI development server on port 8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend will be live at: `http://127.0.0.1:8000`
Interactive API Docs (Swagger UI): `http://127.0.0.1:8000/docs`

---

### 2. Frontend Setup & Startup

Open a second PowerShell terminal in the project root:

```powershell
# Navigate to frontend directory
cd "c:\Projects\project 7 - face checking tool\frontend"

# Install npm dependencies
npm install

# Run frontend unit tests (7 tests with Vitest)
npm test

# Verify production build compilation
npm run build

# Start Vite development server
npm run dev
```

Frontend will be live at: `http://localhost:5173`

---

## Phase 1 Capabilities & Safeguards

| Component | Status | Details |
| :--- | :---: | :--- |
| **Image Validation** | Validated | Verifies true magic bytes (JPEG `FF D8 FF`, PNG `89 50 4E 47`, WebP `RIFF..WEBP`), rejects renamed executables, enforces 10 MB and 16 MP limits. |
| **Quality Diagnostics** | Active | Computes mean luminance, contrast standard deviation, Laplacian variance sharpness, and aspect ratio. |
| **Modular Engine Interface** | Active | Abstract `FacialEmbeddingEngine` contract ready to receive ArcFace, AdaFace, or FaceNet in Step 02. |
| **Compare Action** | Anti-Fabrication | Correctly reports `status: "engine_pending_integration"`, withholds simulated percentages, and generates image differential analysis. |
| **Metadata History** | Ephemeral | Stores evaluation metadata (SHA-256 prefixes, dimensions, timestamp) in session memory with zero image persistence. |
| **Cyber Aesthetics** | Active | Dark charcoal background, crimson accents, monospace telemetry, accessible keyboard navigation, responsive layout. |

---

## Known Limitations in Phase 1

1. **No Neural Inference:** Face similarity scoring is not active until a documented model checkpoint (e.g., ArcFace-ResNet100) is mounted in Step 02.
2. **Face Detection Landmark Crop:** In Step 01, technical diagnostics are computed on the full container image. Landmark alignment (MTCNN / RetinaFace) is slated for Step 02.
3. **No Batch Test Execution:** The Test Lab and Benchmarks pages present architecture definitions and protocols; benchmark runs await Step 02/03.

---

## Privacy & Ethical Governance Manifesto

1. **Ephemeral Processing:** Uploaded images are evaluated in-memory and discarded upon response delivery.
2. **Local Execution:** No images or biometric coordinates are transmitted to external clouds or third-party servers.
3. **Auditability:** Every pair comparison outputs a tamper-evident SHA-256 fingerprint prefix and exportable JSON telemetry report.
