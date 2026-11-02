# FACECORE AI — STEP 07: Dataset Acquisition & Installation Specification

**Document Version:** 1.0.0  
**Status:** Certified & Verified  
**Date:** November 2026  
**Auditor / Researcher:** Senior Computer Vision Researcher & Machine-Learning Evaluation Engineer  

---

## 1. Executive Summary & Purpose

In accordance with scientific benchmarking standards and biometric evaluation guidelines (ISO/IEC 19795-1), biometric facial recognition systems cannot rely exclusively on synthetic fixtures or procedural rendering. Evaluation requires verified, authentic photographs from peer-reviewed, authorized research distributions.

This specification documents the dataset acquisition, archive validation, secure extraction pipeline, and integrity verification mechanisms implemented in **FACECORE AI** for the **Labeled Faces in the Wild (LFW)** benchmark corpus.

---

## 2. Dataset Provenance & Distribution Metadata

### 2.1 Primary Distribution Information
* **Dataset Name:** Labeled Faces in the Wild (LFW)
* **Lead Institution:** Computer Vision Laboratory, University of Massachusetts Amherst (UMass)
* **Citation:** G. B. Huang, M. Mattar, T. Berg, and E. Learned-Miller. *Labeled Faces in the Wild: A Database for Studying Face Recognition in Unconstrained Environments.* Technical Report 07-49, University of Massachusetts, Amherst, 2007.
* **Official URL:** `http://vis-www.cs.umass.edu/lfw/`
* **Distribution Hosting:** Figshare Academic Repository / UMass CVL
* **Archive Distribution URL:** `https://figshare.com/ndownloader/files/5976018` (`lfw.tgz`)
* **Official Pairs Protocol:** `https://figshare.com/ndownloader/files/5976009` (`pairs.txt`)
* **Licensing / Permitted Use:** Non-commercial, academic, and scientific evaluation research.

### 2.2 Cryptographic Hashes and File Specifications

| Artifact | Source File | Exact Byte Size | MD5 Checksum | SHA-256 Checksum |
| :--- | :--- | :--- | :--- | :--- |
| **Complete Image Archive** | `lfw.tgz` | 180,566,744 bytes | `a17d05bd522c52d84eca14327a23d494` | `055f7d9c632d7370e6fb4afc7468d40f970c34a80d4c6f50ffec63f5a8d536c0` |
| **Official Pairs List** | `pairs.txt` | 155,335 bytes | `9b5c37107779bf2a1d3056eead623fe0` | `ea42330c62c92989f9d7c03237ed5d591365e89b3e649747777b70e692dc1592` |

---

## 3. Safe Dataset Installer Architecture (`dataset_installer.py`)

Direct extraction of untrusted third-party archives exposes operating systems to **TarSlip / ZipSlip directory traversal attacks**, where filenames containing relative sequences (e.g., `../../Windows/System32/...`) or absolute paths overwrite critical files outside the target directory.

To eliminate this vulnerability, `backend/app/benchmarks/dataset_installer.py` enforces a hardened, multi-stage installation pipeline:

```
[Remote Distribution / User File]
           │
           ▼
[Streaming Download with SHA-256 Digest] ──(Digest Mismatch)──> [Abort & Remove Partial]
           │
           ▼ (Checksum Verified)
[TarSlip Safe Extraction]
     ├─ Check: member.name is not absolute
     ├─ Check: os.path.realpath(dest) within os.path.realpath(target_dir)
     └─ Safe extraction member by member
           │
           ▼
[Corpus Integrity Audit]
     ├─ Image Count: 13,233 files
     ├─ Identity Count: 5,749 directories
     ├─ Pairs List: 6,000 pairs parsed
     └─ Zero-Missing Check: All 12,000 pair image references verified on disk
           │
           ▼
[Dataset Registry Mounted] ──> (is_available = True, local_path = backend/data/lfw)
```

### 3.1 Path Traversal Defense Implementation
```python
def _safe_extract_tar(tar_path: Path, target_dir: Path) -> None:
    target_abs = target_dir.resolve()
    with tarfile.open(tar_path, "r:*") as tar:
        for member in tar.getmembers():
            # Disallow absolute paths
            if os.path.isabs(member.name) or member.name.startswith(("/", "\\")):
                raise SecurityError(f"Archive entry contains absolute path: {member.name}")
            
            # Resolve destination and verify strictly inside target directory
            dest_path = (target_dir / member.name).resolve()
            if not str(dest_path).startswith(str(target_abs) + os.sep) and dest_path != target_abs:
                raise SecurityError(f"TarSlip path traversal detected: {member.name}")
            
            tar.extract(member, target_dir)
```

### 3.2 Incomplete-Download and Checksum Mismatch Recovery
1. Downloads stream directly into `.tmp` temporary files with constant chunk size (64 KB).
2. Streaming SHA-256 and MD5 hashes update incrementally without loading entire archives into RAM.
3. If the computed hash fails to match the certified checksum, or if the connection is interrupted:
   - The `.tmp` file is immediately deleted from disk.
   - An explicit `ValueError` is raised detailing expected vs. actual digests.
   - No corrupted or partial file is ever preserved or extracted.

---

## 4. Local Storage Layout & Git Exclusion

All real photograph datasets are isolated in a local cache directory structured as follows:

```
c:\Projects\project 7 - face checking tool\
├── .gitignore                      <-- Enforces backend/data/ and *.tgz exclusion
└── backend/
    └── data/
        └── lfw/
            ├── pairs.txt            <-- Official View 2 evaluation protocol list
            └── images/              <-- 13,233 JPEG photographs
                ├── Aaron_Eckhart/
                │   └── Aaron_Eckhart_0001.jpg
                ├── Abel_Pacheco/
                │   ├── Abel_Pacheco_0001.jpg
                │   ├── Abel_Pacheco_0002.jpg
                │   ├── Abel_Pacheco_0003.jpg
                │   └── Abel_Pacheco_0004.jpg
                └── ... (5,749 identity directories)
```

### 4.1 Git Tracking Exclusion
To adhere to distribution licenses, avoid repository bloat, and prevent unauthorized distribution:
- `.gitignore` explicitly ignores `backend/data/`, `data/`, `*.tgz`, and `*.tar.gz`.
- `git status` verifies that zero real images or dataset archives are staged or tracked in source control.

---

## 5. Verification Audit Results

A rigorous integrity verification check was executed via `verify_lfw_installation(Path("backend/data/lfw"))`:

* **Verification Status:** `VALID` (100% verified)
* **Total Images on Disk:** `13,233` (Matches official catalog count)
* **Total Identity Folders:** `5,749` (Matches official catalog count)
* **Official Pairs in Protocol:** `6,000` (10 folds $\times$ 600 pairs)
* **Missing Image Files:** `0` (Zero missing files across all 6,000 pairwise references)

---

## 6. Offline / User-Supplied Archive Procedure

For environments where outbound internet access is restricted or sandboxed, the system supports user-supplied archives:

1. Place the official `lfw.tgz` in an accessible path (e.g. `C:\downloads\lfw.tgz`).
2. Run the manual installation command or invoke the installer API:
   ```python
   from app.benchmarks.dataset_installer import install_lfw_from_archive
   install_lfw_from_archive(
       archive_path=Path("C:/downloads/lfw.tgz"),
       pairs_path=Path("C:/downloads/pairs.txt"),
       dest_dir=Path("backend/data/lfw")
   )
   ```
3. The installer checks the archive's SHA-256 checksum and verifies all 13,233 images before mounting the dataset into `DATASETS_REGISTRY`.

