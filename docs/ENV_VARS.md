# FACECORE AI — Production Environment Variables Reference

This document details all configuration options for the **FACECORE AI** backend and frontend services.

---

## 1. Backend Environment Variables (`backend/.env`)

| Variable Name | Type | Default Value | Description & Security Impact |
| :--- | :---: | :---: | :--- |
| `APP_NAME` | string | `"FACECORE AI"` | Application name displayed in API metadata and Swagger docs. |
| `APP_VERSION` | string | `"1.0.0-prod"` | Current semantic version identifier. |
| `ENVIRONMENT` | string | `"production"` | Operational tier (`development`, `staging`, `production`). In production, debug mode is forced off. |
| `DEBUG` | boolean | `false` | Enable verbose application logging and tracebacks. Keep `false` in production to prevent internal information disclosure. |
| `CORS_ORIGINS` | string | `http://localhost:5173,...` | Comma-delimited list of allowed origin URLs. Never use wildcard `*` in production. |
| `MAX_UPLOAD_SIZE_BYTES` | integer | `15728640` (15 MB) | Hard payload size limit enforced at request stream ingestion. Protects against memory flood attacks. |
| `MIN_IMAGE_DIMENSION` | integer | `48` | Minimum image width and height (48x48 px). Sub-resolution images are rejected to avoid extreme false rejection rates. |
| `MAX_IMAGE_DIMENSION` | integer | `4096` | Maximum image dimension (4096x4096 px). Protects memory allocation during rasterization. |
| `MAX_TOTAL_PIXELS` | integer | `16777216` (16 MP) | Decompression bomb ceiling enforced via `Pillow.Image.MAX_IMAGE_PIXELS`. |
| `AUDIT_LOGGING_ENABLED` | boolean | `true` | If set to `false`, skips all writes to `facecore.db`, ensuring 100% zero-audit footprint for strict GDPR compliance. |
| `AUDIT_RETENTION_DAYS` | integer | `30` | Number of days to retain historical metadata in SQLite before automated pruning. |
| `DATABASE_PATH` | string | `"backend/data/facecore.db"` | Relative or absolute path to SQLite audit database file. |
| `WEIGHTS_DIR` | string | `"backend/app/weights"` | Filesystem directory containing official `face_detection_yunet_2023mar.onnx` and `face_recognition_sface_2021dec.onnx`. |
| `DEFAULT_THRESHOLD_PROFILE` | string | `"balanced"` | Default operating profile: `"high_security"` ($\tau=0.3600$), `"balanced"` ($\tau=0.3132$), or `"high_convenience"` ($\tau=0.2500$). |
| `ADVISORY_MIN_FACE_WIDTH` | integer | `48` | Face bounding box width threshold for triggering resolution quality advisories. |

---

## 2. Frontend Client Environment Variables (`frontend/.env`)

| Variable Name | Type | Default Value | Description |
| :--- | :---: | :---: | :--- |
| `VITE_API_BASE_URL` | string | `"http://localhost:8001"` | Target endpoint of the FastAPI backend. In cloud deployments, point to `https://api.yourdomain.com` or use relative `/api` behind a reverse proxy. |

---

## 3. Configuration Security Best Practices

1. **Never commit `.env` files:** The `.gitignore` is configured to exclude all `.env` files except `.env.example`.
2. **Strict CORS Whitelisting:** When deploying the frontend to a public domain (e.g. `https://facecore.example.com`), configure `CORS_ORIGINS=https://facecore.example.com` on the backend.
3. **Audit Privacy:** If operating in environments subject to GDPR or HIPAA biometric restrictions, set `AUDIT_LOGGING_ENABLED=false` or configure daily pruning jobs.

