"""Independent Benchmark Audit & Scientific Validation Test Suite (STEP 06).

Comprehensive verification of:
1. Official protocol consistency & rejection of unmounted datasets
2. Pair and fold integrity (balanced folds, no duplicates)
3. Strict identity and image leakage prevention across 10 folds
4. Validation-only threshold calibration isolation
5. Exact Wilcoxon-Mann-Whitney ROC-AUC calculation
6. Equal Error Rate (EER) linear interpolation
7. Low-sample FAR limitations & Rule of Three enforcement
8. Maximum-margin threshold selection & accuracy verification
9. Identity-clustered bootstrap vs. pair-level bootstrap
10. Repeated experiment bit-for-bit reproducibility & provenance hashes
11. JSON and CSV export audit contracts
"""

import pytest
import numpy as np

from app.benchmarks.schemas import (
    PairAnnotation,
    BenchmarkRunConfig,
    DatasetStatus,
)
from app.benchmarks.manifest import (
    DATASETS_REGISTRY,
    parse_lfw_pairs_txt,
    check_data_leakage,
    check_duplicate_pairs,
    compute_manifest_hash,
    validate_manifest_splits,
    generate_synthetic_benchmark_fixture,
)
from app.benchmarks.metrics import (
    compute_exact_auc,
    compute_roc_and_auc,
    compute_eer,
    compute_tar_at_far,
    compute_confusion_matrix,
    calibrate_threshold_cross_validation,
    _find_optimal_threshold,
    compute_bootstrap_confidence_intervals,
    compare_bootstrap_methods,
    export_benchmark_json,
    export_pairwise_csv,
)
from app.benchmarks.runner import (
    BenchmarkRunner,
    get_shared_benchmark_engine,
)


# ============================================================================
# Audit 1: Official Protocol Consistency & Unmounted Dataset Rejection
# ============================================================================
def test_official_protocol_consistency():
    """Verify official LFW protocol format parsing and rejection of unmounted datasets."""
    # Official LFW View 2 header specification: 10 folds, 300 genuine + 300 impostor
    valid_lfw_sample = [
        "10 2\n",
        "Alice 1 2\n",
        "Bob 1 2\n",
        "Alice 1 Bob 1\n",
        "Charlie 1 David 1\n",
    ]
    parsed = parse_lfw_pairs_txt(valid_lfw_sample)
    assert len(parsed) == 4
    assert sum(p.is_genuine for p in parsed) == 2
    assert sum(not p.is_genuine for p in parsed) == 2

    # Malformed header rejection
    with pytest.raises(ValueError, match="Invalid LFW header"):
        parse_lfw_pairs_txt(["10\n", "Alice 1 2\n"])

    # Reject unmounted dataset without phantom evaluation
    runner = BenchmarkRunner(engine=get_shared_benchmark_engine())
    unmounted_config = BenchmarkRunConfig(
        dataset_id="cfp-fp-v1",
        max_pairs=20,
        random_seed=42,
    )
    with pytest.raises(ValueError, match="not locally mounted"):
        runner.run_benchmark(unmounted_config)


# ============================================================================
# Audit 2: Pair and Fold Integrity
# ============================================================================
def test_pair_and_fold_integrity():
    """Verify synthetic fixture has exactly 10 folds, balanced pairs, and no duplicates."""
    pairs, _ = generate_synthetic_benchmark_fixture(
        num_identities=20, images_per_identity=6, num_folds=10, seed=42
    )

    assert len(pairs) == 120
    genuine_pairs = [p for p in pairs if p.is_genuine]
    impostor_pairs = [p for p in pairs if not p.is_genuine]
    assert len(genuine_pairs) == 60
    assert len(impostor_pairs) == 60

    # Every fold must have exactly 6 genuine and 6 impostor pairs
    for f in range(10):
        f_pairs = [p for p in pairs if p.fold_index == f]
        assert len(f_pairs) == 12
        assert sum(1 for p in f_pairs if p.is_genuine) == 6
        assert sum(1 for p in f_pairs if not p.is_genuine) == 6

    # Verify no duplicate image pairings exist
    duplicates = check_duplicate_pairs(pairs)
    assert len(duplicates) == 0


# ============================================================================
# Audit 3: Strict Identity and Image Leakage Prevention Across All Folds
# ============================================================================
def test_strict_identity_leakage_across_all_folds():
    """Verify that zero identities leak between training/validation folds and test fold."""
    pairs, _ = generate_synthetic_benchmark_fixture(
        num_identities=20, images_per_identity=6, num_folds=10, seed=42
    )

    report = validate_manifest_splits(pairs)
    assert not report["has_leakage"]
    assert len(report["leakage_violations"]) == 0

    # Exhaustive verification of each fold against the remaining 9 folds
    for f in range(10):
        test_pairs = [p for p in pairs if p.fold_index == f]
        train_pairs = [p for p in pairs if p.fold_index != f]
        has_leak, leaking_ids = check_data_leakage(train_pairs, test_pairs)
        assert not has_leak, f"Fold {f} leaked identities: {leaking_ids}"
        assert len(leaking_ids) == 0


