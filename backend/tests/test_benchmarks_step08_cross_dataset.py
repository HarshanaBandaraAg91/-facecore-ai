"""Cross-Dataset Generalization & Advanced Robustness Evaluation Test Suite (STEP 08).

Comprehensive verification of:
1. CALFW (Cross-Age LFW) pairs parsing and image resolution.
2. CPLFW (Cross-Pose LFW) pairs parsing and 4-digit zero-padding resolution.
3. CFP-FP (Celebrities in Frontal-Profile) pair list parsing and fold partitioning.
4. AgeDB-30 pair list parsing and 30-year chronological gap labels.
5. Threshold transfer math and validation/test isolation.
6. Rejection of unmounted/restricted datasets (CFP-FP, AgeDB-30).
7. Real-world photograph inference on CPLFW cross-pose pairs.
8. Real-world photograph inference on CALFW cross-age pairs.
9. Controlled optical, transmission, and environmental robustness perturbations.
10. Scientific Markdown report export contract.
"""

import os
import io
import pytest
import numpy as np

from app.benchmarks.schemas import (
    BenchmarkRunConfig,
    BenchmarkResult,
    ConfusionMatrix,
    PairAnnotation,
)
from app.benchmarks.manifest import (
    DATASETS_REGISTRY,
    parse_calfw_pairs_csv,
    parse_cplfw_pairs_csv,
    parse_cfp_fp_pairs_txt,
    parse_agedb_pairs_txt,
    sync_dataset_registry_with_disk,
)
from app.benchmarks.metrics import (
    evaluate_transferred_threshold,
    export_benchmark_markdown,
    compute_roc_and_auc,
    compute_eer,
)
from app.benchmarks.runner import (
    BenchmarkRunner,
    get_shared_benchmark_engine,
)
from app.benchmarks.robustness import (
    apply_gaussian_blur,
    apply_resolution_degradation,
    apply_illumination_scaling,
    apply_partial_occlusion,
    apply_jpeg_compression,
    ROBUSTNESS_CONDITIONS,
)


# ============================================================================
# Test 1: CALFW Pairs Parser
# ============================================================================
def test_calfw_pairs_parser_format():
    """Verify CALFW CSV parsing parses genuine and impostor records across 10 folds."""
    sample_csv = (
        "pair_id,fold_id,fold_position,is_same,image_a,image_b\n"
        "0,1,0,1,Carl_Reiner_0001.jpg,Carl_Reiner_0002.jpg\n"
        "1,1,1,0,Carl_Reiner_0001.jpg,Bill_Gates_0001.jpg\n"
        "2,2,0,1,George_W_Bush_0001.jpg,George_W_Bush_0002.jpg\n"
        "3,2,1,0,George_W_Bush_0001.jpg,Tony_Blair_0001.jpg\n"
    )
    # Mock images base with dummy files
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        for name, img in [
            ("Carl_Reiner", "Carl_Reiner_0001.jpg"),
            ("Carl_Reiner", "Carl_Reiner_0002.jpg"),
            ("Bill_Gates", "Bill_Gates_0001.jpg"),
            ("George_W_Bush", "George_W_Bush_0001.jpg"),
            ("George_W_Bush", "George_W_Bush_0002.jpg"),
            ("Tony_Blair", "Tony_Blair_0001.jpg"),
        ]:
            os.makedirs(os.path.join(tmp_dir, name), exist_ok=True)
            with open(os.path.join(tmp_dir, name, img), "w") as f:
                f.write("dummy")

        pairs = parse_calfw_pairs_csv(sample_csv, tmp_dir, require_all=True)
        assert len(pairs) == 4
        assert pairs[0].is_genuine is True
        assert pairs[0].fold_index == 0
        assert pairs[1].is_genuine is False
        assert pairs[2].fold_index == 1
        assert pairs[0].condition == "cross_age"


