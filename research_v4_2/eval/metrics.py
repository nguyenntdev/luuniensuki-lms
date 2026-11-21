"""Evaluation metrics library for Research V4.2.

Provides exact, reproducible implementations for classification, ranking,
continuous latency/regression, calibration, selective risk, and agreement metrics.
"""

from __future__ import annotations

import math
from typing import List, Sequence, Union
import numpy as np


def accuracy(y_true: Sequence[int], y_pred: Sequence[int]) -> float:
    """Compute standard classification accuracy."""
    yt = np.asarray(y_true)
    yp = np.asarray(y_pred)
    if len(yt) == 0:
        return 0.0
    return float(np.mean(yt == yp))


def roc_auc(y_true: Sequence[int], y_score: Sequence[float]) -> float:
    """Compute Area Under the Receiver Operating Characteristic Curve (ROC-AUC) via trapezoidal rule."""
    yt = np.asarray(y_true, dtype=int)
    ys = np.asarray(y_score, dtype=float)
    if len(yt) == 0:
        return 0.5
    pos_mask = (yt == 1)
    n_pos = int(np.sum(pos_mask))
    n_neg = len(yt) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5

    # Rank-sum calculation (Mann-Whitney U)
    order = np.argsort(ys)
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(len(ys)) + 1

    # Handle ties by assigning average rank
    sorted_scores = ys[order]
    _, unique_indices, counts = np.unique(sorted_scores, return_index=True, return_counts=True)
    for idx, count in zip(unique_indices, counts):
        if count > 1:
            tie_ranks = np.mean(np.arange(idx + 1, idx + count + 1))
            tied_indices = order[idx : idx + count]
            ranks[tied_indices] = tie_ranks

    sum_pos_ranks = float(np.sum(ranks[pos_mask]))
    u = sum_pos_ranks - (n_pos * (n_pos + 1)) / 2.0
    return float(u / (n_pos * n_neg))


def nll(y_true: Sequence[int], y_prob: Sequence[float], eps: float = 1e-15) -> float:
    """Negative Log-Likelihood (Binary Cross-Entropy)."""
    yt = np.asarray(y_true, dtype=float)
    yp = np.clip(np.asarray(y_prob, dtype=float), eps, 1.0 - eps)
    if len(yt) == 0:
        return 0.0
    losses = -(yt * np.log(yp) + (1.0 - yt) * np.log(1.0 - yp))
    return float(np.mean(losses))


def brier_score(y_true: Sequence[int], y_prob: Sequence[float]) -> float:
    """Compute Brier Score (Mean Squared Probability Error)."""
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_prob, dtype=float)
    if len(yt) == 0:
        return 0.0
    return float(np.mean((yp - yt) ** 2))


def ece(y_true: Sequence[int], y_prob: Sequence[float], n_bins: int = 10) -> float:
    """Expected Calibration Error with equal-width binning."""
    yt = np.asarray(y_true, dtype=int)
    yp = np.asarray(y_prob, dtype=float)
    n = len(yt)
    if n == 0:
        return 0.0

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece_val = 0.0
    for i in range(n_bins):
        b_low, b_high = bins[i], bins[i + 1]
        mask = (yp >= b_low) & (yp <= b_high if i == n_bins - 1 else yp < b_high)
        n_b = np.sum(mask)
        if n_b > 0:
            bin_acc = float(np.mean(yt[mask]))
            bin_conf = float(np.mean(yp[mask]))
            ece_val += (n_b / n) * abs(bin_acc - bin_conf)
    return float(ece_val)


def f1_score(y_true: Sequence[int], y_pred: Sequence[int]) -> float:
    """Binary F1 score."""
    yt = np.asarray(y_true, dtype=int)
    yp = np.asarray(y_pred, dtype=int)
    tp = int(np.sum((yt == 1) & (yp == 1)))
    fp = int(np.sum((yt == 0) & (yp == 1)))
    fn = int(np.sum((yt == 1) & (yp == 0)))
    if tp == 0:
        return 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    if precision + recall == 0:
        return 0.0
    return float(2.0 * (precision * recall) / (precision + recall))


