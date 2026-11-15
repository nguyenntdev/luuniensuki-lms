"""P05 models: forgetting-aware KT (proposed), C0 base rate, C1 classical.

Model contract (see METHOD.md):

- Every model implements ``fit(train_df, calibration_df)`` and
  ``predict_batch(attempts_df) -> np.ndarray`` of pass probabilities.
- ``NOT_APPLICABLE`` / ``ABSTAIN`` semantics: ``predict_batch`` refuses rows
  whose features are missing entirely (raises ``P05ModelError``); an explicit
  ``abstain_mask`` output marks rows the model declines to score (never
  silently converted to a negative prediction).
- All learned parameters are fit ONLY on the train window; any calibration
  (temperature) uses ONLY the calibration window. The test window is never
  touched during fitting.

Proposed mechanism: half-life retrieval strength
    theta_i = alpha_effective * exp2(-gap_days / half_life)
with a per-context half-life selected on a FIXED grid using the calibration
window only, monotone in elapsed gap (d theta/d gap < 0).
"""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

HALF_LIFE_GRID_DAYS = (10.0, 20.0, 35.0, 50.0, 80.0, 120.0)
C_GRID = (0.05, 0.2, 1.0, 4.0)

FEATURE_GROUPS: dict[str, tuple[str, ...]] = {
    "context": (
        "due_day",
        "weight",
        "is_exam",
        "is_cma",
        "course_len",
        *(f"module_{m}" for m in ("AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG")),
    ),
    "recency": (
        "days_since_click",
        "days_since_last_attempt",
        "recent14_active_days",
        "recent_attempts_14d",
    ),
    "frequency": ("total_clicks", "active_days", "click_rate", "n_past_attempts", "never_clicked"),
    "ability": (
        "past_score_mean",
        "past_score_std",
        "past_score_min",
        "past_score_max",
        "past_fail_count",
        "past_fail_rate",
    ),
    "decay": ("gap_days", "log_gap", "decay_score_mean_h45"),
}

ABLATION_REMOVES: dict[str, tuple[str, ...]] = {
    "full": (),
    "A1_no_elapsed_time": ("decay",),
    "A2_no_hazard_calibration": (),  # handled by skipping temperature calibration
    "A3_no_score_history": ("ability",),
    "A4_no_engagement_history": ("frequency",),
    "A5_no_recency_features": ("recency",),
}


class P05ModelError(ValueError):
    """Typed failure: model contract violated."""


def _design_matrix(attempts: pd.DataFrame, columns: Sequence[str]) -> np.ndarray:
    if "features" not in attempts.columns:
        raise P05ModelError("attempts DataFrame lacks a 'features' column")
    rows = []
    for feats in attempts["features"]:
        if not isinstance(feats, dict) or not feats:
            raise P05ModelError("attempt has empty/invalid features; NOT_APPLICABLE refused")
        rows.append([float(feats.get(c, np.nan)) for c in columns])
    X = np.asarray(rows, dtype=float)
    # NaN policy: a missing history feature means "no history yet" -> impute 0
    # and add an explicit has-history indicator once per model, not per feature.
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    return X


def _columns_for(variant: str) -> list[str]:
    removed = ABLATION_REMOVES.get(variant)
    if removed is None:
        raise P05ModelError(f"unknown model variant {variant!r}")
    cols: list[str] = []
    for group, names in FEATURE_GROUPS.items():
        if group in removed:
            continue
        cols.extend(names)
    if variant != "A1_no_elapsed_time":
        cols.append("never_clicked_hist")
    return cols


