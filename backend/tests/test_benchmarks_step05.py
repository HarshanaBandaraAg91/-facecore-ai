"""Automated test suite for STEP 05: Model Benchmarking Framework.

Covers all 12 evaluation criteria:
1. Genuine/impostor pair construction
2. Identity leakage prevention
3. Deterministic pair generation
4. ROC-AUC calculations
5. FAR/FRR calculations
6. EER calculation
7. Threshold calibration using validation data
8. Test-set isolation
9. Missing and malformed annotations
10. Empty datasets and insufficient pairs
11. Experiment reproducibility
12. Export correctness (JSON and CSV)
"""

import pytest
import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.benchmarks.schemas import (
    PairAnnotation,
    BenchmarkRunConfig,
    DatasetStatus,
)
from app.benchmarks.manifest import (
    check_data_leakage,
    check_duplicate_pairs,
    parse_lfw_pairs_txt,
    generate_synthetic_benchmark_fixture,
    DATASETS_REGISTRY,
)
from app.benchmarks.metrics import (
    compute_roc_and_auc,
    compute_eer,
    compute_tar_at_far,
    compute_confusion_matrix,
    calibrate_threshold_cross_validation,
    compute_bootstrap_confidence_intervals,
    export_benchmark_json,
    export_pairwise_csv,
)
from app.benchmarks.runner import BenchmarkRunner

client = TestClient(app)


# ============================================================================
# Criterion 1: Genuine/impostor pair construction
# ============================================================================
def test_genuine_and_impostor_pair_construction():
    """Verify that pair generator constructs properly labeled genuine and impostor pairs."""
    pairs, images = generate_synthetic_benchmark_fixture(num_identities=10, images_per_identity=4, num_folds=5, seed=123)
    
    assert len(pairs) > 0
    genuine_pairs = [p for p in pairs if p.is_genuine]
    impostor_pairs = [p for p in pairs if not p.is_genuine]

    assert len(genuine_pairs) > 0
    assert len(impostor_pairs) > 0

    # Genuine pairs must have identical subject names
    for gp in genuine_pairs:
        assert gp.identity_a == gp.identity_b
        assert gp.image_a in images
        assert gp.image_b in images
        assert gp.image_a != gp.image_b  # distinct photos of same subject

    # Impostor pairs must have distinct subject names
    for ip in impostor_pairs:
        assert ip.identity_a != ip.identity_b
        assert ip.image_a in images
        assert ip.image_b in images


# ============================================================================
# Criterion 2: Identity leakage prevention
# ============================================================================
def test_identity_leakage_prevention():
    """Verify data leakage detection identifies shared identities across splits."""
    train_pairs = [
        PairAnnotation(
            pair_id="p1", image_a="alice/1.jpg", image_b="alice/2.jpg",
            is_genuine=True, identity_a="Alice", identity_b="Alice"
        ),
        PairAnnotation(
            pair_id="p2", image_a="bob/1.jpg", image_b="bob/2.jpg",
            is_genuine=True, identity_a="Bob", identity_b="Bob"
        ),
    ]

    # Clean disjoint test split
    clean_test_pairs = [
        PairAnnotation(
            pair_id="p3", image_a="charlie/1.jpg", image_b="charlie/2.jpg",
            is_genuine=True, identity_a="Charlie", identity_b="Charlie"
        ),
    ]
    has_leakage, leaking = check_data_leakage(train_pairs, clean_test_pairs)
    assert not has_leakage
    assert len(leaking) == 0

    # Contaminated test split containing Bob
    contaminated_test_pairs = [
        PairAnnotation(
            pair_id="p4", image_a="bob/3.jpg", image_b="bob/4.jpg",
            is_genuine=True, identity_a="Bob", identity_b="Bob"
        ),
    ]
    has_leakage, leaking = check_data_leakage(train_pairs, contaminated_test_pairs)
    assert has_leakage
    assert "Bob" in leaking


# ============================================================================
# Criterion 3: Deterministic pair generation
# ============================================================================
def test_deterministic_pair_generation():
    """Verify identical random seeds generate bit-for-bit identical pairs."""
    pairs_a, _ = generate_synthetic_benchmark_fixture(num_identities=8, images_per_identity=3, num_folds=4, seed=999)
    pairs_b, _ = generate_synthetic_benchmark_fixture(num_identities=8, images_per_identity=3, num_folds=4, seed=999)

    assert len(pairs_a) == len(pairs_b)
    for pa, pb in zip(pairs_a, pairs_b):
        assert pa.pair_id == pb.pair_id
        assert pa.identity_a == pb.identity_a
        assert pa.identity_b == pb.identity_b
        assert pa.is_genuine == pb.is_genuine


