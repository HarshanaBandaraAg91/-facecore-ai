"""Statistical and mathematical metric calculations for face verification benchmarks.

Adheres to strict biometric evaluation standards:
- ROC and Trapezoidal ROC-AUC
- Equal Error Rate (EER) with fine interpolation
- FAR, FRR, and TAR @ fixed FAR operating points
- Cross-validation threshold calibration (never optimizing on test partitions)
- 95% Bootstrap Confidence Intervals
- CSV and JSON export routines
"""

import io
import csv
import json
from typing import List, Tuple, Dict, Any, Optional
import numpy as np

from app.benchmarks.schemas import (
    ROCCurvePoint,
    TARAtFAR,
    ConfusionMatrix,
    ConfidenceInterval,
    BenchmarkResult,
)


def compute_confusion_matrix(
    scores: np.ndarray,
    labels: np.ndarray,
    threshold: float,
) -> ConfusionMatrix:
    """Compute confusion matrix and related classification rates at a specific threshold."""
    scores = np.asarray(scores, dtype=np.float32)
    labels = np.asarray(labels, dtype=bool)

    if len(scores) != len(labels) or len(scores) == 0:
        raise ValueError("Scores and labels must be non-empty and of identical length.")

    preds = scores >= threshold
    tp = int(np.sum(preds & labels))
    fp = int(np.sum(preds & ~labels))
    tn = int(np.sum(~preds & ~labels))
    fn = int(np.sum(~preds & labels))
    total = len(labels)

    accuracy = float((tp + tn) / total) if total > 0 else 0.0
    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 1.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = (
        float(2.0 * precision * recall / (precision + recall))
        if (precision + recall) > 0
        else 0.0
    )

    return ConfusionMatrix(
        tp=tp,
        fp=fp,
        tn=tn,
        fn=fn,
        accuracy=round(accuracy, 5),
        precision=round(precision, 5),
        recall=round(recall, 5),
        f1_score=round(f1, 5),
    )


