"""FACECORE AI — Independent Statistical Forensic Audit Engine (STEP 09.1).

This module implements an entirely independent metric recalculation engine
WITHOUT importing or calling any production functions from app.benchmarks.metrics.
All calculations are implemented from first mathematical principles using exact
rational and floating-point arithmetic.
"""

from fractions import Fraction
import math
from typing import Dict, List, Optional, Tuple, Any
import numpy as np


# ============================================================================
# 1. Exact Count-Based Rates & Rational Arithmetic
# ============================================================================
def calculate_confusion_counts(
    scores: np.ndarray,
    labels: np.ndarray,
    threshold: float,
    strict_greater: bool = False,
) -> Dict[str, int]:
    """Calculate confusion matrix counts with explicit threshold equality semantics."""
    scores = np.asarray(scores, dtype=np.float64)
    labels = np.asarray(labels, dtype=bool)

    if strict_greater:
        preds = scores > threshold
    else:
        preds = scores >= threshold

    tp = int(np.sum(preds & labels))
    fp = int(np.sum(preds & ~labels))
    tn = int(np.sum(~preds & ~labels))
    fn = int(np.sum(~preds & labels))

    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def calculate_rational_metrics(tp: int, fp: int, tn: int, fn: int) -> Dict[str, Any]:
    """Compute exact rational classification rates using fractions.Fraction."""
    total = tp + fp + tn + fn
    if total == 0:
        raise ValueError("Cannot calculate rates on empty sample (total=0).")

    accuracy = Fraction(tp + tn, total)
    precision = Fraction(tp, tp + fp) if (tp + fp) > 0 else Fraction(0, 1)
    recall = Fraction(tp, tp + fn) if (tp + fn) > 0 else Fraction(0, 1)

    f1_denom = (2 * tp + fp + fn)
    f1_score = Fraction(2 * tp, f1_denom) if f1_denom > 0 else Fraction(0, 1)

    n_gen = tp + fn
    n_imp = fp + tn

    far = Fraction(fp, n_imp) if n_imp > 0 else Fraction(0, 1)
    frr = Fraction(fn, n_gen) if n_gen > 0 else Fraction(0, 1)
    tar = Fraction(tp, n_gen) if n_gen > 0 else Fraction(0, 1)

    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "total": total,
        "n_genuine": n_gen,
        "n_impostor": n_imp,
        "accuracy_fraction": accuracy,
        "accuracy_float": float(accuracy),
        "precision_fraction": precision,
        "precision_float": float(precision),
        "recall_fraction": recall,
        "recall_float": float(recall),
        "f1_fraction": f1_score,
        "f1_float": float(f1_score),
        "far_fraction": far,
        "far_float": float(far),
        "frr_fraction": frr,
        "frr_float": float(frr),
        "tar_fraction": tar,
        "tar_float": float(tar),
    }


