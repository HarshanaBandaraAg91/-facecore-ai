"""Automated regression test suite for STEP 07: Real-World Dataset Integration and SFace Benchmarking.

Validates:
1. Official LFW 10-fold pairs parsing and format contracts (6,000 pairs, 10 folds).
2. Safe archive extraction with path traversal protection (TarSlip vulnerability defense).
3. Archive checksum validation (rejecting corrupt or tampered payloads).
4. Strict absence of synthetic substitution: missing/unmounted datasets raise errors.
5. Real image inference on verified LFW photographs with YuNet and SFace (no mocks).
6. ISO/IEC 19795-1 Failure to Acquire (FTA) categorization (no faces vs multiple faces).
7. Dataset status and installation API endpoints.
"""

import os
import io
import tarfile
import pytest
import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.benchmarks.schemas import BenchmarkRunConfig, DatasetStatus
from app.benchmarks.manifest import (
    DATASETS_REGISTRY,
    parse_lfw_pairs_txt,
    sync_dataset_registry_with_disk,
)
from app.benchmarks.dataset_installer import (
    safe_extract_tar,
    download_file_with_checksum,
    verify_lfw_installation,
    get_dataset_install_status,
)
from app.benchmarks.runner import (
    benchmark_runner,
    OnDiskImageStore,
    get_shared_benchmark_engine,
)
from app.engine.real_engine import compute_cosine_similarity

client = TestClient(app)