def mae(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    """Mean Absolute Error."""
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    if len(yt) == 0:
        return 0.0
    return float(np.mean(np.abs(yt - yp)))


def rmse(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    """Root Mean Squared Error."""
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    if len(yt) == 0:
        return 0.0
    return float(np.sqrt(np.mean((yt - yp) ** 2)))


def percentile_latency(latencies: Sequence[float], percentile: float = 95.0) -> float:
    """Compute percentile latency in milliseconds."""
    arr = np.asarray(latencies, dtype=float)
    if len(arr) == 0:
        return 0.0
    return float(np.percentile(arr, percentile))


def geometric_mean(values: Sequence[float], eps: float = 1e-9) -> float:
    """Compute geometric mean of positive values."""
    arr = np.asarray(values, dtype=float)
    arr = np.clip(arr, eps, None)
    if len(arr) == 0:
        return 0.0
    return float(np.exp(np.mean(np.log(arr))))


def ndcg_at_k(relevance_true: Sequence[float], scores_pred: Sequence[float], k: int = 10) -> float:
    """Normalized Discounted Cumulative Gain at rank K."""
    rel = np.asarray(relevance_true, dtype=float)
    scores = np.asarray(scores_pred, dtype=float)
    if len(rel) == 0 or k <= 0:
        return 0.0

    k = min(k, len(rel))
    order = np.argsort(-scores)[:k]
    dcg = float(np.sum(rel[order] / np.log2(np.arange(2, k + 2))))

    ideal_order = np.argsort(-rel)[:k]
    idcg = float(np.sum(rel[ideal_order] / np.log2(np.arange(2, k + 2))))
    if idcg <= 0.0:
        return 0.0
    return float(dcg / idcg)


def aurc(risks: Sequence[float], coverages: Sequence[float]) -> float:
    """Area Under the Risk-Coverage curve for selective classification."""
    r = np.asarray(risks, dtype=float)
    c = np.asarray(coverages, dtype=float)
    order = np.argsort(c)
    return float(np.trapz(r[order], c[order]))


def krippendorff_alpha(ratings: Sequence[Sequence[Union[int, float, None]]]) -> float:
    """Compute Krippendorff's Alpha for nominal agreement across multiple raters with missing values.
    
    ratings: 2D array of shape (units, raters). None or NaN represents missing rating.
    """
    matrix = np.array(ratings, dtype=object)
    n_units, n_raters = matrix.shape

    # Find unique non-null categories
    all_vals = []
    for u in range(n_units):
        for r in range(n_raters):
            val = matrix[u, r]
            if val is not None and not (isinstance(val, float) and math.isnan(val)):
                all_vals.append(val)
    categories = sorted(list(set(all_vals)))
    if len(categories) <= 1:
        return 1.0  # Perfect agreement if only 1 category used

    cat_to_idx = {cat: i for i, cat in enumerate(categories)}
    num_cats = len(categories)

    # Unit coincident coincidence matrix
    coincidence = np.zeros((num_cats, num_cats), dtype=float)
    total_pairs = 0.0

    for u in range(n_units):
        unit_vals = [
            cat_to_idx[matrix[u, r]]
            for r in range(n_raters)
            if matrix[u, r] is not None and not (isinstance(matrix[u, r], float) and math.isnan(matrix[u, r]))
        ]
        m_u = len(unit_vals)
        if m_u > 1:
            counts = np.bincount(unit_vals, minlength=num_cats)
            for c1 in range(num_cats):
                for c2 in range(num_cats):
                    if c1 == c2:
                        coincidence[c1, c1] += counts[c1] * (counts[c1] - 1) / (m_u - 1)
                    else:
                        coincidence[c1, c2] += counts[c1] * counts[c2] / (m_u - 1)
            total_pairs += m_u

    if total_pairs == 0:
        return 0.0

    # Marginals
    n_c = np.sum(coincidence, axis=1)
    total_entries = np.sum(n_c)
    if total_entries == 0:
        return 0.0

    # Observed disagreement
    observed_disagreement = np.sum(coincidence) - np.trace(coincidence)

    # Expected disagreement
    expected_disagreement = 0.0
    for c1 in range(num_cats):
        for c2 in range(num_cats):
            if c1 != c2:
                expected_disagreement += (n_c[c1] * n_c[c2]) / (total_entries - 1)

    if expected_disagreement == 0:
        return 1.0

    alpha = 1.0 - (observed_disagreement / expected_disagreement)
    return float(alpha)