def compute_exact_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Calculate exact analytical Area Under ROC Curve via Wilcoxon-Mann-Whitney U statistic.

    Formulation:
        AUC = (sum_{i in Gen} sum_{j in Imp} [I(s_i > s_j) + 0.5 * I(s_i == s_j)]) / (N_gen * N_imp)
    Guarantees exact mathematical equivalence to the integral of the true continuous ROC curve,
    properly accounting for score ties without threshold discretization error.
    """
    scores = np.asarray(scores, dtype=np.float32)
    labels = np.asarray(labels, dtype=bool)

    pos = scores[labels]
    neg = scores[~labels]
    n_pos = len(pos)
    n_neg = len(neg)

    if n_pos == 0 or n_neg == 0:
        raise ValueError("Cannot compute AUC with 0 genuine or 0 impostor pairs.")

    greater = np.sum(pos[:, None] > neg[None, :])
    equal = np.sum(pos[:, None] == neg[None, :])
    u_stat = float(greater + 0.5 * equal)
    return float(u_stat / (n_pos * n_neg))


def compute_roc_and_auc(
    scores: np.ndarray,
    labels: np.ndarray,
    num_thresholds: int = 250,
) -> Tuple[List[ROCCurvePoint], float]:
    """Calculate ROC curve telemetry points and exact analytical Area Under the Curve (AUC)."""
    scores = np.asarray(scores, dtype=np.float32)
    labels = np.asarray(labels, dtype=bool)

    n_gen = int(np.sum(labels))
    n_imp = int(np.sum(~labels))

    if n_gen == 0 or n_imp == 0:
        raise ValueError("Cannot compute ROC curve with 0 genuine or 0 impostor pairs.")

    # Threshold evaluation sweep for ROC curve visualization
    score_min = float(np.min(scores))
    score_max = float(np.max(scores))
    thresholds = np.linspace(score_max + 0.01, score_min - 0.01, num_thresholds)

    curve_points: List[ROCCurvePoint] = []
    for t in thresholds:
        preds = scores >= t
        tp = float(np.sum(preds & labels))
        fp = float(np.sum(preds & ~labels))
        fn = float(np.sum(~preds & labels))

        far = float(fp / n_imp)
        frr = float(fn / n_gen)
        tar = float(1.0 - frr)
        prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 1.0

        curve_points.append(
            ROCCurvePoint(
                threshold=round(float(t), 5),
                far=round(far, 5),
                frr=round(frr, 5),
                tar=round(tar, 5),
                precision=round(prec, 5),
                recall=round(tar, 5),
            )
        )

    # Compute exact analytical AUC via Wilcoxon-Mann-Whitney U statistic
    exact_auc = compute_exact_auc(scores, labels)
    return curve_points, round(exact_auc, 5)


def compute_eer(
    scores: np.ndarray,
    labels: np.ndarray,
    search_steps: int = 1000,
) -> Tuple[float, float]:
    """Calculate Equal Error Rate (EER) with exact linear interpolation between crossover points."""
    scores = np.asarray(scores, dtype=np.float32)
    labels = np.asarray(labels, dtype=bool)

    n_gen = int(np.sum(labels))
    n_imp = int(np.sum(~labels))
    if n_gen == 0 or n_imp == 0:
        raise ValueError("Cannot compute EER with 0 genuine or 0 impostor pairs.")

    thresholds = np.linspace(float(np.min(scores)), float(np.max(scores)), search_steps)

    fars = []
    frrs = []
    for t in thresholds:
        preds = scores >= t
        fp = float(np.sum(preds & ~labels))
        fn = float(np.sum(~preds & labels))
        fars.append(fp / n_imp)
        frrs.append(fn / n_gen)

    fars_arr = np.array(fars, dtype=np.float64)
    frrs_arr = np.array(frrs, dtype=np.float64)
    diff = fars_arr - frrs_arr

    # 1. Exact zero difference match
    zero_idx = np.where(np.isclose(diff, 0.0, atol=1e-7))[0]
    if len(zero_idx) > 0:
        idx = zero_idx[0]
        return round(float(fars_arr[idx]), 5), round(float(thresholds[idx]), 5)

    # 2. Adjacent linear interpolation across crossover interval (where FAR - FRR changes sign)
    crossover_indices = np.where(diff[:-1] * diff[1:] <= 0)[0]
    if len(crossover_indices) > 0:
        i = crossover_indices[0]
        t1, t2 = thresholds[i], thresholds[i + 1]
        far1, far2 = fars_arr[i], fars_arr[i + 1]
        frr1, frr2 = frrs_arr[i], frrs_arr[i + 1]

        # Solve for alpha in [0, 1] where far(alpha) == frr(alpha):
        # far1 + alpha * (far2 - far1) = frr1 + alpha * (frr2 - frr1)
        denom = (frr2 - frr1) - (far2 - far1)
        if abs(denom) > 1e-9:
            alpha = (far1 - frr1) / denom
            alpha = max(0.0, min(1.0, float(alpha)))
            eer_interp = far1 + alpha * (far2 - far1)
            t_interp = t1 + alpha * (t2 - t1)
            return round(float(eer_interp), 5), round(float(t_interp), 5)

    # 3. Minimum discrete absolute difference fallback
    best_idx = int(np.argmin(np.abs(diff)))
    best_eer = (fars_arr[best_idx] + frrs_arr[best_idx]) / 2.0
    return round(float(best_eer), 5), round(float(thresholds[best_idx]), 5)


def compute_tar_at_far(
    scores: np.ndarray,
    labels: np.ndarray,
    target_fars: Optional[List[float]] = None,
) -> List[TARAtFAR]:
    """Calculate True Acceptance Rate at predefined FAR operating points with statistical sample validation."""
    if target_fars is None:
        target_fars = [0.1, 0.05, 0.01, 0.001]

    scores = np.asarray(scores, dtype=np.float32)
    labels = np.asarray(labels, dtype=bool)

    n_gen = int(np.sum(labels))
    n_imp = int(np.sum(~labels))
    if n_gen == 0 or n_imp == 0:
        return []

    # Sort impostor scores descending
    imp_scores = np.sort(scores[~labels])[::-1]
    results: List[TARAtFAR] = []

    for alpha in target_fars:
        # Find threshold achieving empirical FAR <= alpha
        cutoff_idx = int(np.floor(alpha * n_imp))
        if cutoff_idx >= len(imp_scores):
            thresh = float(imp_scores[-1])
        elif cutoff_idx <= 0:
            thresh = float(imp_scores[0]) + 1e-4
        else:
            thresh = float(imp_scores[cutoff_idx])

        # Evaluate empirical false accepts and true accepts at this threshold
        fa_count = int(np.sum(scores[~labels] >= thresh))
        observed_far = float(fa_count / n_imp)
        tp_count = int(np.sum(scores[labels] >= thresh))
        tar = float(tp_count / n_gen) if n_gen > 0 else 0.0

        # Statistical sample size validation:
        # 1. Basic sample validity: N_imp >= 1 / alpha (at least 1 error theoretically observable)
        is_valid = n_imp >= (1.0 / alpha)
        # 2. Rule of Three validity (Wayman 1999): N_imp >= 3 / alpha for 95% CI upper bound <= alpha
        rule_of_three_threshold = int(np.ceil(3.0 / alpha))
        r3_valid = n_imp >= rule_of_three_threshold

        advisory = None
        if not r3_valid:
            advisory = (
                f"Sample size (N={n_imp} impostor pairs) is insufficient to reliably validate "
                f"target FAR={alpha}. Rule of Three requires at least {rule_of_three_threshold} impostors."
            )

        results.append(
            TARAtFAR(
                far_target=alpha,
                tar=round(tar, 5),
                threshold=round(thresh, 5),
                observed_far=round(observed_far, 5),
                false_accept_count=fa_count,
                total_impostors=n_imp,
                is_statistically_valid=is_valid,
                rule_of_three_valid=r3_valid,
                sample_size_advisory=advisory,
            )
        )

    return results


def calibrate_threshold_cross_validation(
    scores: np.ndarray,
    labels: np.ndarray,
    folds: np.ndarray,
    return_oof_preds: bool = False,
) -> Any:
    """Strictly calibrate decision threshold on validation folds and evaluate on test fold."""
    scores = np.asarray(scores, dtype=np.float32)
    labels = np.asarray(labels, dtype=bool)
    folds = np.asarray(folds, dtype=int)

    unique_folds = np.unique(folds)
    oof_preds = np.zeros(len(scores), dtype=bool)

    if len(unique_folds) <= 1:
        opt_thresh, acc = _find_optimal_threshold(scores, labels)
        oof_preds = scores >= opt_thresh
        if return_oof_preds:
            return round(acc, 5), round(opt_thresh, 5), [round(acc, 5)], oof_preds
        return round(acc, 5), round(opt_thresh, 5), [round(acc, 5)]

    fold_accuracies: List[float] = []
    calibrated_thresholds: List[float] = []

    for k in unique_folds:
        val_mask = folds != k
        test_mask = folds == k

        if not np.any(val_mask) or not np.any(test_mask):
            continue

        # Calibrate threshold solely on validation folds
        val_scores = scores[val_mask]
        val_labels = labels[val_mask]
        tau_k, _ = _find_optimal_threshold(val_scores, val_labels)
        calibrated_thresholds.append(tau_k)

        # Apply calibrated tau_k to unseen test fold k
        test_scores = scores[test_mask]
        test_labels = labels[test_mask]
        k_preds = test_scores >= tau_k
        oof_preds[test_mask] = k_preds
        test_acc = float(np.mean(k_preds == test_labels))
        fold_accuracies.append(test_acc)

    mean_acc = float(np.mean(fold_accuracies)) if fold_accuracies else 0.0
    mean_tau = float(np.mean(calibrated_thresholds)) if calibrated_thresholds else 0.0

    if return_oof_preds:
        return round(mean_acc, 5), round(mean_tau, 5), [round(a, 5) for a in fold_accuracies], oof_preds
    return round(mean_acc, 5), round(mean_tau, 5), [round(a, 5) for a in fold_accuracies]


def _find_optimal_threshold(scores: np.ndarray, labels: np.ndarray) -> Tuple[float, float]:
    """Find decision threshold maximizing validation classification accuracy.

    Uses candidate evaluation across sorted unique score midpoints and selects
    the midpoint of the largest contiguous optimal segment for maximum margin.
    """
    sorted_unique = np.unique(scores)
    if len(sorted_unique) == 1:
        t = float(sorted_unique[0])
        acc = float(np.mean((scores >= t) == labels))
        return t, acc

    # Candidate evaluation points: midpoints between consecutive unique scores, plus boundaries
    midpoints = (sorted_unique[:-1] + sorted_unique[1:]) / 2.0
    candidates = np.concatenate([
        [sorted_unique[0] - 0.01],
        midpoints,
        [sorted_unique[-1] + 0.01],
    ])

    best_acc = -1.0
    best_thresholds: List[float] = []
    total = len(labels)

    for t in candidates:
        preds = scores >= t
        acc = float(np.sum(preds == labels) / total)
        if acc > best_acc + 1e-7:
            best_acc = acc
            best_thresholds = [float(t)]
        elif abs(acc - best_acc) <= 1e-7:
            best_thresholds.append(float(t))

    if not best_thresholds:
        return 0.0, 0.0

    # Identify contiguous optimal intervals and choose midpoint of the largest contiguous segment
    best_thresholds.sort()
    segments: List[List[float]] = [[best_thresholds[0]]]
    for i in range(1, len(best_thresholds)):
        # If consecutive candidates in best_thresholds are adjacent in candidates array
        prev_idx = np.where(candidates == best_thresholds[i - 1])[0]
        curr_idx = np.where(candidates == best_thresholds[i])[0]
        if len(prev_idx) > 0 and len(curr_idx) > 0 and curr_idx[0] - prev_idx[0] == 1:
            segments[-1].append(best_thresholds[i])
        else:
            segments.append([best_thresholds[i]])

    largest_segment = max(segments, key=len)
    opt_midpoint = float((largest_segment[0] + largest_segment[-1]) / 2.0)

    # Verify that opt_midpoint indeed achieves best_acc
    mid_acc = float(np.mean((scores >= opt_midpoint) == labels))
    if mid_acc < best_acc - 1e-6:
        # Fallback to the median optimal candidate
        opt_midpoint = float(best_thresholds[len(best_thresholds) // 2])

    return float(opt_midpoint), best_acc


def compute_bootstrap_confidence_intervals(
    scores: np.ndarray,
    labels: np.ndarray,
    optimal_threshold: float,
    clusters: Optional[List[str]] = None,
    n_bootstraps: int = 1000,
    seed: int = 42,
) -> List[ConfidenceInterval]:
    """Calculate 95% Confidence Intervals via non-parametric Bootstrap Resampling.

    Supports both standard pair-level bootstrap and identity-clustered bootstrap.
    When 'clusters' (e.g. subject identities or fold IDs) are provided, resamples
    clusters with replacement to preserve within-subject correlation structure.
    """
    rng = np.random.RandomState(seed)
    n_samples = len(scores)

    if n_samples < 10:
        return []

    acc_boots = []
    eer_boots = []
    auc_boots = []

    if clusters is not None and len(clusters) == n_samples:
        cluster_arr = np.asarray(clusters)
        unique_clusters = np.unique(cluster_arr)
        n_clusters = len(unique_clusters)
        use_clustering = n_clusters >= 4
    else:
        use_clustering = False

    for _ in range(n_bootstraps):
        if use_clustering:
            # Identity-clustered bootstrap: sample clusters with replacement
            sampled_c = rng.choice(unique_clusters, size=n_clusters, replace=True)
            sampled_indices = []
            for c in sampled_c:
                sampled_indices.extend(np.where(cluster_arr == c)[0])
            idx = np.array(sampled_indices, dtype=int)
        else:
            # Standard pair-level bootstrap
            idx = rng.randint(0, n_samples, size=n_samples)

        b_scores = scores[idx]
        b_labels = labels[idx]

        if np.sum(b_labels) == 0 or np.sum(~b_labels) == 0:
            continue

        preds = b_scores >= optimal_threshold
        acc_boots.append(float(np.mean(preds == b_labels)))

        try:
            eer_val, _ = compute_eer(b_scores, b_labels, search_steps=100)
            eer_boots.append(eer_val)
        except Exception:
            pass

        try:
            auc_val = compute_exact_auc(b_scores, b_labels)
            auc_boots.append(auc_val)
        except Exception:
            pass

    intervals: List[ConfidenceInterval] = []

    def make_ci(name: str, values: List[float]):
        if not values:
            return None
        arr = np.array(values)
        return ConfidenceInterval(
            metric=name,
            mean=round(float(np.mean(arr)), 5),
            ci_lower=round(float(np.percentile(arr, 2.5)), 5),
            ci_upper=round(float(np.percentile(arr, 97.5)), 5),
            confidence_level=0.95,
        )

    ci_acc = make_ci("Accuracy", acc_boots)
    ci_eer = make_ci("EER", eer_boots)
    ci_auc = make_ci("ROC-AUC", auc_boots)

    for item in [ci_acc, ci_eer, ci_auc]:
        if item is not None:
            intervals.append(item)

    return intervals


def compare_bootstrap_methods(
    scores: np.ndarray,
    labels: np.ndarray,
    optimal_threshold: float,
    clusters: List[str],
    n_bootstraps: int = 500,
    seed: int = 42,
) -> Dict[str, Any]:
    """Compare empirical confidence intervals between Pair-Level and Identity-Clustered Bootstrap."""
    ci_pair = compute_bootstrap_confidence_intervals(
        scores, labels, optimal_threshold, clusters=None, n_bootstraps=n_bootstraps, seed=seed
    )
    ci_cluster = compute_bootstrap_confidence_intervals(
        scores, labels, optimal_threshold, clusters=clusters, n_bootstraps=n_bootstraps, seed=seed
    )
    return {
        "pair_level": {ci.metric: {"lower": ci.ci_lower, "upper": ci.ci_upper, "width": round(ci.ci_upper - ci.ci_lower, 5)} for ci in ci_pair},
        "identity_clustered": {ci.metric: {"lower": ci.ci_lower, "upper": ci.ci_upper, "width": round(ci.ci_upper - ci.ci_lower, 5)} for ci in ci_cluster},
    }


def export_benchmark_json(result: BenchmarkResult) -> str:
    """Serialize full benchmark run result to formatted JSON string."""
    return result.model_dump_json(indent=2)


def export_pairwise_csv(
    pair_ids: List[str],
    identities_a: List[str],
    identities_b: List[str],
    is_genuine_list: List[bool],
    similarity_scores: List[float],
    threshold: float,
) -> str:
    """Generate structured CSV of all evaluated pairs with classification decisions."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "pair_id",
        "identity_a",
        "identity_b",
        "ground_truth",
        "similarity_score",
        "decision_threshold",
        "predicted_label",
        "classification_outcome",
    ])

    for pid, ida, idb, gen, score in zip(
        pair_ids, identities_a, identities_b, is_genuine_list, similarity_scores
    ):
        pred_match = score >= threshold
        if gen and pred_match:
            outcome = "TRUE_POSITIVE"
        elif not gen and not pred_match:
            outcome = "TRUE_NEGATIVE"
        elif not gen and pred_match:
            outcome = "FALSE_POSITIVE"
        else:
            outcome = "FALSE_NEGATIVE"

        writer.writerow([
            pid,
            ida,
            idb,
            "GENUINE" if gen else "IMPOSTOR",
            f"{score:.5f}",
            f"{threshold:.5f}",
            "MATCH" if pred_match else "NON_MATCH",
            outcome,
        ])

    return output.getvalue()