def test_official_lfw_pairs_parser_real_file():
    """Verify that the official LFW pairs.txt file parses exactly 6,000 pairs into 10 balanced folds."""
    pairs_path = os.path.join("backend", "data", "lfw", "pairs.txt")
    if not os.path.isfile(pairs_path):
        pairs_path = os.path.join("data", "lfw", "pairs.txt")

    assert os.path.isfile(pairs_path), "pairs.txt must be present on disk for Step 07"

    with open(pairs_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    pairs = parse_lfw_pairs_txt(lines)
    assert len(pairs) == 6000, f"Expected 6,000 official pairs, got {len(pairs)}"

    # Check 10 folds
    folds = sorted(list({p.fold_index for p in pairs}))
    assert folds == list(range(10)), f"Expected folds 0-9, got {folds}"

    for f in folds:
        fold_pairs = [p for p in pairs if p.fold_index == f]
        gen_pairs = [p for p in fold_pairs if p.is_genuine]
        imp_pairs = [p for p in fold_pairs if not p.is_genuine]
        assert len(fold_pairs) == 600, f"Fold {f} must have 600 pairs"
        assert len(gen_pairs) == 300, f"Fold {f} must have 300 genuine pairs"
        assert len(imp_pairs) == 300, f"Fold {f} must have 300 impostor pairs"


def test_safe_extract_tar_path_traversal_protection(tmp_path):
    """Verify that safe_extract_tar strictly blocks directory traversal attacks (TarSlip)."""
    tar_path = os.path.join(tmp_path, "malicious.tar")
    extract_target = os.path.join(tmp_path, "safe_dir")
    os.makedirs(extract_target, exist_ok=True)

    # Create a malicious tar archive containing a traversal member
    with tarfile.open(tar_path, "w") as tar:
        payload = b"malicious content"
        ti = tarfile.TarInfo(name="../escaped_file.txt")
        ti.size = len(payload)
        tar.addfile(ti, io.BytesIO(payload))

    with pytest.raises(ValueError, match="path traversal or absolute path"):
        safe_extract_tar(tar_path, extract_target)

    # Ensure no file was written outside target
    assert not os.path.isfile(os.path.join(tmp_path, "escaped_file.txt"))


def test_download_file_checksum_rejection(tmp_path):
    """Verify that download_file_with_checksum rejects files with mismatched MD5 or SHA-256."""
    fake_dest = os.path.join(tmp_path, "test_file.txt")
    # Using an invalid expected checksum must raise ValueError
    with pytest.raises(ValueError, match="checksum verification failed"):
        download_file_with_checksum(
            url="https://raw.githubusercontent.com/davidsandberg/facenet/master/data/pairs.txt",
            dest_path=fake_dest,
            expected_sha256="0000000000000000000000000000000000000000000000000000000000000000",
        )


def test_synthetic_fallback_prevention():
    """Verify that requesting an unmounted dataset strictly raises ValueError without silent synthetic fallback."""
    cfg = BenchmarkRunConfig(
        dataset_id="cfp-fp-v1",
        evaluate_robustness=False,
    )
    with pytest.raises(ValueError, match="images are not locally mounted"):
        benchmark_runner.run_benchmark(cfg)


def test_on_disk_image_store_lazy_access():
    """Verify that OnDiskImageStore resolves existing files and returns None for missing ones."""
    images_base = os.path.join("backend", "data", "lfw", "images")
    if not os.path.isdir(images_base):
        images_base = os.path.join("data", "lfw", "images")

    assert os.path.isdir(images_base)
    store = OnDiskImageStore(images_base)

    # Known existing file
    existing_key = "Abel_Pacheco/Abel_Pacheco_0001.jpg"
    assert existing_key in store
    data = store.get(existing_key)
    assert data is not None
    assert len(data) > 0
    assert data.startswith(b"\xff\xd8")  # JPEG SOI magic bytes

    # Non-existent file
    missing_key = "NonExistent_Person/NonExistent_0001.jpg"
    assert missing_key not in store
    assert store.get(missing_key) is None


def test_real_lfw_image_inference_no_mocks():
    """Execute genuine YuNet detection and SFace embedding extraction on real LFW human photographs."""
    engine = get_shared_benchmark_engine()
    assert engine.is_ready()

    images_base = os.path.join("backend", "data", "lfw", "images")
    if not os.path.isdir(images_base):
        images_base = os.path.join("data", "lfw", "images")

    # Load 2 photos of Abel Pacheco (genuine pair) and 1 photo of Dean Barker (impostor)
    with open(os.path.join(images_base, "Abel_Pacheco", "Abel_Pacheco_0001.jpg"), "rb") as f:
        bytes_a1 = f.read()
    with open(os.path.join(images_base, "Abel_Pacheco", "Abel_Pacheco_0004.jpg"), "rb") as f:
        bytes_a4 = f.read()
    with open(os.path.join(images_base, "Dean_Barker", "Dean_Barker_0001.jpg"), "rb") as f:
        bytes_b1 = f.read()

    # Detect and extract
    _, emb_a1, conf_a1, bbox_a1, _ = engine.detect_and_extract_face(bytes_a1, slot_label="Probe")
    _, emb_a4, conf_a4, bbox_a4, _ = engine.detect_and_extract_face(bytes_a4, slot_label="Genuine")
    _, emb_b1, conf_b1, bbox_b1, _ = engine.detect_and_extract_face(bytes_b1, slot_label="Impostor")

    assert emb_a1.shape == (128,)
    assert emb_a4.shape == (128,)
    assert emb_b1.shape == (128,)

    sim_genuine = compute_cosine_similarity(emb_a1, emb_a4)
    sim_impostor = compute_cosine_similarity(emb_a1, emb_b1)

    # Real human facial biometric separation: genuine similarity should be substantially higher than impostor
    assert sim_genuine > 0.50, f"Expected genuine similarity > 0.50, got {sim_genuine}"
    assert sim_impostor < 0.25, f"Expected impostor similarity < 0.25, got {sim_impostor}"
    assert sim_genuine > sim_impostor + 0.35, "Genuine and impostor distributions must be distinctly separated"


def test_real_lfw_benchmark_execution_and_metrics():
    """Run a controlled 60-pair benchmark across 10 folds on real LFW photographs."""
    cfg = BenchmarkRunConfig(
        dataset_id="lfw-canonical-v1",
        evaluate_robustness=False,
        max_pairs=60,
        random_seed=42,
        face_selection_policy="center_face",
    )
    result = benchmark_runner.run_benchmark(cfg)

    assert result.is_real_photographs is True
    assert result.status == DatasetStatus.COMPLETED
    assert result.total_pairs == 60
    assert result.genuine_pairs == 30
    assert result.impostor_pairs == 30
    assert result.failure_to_acquire_count == 0
    assert result.failure_to_acquire_rate == 0.0
    assert result.accuracy > 0.90, f"Expected high accuracy on LFW, got {result.accuracy}"
    assert result.auc > 0.95, f"Expected high AUC on LFW, got {result.auc}"
    assert result.optimal_threshold < 0.50, f"Real threshold should be ~0.3-0.4, got {result.optimal_threshold}"
    assert "View 2" in result.evaluation_protocol


def test_iso_fta_tracking_under_strict_single_face_policy():
    """Verify that multiple background faces are properly recorded as FTA under strict_single_face policy."""
    cfg = BenchmarkRunConfig(
        dataset_id="lfw-canonical-v1",
        evaluate_robustness=False,
        max_pairs=60,
        random_seed=42,
        face_selection_policy="strict_single_face",
    )
    result = benchmark_runner.run_benchmark(cfg)

    assert result.fta_breakdown is not None
    # Under strict single face policy, news photos with background faces trigger multiple_faces_detected
    assert result.fta_breakdown.multiple_faces_detected > 0
    assert result.failure_to_acquire_count == result.fta_breakdown.multiple_faces_detected
    assert result.failure_to_acquire_rate > 0.0


def test_datasets_api_endpoints_reflect_lfw_installation():
    """Verify that GET /api/benchmarks/datasets and /api/benchmarks/datasets/lfw-canonical-v1/status return verified status."""
    sync_dataset_registry_with_disk()

    res_list = client.get("/api/benchmarks/datasets")
    assert res_list.status_code == 200
    datasets = res_list.json()

    lfw = next((d for d in datasets if d["dataset_id"] == "lfw-canonical-v1"), None)
    assert lfw is not None
    assert lfw["is_available"] is True
    assert lfw["verification_status"] == DatasetStatus.DATASET_VERIFIED
    assert lfw["total_images"] == 13233
    assert lfw["total_pairs"] == 6000

    # Check status endpoint
    res_status = client.get("/api/benchmarks/datasets/lfw-canonical-v1/status")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["status"] == "VERIFIED"
    assert status_data["details"]["is_complete_lfw"] is True
    assert status_data["details"]["images_found"] == 13233

