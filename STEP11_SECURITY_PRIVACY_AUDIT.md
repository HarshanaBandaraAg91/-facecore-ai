# FACECORE AI — STEP 11: SECURITY & BIOMETRIC PRIVACY AUDIT
**Document Reference:** `STEP11_SECURITY_PRIVACY_AUDIT.md`  
**Execution Date:** 2026-11-02  
**Auditor:** Senior Biometric Systems & Security Auditor / Release Engineer  
**Pipeline:** OpenCV YuNet + SFace (128-d) + Cosine Similarity  
**Target Codebase:** `backend/app/services/image_validator.py`, `backend/app/main.py`, `backend/app/db/database.py`, `backend/app/config.py`  

---

## 1. Executive Summary

A comprehensive, code-path-level security and privacy audit was conducted across the FACECORE AI application. The inspection evaluated input validation, memory safety, denial-of-service resilience, error information leakage, CORS configuration, path traversal protections, biometric data lifecycle, and the privacy implications of the SQLite audit log.

### Security & Privacy Summary Matrix

| Audit Domain | Scope / Risk Evaluated | Status | Safeguard Mechanism |
| :--- | :--- | :---: | :--- |
| **File Type Validation** | Extension spoofing, polyglot payloads | **PASS** | Magic byte header sniffing (JPEG, PNG, WebP) independent of client MIME/extension. |
| **Decompression Bombs** | Pixel flood attacks / Memory exhaustion | **PASS** | `Image.MAX_IMAGE_PIXELS = 16,777,216` (16 MP) hard ceiling enforced prior to rasterization. |
| **Dimension Guards** | Sub-resolution and giant canvas attacks | **PASS** | Rejection if $W, H < 48\text{ px}$ or $W, H > 4096\text{ px}$. |
| **Image Persistence** | Biometric data leakage to disk / cloud | **PASS** | 100% ephemeral RAM execution via `cv2.imdecode`; zero disk writes. |
| **Embedding Persistence** | Biometric template storage risk | **PASS** | 128-d float embeddings are garbage collected post-comparison; zero vector persistence in DB. |
| **Telemetry & Outbound** | Unauthorized phone-home or tracking | **PASS** | Strictly offline; zero network calls or third-party SDK analytics. |
| **Error Handling** | Information disclosure / stack trace leakage | **PASS** | Global structured exception handler; returns typed `ErrorCode` without internal paths. |
| **CORS Policy** | Cross-Origin Request Forgery / Hijacking | **PASS** | Explicit whitelist of localhost/127.0.0.1 origins; wildcard `*` strictly prohibited. |
| **Path Traversal** | Directory traversal in archive extractors | **PASS** | Canonical path resolution (`os.path.commonpath`) verifies extraction paths. |
| **Audit Log Governance** | Metadata linkability & suspect tracking | **PASS** | Documented linkage risk; configurable retention, disable switch, and pruning endpoint. |

---

## 2. Ingestion Pipeline & Memory Safety Verification

### 2.1 Magic Byte Signature Sniffing
Client-supplied MIME types and file extensions are completely untrusted. The ingestion gateway in [`image_validator.py`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/backend/app/services/image_validator.py) inspects raw binary headers:
- **JPEG:** Verifies prefix `\xFF\xD8\xFF`.
- **PNG:** Verifies 8-byte signature `\x89PNG\r\n\x1a\n`.
- **WebP:** Verifies bytes 0-4 `RIFF` and bytes 8-12 `WEBP`.

Any file disguised with an image extension (e.g., an executable or HTML payload named `photo.jpg`) is immediately rejected with HTTP 200/422 and code `UNSUPPORTED_FORMAT`.

### 2.2 Decompression Bomb Protection (ZIP / Pixel Bombs)
Attackers can submit tiny compressed files (e.g., a 50 KB image that expands to 100,000 x 100,000 pixels in RAM) to exhaust server memory:
- **Mitigation:** `Pillow.Image.MAX_IMAGE_PIXELS` is explicitly set to `16,777,216` (16 megapixels) via `settings.max_total_pixels`.
- **Pre-allocation check:** Image header dimensions are read without decompressing pixel arrays (`Image.open(stream)` followed by `verify()`). If $W \times H > 16,777,216$, Pillow raises `DecompressionBombError`, which is trapped and rejected cleanly.
- **Payload Size Cap:** Payloads exceeding `settings.max_upload_size_bytes` (15 MB) are rejected before memory allocation.

### 2.3 Ephemeral Memory Lifecycle & Zero Disk Writes
- Uploaded byte streams (`UploadFile.read()`) reside strictly in temporary RAM.
- Raster arrays are decoded directly via `cv2.imdecode(np.frombuffer(raw_bytes, np.uint8), cv2.IMREAD_COLOR)`.
- No temporary image files are written to `/tmp`, `%TEMP%`, or disk cache.
- Local variables referencing raw buffers and numpy arrays go out of scope at the conclusion of the comparison handler and are reclaimed by Python's garbage collector.

