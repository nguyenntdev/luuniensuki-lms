"""Evaluation package for Research V4.2."""

from research_v4_2.eval.metrics import (
    accuracy,
    roc_auc,
    nll,
    brier_score,
    ece,
    f1_score,
    mae,
    rmse,
    percentile_latency,
    geometric_mean,
    ndcg_at_k,
    aurc,
    krippendorff_alpha,
)
from research_v4_2.eval.statistics import (
    cluster_bootstrap_ci,
    paired_cluster_bootstrap_delta,
    paired_permutation_test,
    holm_bonferroni,
    power_feasibility_check,
)

__all__ = [
    "accuracy",
    "roc_auc",
    "nll",
    "brier_score",
    "ece",
    "f1_score",
    "mae",
    "rmse",
    "percentile_latency",
    "geometric_mean",
    "ndcg_at_k",
    "aurc",
    "krippendorff_alpha",
    "cluster_bootstrap_ci",
    "paired_cluster_bootstrap_delta",
    "paired_permutation_test",
    "holm_bonferroni",
    "power_feasibility_check",
]
