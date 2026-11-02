# FACECORE AI — GitHub Repository Setup & DevOps Guide

This guide details the procedure to initialize, configure, and maintain the **FACECORE AI** repository on GitHub.

> [!IMPORTANT]
> **Approval Notice:** Do not run remote push commands without operator authorization.

---

## 1. Initializing and Connecting the Repository

### Step 1: Verify Git Status and Exclusions
Verify that no sensitive files, local caches, databases, or large raw datasets are untracked:
```bash
git status
```
Ensure that:
- `.env` files are NOT staged.
- `backend/data/*.db` is NOT staged.
- `node_modules/` and `.venv/` are NOT staged.
- Required models in `backend/app/weights/` ARE visible.

### Step 2: Add Files & Create Initial Clean Commit
```bash
# Add all files respected by .gitignore
git add .

# Verify staged file list before committing
git status

# Author the initial commit
git commit -m "feat: FACECORE AI v1.0.0-prod complete biometric verification platform"
```

### Step 3: Link Remote GitHub Repository & Push
```bash
# Rename active branch to main if needed
git branch -M main

# Add official remote origin URL (Replace with your actual repo URL)
git remote add origin https://github.com/your-org/facecore-ai.git

# Push initial release branch
git push -u origin main
```

---

## 2. Model Weights Handling in Git

FACECORE AI requires two official ONNX model files:
1. `face_detection_yunet_2023mar.onnx` (~232 KB)
2. `face_recognition_sface_2021dec.onnx` (~38.7 MB)

### Direct Git Tracking vs Git LFS
- **Direct Git (Default):** GitHub's maximum file size limit is **100 MB**, and files under **50 MB** do not trigger any warnings. Since SFace is 38.7 MB and YuNet is 232 KB, both files can be tracked directly in Git without external LFS servers.
- **Git LFS (Optional Enterprise Practice):** If your organization prefers to keep binary assets in Large File Storage:
  ```bash
  git lfs install
  git lfs track "backend/app/weights/*.onnx"
  git add .gitattributes
  ```

---

## 3. GitHub Actions Continuous Integration (CI) Workflow

To maintain the 100% regression pass guarantee on every commit and pull request, create `.github/workflows/ci.yml`:

```yaml
name: FACECORE AI CI Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  backend-test:
    name: Backend Regression & Safety Suite
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - name: Install System Dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y libgl1 libglib2.0-0

      - name: Install Python Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.txt

      - name: Verify Model Weights Checksums
        run: python backend/scripts/verify_weights.py

      - name: Run Backend Test Suite (112 tests)
        run: pytest backend/tests -v

  frontend-test:
    name: Frontend Vitest & Production Build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install Dependencies
        run: npm --prefix frontend ci

      - name: Run Frontend Tests (54 tests)
        run: npm --prefix frontend test -- --run

      - name: Compile Production Build
        run: npm --prefix frontend run build
```

---

## 4. Repository Security & Branch Protection Recommendations

1. **Branch Protection:**
   - Require pull request reviews before merging into `main`.
   - Require status checks to pass (`Backend Regression & Safety Suite` and `Frontend Vitest & Production Build`).
   - Require signed commits if mandated by corporate compliance.
2. **Secret Scanning:**
   - Enable GitHub Secret Scanning and Dependabot alerts.
3. **Release Tagging:**
   - Create signed semantic tags for production increments:
     ```bash
     git tag -a v1.0.0 -m "Release v1.0.0-prod: Clean local deployment qualification"
     git push origin v1.0.0
     ```

