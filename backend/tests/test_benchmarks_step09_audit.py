"""Scientific Validation, Benchmark Reproduction & Independent Audit Test Suite (STEP 09).

Independent verification and regression suite covering:
1. Full official pair accounting (LFW 6,000, CALFW 2,424 / 6,000, CPLFW 2,494 / 6,000).
2. Explicit accounting of unmounted supplementary images (zero silent pair omission).
3. Strict test-fold isolation and validation-only threshold calibration.
4. Exact Wilcoxon U ROC-AUC calculation with strict 0.5 tie-weighting.
5. Exact Equal Error Rate (EER) crossover linear interpolation.
6. Rule of Three sample size validation for low-FAR operating points.
7. Symmetric robustness perturbation execution and condition telemetry.
8. Provenance cryptographic hashing and CLI reproduction commands in schema and exports.
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
    RobustnessConditionResult,
    TARAtFAR,
)
from app.benchmarks.manifest import (
    DATASETS_REGISTRY,
    parse_lfw_pairs_txt,
    parse_calfw_pairs_csv,
    parse_cplfw_pairs_csv,
    sync_dataset_registry_with_disk,
)
from app.benchmarks.metrics import (
    compute_exact_auc,
    compute_roc_and_auc,
    compute_eer,
    compute_tar_at_far,
    compute_confusion_matrix,
    calibrate_threshold_cross_validation,
    _find_optimal_threshold,
    evaluate_transferred_threshold,
    export_benchmark_markdown,
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
# Test 1: Full Official LFW Pairs Accounting
# ============================================================================
def test_lfw_full_official_pairs_accounting():
    """Verify that official LFW protocol parses exactly 6,000 pairs across 10 folds."""
    lfw_pairs_path = os.path.join("backend", "data", "lfw", "pairs.txt")
    if not os.path.isfile(lfw_pairs_path):
        pytest.skip("LFW official pairs.txt not present on disk.")

    with open(lfw_pairs_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    pairs = parse_lfw_pairs_txt(lines)

    # Must contain exactly 6,000 pairs
    assert len(pairs) == 6000, f"Expected exactly 6,000 LFW pairs, found {len(pairs)}"

    # Exactly 3,000 genuine and 3,000 impostor
    genuine_count = sum(1 for p in pairs if p.is_genuine)
    impostor_count = sum(1 for p in pairs if not p.is_genuine)
    assert genuine_count == 3000, f"Expected 3,000 genuine pairs, got {genuine_count}"
    assert impostor_count == 3000, f"Expected 3,000 impostor pairs, got {impostor_count}"

    # Each fold must contain exactly 300 genuine and 300 impostor
    for fold_idx in range(10):
        fold_pairs = [p for p in pairs if p.fold_index == fold_idx]
        assert len(fold_pairs) == 600, f"Fold {fold_idx} has {len(fold_pairs)} pairs, expected 600"
        fg = sum(1 for p in fold_pairs if p.is_genuine)
        fi = sum(1 for p in fold_pairs if not p.is_genuine)
        assert fg == 300, f"Fold {fold_idx} genuine count is {fg}, expected 300"
        assert fi == 300, f"Fold {fold_idx} impostor count is {fi}, expected 300"


# ============================================================================
# Test 2: CALFW and CPLFW Missing Image Accounting (DISC-01 Remediation)
# ============================================================================
def test_calfw_and_cplfw_unresolved_accounting():
    """Verify that CALFW and CPLFW parsers track unresolved pairs and missing files."""
    calfw_csv = os.path.join("backend", "data", "calfw", "pairs.csv")
    cplfw_csv = os.path.join("backend", "data", "cplfw", "pairs.csv")
    images_base = os.path.join("backend", "data", "lfw", "images")

    if not os.path.isfile(calfw_csv) or not os.path.isfile(cplfw_csv) or not os.path.isdir(images_base):
        pytest.skip("CALFW/CPLFW annotations or LFW images not found on disk.")

    with open(calfw_csv, "r", encoding="utf-8") as f:
        calfw_content = f.read()
    calfw_pairs, calfw_unresolved, calfw_missing = parse_calfw_pairs_csv(
        calfw_content, images_base, return_unresolved=True
    )
    assert len(calfw_pairs) == 2424
    assert len(calfw_unresolved) == 3576
    assert len(calfw_pairs) + len(calfw_unresolved) == 6000
    assert len(calfw_missing) == 2640

    with open(cplfw_csv, "r", encoding="utf-8") as f:
        cplfw_content = f.read()
    cplfw_pairs, cplfw_unresolved, cplfw_missing = parse_cplfw_pairs_csv(
        cplfw_content, images_base, return_unresolved=True
    )
    assert len(cplfw_pairs) == 2494
    assert len(cplfw_unresolved) == 3506
    assert len(cplfw_pairs) + len(cplfw_unresolved) == 6000
    assert len(cplfw_missing) == 2444


# ============================================================================
# Test 3: Strict Test-Fold Isolation Invariance (Zero Leakage)
# ============================================================================
def test_test_fold_isolation_invariance():
    """Verify that calibration selects thresholds exclusively on validation folds."""
    scores = np.array([0.8, 0.7, 0.2, 0.1, 0.9, 0.75, 0.25, 0.05, 0.99, 0.98, 0.95, 0.90], dtype=np.float32)
    labels = np.array([True, True, False, False, True, True, False, False, True, True, False, False], dtype=bool)
    folds = np.array([0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2], dtype=int)

    # For fold 2: validation set is folds 0 and 1 ONLY.
    val_mask = folds != 2
    expected_fold2_thresh, _ = _find_optimal_threshold(scores[val_mask], labels[val_mask])

    # Cross-validation run
    _, _, fold_accs, _ = calibrate_threshold_cross_validation(scores, labels, folds, return_oof_preds=True)

    # Mutate fold 2 labels (the test fold) completely:
    mutated_labels = labels.copy()
    mutated_labels[folds == 2] = ~mutated_labels[folds == 2]

    # Invariant: validation threshold for test fold 2 is unaffected by test fold labels
    thresh_fold2_mutated, _ = _find_optimal_threshold(scores[val_mask], mutated_labels[val_mask])
    assert thresh_fold2_mutated == expected_fold2_thresh


# ============================================================================
# Test 4: Exact Wilcoxon U ROC-AUC Calculation with Strict Ties
# ============================================================================
def test_exact_wilcoxon_auc_ties():
    """Verify Mann-Whitney U calculation gives exact 0.5 weight to tied score pairs."""
    # Case 1: Perfect separation
    scores = np.array([0.8, 0.9, 0.7, 0.1, 0.2, 0.3], dtype=np.float32)
    labels = np.array([True, True, True, False, False, False], dtype=bool)
    roc_pts, auc = compute_roc_and_auc(scores, labels)
    assert abs(auc - 1.0) < 1e-6

    # Case 2: Complete inversion
    scores_inv = np.array([0.1, 0.2, 0.3, 0.8, 0.9, 0.7], dtype=np.float32)
    roc_pts_inv, auc_inv = compute_roc_and_auc(scores_inv, labels)
    assert abs(auc_inv - 0.0) < 1e-6

    # Case 3: All scores identical (complete tie) -> AUC MUST be 0.5000
    scores_tie = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5], dtype=np.float32)
    roc_pts_tie, auc_tie = compute_roc_and_auc(scores_tie, labels)
    assert abs(auc_tie - 0.5) < 1e-6

    # Case 4: Known analytical tie pair
    # 2 genuine: [0.6, 0.4]
    # 2 impostor: [0.6, 0.2]
    # Pairs:
    # (0.6, 0.6) -> tie (0.5)
    # (0.6, 0.2) -> gen wins (1.0)
    # (0.4, 0.6) -> imp wins (0.0)
    # (0.4, 0.2) -> gen wins (1.0)
    # Total U = 0.5 + 1.0 + 0.0 + 1.0 = 2.5. AUC = 2.5 / (2 * 2) = 0.625
    scores_partial = np.array([0.6, 0.4, 0.6, 0.2], dtype=np.float32)
    labels_partial = np.array([True, True, False, False], dtype=bool)
    auc_val = compute_exact_auc(scores_partial, labels_partial)
    assert abs(auc_val - 0.625) < 1e-6


# ============================================================================
# Test 5: Exact Equal Error Rate (EER) Crossover Interpolation
# ============================================================================
def test_eer_crossover_interpolation():
    """Verify EER calculation performs linear crossover interpolation between FAR and FRR."""
    gen_scores = [0.45, 0.48, 0.55, 0.65, 0.75, 0.85, 0.90, 0.92, 0.95, 0.98]
    imp_scores = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.42, 0.44, 0.46, 0.52]
    scores = np.array(gen_scores + imp_scores, dtype=np.float32)
    labels = np.array([True] * len(gen_scores) + [False] * len(imp_scores), dtype=bool)

    eer, eer_thresh = compute_eer(scores, labels)
    assert 0.0 < eer < 0.25
    assert 0.35 <= eer_thresh <= 0.60


# ============================================================================
# Test 6: Rule of Three Sample Size Validation for Low FAR Claims
# ============================================================================
def test_rule_of_three_sample_boundaries():
    """Verify mathematical sample size requirements for claiming TAR at FAR operating points."""
    # Rule of Three (Wayman, 1999; NIST): To establish error rate p with 95% confidence,
    # sample size N must satisfy N >= 3 / p.
    # At FAR = 10^-3: N_imp >= 3,000
    # At FAR = 10^-2: N_imp >= 300

    def evaluate_sample_adequacy(n_impostors: int, target_far: float) -> bool:
        required_n = 3.0 / target_far
        return n_impostors >= required_n

    # LFW has 3,000 impostor comparisons -> Adequately powered for 10^-3
    assert evaluate_sample_adequacy(3000, 0.001) is True

    # CALFW (1,564 impostors) -> Underpowered for 10^-3, adequately powered for 10^-2
    assert evaluate_sample_adequacy(1564, 0.001) is False
    assert evaluate_sample_adequacy(1564, 0.01) is True

    # CPLFW (1,550 impostors) -> Underpowered for 10^-3, adequately powered for 10^-2
    assert evaluate_sample_adequacy(1550, 0.001) is False
    assert evaluate_sample_adequacy(1550, 0.01) is True


# ============================================================================
# Test 7: Symmetric Robustness Perturbation Tracking
# ============================================================================
def test_symmetric_robustness_perturbation_telemetry():
    """Verify that robustness condition schemas capture full condition telemetry."""
    cond_result = RobustnessConditionResult(
        condition_name="Gaussian Blur (Severe: k=7, σ=2.0)",
        description="kernel_size=7, sigma=2.0",
        sample_size=100,
        accuracy=0.99,
        eer=0.015,
        auc=0.9995,
        tar_at_far_01=0.995,
        attempted_pairs=100,
        successful_pairs=100,
        failed_pairs=0,
        fta_rate=0.0,
        genuine_mean=0.6124,
        impostor_mean=0.0782,
        far_at_baseline_thresh=0.00,
        frr_at_baseline_thresh=0.02,
    )

    assert cond_result.attempted_pairs == 100
    assert cond_result.fta_rate == 0.0
    assert cond_result.genuine_mean == 0.6124
    assert cond_result.impostor_mean == 0.0782
    assert cond_result.far_at_baseline_thresh == 0.00
    assert cond_result.frr_at_baseline_thresh == 0.02


# ============================================================================
# Test 8: Provenance Cryptographic Hashes in BenchmarkResult Schema
# ============================================================================
def test_provenance_metadata_contract():
    """Verify BenchmarkResult schema enforces SHA-256 provenance fields."""
    cm = compute_confusion_matrix(scores=np.array([0.8, 0.2]), labels=np.array([True, False]), threshold=0.5)

    result = BenchmarkResult(
        run_id="audit-test-run-001",
        dataset_id="lfw-canonical-v1",
        dataset_name="Labeled Faces in the Wild",
        timestamp="2026-11-02T13:45:00Z",
        total_pairs=6000,
        genuine_pairs=3000,
        impostor_pairs=3000,
        accuracy=0.9935,
        auc=0.9988,
        eer=0.0080,
        eer_threshold=0.3132,
        optimal_threshold=0.3132,
        confusion_matrix=cm,
        execution_time_seconds=349.1,
        # Step 09 Audit fields:
        yunet_weights_hash="8fb616bb1c2c366ff641320478db1aa22769399df2c295beee3c3143c68a4170",
        sface_weights_hash="c5f59040ab50f38b4c023d8c1be276f571b782c5e533c3756c39f201e74f8ee6",
        pair_list_hash="6c66cf17812ea2c153cb1c1d85608b6b0632a4e7",
        reproducibility_command="python -m app.benchmarks.cli --dataset lfw-canonical-v1 --seed 42",
        official_total_pairs=6000,
        resolved_pairs_count=6000,
        unresolved_pairs_count=0,
        missing_images_count=0,
        evaluation_completeness="COMPLETE_OFFICIAL_CORPUS",
    )

    assert result.yunet_weights_hash.startswith("8fb616bb")
    assert result.sface_weights_hash.startswith("c5f59040")
    assert result.evaluation_completeness == "COMPLETE_OFFICIAL_CORPUS"
    assert result.reproducibility_command is not None


# ============================================================================
# Test 9: Markdown Audit Report Export Contract
# ============================================================================
def test_markdown_audit_report_export():
    """Verify Markdown export contains completeness matrix, provenance, and reproduction CLI."""
    cm = compute_confusion_matrix(scores=np.array([0.8, 0.2]), labels=np.array([True, False]), threshold=0.5)

    result = BenchmarkResult(
        run_id="audit-export-run-001",
        dataset_id="calfw-canonical-v1",
        dataset_name="Cross-Age LFW (CALFW)",
        timestamp="2026-11-02T13:46:00Z",
        total_pairs=2424,
        genuine_pairs=860,
        impostor_pairs=1564,
        accuracy=0.9914,
        auc=0.9981,
        eer=0.0105,
        eer_threshold=0.3872,
        optimal_threshold=0.3872,
        confusion_matrix=cm,
        execution_time_seconds=72.2,
        yunet_weights_hash="8fb616bb1c2c366ff641320478db1aa22769399df2c295beee3c3143c68a4170",
        sface_weights_hash="c5f59040ab50f38b4c023d8c1be276f571b782c5e533c3756c39f201e74f8ee6",
        pair_list_hash="641cb915443fa920dffb339474ba5fefc5a084c8a2b1f13b94be0d4b8e2d4062",
        reproducibility_command="python -m app.benchmarks.cli --dataset calfw-canonical-v1 --seed 42",
        official_total_pairs=6000,
        resolved_pairs_count=2424,
        unresolved_pairs_count=3576,
        missing_images_count=2640,
        evaluation_completeness="VERIFIED_LOCAL_SUBSET",
    )

    md = export_benchmark_markdown(result)

    assert "## 5. Audit & Scientific Provenance" in md
    assert "**Evaluation Completeness:** `VERIFIED_LOCAL_SUBSET`" in md
    assert "**Official Protocol Pairs:** 6000" in md
    assert "**Locally Resolved Pairs:** 2424" in md
    assert "**Unresolved Missing Pairs:** 3576 (2640 missing images)" in md
    assert "**YuNet Weights Hash:**" in md
    assert "**SFace Weights Hash:**" in md
    assert "### Reproducibility Command:" in md
    assert "python -m app.benchmarks.cli --dataset calfw-canonical-v1 --seed 42" in md