# ============================================================================
# Test 2: CPLFW Pairs Parser
# ============================================================================
def test_cplfw_pairs_parser_format():
    """Verify CPLFW CSV parsing standardizes filenames to 4-digit zero-padding."""
    sample_csv = (
        "pair_id,fold_id,fold_position,is_same,image_a,image_b\n"
        "0,1,0,1,Ingrid_Betancourt_1.jpg,Ingrid_Betancourt_2.jpg\n"
        "1,1,1,0,Ingrid_Betancourt_1.jpg,Jonathan_Woodgate_3.jpg\n"
    )
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        for name, canon in [
            ("Ingrid_Betancourt", "Ingrid_Betancourt_0001.jpg"),
            ("Ingrid_Betancourt", "Ingrid_Betancourt_0002.jpg"),
            ("Jonathan_Woodgate", "Jonathan_Woodgate_0003.jpg"),
        ]:
            os.makedirs(os.path.join(tmp_dir, name), exist_ok=True)
            with open(os.path.join(tmp_dir, name, canon), "w") as f:
                f.write("dummy")

        pairs = parse_cplfw_pairs_csv(sample_csv, tmp_dir, require_all=True)
        assert len(pairs) == 2
        assert pairs[0].image_a == "Ingrid_Betancourt/Ingrid_Betancourt_0001.jpg"
        assert pairs[0].image_b == "Ingrid_Betancourt/Ingrid_Betancourt_0002.jpg"
        assert pairs[0].condition == "cross_pose"


# ============================================================================
# Test 3: CFP-FP Pairs Parser
# ============================================================================
def test_cfp_fp_pairs_parser():
    """Verify CFP-FP pair list parsing and fold assignment."""
    lines = [
        "001/01.jpg 001/11.jpg 1",
        "001/02.jpg 002/11.jpg 0",
    ]
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        os.makedirs(os.path.join(tmp_dir, "001"), exist_ok=True)
        os.makedirs(os.path.join(tmp_dir, "002"), exist_ok=True)
        for p in ["001/01.jpg", "001/11.jpg", "001/02.jpg", "002/11.jpg"]:
            with open(os.path.join(tmp_dir, p), "w") as f:
                f.write("dummy")

        pairs = parse_cfp_fp_pairs_txt(lines, tmp_dir, require_all=True)
        assert len(pairs) == 2
        assert pairs[0].is_genuine is True
        assert pairs[1].is_genuine is False
        assert pairs[0].condition == "frontal_profile"


# ============================================================================
# Test 4: AgeDB-30 Pairs Parser
# ============================================================================
def test_agedb_30_pairs_parser():
    """Verify AgeDB-30 pair list parsing and identity string extraction."""
    lines = [
        "Javed_Miandad_00_50.jpg Javed_Miandad_01_20.jpg 1",
        "Frank_Sinatra_00_30.jpg Tom_Cruise_01_55.jpg 0",
    ]
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        for p in ["Javed_Miandad_00_50.jpg", "Javed_Miandad_01_20.jpg", "Frank_Sinatra_00_30.jpg", "Tom_Cruise_01_55.jpg"]:
            with open(os.path.join(tmp_dir, p), "w") as f:
                f.write("dummy")

        pairs = parse_agedb_pairs_txt(lines, tmp_dir, require_all=True)
        assert len(pairs) == 2
        assert pairs[0].identity_a == "Javed_Miandad"
        assert pairs[1].identity_b == "Tom_Cruise"
        assert pairs[0].condition == "cross_age_30yr"


# ============================================================================
# Test 5: Threshold Transfer Evaluation Math
# ============================================================================
def test_threshold_transfer_evaluation_math():
    """Verify threshold transfer accurately evaluates fixed threshold without data snooping."""
    scores = np.array([0.70, 0.65, 0.20, 0.10], dtype=np.float32)
    labels = np.array([True, True, False, False], dtype=bool)

    # Perfect transfer at tau = 0.35
    acc, cm = evaluate_transferred_threshold(scores, labels, threshold=0.35)
    assert acc == 1.0
    assert cm.tp == 2
    assert cm.tn == 2
    assert cm.fp == 0
    assert cm.fn == 0

    # Misclassification when threshold transferred too high (tau = 0.68)
    acc_high, cm_high = evaluate_transferred_threshold(scores, labels, threshold=0.68)
    assert acc_high == 0.75  # 1 false negative (0.65 < 0.68)
    assert cm_high.fn == 1


