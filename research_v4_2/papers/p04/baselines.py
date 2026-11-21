"""P04 Baselines: C0 (Empirical Base Rate) and C1 (Ridge Logistic Regression on Standard Bag-of-Concepts).
C2: Domain Adversarial / CORAL style feature alignment baseline.
"""
from __future__ import annotations

import numpy as np
from typing import Dict, Any, List, Optional
from sklearn.linear_model import LogisticRegression


class C0GlobalBaseRate:
    """C0: Predicts global train base rate probability."""
    def __init__(self):
        self.prior = 0.5

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.prior = float(np.mean(y)) if len(y) > 0 else 0.5
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        prob = np.full(len(X), self.prior)
        return np.column_stack([1.0 - prob, prob])


class C1StandardLogistic:
    """C1: Standard regularized Logistic Regression without shift adaptation."""
    def __init__(self, C: float = 1.0, random_state: int = 42):
        self.model = LogisticRegression(C=C, random_state=random_state, max_iter=200)

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.model.fit(X, y)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)


class C2DomainCORAL:
    """C2: Correlation Alignment (CORAL) baseline aligning second-order feature statistics."""
    def __init__(self, C: float = 1.0, random_state: int = 42):
        self.C = C
        self.random_state = random_state
        self.model = LogisticRegression(C=C, random_state=random_state, max_iter=200)
        self.A_coral: Optional[np.ndarray] = None

    def fit(self, X_source: np.ndarray, y_source: np.ndarray, X_target: Optional[np.ndarray] = None):
        if X_target is None or len(X_target) < 2:
            self.model.fit(X_source, y_source)
            return self
        # CORAL alignment transformation
        cov_s = np.cov(X_source, rowvar=False) + np.eye(X_source.shape[1]) * 1e-5
        cov_t = np.cov(X_target, rowvar=False) + np.eye(X_target.shape[1]) * 1e-5
        
        # Whitening source and recoloring with target
        # S^(-1/2) * T^(1/2)
        try:
            u_s, s_s, v_s = np.linalg.svd(cov_s)
            u_t, s_t, v_t = np.linalg.svd(cov_t)
            whitening_s = u_s @ np.diag(1.0 / np.sqrt(s_s)) @ v_s
            coloring_t = u_t @ np.diag(np.sqrt(s_t)) @ v_t
            self.A_coral = whitening_s @ coloring_t
            X_aligned = X_source @ self.A_coral
        except Exception:
            X_aligned = X_source
            self.A_coral = None

        self.model.fit(X_aligned, y_source)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)