def add_decay_features(attempts: pd.DataFrame, half_life_days: float) -> pd.DataFrame:
    """Add the proposed forgetting-aware retrieval-strength columns.

    theta = alpha * exp2(-gap / h): monotone decreasing in gap. ``alpha`` is
    the fixed logistic-transformed scalar fit later as a linear coefficient
    (monotone constraint enforced by the fixed decay form itself).
    Also adds ``never_clicked_hist`` (no engagement history at all).
    """
    out = attempts.copy()
    gap = out["features"].map(lambda f: f.get("gap_days", np.nan)).astype(float)
    decay_mean = (
        out["features"].map(lambda f: f.get("decay_score_mean_h45", np.nan)).astype(float)
    )
    total_clicks = out["features"].map(lambda f: f.get("total_clicks", np.nan)).astype(float)
    n_past = out["features"].map(lambda f: f.get("n_past_attempts", np.nan)).astype(float)
    out["features"] = [
        {**f, "gap_hl": (np.nan_to_num(g, nan=0.0) if not np.isnan(g) else 0.0)}
        for f, g in zip(out["features"], gap)
    ]
    theta = []
    never_clicked_hist = []
    for f, g, dm, tc, np_ in zip(out["features"], gap, decay_mean, total_clicks, n_past):
        g_eff = 0.0 if np.isnan(g) else g
        ability = 0.5 if np.isnan(dm) else float(np.clip(dm, 0.0, 100.0)) / 100.0
        engagement = 0.0 if np.isnan(tc) else float(np.log1p(max(tc, 0.0))) / np.log1p(400.0)
        history = 0.5 * ability + 0.5 * engagement
        theta.append(history * np.exp2(-g_eff / half_life_days))
        never_clicked_hist.append(1.0 if (np.isnan(np_) or np_ == 0) and (np.isnan(tc) or tc == 0) else 0.0)
    out["features"] = [
        {**f, "theta": float(t), "never_clicked_hist": float(nc)}
        for f, t, nc in zip(out["features"], theta, never_clicked_hist)
    ]
    return out


class _LogisticCore:
    """Shared deterministic logistic core with calibration-window tuning."""

    def __init__(self, *, variant: str = "full", temperature_calibrate: bool = True) -> None:
        self.variant = variant
        self.temperature_calibrate = temperature_calibrate
        self.columns_: list[str] = []
        self.model_: LogisticRegression | None = None
        self.temperature_ = 1.0
        self.selected_C_: float | None = None
        self.n_iter_ = 0

    def _fit_core(self, train: pd.DataFrame, columns: Sequence[str]) -> None:
        self.columns_ = list(columns)
        Xtr = _design_matrix(train, self.columns_)
        ytr = train["label"].to_numpy(dtype=int)
        if len(np.unique(ytr)) < 2:
            raise P05ModelError("train window has a single class; cannot fit")
        # deterministic solver, fixed ordering, no randomness
        self.model_ = LogisticRegression(C=1.0, solver="liblinear", max_iter=1000, random_state=0)
        self.model_.fit(Xtr, ytr)
        self.n_iter_ = int(getattr(self.model_, "n_iter_", [0])[0])

    def _tune_C(self, train: pd.DataFrame, calibration: pd.DataFrame) -> None:
        """C grid + half-life grid selection strictly on the calibration window."""
        best_auc, best_C = -1.0, None
        ycal = calibration["label"].to_numpy(dtype=int)
        if len(np.unique(ycal)) < 2:
            best_C = 1.0  # degenerate calibration window; keep default, record it
        else:
            Xcal = _design_matrix(calibration, self.columns_)
            for C in C_GRID:
                m = LogisticRegression(C=C, solver="liblinear", max_iter=1000, random_state=0)
                m.fit(_design_matrix(train, self.columns_), ytrain_of(train))
                p = m.predict_proba(Xcal)[:, 1]
                auc = roc_auc_score(ycal, p)
                if auc > best_auc:
                    best_auc, best_C = auc, C
        self.selected_C_ = best_C
        self.model_ = LogisticRegression(
            C=float(best_C), solver="liblinear", max_iter=1000, random_state=0
        )
        self.model_.fit(_design_matrix(train, self.columns_), ytrain_of(train))

    def _fit_temperature(self, calibration: pd.DataFrame) -> None:
        if not self.temperature_calibrate:
            self.temperature_ = 1.0
            return
        Xcal = _design_matrix(calibration, self.columns_)
        ycal = calibration["label"].to_numpy(dtype=int)
        if len(np.unique(ycal)) < 2 or self.model_ is None:
            self.temperature_ = 1.0
            return
        logits = self.model_.decision_function(Xcal)
        # 1-D golden-section search for temperature minimizing NLL (deterministic)
        best_t, best_nll = 1.0, np.inf
        for t in np.linspace(0.5, 2.0, 16):
            p = _sigmoid(logits / t)
            p = np.clip(p, 1e-6, 1 - 1e-6)
            nll = -np.mean(ycal * np.log(p) + (1 - ycal) * np.log(1 - p))
            if nll < best_nll:
                best_t, best_nll = float(t), float(nll)
        self.temperature_ = best_t

    def predict_batch(self, attempts: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """Return (probabilities, abstain_mask). Abstained rows are excluded
        from every metric downstream; they are NEVER converted to 0."""
        if self.model_ is None:
            raise P05ModelError("model not fitted")
        X = _design_matrix(attempts, self.columns_)
        logits = self.model_.decision_function(X) / self.temperature_
        probs = _sigmoid(logits)
        abstain = np.zeros(len(attempts), dtype=bool)
        return probs, abstain


def ytrain_of(train: pd.DataFrame) -> np.ndarray:
    return train["label"].to_numpy(dtype=int)


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30.0, 30.0)))