# ============================================================================
# 2. Exact Wilcoxon-Mann-Whitney U Statistic (Analytical ROC-AUC)
# ============================================================================
def calculate_exact_wilcoxon_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Independently calculate exact Mann-Whitney U statistic with strict 0.5 ties.

    AUC = [sum_{i in Gen} sum_{j in Imp} (I(s_i > s_j) + 0.5 * I(s_i == s_j))] / (N_gen * N_imp)
    """
    scores = np.asarray(scores, dtype=np.float64)
    labels = np.asarray(labels, dtype=bool)

    pos = scores[labels]
    neg = scores[~labels]
    n_pos = len(pos)
    n_neg = len(neg)

    if n_pos == 0 or n_neg == 0:
        raise ValueError("Cannot calculate AUC with 0 genuine or 0 impostor pairs.")

    # Pairwise broadcast comparisons
    greater = np.sum(pos[:, None] > neg[None, :], dtype=np.int64)
    equal = np.sum(pos[:, None] == neg[None, :], dtype=np.int64)

    u_stat = float(greater) + 0.5 * float(equal)
    return float(u_stat / (n_pos * n_neg))


# ============================================================================
# 3. Equal Error Rate (EER) with Exact Linear Crossover Interpolation
# ============================================================================
def calculate_independent_eer(
    scores: np.ndarray,
    labels: np.ndarray,
    num_grid_points: int = 50000,
) -> Tuple[float, float]:
    """Independently calculate EER via linear interpolation between crossover thresholds."""
    scores = np.asarray(scores, dtype=np.float64)
    labels = np.asarray(labels, dtype=bool)

    pos = scores[labels]
    neg = scores[~labels]
    n_pos = len(pos)
    n_neg = len(neg)

    if n_pos == 0 or n_neg == 0:
        raise ValueError("Cannot calculate EER with 0 genuine or 0 impostor pairs.")

    min_s = float(scores.min())
    max_s = float(scores.max())
    grid = np.linspace(min_s - 1e-4, max_s + 1e-4, num_grid_points)

    # Vectorized FAR and FRR
    fars = np.mean(neg[:, None] >= grid[None, :], axis=0)
    frrs = np.mean(pos[:, None] < grid[None, :], axis=0)
    diffs = fars - frrs

    # Identify zero-crossing points
    cross_idx = np.where(np.diff(np.sign(diffs)))[0]
    if len(cross_idx) > 0:
        idx = cross_idx[0]
        t0, t1 = grid[idx], grid[idx + 1]
        far0, far1 = fars[idx], fars[idx + 1]
        frr0, frr1 = frrs[idx], frrs[idx + 1]

        # Solve for intersection where FAR(t) = FRR(t):
        # far(t) = far0 + (t - t0) * (far1 - far0) / (t1 - t0)
        # frr(t) = frr0 + (t - t0) * (frr1 - frr0) / (t1 - t0)
        denom = (far1 - far0) - (frr1 - frr0)
        if abs(denom) > 1e-12:
            fraction = (frr0 - far0) / denom
            eer_thresh = t0 + fraction * (t1 - t0)
            eer_val = far0 + fraction * (far1 - far0)
        else:
            eer_thresh = (t0 + t1) / 2.0
            eer_val = (far0 + frr0) / 2.0
    else:
        min_idx = np.argmin(np.abs(diffs))
        eer_thresh = float(grid[min_idx])
        eer_val = float((fars[min_idx] + frrs[min_idx]) / 2.0)

    return float(eer_val), float(eer_thresh)


# ============================================================================
# 4. Exact Clopper-Pearson Binomial Confidence Intervals
# ============================================================================
def binomial_cdf(k: int, n: int, p: float) -> float:
    """Binomial distribution CDF: P(X <= k; n, p)."""
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    if p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 0.0

    # Direct log-binomial sum
    total_prob = 0.0
    for i in range(k + 1):
        log_c = math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
        term = math.exp(log_c + i * math.log(p) + (n - i) * math.log(1.0 - p))
        total_prob += term
    return min(1.0, total_prob)


def calculate_clopper_pearson_ci(k: int, n: int, confidence_level: float = 0.95) -> Tuple[float, float]:
    """Exact Clopper-Pearson binomial confidence interval via bisection on CDF."""
    if n <= 0:
        raise ValueError("Sample size n must be positive.")
    if k < 0 or k > n:
        raise ValueError(f"k must be in [0, {n}], got {k}.")

    alpha = 1.0 - confidence_level

    # Lower bound
    if k == 0:
        lower = 0.0
    else:
        low, high = 0.0, float(k) / n
        target = 1.0 - alpha / 2.0
        for _ in range(80):
            mid = (low + high) / 2.0
            val = binomial_cdf(k - 1, n, mid)
            if val > target:
                low = mid
            else:
                high = mid
        lower = (low + high) / 2.0

    # Upper bound
    if k == n:
        upper = 1.0
    else:
        low, high = float(k) / n, 1.0
        target = alpha / 2.0
        for _ in range(80):
            mid = (low + high) / 2.0
            val = binomial_cdf(k, n, mid)
            if val < target:
                high = mid
            else:
                low = mid
        upper = (low + high) / 2.0

    return float(lower), float(upper)


def calculate_rule_of_three_bound(n: int, confidence: float = 0.95) -> Dict[str, float]:
    """Rule of Three and exact zero-event upper bound for n trials."""
    if n <= 0:
        raise ValueError("n must be positive.")

    # Exact one-sided 95% bound: 1 - 0.05^(1/n)
    alpha = 1.0 - confidence
    exact_one_sided_upper = 1.0 - math.pow(alpha, 1.0 / n)

    # Standard Rule of Three approximation: -ln(alpha) / n ~= 3.0 / n
    rule_of_three_upper = -math.log(alpha) / n
    heuristic_three_over_n = 3.0 / n

    # Exact two-sided 95% CI upper bound: 1 - 0.025^(1/n)
    exact_two_sided_upper = 1.0 - math.pow(alpha / 2.0, 1.0 / n)

    return {
        "n": n,
        "rule_of_three_approx": heuristic_three_over_n,
        "log_exact_upper": rule_of_three_upper,
        "exact_one_sided_upper": exact_one_sided_upper,
        "exact_two_sided_upper": exact_two_sided_upper,
    }


# ============================================================================
# 5. Independent Cross-Validation & Estimator Suite
# ============================================================================
def _find_opt_accuracy_threshold(scores: np.ndarray, labels: np.ndarray, steps: int = 5000) -> Tuple[float, float]:
    """Find threshold that maximizes empirical accuracy on a set of scores and labels."""
    min_s = float(scores.min())
    max_s = float(scores.max())
    candidates = np.linspace(min_s, max_s, steps)
    best_acc = -1.0
    best_t = 0.0
    for t in candidates:
        acc = float(np.mean((scores >= t) == labels))
        if acc > best_acc:
            best_acc = acc
            best_t = float(t)
    return best_t, best_acc


def evaluate_four_accuracy_estimators(
    scores: np.ndarray,
    labels: np.ndarray,
    folds: np.ndarray,
) -> Dict[str, Any]:
    """Evaluate and contrast the four primary cross-validation accuracy estimators.

    Estimator A: Mean of per-fold test accuracies using fold-specific validation thresholds.
    Estimator B: Pooled Out-of-Fold (OOF) accuracy using fold-specific validation thresholds.
    Estimator C: In-sample global accuracy using a single global accuracy-maximizing threshold.
    Estimator D: Mean of per-fold test accuracies evaluated at the mean validation threshold.
    """
    scores = np.asarray(scores, dtype=np.float64)
    labels = np.asarray(labels, dtype=bool)
    folds = np.asarray(folds, dtype=int)

    unique_folds = sorted(list(set(folds)))
    n_folds = len(unique_folds)
    n_total = len(scores)

    per_fold_threshs: List[float] = []
    per_fold_accs: List[float] = []
    per_fold_confusion: List[Dict[str, int]] = []
    oof_predictions = np.zeros(n_total, dtype=bool)

    for k in unique_folds:
        val_mask = (folds != k)
        test_mask = (folds == k)

        # 1. Validation-only threshold selection (strictly excluding test fold k)
        val_t, _ = _find_opt_accuracy_threshold(scores[val_mask], labels[val_mask])
        per_fold_threshs.append(val_t)

        # 2. Evaluate on test fold k
        test_preds = (scores[test_mask] >= val_t)
        oof_predictions[test_mask] = test_preds

        acc_k = float(np.mean(test_preds == labels[test_mask]))
        per_fold_accs.append(acc_k)

        counts_k = calculate_confusion_counts(scores[test_mask], labels[test_mask], val_t)
        per_fold_confusion.append(counts_k)

    # Estimator A
    estimator_a_mean = float(np.mean(per_fold_accs))
    estimator_a_std = float(np.std(per_fold_accs, ddof=1)) if n_folds > 1 else 0.0

    # Estimator B
    estimator_b_pooled = float(np.mean(oof_predictions == labels))
    oof_tp = int(np.sum(oof_predictions & labels))
    oof_fp = int(np.sum(oof_predictions & ~labels))
    oof_tn = int(np.sum(~oof_predictions & ~labels))
    oof_fn = int(np.sum(~oof_predictions & labels))
    estimator_b_metrics = calculate_rational_metrics(oof_tp, oof_fp, oof_tn, oof_fn)

    # Estimator C
    global_t, global_in_sample_acc = _find_opt_accuracy_threshold(scores, labels)
    global_counts = calculate_confusion_counts(scores, labels, global_t)
    estimator_c_metrics = calculate_rational_metrics(
        global_counts["tp"], global_counts["fp"], global_counts["tn"], global_counts["fn"]
    )

    # Estimator D
    mean_val_thresh = float(np.mean(per_fold_threshs))
    accs_at_mean_thresh = [
        float(np.mean((scores[folds == k] >= mean_val_thresh) == labels[folds == k]))
        for k in unique_folds
    ]
    estimator_d_mean = float(np.mean(accs_at_mean_thresh))

    return {
        "n_folds": n_folds,
        "per_fold_thresholds": per_fold_threshs,
        "per_fold_accuracies": per_fold_accs,
        "per_fold_confusion": per_fold_confusion,
        "estimator_a_mean_per_fold": estimator_a_mean,
        "estimator_a_std_per_fold": estimator_a_std,
        "estimator_b_pooled_oof": estimator_b_pooled,
        "estimator_b_confusion": estimator_b_metrics,
        "estimator_c_in_sample_global_acc": global_in_sample_acc,
        "estimator_c_global_threshold": global_t,
        "estimator_c_confusion": estimator_c_metrics,
        "estimator_d_mean_at_mean_thresh": estimator_d_mean,
        "mean_validation_threshold": mean_val_thresh,
    }


# ============================================================================
# 8. STEP 09.2: Forensic Operating-Point & Leakage Audit Engine
# ============================================================================

def detect_threshold_leakage(
    scores: np.ndarray,
    labels: np.ndarray,
    reported_threshold: float,
    target_far: float,
) -> Dict[str, Any]:
    """Detect whether a reported operating threshold was calculated using pooled test scores."""
    scores = np.asarray(scores, dtype=np.float64)
    labels = np.asarray(labels, dtype=bool)

    imp_scores = scores[~labels]
    n_imp = len(imp_scores)

    if n_imp == 0:
        raise ValueError("Cannot audit threshold leakage without impostor scores.")

    # Number of impostors exceeding the threshold
    fp_count = int(np.sum(imp_scores >= reported_threshold))
    empirical_far = fp_count / n_imp

    # Sorted impostor rank
    sorted_imp = np.sort(imp_scores)[::-1]
    rank_matches = np.where(np.isclose(sorted_imp, reported_threshold, atol=1e-5))[0]

    is_exact_order_statistic = len(rank_matches) > 0
    matched_rank = int(rank_matches[0]) + 1 if is_exact_order_statistic else None

    # Check if this exactly equals the pooled in-sample quantile for target_far
    target_max_fp = int(np.floor(target_far * n_imp))
    is_in_sample_leaked = (fp_count <= target_max_fp and (fp_count + 1) > target_max_fp) or is_exact_order_statistic

    return {
        "reported_threshold": reported_threshold,
        "target_far": target_far,
        "total_impostors": n_imp,
        "false_accepts_count": fp_count,
        "empirical_far": empirical_far,
        "is_exact_order_statistic": is_exact_order_statistic,
        "matched_rank": matched_rank,
        "is_in_sample_leaked": is_in_sample_leaked,
        "leakage_classification": "THRESHOLD_SELECTION_LEAKAGE" if is_in_sample_leaked else "CLEAN_OR_INDEPENDENT",
    }


def evaluate_leak_free_operating_points(
    scores: np.ndarray,
    labels: np.ndarray,
    folds: np.ndarray,
    target_fars: List[float],
) -> Dict[str, Any]:
    """Execute strict fold-isolated cross-validation for target operating points (TAR @ FAR).

    Calibrates tau_k strictly on validation folds (folds != k) to satisfy target FAR.
    Evaluates tau_k strictly on out-of-fold test partition (folds == k).
    """
    scores = np.asarray(scores, dtype=np.float64)
    labels = np.asarray(labels, dtype=bool)
    folds = np.asarray(folds, dtype=np.int32)

    unique_folds = np.unique(folds)
    n_folds = len(unique_folds)

    results_by_far = {}

    for target_far in target_fars:
        far_key = f"{target_far:.4f}"
        
        # Check validation feasibility
        # Determine average validation impostor count
        val_imp_counts = [np.sum((folds != k) & ~labels) for k in unique_folds]
        min_val_imp = min(val_imp_counts)
        allowed_val_fa = int(np.floor(target_far * min_val_imp))

        if allowed_val_fa < 1 and target_far < (1.0 / min_val_imp):
            results_by_far[far_key] = {
                "target_far": target_far,
                "status": "NOT STATISTICALLY SUPPORTED",
                "reason": (
                    f"Sample size insufficient: on {min_val_imp} validation impostors, "
                    f"target FAR {target_far*100:.2f}% requires < 1 error ({target_far * min_val_imp:.3f}). "
                    f"A single false acceptance would yield {(1.0/min_val_imp)*100:.4f}% FAR."
                ),
                "is_statistically_supported": False,
            }
            continue

        per_fold_thresholds = []
        per_fold_val_fa = []
        oof_tp = 0
        oof_fp = 0
        oof_tn = 0
        oof_fn = 0

        for k in unique_folds:
            val_mask = (folds != k)
            test_mask = (folds == k)

            val_imp = np.sort(scores[val_mask & ~labels])[::-1]
            n_val_imp = len(val_imp)
            max_fa = int(np.floor(target_far * n_val_imp))

            if max_fa == 0:
                tau_k = float(val_imp[0]) + 1e-6
            else:
                tau_k = float(val_imp[max_fa])

            per_fold_thresholds.append(tau_k)
            per_fold_val_fa.append(int(np.sum(val_imp >= tau_k)))

            test_s = scores[test_mask]
            test_l = labels[test_mask]

            preds = (test_s >= tau_k)
            oof_tp += int(np.sum(preds & test_l))
            oof_fp += int(np.sum(preds & ~test_l))
            oof_tn += int(np.sum(~preds & ~test_l))
            oof_fn += int(np.sum(~preds & test_l))

        total_gen = oof_tp + oof_fn
        total_imp = oof_fp + oof_tn

        out_of_fold_tar = oof_tp / total_gen if total_gen > 0 else 0.0
        out_of_fold_far = oof_fp / total_imp if total_imp > 0 else 0.0

        # Binomial CI on out-of-fold FAR
        far_ci_lower, far_ci_upper = calculate_clopper_pearson_ci(oof_fp, total_imp)

        # Pooled in-sample leaked threshold comparison
        pooled_imp = np.sort(scores[~labels])[::-1]
        pooled_max_fa = int(np.floor(target_far * len(pooled_imp)))
        leaked_threshold = float(pooled_imp[pooled_max_fa]) if pooled_max_fa > 0 else float(pooled_imp[0])

        results_by_far[far_key] = {
            "target_far": target_far,
            "status": "VALIDATED_LEAK_FREE",
            "is_statistically_supported": True,
            "n_folds": n_folds,
            "per_fold_thresholds": per_fold_thresholds,
            "mean_threshold": float(np.mean(per_fold_thresholds)),
            "std_threshold": float(np.std(per_fold_thresholds, ddof=1)) if n_folds > 1 else 0.0,
            "min_threshold": float(min(per_fold_thresholds)),
            "max_threshold": float(max(per_fold_thresholds)),
            "out_of_fold_tp": oof_tp,
            "out_of_fold_fp": oof_fp,
            "out_of_fold_tn": oof_tn,
            "out_of_fold_fn": oof_fn,
            "out_of_fold_tar": out_of_fold_tar,
            "out_of_fold_far": out_of_fold_far,
            "out_of_fold_far_ci_95": [far_ci_lower, far_ci_upper],
            "in_sample_leaked_threshold": leaked_threshold,
            "threshold_leakage_detected": any(
                not np.isclose(tau, leaked_threshold, atol=1e-5) for tau in per_fold_thresholds
            ),
        }

    return results_by_far


def evaluate_required_sample_size_for_far(
    target_far: float,
    expected_rate: float = 0.0,
    confidence: float = 0.95,
) -> Dict[str, Any]:
    """Calculate required sample size of impostor comparisons to support a target FAR claim."""
    if target_far <= 0 or target_far >= 1.0:
        raise ValueError("target_far must be in (0, 1).")
    if expected_rate < 0 or expected_rate >= target_far:
        raise ValueError("expected_rate must be non-negative and strictly less than target_far.")

    alpha = 1.0 - confidence

    # 1. Zero-error scenario: Rule of Three / exact binomial inversion
    n_zero_rule_of_three = math.ceil(-math.log(alpha) / target_far)
    n_zero_exact = math.ceil(math.log(alpha) / math.log(1.0 - target_far))

    # 2. Non-zero expected error rate scenario (Normal approximation / Wilson score)
    if expected_rate > 0.0:
        # z_{1 - alpha/2} for two-sided 95% CI (1.95996)
        z = 1.959963984540054
        margin = target_far - expected_rate
        # N >= [z^2 * r * (1 - r)] / margin^2
        variance = expected_rate * (1.0 - expected_rate)
        n_expected = math.ceil((z * z * variance) / (margin * margin))
    else:
        n_expected = n_zero_exact

    return {
        "target_far": target_far,
        "expected_rate": expected_rate,
        "confidence": confidence,
        "min_n_zero_errors_rule_of_three": n_zero_rule_of_three,
        "min_n_zero_errors_exact": n_zero_exact,
        "min_n_at_expected_rate": n_expected,
        "target_far_percent": target_far * 100.0,
    }


def calculate_imbalanced_metrics(tp: int, fp: int, tn: int, fn: int) -> Dict[str, Any]:
    """Compute balanced classification metrics addressing prevalence skew."""
    total = tp + fp + tn + fn
    if total == 0:
        raise ValueError("Cannot calculate metrics on empty sample (total=0).")

    n_gen = tp + fn
    n_imp = fp + tn

    gen_prevalence = n_gen / total if total > 0 else 0.0
    imp_prevalence = n_imp / total if total > 0 else 0.0
    imbalance_ratio = n_imp / n_gen if n_gen > 0 else float("inf")

    # Ordinary accuracy
    ordinary_acc = (tp + tn) / total if total > 0 else 0.0

    # Sensitivity / Recall / TPR
    tpr = tp / n_gen if n_gen > 0 else 0.0
    # Specificity / TNR
    tnr = tn / n_imp if n_imp > 0 else 0.0

    # Balanced Accuracy: (TPR + TNR) / 2
    balanced_acc = (tpr + tnr) / 2.0

    # Precision / PPV
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    # F1 score
    f1 = (2 * precision * tpr) / (precision + tpr) if (precision + tpr) > 0 else 0.0

    far = fp / n_imp if n_imp > 0 else 0.0
    frr = fn / n_gen if n_gen > 0 else 0.0

    skew_bias = ordinary_acc - balanced_acc

    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "total": total,
        "n_genuine": n_gen,
        "n_impostor": n_imp,
        "genuine_prevalence": gen_prevalence,
        "impostor_prevalence": imp_prevalence,
        "imbalance_ratio": imbalance_ratio,
        "ordinary_accuracy": ordinary_acc,
        "balanced_accuracy": balanced_acc,
        "skew_bias": skew_bias,
        "genuine_recall_tpr": tpr,
        "impostor_rejection_tnr": tnr,
        "precision_ppv": precision,
        "f1_score": f1,
        "far": far,
        "frr": frr,
    }


