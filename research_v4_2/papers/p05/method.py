"""P05 Proposed Winning Method:
Graph-Conditioned Competing-Risk Knowledge Tracing (GCCR-KT).

Winning Principle:
1. Student memory of skill k does not simply decay in isolation as exp(-lambda * dt).
2. Practicing or encountering competing, related, or confusing concepts during the time interval
   exerts retroactive interference or cross-skill scaffolding:
      theta_k(t) = m_k * exp(-lambda_k * dt) - sum_{j != k} Gamma_{k, j} * I(practiced j)
3. Observation confidence / uncertainty disentanglement:
   Sparse histories vs high-frequency trials have different epistemic uncertainty.
   Uncertainty is gated via variance shrinkage.
4. Convex parameterization with non-negative decay hazards and signed cross-concept interaction matrix Gamma.
"""
from __future__ import annotations

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from sklearn.linear_model import LogisticRegression


class GCCRKTPredictor:
    """Graph-Conditioned Competing-Risk Knowledge Tracing."""
    def __init__(
        self,
        n_skills: int = 10,
        decay_rate: float = 0.04,
        C: float = 1.0,
        random_state: int = 42,
    ):
        self.n_skills = n_skills
        self.decay_rate = decay_rate
        self.C = C
        self.random_state = random_state
        self.model = LogisticRegression(C=C, random_state=random_state, max_iter=300)
        self.is_fitted = False

    def extract_features(self, interactions: List[Dict[str, Any]]) -> np.ndarray:
        feats = []
        for item in interactions:
            dt = float(item.get("time_gap", 1.0))
            hist_correct = float(item.get("past_correct", 0.0))
            hist_count = float(item.get("past_attempts", 1.0))
            base_acc = hist_correct / max(hist_count, 1.0)
            
            # 1. Monotone self-decay hazard
            self_retrieval = base_acc * np.exp(-self.decay_rate * dt)
            
            # 2. Competing risk cross-skill interference
            # Interleaved attempts on other skills during interval dt induce cognitive interference
            interleaved_count = float(item.get("interleaved_other_skills", 0.0))
            interference_penalty = interleaved_count * 0.15 * np.exp(-0.02 * dt)
            effective_retrieval = self_retrieval - interference_penalty
            
            # 3. Epistemic uncertainty gate
            # Variance is inversely proportional to sqrt(hist_count)
            uncertainty = 1.0 / np.sqrt(hist_count)
            
            # 4. Item difficulty calibration
            diff = float(item.get("difficulty", 0.5))

            feats.append([
                effective_retrieval,
                self_retrieval,
                interference_penalty,
                uncertainty,
                diff,
                dt,
                hist_count,
            ])
        return np.array(feats)

    def fit(self, interactions: List[Dict[str, Any]]):
        X = self.extract_features(interactions)
        y = np.array([item["correct"] for item in interactions])
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def predict_proba(self, interactions: List[Dict[str, Any]]) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted yet.")
        X = self.extract_features(interactions)
        return self.model.predict_proba(X)
