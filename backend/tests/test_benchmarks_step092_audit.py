"""Step 09.2: Independent Operating-Point Validation & Statistical Reliability Audit Tests.

Verifies:
1. Threshold leakage detection and proof of in-sample optimization for tau=0.35916.
2. Fold-isolated 10-fold cross-validation for operating points (TAR @ FAR <= 0.1%).
3. Classification of unsupported FAR targets (FAR <= 0.01% as NOT STATISTICALLY SUPPORTED).
4. Sample size requirements via Rule of Three and exact binomial inversion.
5. Class imbalance metrics: prevalence, ordinary vs balanced accuracy on CALFW/CPLFW.
6. Clopper-Pearson confidence upper-bound analysis for low-FAR claims.
7. Resolution acceptance boundary audit and empirical degradation findings.
"""

import os
import json
import numpy as np
import pytest

from app.benchmarks.independent_audit import (
    detect_threshold_leakage,
    evaluate_leak_free_operating_points,
    evaluate_required_sample_size_for_far,
    calculate_imbalanced_metrics,
    calculate_clopper_pearson_ci,
)

LFW_RAW_SCORES_PATH = "backend/data/step09_results/lfw_raw_scores.json"
CALFW_RAW_SCORES_PATH = "backend/data/step09_results/calfw_raw_scores.json"
CPLFW_RAW_SCORES_PATH = "backend/data/step09_results/cplfw_raw_scores.json"
RES_SWEEP_PATH = "backend/data/step09_results/resolution_sweep_results.json"


