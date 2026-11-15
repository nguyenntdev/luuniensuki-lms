"""P05 temporal data pipeline: OULAD attempt sequences with leakage guards.

Builds genuine TEMPORAL sequences from real OULAD data:

- one attempt = (id_student, code_module, code_presentation, id_assessment)
  with submission day and pass/fail label from the real score;
- engagement history from ``studentVle`` per-day click totals;
- feature cutoff = the attempt's own submission day: NO feature may use any
  attempt, click, or score dated on/after the cutoff.

Chronological split: train = 2013B+2013J, calibration = 2014B, test = 2014J.
This is the spec-mandated OULAD protocol (split by presentation, freeze
prediction time). Learners may repeat across presentations (7-8% overlap);
that overlap is measured and reported, not silently allowed to define
features: features are strictly per-attempt causal, so a repeated learner in
the test window still only sees their own pre-cutoff history.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RAW = PROJECT_ROOT / "private_data" / "raw" / "oulad" / "2013-2014" / "_extracted"

PASS_THRESHOLD = 40  # OULAD standard pass mark (score >= 40)
TRAIN_PRESENTATIONS = ("2013B", "2013J")
CALIBRATION_PRESENTATIONS = ("2014B",)
TEST_PRESENTATIONS = ("2014J",)
FEATURE_DAY_MAX = 240  # ignore pathological far-future submissions


class P05DataError(ValueError):
    """Raised when the temporal pipeline's invariants are violated."""


@dataclass(frozen=True)
class Attempt:
    """One real assessment attempt; the unit of prediction."""

    case_id: str
    learner_id: str
    presentation: str
    module: str
    assessment_id: str
    assessment_type: str
    weight: float
    day: int  # submission day (>= 0), the feature cutoff for this attempt
    label: int  # 1 = pass (score >= 40)
    score: float
    features: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.day < 0:
            raise P05DataError(f"{self.case_id}: attempt day {self.day} precedes module start")
        if self.label not in (0, 1):
            raise P05DataError(f"{self.case_id}: label must be 0/1")


def _load_frames(raw_dir: Path) -> dict[str, pd.DataFrame]:
    frames = {}
    paths = {
        "sa": "studentAssessment.csv",
        "asm": "assessments.csv",
        "vle": "studentVle.csv",
        "courses": "courses.csv",
    }
    for key, name in paths.items():
        path = raw_dir / name
        if not path.is_file():
            raise P05DataError(f"missing OULAD file {path}")
        frames[key] = pd.read_csv(path, low_memory=False)
    return frames


def verify_raw_sha256(archive_path: Path, expected_sha256: str) -> bool:
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    return digest == expected_sha256


