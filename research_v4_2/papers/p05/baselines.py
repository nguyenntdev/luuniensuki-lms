"""P05 Baselines: C0 (Global Base Rate) and C1 (HawkesKT / Exponential Forgetting KT).
"""
from __future__ import annotations

import numpy as np
from typing import Dict, Any, List, Optional
from sklearn.linear_model import LogisticRegression


class C0GlobalBaseRateKT:
    """C0: Predicts global train base rate accuracy."""
    def __init__(self):
        self.prior = 0.5

    def fit(self, interactions: List[Dict[str, Any]]):
        labels = [item["correct"] for item in interactions]
        self.prior = float(np.mean(labels)) if len(labels) > 0 else 0.5
        return self

    def predict_proba(self, interactions: List[Dict[str, Any]]) -> np.ndarray:
        prob = np.full(len(interactions), self.prior)
        return np.column_stack([1.0 - prob, prob])


class C1HawkesKT:
    """C1: HawkesKT / Exponential Decay Baseline.
    
    Models memory strength as decaying exponentially with elapsed time gap Delta_t:
       m(t) = sum_{j < t} w_j * exp(-lambda * (t - t_j))
    Lacks cross-skill competing risk interference and uncertainty disentanglement.
    """
    def __init__(self, decay_rate: float = 0.05, C: float = 1.0, random_state: int = 42):
        self.decay_rate = decay_rate
        self.C = C
        self.random_state = random_state
        self.model = LogisticRegression(C=C, random_state=random_state, max_iter=200)

    def extract_features(self, interactions: List[Dict[str, Any]]) -> np.ndarray:
        feats = []
        for item in interactions:
            dt = float(item.get("time_gap", 1.0))
            hist_correct = float(item.get("past_correct", 0.0))
            hist_count = float(item.get("past_attempts", 1.0))
            decayed_strength = (hist_correct / max(hist_count, 1.0)) * np.exp(-self.decay_rate * dt)
            feats.append([decayed_strength, dt, hist_count])
        return np.array(feats)

    def fit(self, interactions: List[Dict[str, Any]]):
        X = self.extract_features(interactions)
        y = np.array([item["correct"] for item in interactions])
        self.model.fit(X, y)
        return self

    def predict_proba(self, interactions: List[Dict[str, Any]]) -> np.ndarray:
        X = self.extract_features(interactions)
        return self.model.predict_proba(X)


class C2LefoKT:
    """C2: LefoKT (Bai et al. 2025) baseline with attention-like recency weighting."""
    def __init__(self, C: float = 1.0, random_state: int = 42):
        self.C = C
        self.random_state = random_state
        self.model = LogisticRegression(C=C, random_state=random_state, max_iter=200)

    def extract_features(self, interactions: List[Dict[str, Any]]) -> np.ndarray:
        feats = []
        for item in interactions:
            dt = float(item.get("time_gap", 1.0))
            hist_correct = float(item.get("past_correct", 0.0))
            hist_count = float(item.get("past_attempts", 1.0))
            recency = 1.0 / (1.0 + np.log1p(dt))
            base_acc = hist_correct / max(hist_count, 1.0)
            feats.append([base_acc * recency, recency, hist_count, dt])
        return np.array(feats)

    def fit(self, interactions: List[Dict[str, Any]]):
        X = self.extract_features(interactions)
        y = np.array([item["correct"] for item in interactions])
        self.model.fit(X, y)
        return self

    def predict_proba(self, interactions: List[Dict[str, Any]]) -> np.ndarray:
        X = self.extract_features(interactions)
        return self.model.predict_proba(X)