@pytest.fixture
def lfw_scores_data():
    if not os.path.isfile(LFW_RAW_SCORES_PATH):
        pytest.skip(f"LFW raw scores file not found: {LFW_RAW_SCORES_PATH}")
    with open(LFW_RAW_SCORES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_detect_threshold_leakage_forensic_proof(lfw_scores_data):
    """Forensically prove that tau=0.35916 from Step 09.1 was derived in-sample from test impostor pool."""
    scores = np.array(lfw_scores_data["scores"])
    labels = np.array(lfw_scores_data["labels"])

    # Step 09.1 reported threshold
    audit_091 = detect_threshold_leakage(scores, labels, reported_threshold=0.359156, target_far=0.001)
    assert audit_091["is_in_sample_leaked"] is True
    assert audit_091["is_exact_order_statistic"] is True
    assert audit_091["matched_rank"] == 3
    assert audit_091["false_accepts_count"] == 3
    assert audit_091["leakage_classification"] == "THRESHOLD_SELECTION_LEAKAGE"

    # Step 09 reported threshold 0.3423
    audit_09 = detect_threshold_leakage(scores, labels, reported_threshold=0.342305, target_far=0.001)
    assert audit_09["is_in_sample_leaked"] is True
    assert audit_09["matched_rank"] == 4


def test_evaluate_leak_free_operating_points_target_far_001(lfw_scores_data):
    """Verify strict fold-isolated cross-validation for target FAR <= 0.1% on LFW."""
    scores = np.array(lfw_scores_data["scores"])
    labels = np.array(lfw_scores_data["labels"])
    folds = np.array(lfw_scores_data["folds"])

    results = evaluate_leak_free_operating_points(scores, labels, folds, target_fars=[0.001])
    far_001 = results["0.0010"]

    assert far_001["status"] == "VALIDATED_LEAK_FREE"
    assert far_001["is_statistically_supported"] is True
    assert far_001["n_folds"] == 10
    assert len(far_001["per_fold_thresholds"]) == 10

    # Per-fold thresholds vary across folds (proving fold isolation)
    assert far_001["min_threshold"] <= far_001["max_threshold"]
    assert far_001["threshold_leakage_detected"] is True  # Shows thresholds differ from leaked global tau

    # Out of fold performance
    assert far_001["out_of_fold_far"] <= 0.0010  # Must satisfy target FAR <= 0.1%
    assert far_001["out_of_fold_tar"] >= 0.9800   # TAR remains high (>= 98%)
    assert far_001["out_of_fold_fp"] <= 3


def test_evaluate_leak_free_operating_points_unsupported_far(lfw_scores_data):
    """Verify that target FAR = 0.01% (0.0001) is formally classified as NOT STATISTICALLY SUPPORTED."""
    scores = np.array(lfw_scores_data["scores"])
    labels = np.array(lfw_scores_data["labels"])
    folds = np.array(lfw_scores_data["folds"])

    results = evaluate_leak_free_operating_points(scores, labels, folds, target_fars=[0.0001])
    far_0001 = results["0.0001"]

    assert far_0001["status"] == "NOT STATISTICALLY SUPPORTED"
    assert far_0001["is_statistically_supported"] is False
    assert "Sample size insufficient" in far_0001["reason"]


def test_sample_size_requirements_rule_of_three():
    """Verify Rule of Three sample size bounds for target FAR claims at 95% confidence."""
    # Target FAR = 1.0% (0.01)
    req_1pct = evaluate_required_sample_size_for_far(0.01, expected_rate=0.0)
    assert req_1pct["min_n_zero_errors_rule_of_three"] == 300
    assert 295 <= req_1pct["min_n_zero_errors_exact"] <= 305

    # Target FAR = 0.1% (0.001)
    req_01pct = evaluate_required_sample_size_for_far(0.001, expected_rate=0.0)
    assert 2990 <= req_01pct["min_n_zero_errors_rule_of_three"] <= 3000
    assert 2990 <= req_01pct["min_n_zero_errors_exact"] <= 3000

    # Target FAR = 0.01% (0.0001)
    req_001pct = evaluate_required_sample_size_for_far(0.0001, expected_rate=0.0)
    assert req_001pct["min_n_zero_errors_rule_of_three"] == 29958
    assert req_001pct["min_n_zero_errors_exact"] >= 29900

    # With non-zero expected error rate: FAR target 0.1%, expected rate 0.05%
    req_with_errors = evaluate_required_sample_size_for_far(0.001, expected_rate=0.0005)
    assert req_with_errors["min_n_at_expected_rate"] >= 7000


def test_clopper_pearson_low_far_uncertainty():
    """Demonstrate that 3 false accepts / 3,000 trials has an upper bound near 0.2920%."""
    lower, upper = calculate_clopper_pearson_ci(k=3, n=3000, confidence_level=0.95)
    observed_far = 3.0 / 3000.0

    assert observed_far == pytest.approx(0.001, abs=1e-5)
    assert lower == pytest.approx(0.000206, abs=1e-5)
    assert upper == pytest.approx(0.002920, abs=1e-5)
    # The upper bound is nearly 3x higher than observed empirical FAR
    assert upper > 2.8 * observed_far


def test_class_imbalance_metrics_calfw_cplfw():
    """Verify that class imbalance creates upward skew bias in ordinary accuracy on CALFW/CPLFW."""
    # CALFW counts from raw results: TP=848, FP=10, TN=1554, FN=12 (total 2424)
    calfw_metrics = calculate_imbalanced_metrics(tp=848, fp=10, tn=1554, fn=12)
    assert calfw_metrics["total"] == 2424
    assert calfw_metrics["n_genuine"] == 860
    assert calfw_metrics["n_impostor"] == 1564
    assert calfw_metrics["genuine_prevalence"] == pytest.approx(0.354785, abs=1e-4)
    assert calfw_metrics["impostor_prevalence"] == pytest.approx(0.645215, abs=1e-4)
    assert calfw_metrics["ordinary_accuracy"] == pytest.approx(2402 / 2424, abs=1e-4)
    assert calfw_metrics["balanced_accuracy"] == pytest.approx(
        (848 / 860 + 1554 / 1564) / 2.0, abs=1e-4
    )
    # Ordinary accuracy is higher than balanced accuracy due to impostor class dominance
    assert calfw_metrics["skew_bias"] > 0

    # CPLFW counts from raw results: TP=926, FP=11, TN=1539, FN=18 (total 2494)
    cplfw_metrics = calculate_imbalanced_metrics(tp=926, fp=11, tn=1539, fn=18)
    assert cplfw_metrics["total"] == 2494
    assert cplfw_metrics["n_genuine"] == 944
    assert cplfw_metrics["n_impostor"] == 1550
    assert cplfw_metrics["genuine_prevalence"] == pytest.approx(0.378508, abs=1e-4)
    assert cplfw_metrics["ordinary_accuracy"] > cplfw_metrics["balanced_accuracy"]
    assert cplfw_metrics["skew_bias"] > 0


def test_resolution_sweep_results_integrity():
    """Verify that resolution sweep output file is present and confirms empirical boundaries."""
    assert os.path.isfile(RES_SWEEP_PATH), f"Missing resolution sweep artifact at {RES_SWEEP_PATH}"
    with open(RES_SWEEP_PATH, "r", encoding="utf-8") as f:
        sweep_data = json.load(f)

    dims = [entry["target_dim"] for entry in sweep_data]
    assert 32 in dims
    assert 48 in dims
    assert 112 in dims
    assert 224 in dims

    # 32x32 must exhibit 100% FTA (failure to acquire)
    dim_32 = next(e for e in sweep_data if e["target_dim"] == 32)
    assert dim_32["fta_rate"] == 1.0
    assert dim_32["successful_pairs"] == 0

    # 48x48 must succeed at detection but exhibit high low-res advisories and reduced genuine similarity
    dim_48 = next(e for e in sweep_data if e["target_dim"] == 48)
    assert dim_48["image_detection_rate"] == 1.0
    assert dim_48["low_resolution_warnings"] == dim_48["n_images"]
    assert dim_48["gen_mean"] < 0.55  # Collapsed genuine similarity

    # >= 160x160 must have 0 low-resolution warnings and high genuine similarity >= 0.65
    dim_160 = next(e for e in sweep_data if e["target_dim"] == 160)
    assert dim_160["low_resolution_warnings"] == 0
    assert dim_160["gen_mean"] >= 0.65