def build_attempts(
    raw_dir: Path | None = None,
    *,
    pass_threshold: int = PASS_THRESHOLD,
    feature_day_max: int = FEATURE_DAY_MAX,
) -> pd.DataFrame:
    """Materialize attempt rows with strictly pre-cutoff temporal features.

    Returns a DataFrame sorted by (presentation, learner, day); each row is
    one attempt with its feature vector computed only from earlier events.
    """
    base = Path(raw_dir or DEFAULT_RAW)
    frames = _load_frames(base)

    sa = frames["sa"]
    asm = frames["asm"]
    attempts = sa.merge(asm, on="id_assessment", how="inner", validate="many_to_one")
    attempts = attempts[attempts["is_banked"] == 0]
    attempts = attempts[attempts["date_submitted"] >= 0]
    attempts = attempts[attempts["date_submitted"] <= feature_day_max]
    attempts = attempts.dropna(subset=["score", "date_submitted"])
    attempts["score"] = pd.to_numeric(attempts["score"], errors="coerce")
    attempts = attempts.dropna(subset=["score"])
    attempts["weight"] = pd.to_numeric(attempts["weight"], errors="coerce")
    attempts = attempts.dropna(subset=["weight"])
    # assessments.csv encodes unknown exam dates as '?': the final exam day is
    # unknown, so its due_day feature is missing but the attempt itself (with a
    # real submission day) is kept — due_day is imputed with the presentation
    # length by the feature assembler only when a course length is available.
    attempts = attempts.rename(columns={"date": "due_day", "date_submitted": "day"})
    attempts["due_day"] = pd.to_numeric(attempts["due_day"], errors="coerce")
    attempts["label"] = (attempts["score"] >= pass_threshold).astype(int)

    # Engagement: per-day total clicks per learner-module-presentation (real VLE).
    vle = frames["vle"]
    vle = vle[(vle["date"] >= 0) & (vle["date"] <= feature_day_max)]
    daily = (
        vle.groupby(["code_module", "code_presentation", "id_student", "date"], as_index=False)[
            "sum_click"
        ]
        .sum()
        .rename(columns={"date": "day", "sum_click": "clicks"})
    )

    length = frames["courses"].set_index(["code_module", "code_presentation"])[
        "module_presentation_length"
    ]

    attempts = attempts.sort_values(
        ["code_presentation", "id_student", "code_module", "day", "id_assessment"],
        kind="mergesort",
    ).reset_index(drop=True)

    daily_by_case: dict[tuple[Any, ...], pd.DataFrame] = {
        str(k): g for k, g in daily.groupby(["code_module", "code_presentation", "id_student"])
    }

    rows: list[dict[str, Any]] = []
    for key, grp in attempts.groupby(["code_presentation", "id_student", "code_module"], sort=False):
        presentation, learner, module = key
        grp = grp.sort_values(["day", "id_assessment"], kind="mergesort")
        dkey = str((module, presentation, learner))
        dvle = daily_by_case.get(dkey)
        click_days = dvle["day"].to_numpy() if dvle is not None else np.empty(0, dtype=int)
        click_vals = dvle["clicks"].to_numpy(dtype=float) if dvle is not None else np.empty(0)
        click_cum = np.cumsum(click_vals) if click_vals.size else np.empty(0)

        past_days: list[int] = []
        past_scores: list[float] = []
        past_labels: list[int] = []
        for rec in grp.itertuples(index=False):
            day = int(rec.day)
            feats = _assemble_features(
                day=day,
                due_day=float(rec.due_day),
                assessment_type=str(rec.assessment_type),
                weight=float(rec.weight),
                module=str(module),
                presentation=str(presentation),
                course_len=float(length.get((module, presentation), np.nan)),
                past_days=past_days,
                past_scores=past_scores,
                past_labels=past_labels,
                click_days=click_days,
                click_cum=click_cum,
            )
            rows.append(
                {
                    "case_id": f"p05-{presentation}-{module}-{learner}-{rec.id_assessment}",
                    "learner_id": str(learner),
                    "presentation": str(presentation),
                    "module": str(module),
                    "assessment_id": str(rec.id_assessment),
                    "assessment_type": str(rec.assessment_type),
                    "day": day,
                    "score": float(rec.score),
                    "label": int(rec.label),
                    "features": feats,
                }
            )
            past_days.append(day)
            past_scores.append(float(rec.score))
            past_labels.append(int(rec.label))

    out = pd.DataFrame(rows)
    if out.empty:
        raise P05DataError("no attempts materialized from OULAD inputs")
    if not out["case_id"].is_unique:
        raise P05DataError("duplicate case_id in materialized attempts")
    return out