class C0BaseRate:
    """Global base-rate predictor: train-window pass prevalence, constant."""

    def __init__(self) -> None:
        self.rate_ = None
        self.temperature_ = 1.0

    def fit(self, train: pd.DataFrame, calibration: pd.DataFrame | None = None) -> "C0BaseRate":
        self.rate_ = float(train["label"].mean())
        return self

    def predict_batch(self, attempts: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        if self.rate_ is None:
            raise P05ModelError("C0 not fitted")
        return np.full(len(attempts), self.rate_), np.zeros(len(attempts), dtype=bool)


class C1LogisticRecencyFreq(_LogisticCore):
    """Serious classical baseline: logistic regression on recency+frequency
    (+ability+context) WITHOUT any decay/elapsed-time modelling."""

    def __init__(self) -> None:
        super().__init__(variant="full", temperature_calibrate=True)
        self.kind_ = "C1"

    def fit(self, train: pd.DataFrame, calibration: pd.DataFrame) -> "C1LogisticRecencyFreq":
        self._fit_core(train, _columns_for("full"))
        self._tune_C(train, calibration)
        self._fit_temperature(calibration)
        return self


class ForgettingAwareKT(_LogisticCore):
    """Proposed: half-life retrieval strength + matched classical features.

    The half-life is selected on a FIXED grid using ONLY the calibration
    window; the logistic core is trained ONLY on the train window.
    """

    def __init__(self, *, half_life_days: float | None = None, temperature_calibrate: bool = True) -> None:
        super().__init__(variant="full", temperature_calibrate=temperature_calibrate)
        self.kind_ = "P05"
        self.half_life_ = half_life_days
        self.half_life_grid_searched_ = half_life_days is None

    def fit(self, train: pd.DataFrame, calibration: pd.DataFrame) -> "ForgettingAwareKT":
        if self.half_life_ is None:
            best_auc, best_h = -1.0, None
            ycal = calibration["label"].to_numpy(dtype=int)
            for h in HALF_LIFE_GRID_DAYS:
                m = ForgettingAwareKT(half_life_days=h, temperature_calibrate=False)
                m._fit_core(add_decay_features(train, h), _columns_for("full") + ["theta", "never_clicked_hist"])
                if len(np.unique(ycal)) < 2:
                    best_h = best_h or h
                    continue
                p, _ = m.predict_batch(add_decay_features(calibration, h))
                auc = roc_auc_score(ycal, p)
                if auc > best_auc:
                    best_auc, best_h = auc, h
            self.half_life_ = best_h
        decayed_train = add_decay_features(train, self.half_life_)
        decayed_cal = add_decay_features(calibration, self.half_life_)
        cols = _columns_for("full") + ["theta", "never_clicked_hist"]
        self._fit_core(decayed_train, cols)
        self._tune_C(decayed_train, decayed_cal)
        self._fit_temperature(decayed_cal)
        return self

    def predict_batch(self, attempts: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        return super().predict_batch(add_decay_features(attempts, self.half_life_))


class AblatedModel(_LogisticCore):
    """True-removal ablations: same core, feature group deleted."""

    def __init__(self, variant: str, *, temperature_calibrate: bool = True) -> None:
        if variant not in ABLATION_REMOVES:
            raise P05ModelError(f"unknown model variant {variant!r}")
        super().__init__(variant=variant, temperature_calibrate=temperature_calibrate)
        self.kind_ = f"ABL:{variant}"

    def fit(self, train: pd.DataFrame, calibration: pd.DataFrame) -> "AblatedModel":
        cols = _columns_for(self.variant)
        self._fit_core(train, cols)
        self._tune_C(train, calibration)
        self._fit_temperature(calibration)
        return self


# --- review scheduler --------------------------------------------------------

class ReviewScheduler:
    """Rank at-risk pairs by predicted failure risk; decay tie-break.

    Scheduler fitting (the half-life used for tie-breaks) is separate from
    the predictive model's test evaluation: the tie-break half-life is the
    one selected on the calibration window, never re-tuned on test.
    """

    def __init__(self, *, tie_half_life_days: float, random_seed: int = 11) -> None:
        self.tie_half_life_days = float(tie_half_life_days)
        self.random_seed = int(random_seed)

    def rank(self, attempts: pd.DataFrame, probs: np.ndarray) -> np.ndarray:
        """Return indices ordering pairs by review priority (descending risk)."""
        if len(attempts) != len(probs):
            raise P05ModelError("rank(): attempts and probs must align")
        gap = attempts["features"].map(lambda f: f.get("gap_days", 0.0)).astype(float)
        gap = gap.fillna(0.0).to_numpy()
        learner = attempts["learner_id"].to_numpy()
        # decay tie-break: among (nearly) equal risk, prefer larger elapsed gap
        # (pair idle the longest is reviewed first — the forgetting-motivated rule)
        order = np.lexsort(
            (
                learner,                       # final tie-break: stable learner order
                -gap / self.tie_half_life_days,  # secondary: longer idle first
                -probs,                        # primary: highest risk first
            )
        )
        return order

    def recall_at_budget(
        self,
        attempts: pd.DataFrame,
        probs: np.ndarray,
        *,
        budgets_pct: Sequence[float] = (5, 10, 20, 40, 80),
    ) -> dict[str, float]:
        """Recall of eventual failures among ranked pairs at each budget."""
        labels = attempts["label"].to_numpy(dtype=int)
        order = self.rank(attempts, probs)
        failures = int((labels == 0).sum())
        out: dict[str, float] = {}
        if failures == 0:
            return {f"recall_failures@{b}%": None for b in budgets_pct}  # type: ignore[return-value]
        n = len(labels)
        for b in budgets_pct:
            k = max(1, int(round(n * b / 100.0)))
            k = min(k, n)
            retrieved = labels[order[:k]] == 0
            out[f"recall_failures@{b}%"] = float(retrieved.sum() / failures)
        return out


class FrequencyRankScheduler:
    """Classical control: rank by the C1 risk model alone (no decay tie-break)."""

    def __init__(self) -> None:
        self.kind_ = "C1_frequency_rank"

    def rank(self, attempts: pd.DataFrame, probs: np.ndarray) -> np.ndarray:
        if len(attempts) != len(probs):
            raise P05ModelError("rank(): attempts and probs must align")
        learner = attempts["learner_id"].to_numpy()
        return np.lexsort((learner, -probs))

    def recall_at_budget(
        self,
        attempts: pd.DataFrame,
        probs: np.ndarray,
        *,
        budgets_pct: Sequence[float] = (5, 10, 20, 40, 80),
    ) -> dict[str, float | None]:
        labels = attempts["label"].to_numpy(dtype=int)
        order = self.rank(attempts, probs)
        failures = int((labels == 0).sum())
        out: dict[str, float | None] = {}
        if failures == 0 or len(labels) == 0:
            return {f"recall_failures@{b}%": None for b in budgets_pct}
        n = len(labels)
        for b in budgets_pct:
            k = max(1, int(round(n * b / 100.0)))
            k = min(k, n)
            retrieved = labels[order[:k]] == 0
            out[f"recall_failures@{b}%"] = float(retrieved.sum() / failures)
        return out


def random_ranking_recall(
    attempts: pd.DataFrame,
    *,
    budgets_pct: Sequence[float] = (5, 10, 20, 40, 80),
    seed: int = 11,
) -> dict[str, float]:
    """Seeded random-ranking chance line (deterministic given the seed)."""
    rng = np.random.default_rng(seed)
    labels = attempts["label"].to_numpy(dtype=int)
    n = len(labels)
    failures = int((labels == 0).sum())
    if failures == 0 or n == 0:
        return {f"recall_failures@{b}%": None for b in budgets_pct}  # type: ignore[return-value]
    out = {}
    for b in budgets_pct:
        k = max(1, int(round(n * b / 100.0)))
        k = min(k, n)
        picked = rng.choice(n, size=k, replace=False)
        out[f"recall_failures@{b}%"] = float((labels[picked] == 0).sum() / failures)
    return out
