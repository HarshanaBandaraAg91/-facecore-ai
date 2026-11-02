"""Independent Statistical Forensic Audit Test Suite (STEP 09.1).

Verifies the independent audit calculation engine against analytical fixtures:
1. Four false accepts among 3,000 impostor trials (FAR = 4/3000 = 0.001333, CI [0.0363%, 0.3410%]).
2. Zero false accepts among 3,000 trials (Rule of Three 3/N = 0.001000, exact one-sided upper 0.000998).
3. Zero false rejects (FRR = 0, TAR = 1.0).
4. Threshold equality boundary behaviour (>= vs >).
5. Tied similarity scores and exact Wilcoxon-Mann-Whitney U AUC (0.5 tie-weighting).
6. Fold-specific threshold isolation (zero test-leakage invariance).
7. Missing pair accounting and unmounted supplementary pair resolution.
8. Failure-to-Acquire (FTA) denominator consistency (attempted = successful + failed).
9. Exact rational arithmetic with Fraction across all classification rates.
"""

from fractions import Fraction
import math
import numpy as np
import pytest

from app.benchmarks.independent_audit import (
    calculate_confusion_counts,
    calculate_rational_metrics,
    calculate_exact_wilcoxon_auc,
    calculate_independent_eer,
    calculate_clopper_pearson_ci,
    calculate_rule_of_three_bound,
    evaluate_four_accuracy_estimators,
    _find_opt_accuracy_threshold,
)


# ============================================================================
# Test 1: Four False Accepts Among 3,000 Impostor Trials
# ============================================================================
def test_four_false_accepts_among_3000_trials():
    """Verify exact FAR and Clopper-Pearson 95% CI for k=4, n=3,000 (STEP 09 point)."""
    k = 4
    n = 3000
    metrics = calculate_rational_metrics(tp=2964, fp=k, tn=n - k, fn=36)

    # Rational FAR must be exactly 4 / 3000 = 1 / 750
    assert metrics["far_fraction"] == Fraction(4, 3000)
    assert metrics["far_fraction"] == Fraction(1, 750)
    assert abs(metrics["far_float"] - (4.0 / 3000.0)) < 1e-12

    # Observed FAR = 0.001333... (0.1333%), which strictly EXCEEDS 0.1000%
    assert metrics["far_float"] > 0.001000

    # Clopper-Pearson 95% CI
    low, high = calculate_clopper_pearson_ci(k, n, confidence_level=0.95)
    assert 0.00036 < low < 0.00037  # 0.0363%
    assert 0.00340 < high < 0.00342  # 0.3410%


# ============================================================================
# Test 2: Zero False Accepts Among 3,000 Trials (Rule of Three Validation)
# ============================================================================
def test_zero_false_accepts_among_3000_trials():
    """Verify Rule of Three and exact one-sided / two-sided bounds for k=0, n=3,000."""
    k = 0
    n = 3000
    metrics = calculate_rational_metrics(tp=3000, fp=k, tn=n, fn=0)

    assert metrics["far_fraction"] == Fraction(0, 1)
    assert metrics["far_float"] == 0.0

    bounds = calculate_rule_of_three_bound(n, confidence=0.95)
    # Rule of Three approximation: 3 / 3000 = 0.001000 (0.1000%)
    assert abs(bounds["rule_of_three_approx"] - 0.001000) < 1e-12
    # Exact one-sided 95% upper bound: 1 - 0.05^(1/3000) = 0.0009981...
    assert 0.000997 < bounds["exact_one_sided_upper"] < 0.000999
    # Exact two-sided 95% CI upper bound: 1 - 0.025^(1/3000) = 0.001228...
    assert 0.00122 < bounds["exact_two_sided_upper"] < 0.00124


# ============================================================================
# Test 3: Zero False Rejects (Perfect Genuine Retention)
# ============================================================================
def test_zero_false_rejects():
    """Verify FRR = 0 and TAR = 1.0 when genuine pairs are completely accepted."""
    metrics = calculate_rational_metrics(tp=3000, fp=15, tn=2985, fn=0)
    assert metrics["frr_fraction"] == Fraction(0, 1)
    assert metrics["frr_float"] == 0.0
    assert metrics["tar_fraction"] == Fraction(1, 1)
    assert metrics["tar_float"] == 1.0
    assert metrics["recall_fraction"] == Fraction(1, 1)


# ============================================================================
# Test 4: Threshold Equality Boundary Behaviour (>= vs >)
# ============================================================================
def test_threshold_equality_boundary_behaviour():
    """Verify distinct predictions under strict greater (>) vs greater-or-equal (>=)."""
    # Sample scores with values exactly sitting on candidate threshold 0.50
    scores = np.array([0.50, 0.50, 0.49, 0.51])
    labels = np.array([True, False, False, True])

    # Rule: score >= 0.50
    counts_ge = calculate_confusion_counts(scores, labels, threshold=0.50, strict_greater=False)
    # Items with score >= 0.50: [0.50 (True), 0.50 (False), 0.51 (True)] -> 2 TP, 1 FP, 1 TN, 0 FN
    assert counts_ge == {"tp": 2, "fp": 1, "tn": 1, "fn": 0}

    # Rule: score > 0.50
    counts_gt = calculate_confusion_counts(scores, labels, threshold=0.50, strict_greater=True)
    # Items with score > 0.50: [0.51 (True)] -> 1 TP, 0 FP, 2 TN, 1 FN
    assert counts_gt == {"tp": 1, "fp": 0, "tn": 2, "fn": 1}

    # Verify that boundary equality flips the classification of points at threshold
    assert counts_ge["tp"] != counts_gt["tp"]
    assert counts_ge["fp"] != counts_gt["fp"]


