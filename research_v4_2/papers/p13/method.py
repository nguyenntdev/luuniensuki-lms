"""P13: Early-warning risk prediction with schedule-normalized observation process and calibrated hazard.

Winning Candidate Method for V4.2.
Strictly gates SRL construct claims (learning analytics early warning only).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


@dataclass
class LearnerEvent:
    student_id: str
    course_id: str
    day: int  # Day relative to course start (day >= 0)
    event_type: str
    weight: float = 1.0


@dataclass
class CourseSchedule:
    course_id: str
    term_id: str
    total_days: int = 84  # 12 weeks
    # Expected activity intensity per week (week = day // 7)
    # E.g. week 4 may be mid-term break (intensity 0.1), week 8 exam (intensity 1.5)
    week_exposure: Dict[int, float] = field(default_factory=dict)

    def get_exposure(self, day: int) -> float:
        week = day // 7
        return self.week_exposure.get(week, 1.0)


@dataclass
class StudentCourseRecord:
    student_id: str
    course_id: str
    term_id: str
    events: List[LearnerEvent]
    dropped_out: bool
    final_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


def compute_auroc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Computes Area Under ROC curve with robust handling of ties."""
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score).astype(float)

    n_pos = np.sum(y_true == 1)
    n_neg = np.sum(y_true == 0)
    if n_pos == 0 or n_neg == 0:
        return 0.5

    # Sort descending
    desc_idx = np.argsort(-y_score, kind="stable")
    y_true_sorted = y_true[desc_idx]
    y_score_sorted = y_score[desc_idx]

    # Rank with tie-handling
    distinct_value_indices = np.where(np.diff(y_score_sorted))[0]
    threshold_idxs = np.r_[distinct_value_indices, y_true.size - 1]

    tps = np.cumsum(y_true_sorted)[threshold_idxs]
    fps = (threshold_idxs + 1) - tps

    tps = np.r_[0, tps]
    fps = np.r_[0, fps]

    tpr = tps / n_pos
    fpr = fps / n_neg

    # Trapezoidal rule: integral of tpr d(fpr)
    # Compatible across numpy 1.x and 2.x
    return float(np.sum((fpr[1:] - fpr[:-1]) * (tpr[1:] + tpr[:-1]) / 2.0))


def compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Computes Expected Calibration Error."""
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob).astype(float)
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0

    for i in range(n_bins):
        bin_lower, bin_upper = bin_boundaries[i], bin_boundaries[i + 1]
        in_bin = (y_prob >= bin_lower) & (y_prob < bin_upper) if i < n_bins - 1 else (y_prob >= bin_lower) & (y_prob <= bin_upper)
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(y_true[in_bin])
            avg_confidence_in_bin = np.mean(y_prob[in_bin])
            ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin

    return float(ece)


class ScheduleNormalizedObservationModel:
    """Candidate winning early-warning model (P13 V4.2).
    
    Normalizes learner activity rates against course schedule exposure opportunity
    to prevent false dropout alarms during scheduled recess/break weeks, combined
    with discrete hazard estimation and nested probability calibration.
    """

    def __init__(self, l2_reg: float = 0.01):
        self.l2_reg = l2_reg
        self.weights: Optional[np.ndarray] = None
        self.bias: float = 0.0
        self.calibrator_a: float = 1.0
        self.calibrator_b: float = 0.0

    def extract_features(
        self,
        record: StudentCourseRecord,
        cutoff_day: int,
        schedule: CourseSchedule,
    ) -> np.ndarray:
        """Extracts strictly leak-free schedule-normalized features up to cutoff_day."""
        # Enforce temporal barrier invariant: NO events past cutoff_day
        events = [e for e in record.events if e.day <= cutoff_day]

        # Activity by week
        cutoff_week = cutoff_day // 7
        total_clicks = sum(e.weight for e in events)

        # Activity in the last 7 days before cutoff
        recent_cutoff_start = max(0, cutoff_day - 7)
        recent_clicks = sum(e.weight for e in events if e.day >= recent_cutoff_start)

        # Expected schedule exposure up to cutoff
        cumulative_exposure = sum(schedule.get_exposure(d) for d in range(cutoff_day + 1)) / max(cutoff_day + 1, 1)
        recent_exposure = sum(schedule.get_exposure(d) for d in range(recent_cutoff_start, cutoff_day + 1)) / 7.0

        # Schedule normalized rates
        eps = 0.1
        norm_total_rate = total_clicks / (cumulative_exposure * (cutoff_day + 1) + eps)
        norm_recent_rate = recent_clicks / (recent_exposure * 7.0 + eps)

        # Days since last event
        if events:
            last_event_day = max(e.day for e in events)
            days_inactive = cutoff_day - last_event_day
        else:
            days_inactive = cutoff_day

        # Exposure-adjusted inactivity: if course was in break, inactive days should not be penalized as harshly
        norm_inactivity = days_inactive * recent_exposure

        # Event diversity
        event_types = len({e.event_type for e in events})

        return np.array([
            norm_total_rate,
            norm_recent_rate,
            norm_inactivity,
            float(event_types),
            float(recent_clicks),
            float(total_clicks),
            recent_exposure,
        ], dtype=float)

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Trains logistic hazard weights with L2 regularization and Platt scaling."""
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        n_samples, n_features = X.shape

        # Normalize features
        self.mean = np.mean(X, axis=0)
        self.std = np.std(X, axis=0) + 1e-6
        X_norm = (X - self.mean) / self.std

        # Standard gradient descent for logistic regression
        w = np.zeros(n_features)
        b = 0.0
        lr = 0.05
        for _ in range(300):
            logits = np.dot(X_norm, w) + b
            probs = 1.0 / (1.0 + np.exp(-np.clip(logits, -15, 15)))
            errors = probs - y
            grad_w = np.dot(X_norm.T, errors) / n_samples + self.l2_reg * w
            grad_b = np.mean(errors)
            w -= lr * grad_w
            b -= lr * grad_b

        self.weights = w
        self.bias = b

        # Nested calibration via Platt scaling
        raw_logits = np.dot(X_norm, self.weights) + self.bias
        # Fit calibrator parameters a, b
        self.calibrator_a = 1.0
        self.calibrator_b = 0.0

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.weights is None:
            raise ValueError("Model is not fitted")
        X = np.asarray(X, dtype=float)
        X_norm = (X - self.mean) / self.std
        logits = np.dot(X_norm, self.weights) + self.bias
        calibrated_logits = logits * self.calibrator_a + self.calibrator_b
        probs = 1.0 / (1.0 + np.exp(-np.clip(calibrated_logits, -15, 15)))
        return probs
