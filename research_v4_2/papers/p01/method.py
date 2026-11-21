"""Proposed Method for P01: Capacity-Coupled Robust Risk Controller.

Addresses worst-course selective risk under term shift and human review capacity constraints.
"""

from __future__ import annotations

import numpy as np
from typing import Dict, Any, Optional
from research_v4_2.papers.p01.baselines import BasePredictor


class CapacityCoupledRiskController:
    """Capacity-Coupled Robust Risk Controller (Proposed Candidate).

    Minimizes worst-group selective risk while strictly satisfying finite-sample
    review capacity constraints sum(a_i) = K.
    Uses calibrated group error profiling, density ratio bounds, and group-risk regularization.
    """

    def __init__(
        self,
        base_model: BasePredictor,
        lambda_robust: float = 2.5,
        min_group_fraction: float = 0.10,
        random_state: int = 42,
    ):
        self.base_model = base_model
        self.lambda_robust = lambda_robust
        self.min_group_fraction = min_group_fraction
        self.random_state = random_state
        self.name = "CapacityCoupledRiskController"
        self.calibrated_group_risks: Dict[int, float] = {}
        self.group_inflation_factors: Dict[int, float] = {}

    def calibrate(
        self,
        X_cal: np.ndarray,
        y_cal: np.ndarray,
        groups_cal: np.ndarray,
    ) -> CapacityCoupledRiskController:
        """Calibrates group-wise base error profiles on calibration data."""
        probs = self.base_model.predict_proba(X_cal)
        preds = (probs[:, 1] >= 0.5).astype(int)
        errors = (preds != y_cal).astype(float)
        mean_err = float(np.mean(errors)) if len(errors) > 0 else 0.3

        unique_groups = np.unique(groups_cal)
        for g in unique_groups:
            mask = groups_cal == g
            if np.sum(mask) > 0:
                g_err = float(np.mean(errors[mask]))
                self.calibrated_group_risks[int(g)] = g_err
                self.group_inflation_factors[int(g)] = g_err / max(1e-4, mean_err)
            else:
                self.calibrated_group_risks[int(g)] = mean_err
                self.group_inflation_factors[int(g)] = 1.0
        return self

    def estimate_density_ratios(self, X: np.ndarray) -> np.ndarray:
        """Estimates bounded importance weights based on feature dispersion."""
        norms = np.linalg.norm(X - np.mean(X, axis=0, keepdims=True), axis=1)
        median_norm = np.median(norms) if len(norms) > 0 else 1.0
        w = 1.0 + 0.3 * np.tanh((norms - median_norm) / (median_norm + 1e-6))
        return np.clip(w, 0.8, 1.4)

    def select(
        self,
        X: np.ndarray,
        target_k: int,
        groups: np.ndarray,
    ) -> np.ndarray:
        """Selects exactly target_k instances to retain for prediction (1=predict, 0=defer to review).

        Optimizes worst-course selective risk by penalizing non-conformity in shifted high-risk strata.
        """
        n = len(X)
        k = min(max(1, target_k), n)
        probs = self.base_model.predict_proba(X)
        preds = (probs[:, 1] >= 0.5).astype(int)

        # Base non-conformity score
        base_nonconf = 1.0 - probs[np.arange(len(preds)), preds]
        density_ratios = self.estimate_density_ratios(X)

        # Compute adjusted scores incorporating group risk inflation and density ratios
        adjusted_scores = np.zeros(n, dtype=float)
        unique_groups = np.unique(groups)

        for g in unique_groups:
            idx = np.where(groups == g)[0]
            factor = self.group_inflation_factors.get(int(g), 1.0)
            # Power scaling by lambda_robust shifts review priority toward high-risk groups
            adjusted_scores[idx] = base_nonconf[idx] * (factor ** self.lambda_robust) * density_ratios[idx]

        # Select top-k smallest adjusted non-conformity scores
        selected = np.zeros(n, dtype=int)
        top_k_indices = np.argsort(adjusted_scores)[:k]
        selected[top_k_indices] = 1

        # Strict invariant verification
        assert np.sum(selected) == k, f"Expected {k} selected, got {np.sum(selected)}"
        return selected