# ============================================================================
# Test 6: Rejection of Unmounted / Restricted Datasets
# ============================================================================
def test_unmounted_dataset_rejection():
    """Verify runner rejects unmounted CFP-FP or AgeDB-30 with explanatory error."""
    runner = BenchmarkRunner(engine=get_shared_benchmark_engine())

    # CFP-FP unmounted
    cfg_cfp = BenchmarkRunConfig(dataset_id="cfp-fp-v1", max_pairs=10)
    with pytest.raises(ValueError, match="CFP-FP dataset is not locally mounted"):
        runner.run_benchmark(cfg_cfp)

    # AgeDB-30 restricted
    cfg_agedb = BenchmarkRunConfig(dataset_id="agedb-30-v1", max_pairs=10)
    with pytest.raises(ValueError, match="AgeDB-30 dataset is restricted"):
        runner.run_benchmark(cfg_agedb)


# ============================================================================
# Test 7: Real Photograph Inference on CPLFW (Cross-Pose)
# ============================================================================
def test_cplfw_real_photograph_inference():
    """Execute end-to-end benchmark on real CPLFW cross-pose photograph pairs."""
    runner = BenchmarkRunner(engine=get_shared_benchmark_engine())
    config = BenchmarkRunConfig(
        dataset_id="cplfw-v1",
        max_pairs=20,
        random_seed=42,
        evaluate_robustness=False,
    )
    result = runner.run_benchmark(config)

    assert result.dataset_id == "cplfw-v1"
    assert result.is_real_photographs is True
    assert result.cross_dataset_condition == "cross_pose"
    assert result.total_pairs >= 10
    assert 0.0 <= result.optimal_threshold <= 1.0
    assert 0.0 <= result.accuracy <= 1.0
    assert result.transferred_threshold is not None
    assert result.transferred_accuracy is not None


# ============================================================================
# Test 8: Real Photograph Inference on CALFW (Cross-Age)
# ============================================================================
def test_calfw_real_photograph_inference():
    """Execute end-to-end benchmark on real CALFW cross-age photograph pairs."""
    runner = BenchmarkRunner(engine=get_shared_benchmark_engine())
    config = BenchmarkRunConfig(
        dataset_id="calfw-v1",
        max_pairs=20,
        random_seed=42,
        evaluate_robustness=False,
    )
    result = runner.run_benchmark(config)

    assert result.dataset_id == "calfw-v1"
    assert result.is_real_photographs is True
    assert result.cross_dataset_condition == "cross_age"
    assert result.total_pairs >= 10
    assert result.optimal_threshold > 0.0
    assert result.transferred_accuracy is not None


# ============================================================================
# Test 9: Controlled Optical & Transmission Robustness Perturbations
# ============================================================================
def test_controlled_robustness_perturbations():
    """Verify image perturbation algorithms preserve valid shape and uint8 range."""
    # Synthetic 112x112 color face patch
    img = np.full((112, 112, 3), 128, dtype=np.uint8)

    # Blur
    blurred = apply_gaussian_blur(img, sigma=2.0)
    assert blurred.shape == img.shape
    assert blurred.dtype == np.uint8

    # Downsampling
    downsampled = apply_resolution_degradation(img, target_dim=32)
    assert downsampled.shape == img.shape
    assert downsampled.dtype == np.uint8

    # Gamma illumination
    scaled = apply_illumination_scaling(img, gamma=1.8)
    assert scaled.shape == img.shape
    assert int(np.mean(scaled)) != int(np.mean(img))

    # JPEG compression
    compressed = apply_jpeg_compression(img, quality=20)
    assert compressed.shape == img.shape
    assert compressed.dtype == np.uint8

    # Partial occlusion
    masked = apply_partial_occlusion(img, region="lower")
    assert masked.shape == img.shape
    assert not np.array_equal(masked, img)


# ============================================================================
# Test 10: Scientific Markdown Report Export Contract
# ============================================================================
def test_export_markdown_report_contract():
    """Verify export_benchmark_markdown produces complete Markdown report."""
    runner = BenchmarkRunner(engine=get_shared_benchmark_engine())
    config = BenchmarkRunConfig(
        dataset_id="facecore-synthetic-fixture-v1",
        max_pairs=20,
        random_seed=42,
        evaluate_robustness=True,
    )
    result = runner.run_benchmark(config)
    md_str = export_benchmark_markdown(result)

    assert "# FACECORE AI — Benchmark Run Report" in md_str
    assert "Verification Accuracy" in md_str
    assert "Optimal Native Threshold" in md_str
    assert "Area Under ROC" in md_str
    assert "Manifest Fingerprint" in md_str
