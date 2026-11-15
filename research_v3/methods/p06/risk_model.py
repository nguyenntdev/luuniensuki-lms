"""P06 risk model: leakage-safe feature pipeline + frozen calibration.

Shared by every arm (C0, C1, PROPOSED, ablations) so all contrasts hold input
information, preprocessing and tuning budget constant (spec §4 benchmark
rules). ``final_result`` never enters features (adapter enforces); the
calibration wrapper fits ONLY on the calibration partition via
``FrozenEstimator`` (sklearn >= 1.6), so the base estimator cannot re-fit on
calibration or test data.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.frozen import FrozenEstimator
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

CATEGORICAL_FEATURES = (
    "gender",
    "region",
    "highest_education",
    "imd_band",
    "age_band",
    "disability",
    "code_module",
    "code_presentation",
)
NUMERIC_FEATURES = (
    "num_of_prev_attempts",
    "studied_credits",
    "early_click_total",
    "early_active_sites",
)

RANDOM_STATE = 0


def build_pipeline() -> Pipeline:
    """Deterministic logistic pipeline (pin: sklearn B00, METHOD.md §5)."""
    cat = OneHotEncoder(handle_unknown="ignore")
    num = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    ct = ColumnTransformer(
        transformers=[("cat", cat, list(CATEGORICAL_FEATURES)), ("num", num, list(NUMERIC_FEATURES))],
        remainder="drop",
    )
    lr = LogisticRegression(
        max_iter=2000,
        C=1.0,
        solver="lbfgs",
        class_weight="balanced",
        random_state=RANDOM_STATE,
    )
    return Pipeline(steps=[("features", ct), ("model", lr)])


class P06RiskModel:
    """Fit on train, calibrate on calibration, score frozen.

    ``raw`` mode (ablation A1) disables calibration and returns uncalibrated
    decision-function margins squashed through a min-max into [0, 1] — a
    monotone but uncalibrated score, exactly the 'no calibrated uncertainty'
    removal.
    """

    def __init__(self, *, raw: bool = False) -> None:
        self.raw = raw
        self._base: Pipeline | None = None
        self._calibrated: Any = None

    def fit(
        self,
        train_rows: Sequence[Mapping[str, Any]],
        calib_rows: Sequence[Mapping[str, Any]],
    ) -> "P06RiskModel":
        X_train = _frame(train_rows)
        y_train = np.array([1 if r["label"] == "Fail" else 0 for r in train_rows], dtype=int)
        self._base = build_pipeline()
        self._base.fit(X_train, y_train)
        if not self.raw:
            frozen = FrozenEstimator(self._base)
            X_cal = _frame(calib_rows)
            y_cal = np.array([1 if r["label"] == "Fail" else 0 for r in calib_rows], dtype=int)
            self._calibrated = CalibratedClassifierCV(frozen, method="sigmoid")
            self._calibrated.fit(X_cal, y_cal)
        return self

    def predict_proba(self, rows: Sequence[Mapping[str, Any]]) -> np.ndarray:
        X = _frame(rows)
        if self.raw:
            margins = self._base.decision_function(X)
            lo, hi = float(margins.min()), float(margins.max())
            if hi <= lo:
                return np.full(len(rows), 0.5)
            return (margins - lo) / (hi - lo)
        return self._calibrated.predict_proba(X)[:, 1]


def _frame(rows: Sequence[Mapping[str, Any]]):
    import pandas as pd

    records = []
    for r in rows:
        feats = dict(r["input"])
        feats["code_module"] = feats.get("code_module", "UNK")
        feats["code_presentation"] = feats.get("code_presentation", "UNK")
        records.append(feats)
    return pd.DataFrame(records, columns=list(CATEGORICAL_FEATURES) + list(NUMERIC_FEATURES))