---

## 3. Biometric Data Privacy & Zero-Persistence Guarantee

### 3.1 Raw Imagery
- **Disk Persistence:** `0.00%` (Zero image files stored).
- **Database Persistence:** `0.00%` (Zero BLOB columns in SQLite schema).
- **External Transmission:** `0.00%` (Zero outbound cloud, CDN, or third-party connections).

### 3.2 128-Dimensional Neural Embeddings
Facial embeddings represent sensitive biometric templates. In FACECORE AI:
- Embeddings are generated in ephemeral memory solely for the duration of the dot-product cosine similarity computation.
- SQLite schema migration 1 (`comparison_audit_log`) contains columns only for scalar scores (`similarity_score`, `display_score`, `threshold_used`, `is_match`), latency, and cryptographic hash prefixes.
- Neither the 128-dimensional embedding float array nor any intermediate layer activations are ever written to disk or returned in API responses.

---

## 4. Comparison Audit Log: Threat Model & Privacy Governance

The comparison audit log stores execution metadata:
```sql
timestamp TEXT, probe_hash_prefix TEXT, reference_hash_prefix TEXT,
similarity_score REAL, display_score REAL, threshold_used REAL,
threshold_profile TEXT, is_match INTEGER, latency_ms REAL,
face_count_a INTEGER, face_count_b INTEGER, quality_flags_a TEXT,
quality_flags_b TEXT, status TEXT
```

### 4.1 Sensitivity Analysis (Linkage & Correlation Risk)
While the audit log does **not** store raw pixels or neural embeddings, it cannot be categorized as entirely non-sensitive:

> [!WARNING]
> **Biometric Correlation & Linkability Risk:**  
> `probe_hash_prefix` and `reference_hash_prefix` store the first 16 hexadecimal characters (64 bits of entropy) of the SHA-256 digest of the uploaded files.  
> 1. **Candidate Verification Attack:** If an adversary has access to candidate source images (e.g., an employee directory, social media profiles, or local disk photos), they can compute SHA-256 hashes of those images. Matching the 16-character prefix will identify which candidate image was submitted with near-zero probability of false collision ($2^{-64}$).  
> 2. **Pairwise Association Discovery:** If Candidate A was compared against Candidate B at a specific timestamp, an auditor or attacker with access to `facecore.db` can deduce that an inquiry occurred between those two identities and observe whether the system determined them to be a match.

### 4.2 Privacy Governance Controls Implemented in Step 11
To mitigate linkage risks and support compliance with data minimization standards, the following governance features were engineered:

1. **Audit Logging Kill-Switch:**
   - Setting `AUDIT_LOGGING_ENABLED=false` in `.env` causes `record_comparison()` to return immediately without writing any record to SQLite.
2. **Automated Data Retention & Pruning:**
   - Default retention window is set to 30 days (`AUDIT_RETENTION_DAYS=30`).
   - Function `prune_comparison_audit_log(retention_days: int)` removes all records older than the configured cutoff.
3. **Explicit Operator Deletion API:**
   - `DELETE /api/history` wipes all audit records immediately (`clear_comparison_history()`).
   - `DELETE /api/history?older_than_days=X` prunes records older than $X$ days.
4. **Local Access Security:**
   - Database resides locally at `backend/data/facecore.db` with standard OS-level access control list (ACL) protections. It is never exposed via unauthenticated public ports.

---

## 5. Network & API Security Audit

### 5.1 CORS Whitelist
Cross-Origin Resource Sharing in [`main.py`](file:///c:/Projects/project%207%20-%20face%20checking%20tool/backend/app/main.py) is strictly bounded:
```python
cors_origins: List[str] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```
No wildcard (`allow_origins=["*"]`) exists in the codebase. Production browsers will block cross-origin requests from external malicious web origins.

### 5.2 Error Information Disclosure
- When an exception occurs, the custom exception handler maps internal errors to clean, typed API responses containing `error_code`, `message`, `timestamp`, and `suggestion`.
- Tracebacks, Python module paths, system filenames, and server environment variables are stripped and kept exclusively in local backend logs.

### 5.3 Path Traversal Protections
- In `backend/app/benchmarks/parsers.py` and `tar_extractor.py`, extracted paths are validated with `os.path.commonpath([target_dir, member_path]) == target_dir`.
- Symlink and relative path (`../../`) escape attacks are prevented.

---

## 6. Security Audit Verdict

### Gate Status: **PASS**
- 100% ephemeral image processing in RAM with zero disk or embedding persistence.
- Complete decompression bomb and magic byte validation.
- Linkability risks of SHA-256 prefixes documented with explicit kill-switch and pruning controls.
- Strict local CORS and masked production error handling.

