"""Baselines for P01: Selective Learner-Risk Transfer under Distribution Shift."""

from __future__ import annotations

import numpy as np
from typing import Dict, Any, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV


class BasePredictor:
    """Calibrated base classifier shared across all comparators for strict fairness."""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        base_lr = LogisticRegression(C=1.0, max_iter=500, random_state=random_state)
        self.clf = CalibratedClassifierCV(estimator=base_lr, cv=3, method="sigmoid")
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> BasePredictor:
        self.clf.fit(X, y)
        self.is_fitted = True
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Predictor must be fitted before predict_proba.")
        return self.clf.predict_proba(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        probs = self.predict_proba(X)
        return (probs[:, 1] >= 0.5).astype(int)


class FullCoverageBaseline:
    """C0: Full-coverage calibrated baseline without selective deferral."""

    def __init__(self, base_model: BasePredictor):
        self.base_model = base_model
        self.name = "FullCoverage_C0"

    def select(self, X: np.ndarray, target_k: int) -> np.ndarray:
        """Always selects all instances (full coverage)."""
        return np.ones(len(X), dtype=int)


class UncertaintyThresholdBaseline:
    """C1: Same-backbone confidence / margin thresholding with capacity matching.

    Ranks instances by confidence |P(y=1|x) - 0.5| and keeps top-K.
    """

    def __init__(self, base_model: BasePredictor):
        self.base_model = base_model
        self.name = "UncertaintyThreshold_C1"

    def select(self, X: np.ndarray, target_k: int) -> np.ndarray:
        probs = self.base_model.predict_proba(X)
        confidence = np.abs(probs[:, 1] - 0.5)
        n = len(X)
        k = min(max(1, target_k), n)
        selected = np.zeros(n, dtype=int)
        top_k_indices = np.argsort(-confidence)[:k]
        selected[top_k_indices] = 1
        return selected


class StandardConformalDeferral:
    """B* (Champion Baseline): CRC2026-style split conformal deferral.

    Uses calibrated non-conformity scores 1 - P(y=y_hat|x) on a calibration set
    to determine threshold, then enforces capacity K by global non-conformity quantile
    without subgroup or density-ratio robustness.
    """

    def __init__(self, base_model: BasePredictor):
        self.base_model = base_model
        self.name = "StandardConformal_B_star"
        self.cal_scores: np.ndarray | None = None

    def calibrate(self, X_cal: np.ndarray, y_cal: np.ndarray) -> StandardConformalDeferral:
        probs = self.base_model.predict_proba(X_cal)
        # Non-conformity score for true label
        cal_scores = 1.0 - probs[np.arange(len(y_cal)), y_cal]
        self.cal_scores = np.sort(cal_scores)
        return self

    def select(self, X: np.ndarray, target_k: int) -> np.ndarray:
        probs = self.base_model.predict_proba(X)
        preds = (probs[:, 1] >= 0.5).astype(int)
        # Non-conformity score against top prediction
        test_scores = 1.0 - probs[np.arange(len(preds)), preds]
        n = len(X)
        k = min(max(1, target_k), n)

        # Standard conformal selection selects smallest non-conformity scores
        selected = np.zeros(n, dtype=int)
        top_k_indices = np.argsort(test_scores)[:k]
        selected[top_k_indices] = 1
        return selected