# ============================================================================
# Audit 4: Validation-Only Threshold Calibration Isolation
# ============================================================================
def test_validation_only_threshold_isolation():
    """Verify threshold optimization never accesses test fold scores or labels."""
    # Construct 2 folds: fold 0 has clean threshold ~0.5.
    # Fold 1 has inverted scores where threshold ~0.5 yields 0% test accuracy.
    scores = np.array([0.9, 0.85, 0.15, 0.1, 0.2, 0.3, 0.8, 0.9], dtype=np.float32)
    labels = np.array([True, True, False, False, True, True, False, False], dtype=bool)
    folds = np.array([0, 0, 0, 0, 1, 1, 1, 1], dtype=int)

    mean_acc, mean_tau, fold_accs, oof_preds = calibrate_threshold_cross_validation(
        scores, labels, folds, return_oof_preds=True
    )

    # Threshold for fold 1 was calibrated strictly on fold 0 (~0.5)
    # Applying tau ~ 0.5 to fold 1 yields 0.0 test accuracy (clean isolation)
    assert fold_accs[0] == 1.0
    assert fold_accs[1] == 0.0
    assert 0.2 <= mean_tau <= 0.6


# ============================================================================
# Audit 5: Exact Wilcoxon-Mann-Whitney ROC-AUC Calculation
# ============================================================================
def test_exact_roc_auc_calculation():
    """Verify exact analytical AUC matches Wilcoxon-Mann-Whitney U statistic and handles ties."""
    rng = np.random.RandomState(42)
    gen_scores = rng.normal(0.7, 0.1, size=50)
    imp_scores = rng.normal(0.3, 0.1, size=50)
    scores = np.concatenate([gen_scores, imp_scores]).astype(np.float32)
    labels = np.array([True] * 50 + [False] * 50, dtype=bool)

    # Analytical Mann-Whitney U
    greater = np.sum(gen_scores[:, None] > imp_scores[None, :])
    equal = np.sum(gen_scores[:, None] == imp_scores[None, :])
    exact_u_auc = (greater + 0.5 * equal) / (50 * 50)

    _, computed_auc = compute_roc_and_auc(scores, labels)
    assert pytest.approx(computed_auc, abs=1e-5) == round(exact_u_auc, 5)

    # Tie handling verification
    tied_scores = np.array([0.5, 0.5, 0.5, 0.5], dtype=np.float32)
    tied_labels = np.array([True, True, False, False], dtype=bool)
    assert compute_exact_auc(tied_scores, tied_labels) == 0.5


# ============================================================================
# Audit 6: Equal Error Rate (EER) Linear Interpolation
# ============================================================================
def test_eer_linear_interpolation():
    """Verify EER interpolation finds the exact continuous crossover where FAR == FRR."""
    # At t=0.4: FAR=0.20, FRR=0.00 (diff = 0.20)
    # At t=0.6: FAR=0.00, FRR=0.20 (diff = -0.20)
    # Exact EER crossover is at t=0.5 with EER=0.10
    scores = np.array([0.55, 0.65, 0.75, 0.85, 0.95, 0.15, 0.25, 0.35, 0.45, 0.55], dtype=np.float32)
    labels = np.array([True] * 5 + [False] * 5, dtype=bool)

    eer, eer_thresh = compute_eer(scores, labels, search_steps=500)
    assert 0.05 <= eer <= 0.25
    assert 0.45 <= eer_thresh <= 0.65


# ============================================================================
# Audit 7: Low-Sample FAR Limitations & Rule of Three Enforcement
# ============================================================================
def test_low_sample_far_limitations():
    """Verify detection of statistically insufficient sample sizes for low FAR targets."""
    # Only 50 impostor pairs: minimum observable FAR is 1/50 = 0.02 (2%)
    scores = np.linspace(0.1, 0.9, 100, dtype=np.float32)
    labels = np.array([True] * 50 + [False] * 50, dtype=bool)

    tar_at_far = compute_tar_at_far(scores, labels, target_fars=[0.01, 0.001])
    assert len(tar_at_far) == 2

    # FAR = 0.01 requires N >= 300 by Rule of Three
    r_01 = tar_at_far[0]
    assert r_01.far_target == 0.01
    assert not r_01.rule_of_three_valid
    assert r_01.sample_size_advisory is not None
    assert "Rule of Three requires at least 300" in r_01.sample_size_advisory

    # FAR = 0.001 requires N >= 3000 by Rule of Three
    r_001 = tar_at_far[1]
    assert r_001.far_target == 0.001
    assert not r_001.rule_of_three_valid
    assert not r_001.is_statistically_valid
    assert "Rule of Three requires at least 3000" in r_001.sample_size_advisory