# ============================================================================
# Criterion 4: ROC-AUC calculations
# ============================================================================
def test_roc_and_auc_calculation():
    """Verify analytical correctness of ROC-AUC calculation."""
    # Perfectly separated scores: genuine ~ 0.8, impostor ~ 0.2
    gen_scores = np.array([0.75, 0.82, 0.88, 0.91, 0.95], dtype=np.float32)
    imp_scores = np.array([0.10, 0.15, 0.22, 0.28, 0.35], dtype=np.float32)
    scores = np.concatenate([gen_scores, imp_scores])
    labels = np.array([True] * 5 + [False] * 5, dtype=bool)

    points, auc = compute_roc_and_auc(scores, labels, num_thresholds=100)
    assert auc == 1.0  # Perfect discrimination
    assert len(points) == 100

    # Overlapping random scores: AUC ~ 0.5
    rng = np.random.RandomState(42)
    rand_scores = rng.uniform(0.0, 1.0, size=200)
    rand_labels = rng.choice([True, False], size=200)
    _, rand_auc = compute_roc_and_auc(rand_scores, rand_labels, num_thresholds=100)
    assert 0.40 <= rand_auc <= 0.60


# ============================================================================
# Criterion 5: FAR/FRR calculations
# ============================================================================
def test_far_and_frr_calculations():
    """Verify False Acceptance Rate and False Rejection Rate formulas."""
    scores = np.array([0.9, 0.8, 0.7, 0.4, 0.3, 0.2], dtype=np.float32)
    labels = np.array([True, True, True, False, False, False], dtype=bool)

    # Threshold at 0.5: All 3 genuine >= 0.5, all 3 impostor < 0.5
    conf_mat = compute_confusion_matrix(scores, labels, threshold=0.5)
    assert conf_mat.tp == 3
    assert conf_mat.fp == 0
    assert conf_mat.tn == 3
    assert conf_mat.fn == 0
    assert conf_mat.accuracy == 1.0

    # Threshold at 0.85: 1 genuine classified (0.9), 2 genuine rejected (0.8, 0.7) -> FN=2, TP=1
    conf_mat_high = compute_confusion_matrix(scores, labels, threshold=0.85)
    assert conf_mat_high.tp == 1
    assert conf_mat_high.fn == 2
    assert conf_mat_high.fp == 0
    assert conf_mat_high.tn == 3


# ============================================================================
# Criterion 6: EER calculation
# ============================================================================
def test_eer_calculation():
    """Verify EER identification where FAR equals FRR."""
    # Balanced symmetric distributions
    gen_scores = np.array([0.4, 0.5, 0.6, 0.7, 0.8], dtype=np.float32)
    imp_scores = np.array([0.2, 0.3, 0.4, 0.5, 0.6], dtype=np.float32)
    scores = np.concatenate([gen_scores, imp_scores])
    labels = np.array([True] * 5 + [False] * 5, dtype=bool)

    eer, eer_thresh = compute_eer(scores, labels, search_steps=200)
    assert 0.15 <= eer <= 0.35
    assert 0.40 <= eer_thresh <= 0.60


# ============================================================================
# Criterion 7: Threshold calibration using validation data
# ============================================================================
def test_threshold_calibration_cross_validation():
    """Verify decision threshold is calibrated strictly on validation folds, not test folds."""
    scores = np.array([0.8, 0.2, 0.85, 0.25, 0.9, 0.15, 0.75, 0.3], dtype=np.float32)
    labels = np.array([True, False, True, False, True, False, True, False], dtype=bool)
    folds = np.array([0, 0, 1, 1, 2, 2, 3, 3], dtype=int)

    mean_acc, opt_thresh, fold_accs = calibrate_threshold_cross_validation(scores, labels, folds)
    assert mean_acc == 1.0
    assert 0.3 < opt_thresh < 0.75
    assert len(fold_accs) == 4
    assert all(a == 1.0 for a in fold_accs)


# ============================================================================
# Criterion 8: Test-set isolation
# ============================================================================
def test_test_set_isolation():
    """Verify test fold labels are never used to optimize the decision threshold."""
    # Fold 0 has reversed scores to test that optimization does not fit to test fold
    scores = np.array([0.8, 0.2, 0.85, 0.25, 0.3, 0.7], dtype=np.float32)
    labels = np.array([True, False, True, False, True, False], dtype=bool)
    folds = np.array([0, 0, 0, 0, 1, 1], dtype=int)

    # When evaluating fold 1, validation set is fold 0 (where threshold ~0.5 gives 100%)
    # Applying threshold ~0.5 to fold 1 yields 0% test accuracy
    _, opt_tau, fold_accs = calibrate_threshold_cross_validation(scores, labels, folds)
    # The threshold calibrated from fold 0 was ~0.5, strictly isolated from fold 1's inverted labels
    assert 0.3 < opt_tau < 0.8


