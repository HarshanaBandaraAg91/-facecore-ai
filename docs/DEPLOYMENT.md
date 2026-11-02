# FACECORE AI — Independent Cloud & Local Deployment Guide

FACECORE AI is designed as a decoupled architecture where the FastAPI backend and React frontend can be deployed together or completely independently across different hosting providers.

```
                    +--------------------------------+
                    |        Client Browser          |
                    +--------------------------------+
                                   |
                 +-----------------+-----------------+
                 |                                   |
       (Static Asset Delivery)              (Biometric API Calls)
                 |                                   |
                 v                                   v
    +--------------------------+        +--------------------------+
    |     Frontend Host        |        |       Backend Host       |
    |  (Vercel/Netlify/Pages)  |        |  (Render/Railway/Docker) |
    |    Vite + React 18       |        |   FastAPI + OpenCV DNN   |
    +--------------------------+        +--------------------------+
                                                     |
                                        +------------+------------+
                                        |                         |
                                        v                         v
                                +---------------+         +---------------+
                                |  Local Memory |         |  SQLite WAL   |
                                | (Ephemeral)   |         | (Audit Log)   |
                                +---------------+         +---------------+
```

---

## 1. Deploying the Backend (Python FastAPI)

### Option A: Containerized Deployment (Docker)

Create a `backend/Dockerfile`:
```dockerfile
FROM python:3.12-slim

# Install system runtime dependencies for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY backend/app ./app
COPY backend/scripts ./scripts

# Ensure data directory exists
RUN mkdir -p data

# Verify neural network model weights integrity
RUN python scripts/verify_weights.py

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
```

Build and run:
```bash
docker build -t facecore-ai-backend -f backend/Dockerfile .
docker run -p 8001:8001 -e ENVIRONMENT=production -e CORS_ORIGINS="https://yourfrontend.domain.com" facecore-ai-backend
```

### Option B: Cloud Platform as a Service (PaaS: Render, Railway, AWS App Runner)
1. Point your service to the `backend/` directory as the root.
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Set Environment Variables:
   - `ENVIRONMENT=production`
   - `CORS_ORIGINS=https://your-frontend-app.vercel.app`
   - `AUDIT_LOGGING_ENABLED=true`
   - `AUDIT_RETENTION_DAYS=30`

---

## 2. Deploying the Frontend (React + Vite)

### Option A: Static Edge Hosting (Vercel, Netlify, Cloudflare Pages)
1. Set the project root to `frontend/`.
2. Build command: `npm run build`
3. Output directory: `dist`
4. Environment variable:
   - `VITE_API_BASE_URL=https://your-backend-api.onrender.com`

### Option B: Nginx Static Web Server
```nginx
server {
    listen 80;
    server_name facecore.yourdomain.com;
    root /var/www/facecore/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Reverse proxy backend API calls (Optional unified domain architecture)
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 3. Local Desktop Deployment

For offline desktop evaluation on Windows:
```powershell
# In project root:
.\start.ps1
# Or double-click:
start.bat
```
- Frontend UI opens at `http://localhost:5173`
- Backend API listens at `http://127.0.0.1:8001`
- Swagger documentation accessible at `http://127.0.0.1:8001/docs`

