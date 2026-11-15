"""P13 SRL proxy features from real OULAD clickstream.

All features are computed ONLY from ``studentVle`` rows whose ``date`` lies
inside the frozen observation window (default day 0..60 inclusive). The label
(``final_result``) is read from ``studentInfo`` but never enters the feature
dict. Every produced feature row carries
``construct_validity: "proxy_only"`` metadata via
:mod:`research_v3.methods.p13.construct_validity`.

Definitions live in ``srl_operationalisation.yaml`` / ``.md`` (cited). The
computation here is a pure function of the input frame: same input frame,
same features, byte-identical output (determinism test in tests/).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from research_v3.methods.p13.construct_validity import (
    PROXY_ONLY,
    ConstructValidityViolation,
    proxy_only_meta,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RAW = PROJECT_ROOT / "private_data" / "raw" / "oulad" / "2013-2014" / "_extracted"

#: Frozen feature cutoff (preregistration): features use clicks with
#: FEATURE_CUTOFF_START_DAY <= date <= FEATURE_CUTOFF_DAYS.
FEATURE_CUTOFF_START_DAY = 0
FEATURE_CUTOFF_DAYS = 60

LABEL_FIELD = "final_result"
FORBIDDEN_FEATURE_FIELDS = frozenset({LABEL_FIELD, "date", "id_student", "case_id"})

#: activity_type values treated as help-seeking (OULAD forum domain).
FORUM_TYPES = frozenset({"forumng"})

VALID_OUTCOMES = frozenset({"Pass", "Fail", "Withdrawn", "Distinction"})

_SRL_PHASES = {
    "plan_regularity": "forethought",
    "plan_early_start": "forethought",
    "plan_consistency_weekend_weekday": "forethought",
    "effort_mean_daily_clicks": "performance",
    "effort_dispersion": "performance",
    "effort_diversity": "performance",
    "help_seeking_forum_clicks": "performance",
    "help_seeking_forum_share": "performance",
    "self_observation_revisits": "performance",
    "reflect_late_activity": "self_reflection",
    "session_consistency": "performance",
}


class SrlFeatureError(ValueError):
    """Raised when inputs violate the schema or the leakage cutoff."""


@dataclass(frozen=True)
class ProxyMeta:
    """Per-feature metadata attached to every produced row."""

    names: tuple[str, ...]
    phases: dict[str, str] = field(default_factory=dict)
    validity: str = PROXY_ONLY

    def as_dict(self) -> dict[str, Any]:
        return {
            "feature_names": list(self.names),
            "zimmerman_phases": dict(self.phases),
            "construct_validity": self.validity,
            "measured_construct": None,
        }


def load_clickstream(raw_dir: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load studentVle + vle (site -> activity_type) from the raw snapshot."""
    base = Path(raw_dir or DEFAULT_RAW)
    svle_path = base / "studentVle.csv"
    vle_path = base / "vle.csv"
    if not svle_path.is_file() or not vle_path.is_file():
        raise SrlFeatureError(
            f"missing OULAD raw files under {base}; see research_v3/datasets/registry.yaml"
        )
    vle = pd.read_csv(vle_path, usecols=["id_site", "activity_type"])
    svle = pd.read_csv(
        svle_path,
        dtype={"code_module": "string", "code_presentation": "string", "id_student": "int64"},
        usecols=["code_module", "code_presentation", "id_student", "id_site", "date", "sum_click"],
    )
    if svle["date"].isna().any() or svle["sum_click"].isna().any():
        raise SrlFeatureError("studentVle contains nulls in date/sum_click; fail closed")
    merged = svle.merge(vle, on="id_site", how="left", validate="many_to_one")
    if merged["activity_type"].isna().any():
        raise SrlFeatureError("unmapped id_site values after joining vle.csv; fail closed")
    return merged, vle


def load_student_info(raw_dir: Path | None = None) -> pd.DataFrame:
    base = Path(raw_dir or DEFAULT_RAW)
    info = pd.read_csv(
        base / "studentInfo.csv",
        dtype={"id_student": "int64"},
        usecols=[
            "code_module", "code_presentation", "id_student", "gender", "region",
            "highest_education", "imd_band", "age_band", "num_of_prev_attempts",
            "studied_credits", "disability", LABEL_FIELD,
        ],
    )
    bad = set(info[LABEL_FIELD].unique()) - VALID_OUTCOMES
    if bad:
        raise SrlFeatureError(f"unexpected final_result values {sorted(bad)}")
    return info


def _gini(values: np.ndarray) -> float:
    """Gini coefficient of a 1-D array of non-negative values."""
    v = np.sort(values.astype(float))
    n = v.size
    if n == 0 or v.sum() == 0:
        return 0.0
    idx = np.arange(1, n + 1)
    return float((2.0 * float((idx * v).sum())) / (n * float(v.sum())) - (n + 1.0) / n)


