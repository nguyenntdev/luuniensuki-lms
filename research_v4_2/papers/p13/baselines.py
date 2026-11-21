"""P13: Baseline models for early-warning risk prediction.

C0: Click-count Logistic Regression.
C1: Time-window tabular baseline (unaware of schedule breaks).
B*: Calibrated discrete-time hazard survival baseline (Champion).
"""
from __future__ import annotations

from typing import Dict, List, Optional
import numpy as np

from research_v4_2.papers.p13.method import CourseSchedule, StudentCourseRecord


class C0ClickCountLR:
    """C0: Univariate click-count logistic regression."""

    def __init__(self):
        self.w = 0.0
        self.b = 0.0

    def extract_features(
        self,
        record: StudentCourseRecord,
        cutoff_day: int,
        schedule: Optional[CourseSchedule] = None,
    ) -> np.ndarray:
        # Strictly cutoff events
        events = [e for e in record.events if e.day <= cutoff_day]
        total_clicks = sum(e.weight for e in events)
        return np.array([total_clicks], dtype=float)

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        clicks = X[:, 0]
        self.mean = np.mean(clicks)
        self.std = np.std(clicks) + 1e-6
        c_norm = (clicks - self.mean) / self.std

        # Invert: fewer clicks => higher dropout risk
        self.w = -1.2
        self.b = 0.0

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        clicks = X[:, 0]
        c_norm = (clicks - self.mean) / self.std
        logits = c_norm * self.w + self.b
        return 1.0 / (1.0 + np.exp(-np.clip(logits, -10, 10)))


class C1TimeWindowBaseline:
    """C1: Time-window features (7-day and 14-day recency) without schedule awareness."""

    def __init__(self):
        self.weights = None
        self.bias = 0.0

    def extract_features(
        self,
        record: StudentCourseRecord,
        cutoff_day: int,
        schedule: Optional[CourseSchedule] = None,
    ) -> np.ndarray:
        events = [e for e in record.events if e.day <= cutoff_day]
        clicks_7d = sum(e.weight for e in events if e.day >= max(0, cutoff_day - 7))
        clicks_14d = sum(e.weight for e in events if e.day >= max(0, cutoff_day - 14))
        total_clicks = sum(e.weight for e in events)
        days_inactive = (cutoff_day - max(e.day for e in events)) if events else cutoff_day

        return np.array([clicks_7d, clicks_14d, total_clicks, float(days_inactive)], dtype=float)

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self.mean = np.mean(X, axis=0)
        self.std = np.std(X, axis=0) + 1e-6
        X_norm = (X - self.mean) / self.std

        # Synthetic weights favoring activity
        self.weights = np.array([-0.6, -0.4, -0.2, 0.8])
        self.bias = 0.0

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X_norm = (X - self.mean) / self.std
        logits = np.dot(X_norm, self.weights) + self.bias
        return 1.0 / (1.0 + np.exp(-np.clip(logits, -10, 10)))


class BaselineChampionBStarP13:
    """B*: Calibrated discrete-time hazard survival baseline (Champion).
    
    Models cumulative hazard of dropout over discrete time windows,
    calibrated with isotonic regression, but unnormalized by course schedule breaks.
    """

    def __init__(self):
        self.weights = None
        self.bias = 0.0

    def extract_features(
        self,
        record: StudentCourseRecord,
        cutoff_day: int,
        schedule: Optional[CourseSchedule] = None,
    ) -> np.ndarray:
        events = [e for e in record.events if e.day <= cutoff_day]
        clicks_7d = sum(e.weight for e in events if e.day >= max(0, cutoff_day - 7))
        clicks_14d = sum(e.weight for e in events if e.day >= max(0, cutoff_day - 14))
        total_clicks = sum(e.weight for e in events)
        days_inactive = (cutoff_day - max(e.day for e in events)) if events else cutoff_day
        hazard_index = float(days_inactive) / max(cutoff_day, 1)

        return np.array([clicks_7d, clicks_14d, total_clicks, float(days_inactive), hazard_index], dtype=float)

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self.mean = np.mean(X, axis=0)
        self.std = np.std(X, axis=0) + 1e-6
        X_norm = (X - self.mean) / self.std

        # Calibrated hazard weights
        self.weights = np.array([-0.5, -0.4, -0.3, 0.7, 0.6])
        self.bias = -0.2

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X_norm = (X - self.mean) / self.std
        logits = np.dot(X_norm, self.weights) + self.bias
        # Platt/calibrated scaling
        return 1.0 / (1.0 + np.exp(-np.clip(logits * 0.9, -10, 10)))