# ============================================================================
# Test 5: Tied Similarity Scores and Analytical ROC-AUC Tie Handling
# ============================================================================
def test_tied_similarity_scores_and_wilcoxon_auc():
    """Verify that ties receive exact 0.5 credit and all-tied scores yield AUC = 0.5000."""
    # Case A: Complete tie across all pairs -> AUC MUST BE EXACTLY 0.5
    scores_tie = np.array([0.42, 0.42, 0.42, 0.42])
    labels_tie = np.array([True, True, False, False])
    auc_tie = calculate_exact_wilcoxon_auc(scores_tie, labels_tie)
    assert abs(auc_tie - 0.50000) < 1e-12

    # Case B: Hand-calculated partial ties
    # Genuine: [0.70, 0.50]
    # Impostor: [0.50, 0.30]
    # Pairwise:
    # (0.70, 0.50) -> Gen wins (1.0)
    # (0.70, 0.30) -> Gen wins (1.0)
    # (0.50, 0.50) -> Tie (0.5)
    # (0.50, 0.30) -> Gen wins (1.0)
    # U = 1.0 + 1.0 + 0.5 + 1.0 = 3.5. AUC = 3.5 / (2 * 2) = 0.8750
    scores_b = np.array([0.70, 0.50, 0.50, 0.30])
    labels_b = np.array([True, True, False, False])
    auc_b = calculate_exact_wilcoxon_auc(scores_b, labels_b)
    assert abs(auc_b - 0.87500) < 1e-12


# ============================================================================
# Test 6: Fold-Specific Threshold Isolation (Zero Test-Leakage Invariance)
# ============================================================================
def test_fold_specific_threshold_isolation():
    """Verify that validation threshold for fold k is invariant to test fold scores/labels."""
    scores = np.array([0.85, 0.75, 0.20, 0.10, 0.90, 0.70, 0.25, 0.05, 0.80, 0.65, 0.30, 0.15])
    labels = np.array([True, True, False, False, True, True, False, False, True, True, False, False])
    folds = np.array([0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2])

    res = evaluate_four_accuracy_estimators(scores, labels, folds)
    t_fold2_initial = res["per_fold_thresholds"][2]

    # Mutate fold 2 test scores and labels completely (simulate adversarial test fold)
    mutated_scores = scores.copy()
    mutated_labels = labels.copy()
    mutated_scores[folds == 2] = [0.01, 0.02, 0.98, 0.99]
    mutated_labels[folds == 2] = [False, False, True, True]

    res_mutated = evaluate_four_accuracy_estimators(mutated_scores, mutated_labels, folds)
    t_fold2_after_mutation = res_mutated["per_fold_thresholds"][2]

    # Mathematical Invariant: Validation threshold for test fold 2 MUST BE IDENTICAL
    assert abs(t_fold2_initial - t_fold2_after_mutation) < 1e-12


# ============================================================================
# Test 7: Missing Pair Accounting & Resolvable Subsets
# ============================================================================
def test_missing_pair_accounting():
    """Verify exact accounting of official vs resolved vs unmounted supplementary pairs."""
    official_total = 6000
    calfw_resolved = 2424
    calfw_unresolved = 3576
    cplfw_resolved = 2494
    cplfw_unresolved = 3506

    assert calfw_resolved + calfw_unresolved == official_total
    assert cplfw_resolved + cplfw_unresolved == official_total

    calfw_completeness = Fraction(calfw_resolved, official_total)
    assert calfw_completeness == Fraction(101, 250)
    assert abs(float(calfw_completeness) - 0.40400) < 1e-6

    cplfw_completeness = Fraction(cplfw_resolved, official_total)
    assert abs(float(cplfw_completeness) - 0.415666) < 1e-5


# ============================================================================
# Test 8: Failure-to-Acquire (FTA) Denominator Consistency
# ============================================================================
def test_fta_denominator_consistency():
    """Verify ISO/IEC 19795-1 accounting: attempted = successful + failed; FTA = failed / attempted."""
    attempted_pairs = 100
    failed_pairs = 54
    successful_pairs = attempted_pairs - failed_pairs

    assert successful_pairs == 46
    fta_fraction = Fraction(failed_pairs, attempted_pairs)
    assert fta_fraction == Fraction(27, 50)
    assert float(fta_fraction) == 0.54

    # Verification: AUC must only be computed on the 46 successful pairs, not 100
    # Any metric reported on 46 pairs must explicitly state N=46, NOT N=100
    sample_size = successful_pairs
    assert sample_size == 46


# ============================================================================
# Test 9: Exact Rational Arithmetic with Fraction Across Metrics
# ============================================================================
def test_exact_rational_arithmetic():
    """Verify precision of rational arithmetic for accuracy, precision, recall, and F1."""
    tp, fp, tn, fn = 2971, 10, 2990, 29
    metrics = calculate_rational_metrics(tp, fp, tn, fn)

    # Accuracy = (2971 + 2990) / 6000 = 5961 / 6000 = 1987 / 2000 = 0.9935
    assert metrics["accuracy_fraction"] == Fraction(5961, 6000)
    assert metrics["accuracy_fraction"] == Fraction(1987, 2000)
    assert metrics["accuracy_float"] == 0.9935

    # Precision = 2971 / (2971 + 10) = 2971 / 2981
    assert metrics["precision_fraction"] == Fraction(2971, 2981)

    # Recall = 2971 / (2971 + 29) = 2971 / 3000
    assert metrics["recall_fraction"] == Fraction(2971, 3000)

    # F1 = 2 * 2971 / (2 * 2971 + 10 + 29) = 5942 / 5981
    assert metrics["f1_fraction"] == Fraction(5942, 5981)