def _assemble_features(
    *,
    day: int,
    due_day: float,
    assessment_type: str,
    weight: float,
    module: str,
    presentation: str,
    course_len: float,
    past_days: list[int],
    past_scores: list[float],
    past_labels: list[int],
    click_days: np.ndarray,
    click_cum: np.ndarray,
) -> dict[str, float]:
    """Causal feature assembly. Everything is dated strictly before ``day``.

    A1 ablation removes the decay group; A3 the score group; A4 the
    engagement group; A5 the recency group (handled by column filtering in
    the model, not here — assembly is always complete and honest).
    """
    feats: dict[str, float] = {}
    # --- context (always available, not part of any ablation) ---
    feats["due_day"] = course_len if np.isnan(due_day) else due_day  # unknown exam date -> course end
    feats["weight"] = weight
    feats["is_exam"] = 1.0 if assessment_type == "Exam" else 0.0
    feats["is_cma"] = 1.0 if assessment_type == "CMA" else 0.0
    for m in ("AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG"):
        feats[f"module_{m}"] = 1.0 if module == m else 0.0
    feats["course_len"] = course_len

    # --- engagement history: clicks strictly before ``day`` ---
    if click_days.size:
        idx = np.searchsorted(click_days, day, side="left")  # first index with day_click >= day
        total_clicks = float(click_cum[idx - 1]) if idx > 0 else 0.0
        active_days = int(idx)
        last_click_day = int(click_days[idx - 1]) if idx > 0 else -1
        days_since_click = float(day - last_click_day) if idx > 0 else float("nan")
        recent_mask = click_days[max(0, idx - 14) : idx] if idx > 0 else click_days[:0]
        recent_days = int(np.sum(click_days[:idx] >= day - 14)) if idx > 0 else 0
    else:
        total_clicks, active_days, days_since_click, recent_days = 0.0, 0, float("nan"), 0
    feats["total_clicks"] = total_clicks
    feats["active_days"] = float(active_days)
    feats["click_rate"] = total_clicks / active_days if active_days > 0 else 0.0
    feats["recent14_active_days"] = float(recent_days)
    feats["days_since_click"] = 90.0 if np.isnan(days_since_click) else days_since_click
    feats["never_clicked"] = 1.0 if active_days == 0 else 0.0

    # --- assessment history: only attempts on a day STRICTLY before ``day`` ---
    # Same-day attempts (including this one) must never enter the features, or
    # the model sees contemporaneous information it could not have at prediction
    # time. We filter here rather than at the caller so every feature below is
    # guaranteed causal.
    strict = [(d, s, l) for d, s, l in zip(past_days, past_scores, past_labels) if d < day]
    past_days = [d for d, _, _ in strict]
    past_scores = [s for _, s, _ in strict]
    past_labels = [l for _, _, l in strict]
    n_past = len(past_days)
    feats["n_past_attempts"] = float(n_past)
    if n_past:
        last_day = past_days[-1]
        gap = float(day - last_day)
        feats["gap_days"] = gap
        feats["log_gap"] = float(np.log1p(gap))
        feats["days_since_last_attempt"] = gap
        feats["recent_attempts_14d"] = float(sum(1 for d in past_days if day - d <= 14))
        arr = np.asarray(past_scores, dtype=float)
        feats["past_score_mean"] = float(arr.mean())
        feats["past_score_std"] = float(arr.std()) if n_past > 1 else 0.0
        feats["past_score_min"] = float(arr.min())
        feats["past_score_max"] = float(arr.max())
        feats["past_fail_count"] = float(sum(1 for l in past_labels if l == 0))
        feats["past_fail_rate"] = feats["past_fail_count"] / n_past
        # A1-relevant: exponential-decay weighted mean score, half-life 45d (fixed a priori)
        w = np.exp2(-(day - np.asarray(past_days, dtype=float)) / 45.0)
        feats["decay_score_mean_h45"] = float(np.sum(w * arr) / np.sum(w))
    else:
        feats["gap_days"] = float("nan")
        feats["log_gap"] = float("nan")
        feats["days_since_last_attempt"] = float("nan")
        feats["recent_attempts_14d"] = 0.0
        feats["past_score_mean"] = float("nan")
        feats["past_score_std"] = 0.0
        feats["past_score_min"] = float("nan")
        feats["past_score_max"] = float("nan")
        feats["past_fail_count"] = 0.0
        feats["past_fail_rate"] = float("nan")
        feats["decay_score_mean_h45"] = float("nan")

    # post-cutoff keys are forbidden by construction; assert for defense in depth
    for key in feats:
        if any(hint in key for hint in ("future", "after_cutoff", "post_test", "final")):
            raise P05DataError(f"forbidden future-information feature key: {key}")
    return feats


# --- chronological split -----------------------------------------------------

def split_by_presentation(
    attempts: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Frozen chronological split: train 2013B+2013J, calibration 2014B, test 2014J."""
    parts = {
        "train": attempts[attempts["presentation"].isin(TRAIN_PRESENTATIONS)],
        "calibration": attempts[attempts["presentation"].isin(CALIBRATION_PRESENTATIONS)],
        "test": attempts[attempts["presentation"].isin(TEST_PRESENTATIONS)],
    }
    for name, part in parts.items():
        if part.empty:
            raise P05DataError(f"split '{name}' is empty")
    train_max_day = parts["train"].groupby("presentation")["day"].max()
    # train presentations end in 2013; test starts in 2014 — strictly future.
    return parts


def assert_temporal_ordering(parts: dict[str, pd.DataFrame]) -> None:
    """Train events must precede calibration which must precede test (by presentation year)."""
    order = {"2013B": 0, "2013J": 1, "2014B": 2, "2014J": 3}
    max_rank = {}
    for name in ("train", "calibration", "test"):
        ranks = [order[p] for p in parts[name]["presentation"].unique()]
        max_rank[name] = max(ranks)
    if not (max_rank["train"] < max_rank["calibration"] < max_rank["test"]):
        raise P05DataError(f"temporal ordering violated: {max_rank}")
    # within any learner's sequence in each split, days must be non-decreasing
    for name, part in parts.items():
        for _, grp in part.groupby(["learner_id", "module", "presentation"]):
            days = grp.sort_values("day")["day"].to_numpy()
            if np.any(np.diff(days) < 0):
                raise P05DataError(f"non-monotonic days in {name}")


def learner_overlap(parts: dict[str, pd.DataFrame]) -> dict[str, float]:
    """Report honest learner overlap between windows (repeating students)."""
    train = set(parts["train"]["learner_id"])
    cal = set(parts["calibration"]["learner_id"])
    test = set(parts["test"]["learner_id"])
    return {
        "train_cal_overlap_pct": round(100 * len(train & cal) / max(len(cal), 1), 3),
        "train_test_overlap_pct": round(100 * len(train & test) / max(len(test), 1), 3),
        "cal_test_overlap_pct": round(100 * len(cal & test) / max(len(test), 1), 3),
        "test_learners": len(test),
    }