def evaluate_transferred_threshold(
    scores: np.ndarray,
    labels: np.ndarray,
    threshold: float,
) -> Tuple[float, ConfusionMatrix]:
    """Evaluate accuracy and confusion matrix under a fixed transferred threshold without tuning."""
    preds = scores >= threshold
    tp = int(np.sum(preds & labels))
    fp = int(np.sum(preds & ~labels))
    tn = int(np.sum(~preds & ~labels))
    fn = int(np.sum(~preds & labels))
    total = len(labels)
    acc = float((tp + tn) / total) if total > 0 else 0.0
    prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 1.0
    rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = float(2.0 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

    cm = ConfusionMatrix(
        tp=tp,
        fp=fp,
        tn=tn,
        fn=fn,
        accuracy=round(acc, 5),
        precision=round(prec, 5),
        recall=round(rec, 5),
        f1_score=round(f1, 5),
    )
    return round(acc, 5), cm


def export_benchmark_markdown(result: BenchmarkResult) -> str:
    """Generate comprehensive scientific Markdown audit report for a benchmark run."""
    md = []
    md.append(f"# FACECORE AI — Benchmark Run Report: `{result.run_id}`\n")
    md.append(f"**Dataset:** {result.dataset_name} (`{result.dataset_id}`)")
    md.append(f"**Evaluated Model:** {result.model_name} (v{result.model_version})")
    md.append(f"**Timestamp:** {result.timestamp}")
    md.append(f"**Execution Duration:** {result.execution_time_seconds:.2f} seconds")
    md.append(f"**Evaluation Protocol:** {result.evaluation_protocol or 'Standard'}\n")

    md.append("## 1. Summary Metrics\n")
    md.append("| Metric | Observed Value |")
    md.append("| :--- | :--- |")
    md.append(f"| **Verification Accuracy** | **{result.accuracy * 100.0:.2f}%** |")
    md.append(f"| **Optimal Native Threshold ($\\tau^*$)** | **{result.optimal_threshold:.4f}** |")
    md.append(f"| **Area Under ROC (AUC)** | **{result.auc:.4f}** |")
    md.append(f"| **Equal Error Rate (EER)** | **{result.eer * 100.0:.2f}%** (at $\\tau={result.eer_threshold:.4f}$) |")
    md.append(f"| **Total Evaluated Pairs** | {result.total_pairs} ({result.genuine_pairs} genuine, {result.impostor_pairs} impostor) |")
    md.append(f"| **Failure-to-Acquire (FTA Rate)** | {result.failure_to_acquire_rate * 100.0:.2f}% ({result.failure_to_acquire_count} failures) |\n")

    if result.transferred_threshold is not None and result.transferred_accuracy is not None:
        md.append("## 2. Threshold Transfer Performance (Cross-Dataset Generalization)\n")
        md.append(f"**Source Threshold:** $\\tau = {result.transferred_threshold:.4f}$ ({result.transferred_threshold_source or 'Transferred'})\n")
        md.append("| Metric | Dataset-Specific Native Threshold | Transferred Threshold | Delta ($\\Delta$) |")
        md.append("| :--- | :--- | :--- | :--- |")
        diff = result.accuracy - result.transferred_accuracy
        md.append(f"| Threshold ($\\tau$) | {result.optimal_threshold:.4f} | {result.transferred_threshold:.4f} | {result.optimal_threshold - result.transferred_threshold:+.4f} |")
        md.append(f"| Accuracy | {result.accuracy * 100.0:.2f}% | {result.transferred_accuracy * 100.0:.2f}% | {-diff * 100.0:+.2f}% |")
        if result.transferred_confusion_matrix:
            tcm = result.transferred_confusion_matrix
            ncm = result.confusion_matrix
            gen_total = ncm.tp + ncm.fn
            imp_total = ncm.tn + ncm.fp
            if gen_total > 0:
                md.append(f"| False Rejection Rate (FRR) | {ncm.fn / gen_total * 100.0:.2f}% | {tcm.fn / gen_total * 100.0:.2f}% | {(tcm.fn - ncm.fn) / gen_total * 100.0:+.2f}% |")
            if imp_total > 0:
                md.append(f"| False Acceptance Rate (FAR) | {ncm.fp / imp_total * 100.0:.2f}% | {tcm.fp / imp_total * 100.0:.2f}% | {(tcm.fp - ncm.fp) / imp_total * 100.0:+.2f}% |\n")

    if result.confidence_intervals:
        md.append("## 3. Bootstrap Confidence Intervals (95% CI)\n")
        md.append("| Metric | Observed Mean | 95% Lower Bound | 95% Upper Bound |")
        md.append("| :--- | :--- | :--- | :--- |")
        for ci in result.confidence_intervals:
            md.append(f"| {ci.metric} | {ci.mean:.4f} | {ci.ci_lower:.4f} | {ci.ci_upper:.4f} |")
        md.append("")

    if result.robustness_results:
        md.append("## 4. Controlled Robustness Degradation Analysis\n")
        md.append("| Perturbation Condition | Sample Size | Accuracy | EER | AUC | TAR @ FAR=1% |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for r in result.robustness_results:
            md.append(f"| **{r.condition_name}** | {r.sample_size} | {r.accuracy * 100.0:.1f}% | {r.eer * 100.0:.1f}% | {r.auc:.4f} | {r.tar_at_far_01 * 100.0:.1f}% |")
        md.append("")

    md.append("## 5. Audit & Scientific Provenance\n")
    md.append(f"- **Evaluation Completeness:** `{result.evaluation_completeness or 'UNKNOWN'}`")
    md.append(f"- **Official Protocol Pairs:** {result.official_total_pairs or result.total_pairs}")
    md.append(f"- **Locally Resolved Pairs:** {result.resolved_pairs_count or result.total_pairs}")
    if result.unresolved_pairs_count:
        md.append(f"- **Unresolved Missing Pairs:** {result.unresolved_pairs_count} ({result.missing_images_count} missing images)")
    md.append(f"- **Pair List Hash (SHA-256):** `{result.pair_list_hash or 'N/A'}`")
    md.append(f"- **YuNet Weights Hash:** `{result.yunet_weights_hash or 'N/A'}`")
    md.append(f"- **SFace Weights Hash:** `{result.sface_weights_hash or 'N/A'}`")
    md.append(f"- **Manifest Fingerprint (SHA-256):** `{result.dataset_manifest_hash}`")
    md.append(f"- **Model Weights Fingerprint:** `{result.model_weights_hash}`")
    md.append(f"- **System Environment:** `{result.system_environment}`")
    md.append(f"- **Metric Calculation Version:** `{result.metric_calculation_version or 'v1'}`")
    if result.reproducibility_command:
        md.append(f"\n### Reproducibility Command:\n```bash\n{result.reproducibility_command}\n```\n")

    return "\n".join(md)