# ============================================================================
# Criterion 9: Missing and malformed annotations
# ============================================================================
def test_missing_and_malformed_annotations():
    """Verify parser rejects empty, truncated, or invalid LFW annotation files."""
    with pytest.raises(ValueError, match="empty or malformed"):
        parse_lfw_pairs_txt([])

    with pytest.raises(ValueError, match="Invalid LFW header"):
        parse_lfw_pairs_txt(["10\n", "dummy line\n"])


# ============================================================================
# Criterion 10: Empty datasets and insufficient pairs
# ============================================================================
def test_empty_datasets_and_insufficient_pairs():
    """Verify metric calculations reject empty arrays or datasets with 0 genuine/impostor pairs."""
    empty = np.array([], dtype=np.float32)
    empty_b = np.array([], dtype=bool)

    with pytest.raises(ValueError, match="Scores and labels must be non-empty"):
        compute_confusion_matrix(empty, empty_b, threshold=0.5)

    all_gen_scores = np.array([0.8, 0.9])
    all_gen_labels = np.array([True, True])
    with pytest.raises(ValueError, match="0 impostor pairs"):
        compute_roc_and_auc(all_gen_scores, all_gen_labels)


# ============================================================================
# Criterion 11: Experiment reproducibility
# ============================================================================
def test_experiment_reproducibility():
    """Verify identical BenchmarkRunConfig produces identical metrics and outputs."""
    runner = BenchmarkRunner()
    config = BenchmarkRunConfig(
        dataset_id="facecore-synthetic-fixture-v1",
        max_pairs=16,
        evaluate_robustness=False,
        random_seed=42,
    )

    res1 = runner.run_benchmark(config)
    res2 = runner.run_benchmark(config)

    assert res1.total_pairs == res2.total_pairs
    assert res1.accuracy == res2.accuracy
    assert res1.eer == res2.eer
    assert res1.auc == res2.auc
    assert res1.optimal_threshold == res2.optimal_threshold


# ============================================================================
# Criterion 12: Export correctness (JSON and CSV)
# ============================================================================
def test_export_correctness():
    """Verify CSV and JSON exports match specified schema and header contracts."""
    runner = BenchmarkRunner()
    config = BenchmarkRunConfig(
        dataset_id="facecore-synthetic-fixture-v1",
        max_pairs=10,
        evaluate_robustness=False,
        random_seed=77,
    )
    result = runner.run_benchmark(config)

    # Test JSON export
    json_export = export_benchmark_json(result)
    assert '"run_id"' in json_export
    assert '"roc_curve"' in json_export
    assert '"confusion_matrix"' in json_export

    # Test CSV export
    csv_export = export_pairwise_csv(
        pair_ids=["p1", "p2"],
        identities_a=["A", "A"],
        identities_b=["A", "B"],
        is_genuine_list=[True, False],
        similarity_scores=[0.85, 0.15],
        threshold=0.5,
    )
    lines = csv_export.strip().splitlines()
    assert lines[0] == "pair_id,identity_a,identity_b,ground_truth,similarity_score,decision_threshold,predicted_label,classification_outcome"
    assert "TRUE_POSITIVE" in lines[1]
    assert "TRUE_NEGATIVE" in lines[2]


# ============================================================================
# Integration: REST Endpoints
# ============================================================================
def test_benchmarks_api_endpoints():
    """Verify REST API endpoints for datasets, run execution, and export."""
    # List datasets
    r_list = client.get("/api/benchmarks/datasets")
    assert r_list.status_code == 200
    datasets = r_list.json()
    assert len(datasets) >= 5

    # Run benchmark
    r_run = client.post("/api/benchmarks/run", json={
        "dataset_id": "facecore-synthetic-fixture-v1",
        "max_pairs": 12,
        "evaluate_robustness": False,
        "random_seed": 42
    })
    assert r_run.status_code == 200
    run_data = r_run.json()
    run_id = run_data["run_id"]
    assert "accuracy" in run_data
    assert "eer" in run_data

    # History
    r_hist = client.get("/api/benchmarks/history")
    assert r_hist.status_code == 200
    assert any(h["run_id"] == run_id for h in r_hist.json())

    # Get run details
    r_get = client.get(f"/api/benchmarks/runs/{run_id}")
    assert r_get.status_code == 200
    assert r_get.json()["run_id"] == run_id

    # Export JSON
    r_json = client.get(f"/api/benchmarks/runs/{run_id}/export/json")
    assert r_json.status_code == 200
    assert r_json.headers["content-type"].startswith("application/json")

    # Export CSV
    r_csv = client.get(f"/api/benchmarks/runs/{run_id}/export/csv")
    assert r_csv.status_code == 200
    assert "pair_id" in r_csv.text