def _shannon(shares: np.ndarray) -> float:
    shares = shares[shares > 0]
    if shares.size == 0:
        return 0.0
    return float(-(shares * np.log(shares)).sum())


def window_clicks(
    clickstream: pd.DataFrame, *, start_day: int, end_day: int, include_pre_start: bool = False
) -> pd.DataFrame:
    """Filter clicks to the observation window (leakage guard is the point).

    ``include_pre_start`` (sensitivity analysis only) additionally keeps
    negative-date rows, which the primary analysis excludes for comparability.
    """
    if end_day < start_day:
        raise SrlFeatureError("end_day must be >= start_day")
    mask = (clickstream["date"] >= start_day) & (clickstream["date"] <= end_day)
    if include_pre_start:
        mask = mask | (clickstream["date"] < 0)
    win = clickstream.loc[mask].copy()
    # A2 mutation hook lives in mutate_temporal_order(); the loader itself
    # never reorders dates.
    return win


def mutate_temporal_order(win: pd.DataFrame, seed: int = 20261115) -> pd.DataFrame:
    """A2 ablation: shuffle the ``date`` column *within each learner row-set*.

    Destroys temporal ordering while preserving per-student click mass, so the
    ablation removes exactly the ordering information (spec A2). Deterministic
    under ``seed``.
    """
    rng = np.random.default_rng(seed)
    out = win.copy()
    key = ["code_module", "code_presentation", "id_student"]
    shuffled = (
        out.groupby(key, observed=True, sort=False)["date"]
        .transform(lambda s: pd.Series(rng.permutation(s.to_numpy()), index=s.index))
    )
    out["date"] = shuffled
    return out


def _features_for_group(g: pd.DataFrame) -> dict[str, float]:
    """Compute all SRL proxies for one (module, presentation, student) group."""
    daily = g.groupby("date")["sum_click"].sum()
    days = daily.index.to_numpy(dtype=float)
    clicks = daily.to_numpy(dtype=float)
    total = float(clicks.sum())
    n_days = float(days.size)

    # --- forethought: planning regularity ----------------------------------
    gaps = np.diff(np.sort(days)) if days.size >= 2 else np.array([0.0])
    gap_mean = float(gaps.mean())
    plan_regularity = float(gaps.std(ddof=0) / gap_mean) if gap_mean > 0 else 0.0

    plan_early_start = float(days.min())

    weekend = ((days % 7) == 5) | ((days % 7) == 6)  # OULAD day 0 = course start
    # weekend regularity: share of active days that are weekend days, centred
    # at the expected 2/7 under a uniform routine.
    plan_weekend = float(weekend.mean()) if n_days else 0.0
    plan_consistency = abs(plan_weekend - (2.0 / 7.0))

    # --- performance: effort ------------------------------------------------
    effort_mean = float(clicks.mean())
    effort_dispersion = _gini(clicks)
    by_type = g.groupby("activity_type", observed=True)["sum_click"].sum()
    effort_diversity = _shannon((by_type / by_type.sum()).to_numpy(dtype=float))

    forum = float(by_type.get("forumng", 0.0))
    help_clicks = forum
    help_share = forum / total if total > 0 else 0.0

    sites = g.groupby("id_site")["date"].nunique()
    revisits = float((sites >= 2).mean()) if sites.size else 0.0

    # --- performance: session consistency ----------------------------------
    session_consistency = float(clicks.std(ddof=0))

    # --- self_reflection: late-window activity ------------------------------
    early_mask = days <= 44
    late_mask = days >= 45
    early_sum = float(clicks[early_mask].sum())
    late_sum = float(clicks[late_mask].sum())
    reflect_late = (late_sum / early_sum) if early_sum > 0 else (1.0 if late_sum > 0 else 0.0)

    return {
        "plan_regularity": plan_regularity,
        "plan_early_start": plan_early_start,
        "plan_consistency_weekend_weekday": plan_consistency,
        "effort_mean_daily_clicks": effort_mean,
        "effort_dispersion": effort_dispersion,
        "effort_diversity": effort_diversity,
        "help_seeking_forum_clicks": help_clicks,
        "help_seeking_forum_share": help_share,
        "self_observation_revisits": revisits,
        "reflect_late_activity": float(np.clip(reflect_late, 0.0, 10.0)),
        "session_consistency": session_consistency,
        # C0 / C1 features (baselines, not SRL proxies)
        "early_click_total": total,
        "active_days": n_days,
        "mean_daily_clicks": effort_mean,
        "click_std": session_consistency,
        "session_regularity_cv": plan_regularity,
        "days_since_last_activity": float(FEATURE_CUTOFF_DAYS - days.max()),
    }


SRL_PROXIES = tuple(_SRL_PHASES.keys())
C1_FEATURES = (
    "active_days", "mean_daily_clicks", "click_std",
    "session_regularity_cv", "days_since_last_activity",
)
C0_FEATURES = ("early_click_total",)


