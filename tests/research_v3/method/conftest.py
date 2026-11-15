"""P05 test fixtures: tiny synthetic-but-realistic attempt sequences.

These fixtures NEVER touch the private OULAD raw directory: unit tests must
run in any environment. The real-data evaluation is a separate, explicitly
marked integration test that skips when raw data is absent.
"""
from __future__ import annotations

import pandas as pd
import pytest


def make_attempts() -> pd.DataFrame:
    """Three learners x two presentations with known temporal structure."""
    def feats(**kw):
        base = {
            "due_day": 100.0, "weight": 10.0, "is_exam": 0.0, "is_cma": 1.0,
            "course_len": 240.0, "module_AAA": 1.0, "gap_days": 10.0,
            "log_gap": 2.4, "decay_score_mean_h45": 70.0,
            "days_since_click": 2.0, "days_since_last_attempt": 10.0,
            "recent14_active_days": 3.0, "recent_attempts_14d": 1.0,
            "total_clicks": 100.0, "active_days": 10.0, "click_rate": 10.0,
            "n_past_attempts": 2.0, "never_clicked": 0.0,
            "past_score_mean": 70.0, "past_score_std": 5.0,
            "past_score_min": 60.0, "past_score_max": 80.0,
            "past_fail_count": 0.0, "past_fail_rate": 0.0,
            "never_clicked_hist": 0.0, "theta": 0.5,
        }
        base.update(kw)
        return base

    rows = []
    seq = [
        # learner, presentation, day, label, feature-override
        ("1", "2013J", 20, 1, {}),
        ("1", "2013J", 50, 1, {}),
        ("1", "2013J", 120, 0, {"gap_days": 70.0, "decay_score_mean_h45": 40.0}),
        ("2", "2013J", 30, 0, {"past_score_mean": 30.0}),
        ("2", "2013J", 60, 0, {"past_score_mean": 30.0}),
        ("2", "2013J", 90, 1, {"past_score_mean": 43.3}),
        ("3", "2013B", 40, 1, {}),
        ("3", "2013B", 80, 1, {}),
        ("3", "2013B", 130, 1, {}),
        ("1", "2014J", 30, 1, {}),
        ("1", "2014J", 100, 0, {"gap_days": 70.0}),
        ("2", "2014J", 45, 0, {}),
        ("3", "2014J", 60, 1, {}),
        ("3", "2014J", 150, 1, {"gap_days": 90.0}),
    ]
    for i, (learner, pres, day, label, over) in enumerate(seq):
        rows.append(
            {
                "case_id": f"syn-{i}",
                "learner_id": learner,
                "presentation": pres,
                "module": "AAA",
                "assessment_id": f"a{i}",
                "assessment_type": "CMA",
                "day": day,
                "score": 70.0 if label else 20.0,
                "label": label,
                "features": feats(),
            }
        )
    return pd.DataFrame(rows)


@pytest.fixture(scope="session")
def synthetic_attempts() -> pd.DataFrame:
    return make_attempts()


@pytest.fixture(scope="session")
def synthetic_parts(synthetic_attempts):
    train = synthetic_attempts[synthetic_attempts["presentation"].isin(["2013B", "2013J"])]
    cal = synthetic_attempts[synthetic_attempts["presentation"] == "2014B"]
    # synthetic data has no 2014B rows; reuse a slice of train as calibration
    # ONLY for unit-level contract tests (never for reported metrics)
    if cal.empty:
        cal = train.head(4)
    test = synthetic_attempts[synthetic_attempts["presentation"] == "2014J"]
    return {"train": train, "calibration": cal, "test": test}


def make_object(
    object_id: str,
    *,
    grade: int = 10,
    layer: int = 1,
    bloom: int | None = None,
    bloom_level: int | None = None,
    anchor: str | None = None,
    anchor_code: str | None = None,
    category: str | None = None,
):
    """Build a valid P10 LearningObject for invariant tests.

    Accepts both ``bloom``/``anchor`` (test call sites) and the canonical
    ``bloom_level``/``anchor_code`` names. Bloom is derived from the layer's
    allowed band when not supplied, so callers only override it deliberately.
    """
    from research_v3.methods.p10.anchors import LAYER_BLOOM_BANDS, LearningObject

    if category is None:
        category = "linh_thu"  # a real registry category that exists for every grade
    level = bloom if bloom is not None else bloom_level
    if level is None:
        lo, hi = LAYER_BLOOM_BANDS[layer]
        level = lo
    if anchor_code is not None:
        code = anchor_code
    elif anchor is not None:
        code = anchor
    else:
        # Default to a real registry code that matches the requested grade, so
        # unknown-anchor tests must opt in explicitly (never silently invented).
        code = f"P10-LOCAL-{category}-G{grade}"
    return LearningObject(
        object_id=object_id,
        urn_slug="cao-dinh",
        motif_name_vi=f"Motif {object_id}",
        category=category,
        grade=grade,
        layer=layer,
        bloom_level=level,
        anchor_code=code,
    )


@pytest.fixture(scope="session")
def anchor_registry():
    """P10 curriculum anchor registry (documented + needs-review codes)."""
    from research_v3.methods.p10.registry import build_anchor_registry

    return build_anchor_registry()


@pytest.fixture(scope="session")
def corpus():
    """P10 heritage learning-object corpus loaded read-only from data/."""
    from research_v3.methods.p10.corpus import load_corpus

    return load_corpus()