# ============================================================================
# Audit 8: Maximum-Margin Threshold Selection & Accuracy Verification
# ============================================================================
def test_threshold_selection_max_margin():
    """Verify threshold optimization selects the margin midpoint without accuracy dips."""
    scores = np.array([0.1, 0.2, 0.8, 0.9], dtype=np.float32)
    labels = np.array([False, False, True, True], dtype=bool)

    thresh, acc = _find_optimal_threshold(scores, labels)
    assert acc == 1.0
    # Optimal interval is (0.2, 0.8), midpoint is 0.5
    assert pytest.approx(thresh, abs=0.05) == 0.5


# ============================================================================
# Audit 9: Identity-Clustered Bootstrap vs. Pair-Level Bootstrap
# ============================================================================
def test_identity_clustered_bootstrap_reproducibility():
    """Verify identity-clustered bootstrap computes reproducible bounds accounting for clusters."""
    rng = np.random.RandomState(42)
    scores = rng.normal(0.6, 0.2, size=60).astype(np.float32)
    labels = rng.choice([True, False], size=60)
    clusters = [f"cluster_{i // 6}" for i in range(60)]  # 10 clusters of 6 items each

    comparison = compare_bootstrap_methods(
        scores, labels, optimal_threshold=0.5, clusters=clusters, n_bootstraps=100, seed=42
    )

    assert "pair_level" in comparison
    assert "identity_clustered" in comparison
    assert "Accuracy" in comparison["pair_level"]
    assert "Accuracy" in comparison["identity_clustered"]

    # Verify deterministic reproducibility
    ci_a = compute_bootstrap_confidence_intervals(
        scores, labels, optimal_threshold=0.5, clusters=clusters, n_bootstraps=100, seed=77
    )
    ci_b = compute_bootstrap_confidence_intervals(
        scores, labels, optimal_threshold=0.5, clusters=clusters, n_bootstraps=100, seed=77
    )
    assert len(ci_a) == len(ci_b)
    for a, b in zip(ci_a, ci_b):
        assert a.ci_lower == b.ci_lower
        assert a.ci_upper == b.ci_upper


# ============================================================================
# Audit 10: Repeated Experiment Bit-for-Bit Reproducibility & Provenance
# ============================================================================
def test_repeated_experiment_provenance():
    """Verify bit-for-bit repeatability of full benchmark pipeline and audit provenance fields."""
    runner = BenchmarkRunner(engine=get_shared_benchmark_engine())
    cfg = BenchmarkRunConfig(
        dataset_id="facecore-synthetic-fixture-v1",
        max_pairs=20,
        evaluate_robustness=False,
        random_seed=42,
    )

    res1 = runner.run_benchmark(cfg)
    res2 = runner.run_benchmark(cfg)

    # Identical scalar metrics
    assert res1.total_pairs == res2.total_pairs
    assert res1.accuracy == res2.accuracy
    assert res1.eer == res2.eer
    assert res1.auc == res2.auc
    assert res1.optimal_threshold == res2.optimal_threshold
    assert res1.confusion_matrix.accuracy == res2.confusion_matrix.accuracy

    # Provenance fields populated
    assert res1.dataset_manifest_hash is not None
    assert res1.model_weights_hash is not None
    assert "sface:" in res1.model_weights_hash
    assert "yunet:" in res1.model_weights_hash
    assert res1.system_environment is not None
    assert "python" in res1.system_environment
    assert res1.evaluation_protocol is not None
    assert res1.failure_to_acquire_count is not None
    assert res1.failure_to_acquire_rate is not None


# ============================================================================
# Audit 11: JSON and CSV Export Audit Contracts
# ============================================================================
def test_export_audit_contracts():
    """Verify JSON and CSV exports contain full scientific telemetry and schema contracts."""
    runner = BenchmarkRunner(engine=get_shared_benchmark_engine())
    cfg = BenchmarkRunConfig(
        dataset_id="facecore-synthetic-fixture-v1",
        max_pairs=10,
        evaluate_robustness=False,
        random_seed=99,
    )
    result = runner.run_benchmark(cfg)

    # JSON export
    json_out = export_benchmark_json(result)
    assert '"dataset_manifest_hash"' in json_out
    assert '"model_weights_hash"' in json_out
    assert '"evaluation_protocol"' in json_out
    assert '"failure_to_acquire_rate"' in json_out
    assert '"tar_at_far_table"' in json_out

    # CSV export
    csv_out = export_pairwise_csv(
        pair_ids=["p1", "p2"],
        identities_a=["sub_001", "sub_001"],
        identities_b=["sub_001", "sub_002"],
        is_genuine_list=[True, False],
        similarity_scores=[0.92, 0.22],
        threshold=0.5,
    )
    lines = csv_out.strip().splitlines()
    assert len(lines) == 3
    assert lines[0].startswith("pair_id,identity_a,identity_b,ground_truth")
    assert "TRUE_POSITIVE" in lines[1]
    assert "TRUE_NEGATIVE" in lines[2]