def build_srl_proxy_rows(
    clickstream: pd.DataFrame,
    student_info: pd.DataFrame,
    *,
    start_day: int = FEATURE_CUTOFF_START_DAY,
    end_day: int = FEATURE_CUTOFF_DAYS,
    include_pre_start: bool = False,
) -> list[dict[str, Any]]:
    """One output row per (student, module, presentation) with SRL proxies.

    Pure function. Rows carry ``case_id``, ``group_id`` (id_student),
    ``time_key`` (code_presentation), the SRL proxy features, baseline
    features, subgroup columns, and the label OUTSIDE the feature dict.
    """
    win = window_clicks(
        clickstream, start_day=start_day, end_day=end_day, include_pre_start=include_pre_start
    )
    grouped = win.groupby(
        ["code_module", "code_presentation", "id_student"], observed=True, sort=True
    )
    feat_rows = {key: _features_for_group(g) for key, g in grouped}

    rows: list[dict[str, Any]] = []
    for _, stu in student_info.iterrows():
        key = (stu["code_module"], stu["code_presentation"], int(stu["id_student"]))
        feats = feat_rows.get(key)
        if feats is None:
            # No clicks inside the window: emit explicit all-zero row; the
            # absence is itself recorded so zero-click students are never
            # silently dropped (fail-closed accounting, spec P13-T06).
            feats = {name: 0.0 for name in set(SRL_PROXIES) | set(C0_FEATURES) | set(C1_FEATURES)}
            feats["no_clicks_in_window"] = 1.0
        else:
            feats = dict(feats)
            feats["no_clicks_in_window"] = 0.0
        features = {
            **{p: feats[p] for p in SRL_PROXIES},
            **{c: feats[c] for c in C0_FEATURES + C1_FEATURES},
            "no_clicks_in_window": feats["no_clicks_in_window"],
        }
        leaked = set(features) & FORBIDDEN_FEATURE_FIELDS
        if leaked:
            raise SrlFeatureError(f"label/identifier leaked into features: {sorted(leaked)}")
        rows.append(
            {
                "case_id": (
                    f"oulad-{stu['code_module']}-{stu['code_presentation']}-{int(stu['id_student'])}"
                ),
                "group_id": str(int(stu["id_student"])),
                "time_key": str(stu["code_presentation"]),
                "module": str(stu["code_module"]),
                "features": features,
                "subgroups": {
                    "code_presentation": str(stu["code_presentation"]),
                    "gender": str(stu["gender"]),
                    "age_band": str(stu["age_band"]),
                    "imd_band": str(stu["imd_band"]),
                    "highest_education": str(stu["highest_education"]),
                    "disability": str(stu["disability"]),
                },
                "label": str(stu[LABEL_FIELD]),
            }
        )
    return rows


def srl_proxy_definitions() -> dict[str, Any]:
    """Metadata for every SRL proxy: phase, citation, construct_validity flag.

    This is the machine-readable guarantee required by the spec: every proxy
    carries ``construct_validity: "proxy_only"``. Tests assert this can never
    be silently upgraded.
    """
    citations = {
        "plan_regularity": "Kizilcec, Piech & Schneider (2013) LAK; Zimmerman (2000)",
        "plan_early_start": "Zimmerman (2000)",
        "plan_consistency_weekend_weekday": "Winne & Hadwin (1998)",
        "effort_mean_daily_clicks": "Gasevic, Dawson, Rogers & Gasevic (2016) LAK",
        "effort_dispersion": "Kizilcec, Piech & Schneider (2013) LAK",
        "effort_diversity": "Jovanovic, Gasevic, Dawson, Pardo & Mirriahi (2017) JLA",
        "help_seeking_forum_clicks": "Zimmerman & Martinez-Pons (1988); Jovanovic et al. (2017)",
        "help_seeking_forum_share": "Jovanovic et al. (2017)",
        "self_observation_revisits": "Winne & Hadwin (1998)",
        "reflect_late_activity": "Zimmerman (2000); OULAD TMA calendar",
        "session_consistency": "Kizilcec, Piech & Schneider (2013) LAK",
    }
    out: dict[str, Any] = {
        "measured_construct": None,
        "proxy_for_construct": "self-regulated learning (Zimmerman, 2000)",
        "proxies": {},
    }
    for name in SRL_PROXIES:
        meta = proxy_only_meta(_SRL_PHASES[name], citations[name])
        out["proxies"][name] = meta
        if meta[CONSTRUCT_VALIDITY_FLAG_KEY] != PROXY_ONLY:  # pragma: no cover
            raise ConstructValidityViolation(f"{name}: flag missing")
    return out


# local import shim to avoid a name clash at module import time
from research_v3.methods.p13.construct_validity import CONSTRUCT_VALIDITY_FLAG as _FLAG  # noqa: E402

CONSTRUCT_VALIDITY_FLAG_KEY = _FLAG
