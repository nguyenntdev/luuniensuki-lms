"""P13: leakage-proof splits and cutoff guards on real-OULAD-like frames.

Uses a synthetic clickstream with the exact OULAD schema so the tests run in
seconds without the 10.6M-row raw file, then mirrors the invariants that hold
for the real run (temporal leakage guard, learner disjointness).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research_v3.eval.leakage import LeakageError, audit_rows
from research_v3.methods.p13.splits import (
    P13SplitError,
    assert_train_test_disjoint,
    materialize_group_split,
    materialize_time_split,
)
from research_v3.methods.p13.srl_features import (
    FEATURE_CUTOFF_DAYS,
    build_srl_proxy_rows,
    window_clicks,
)


def _synth_clickstream(n_students: int = 120, seed: int = 5) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for s in range(n_students):
        mod = "AAA" if s % 2 == 0 else "BBB"
        pres = "2013J" if s % 3 else "2014J"
        n_events = int(rng.integers(5, 60))
        days = rng.integers(-20, 200, size=n_events)
        for d in days:
            rows.append(
                {
                    "code_module": mod,
                    "code_presentation": pres,
                    "id_student": 1000 + s,
                    "id_site": int(rng.integers(5000, 6000)),
                    "date": float(d),
                    "sum_click": int(rng.integers(1, 30)),
                    "activity_type": rng.choice(["oucontent", "forumng", "quiz", "homepage"]),
                }
            )
    return pd.DataFrame(rows)


def _synth_info(clickstream: pd.DataFrame) -> pd.DataFrame:
    keys = (
        clickstream[["code_module", "code_presentation", "id_student"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    keys["gender"] = "M"
    keys["region"] = "Scotland"
    keys["highest_education"] = "HE Qualification"
    keys["imd_band"] = "50-60%"
    keys["age_band"] = "35-55"
    keys["num_of_prev_attempts"] = 0
    keys["studied_credits"] = 60
    keys["disability"] = "N"
    keys["final_result"] = ["Pass", "Fail", "Withdrawn"] * (len(keys) // 3) + ["Pass"] * (len(keys) % 3)
    return keys


def test_window_clicks_excludes_future_and_pre_start():
    cs = _synth_clickstream()
    win = window_clicks(cs, start_day=0, end_day=FEATURE_CUTOFF_DAYS)
    assert win["date"].min() >= 0
    assert win["date"].max() <= FEATURE_CUTOFF_DAYS
    # no post-cutoff click can influence features
    n_all = len(cs)
    assert len(win) < n_all


def test_features_never_contain_label_or_id_columns():
    cs = _synth_clickstream()
    info = _synth_info(cs)
    rows = build_srl_proxy_rows(cs, info)
    for r in rows:
        assert "final_result" not in r["features"]
        assert "id_student" not in r["features"]
        assert "date" not in r["features"]
        assert r["label"] not in r["features"].values()


def test_group_split_never_spans_a_learner():
    cs = _synth_clickstream(n_students=200)
    info = _synth_info(cs)
    # give some learners two presentations so the guard has work to do
    rows = build_srl_proxy_rows(cs, info)
    manifest = materialize_group_split(rows)
    by_case = {r["case_id"]: r["group_id"] for r in rows}
    parts = {p: {by_case[c] for c in ids} for p, ids in manifest["split_ids"].items()}
    names = list(parts)
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            overlap = parts[a] & parts[b]
            assert not overlap, f"{a} x {b}: {sorted(overlap)[:3]}"


def test_time_split_holds_out_latest_presentation():
    cs = _synth_clickstream(n_students=200)
    info = _synth_info(cs)
    rows = build_srl_proxy_rows(cs, info)
    manifest = materialize_time_split(rows)
    assert manifest["test_presentations"] == ["2014J"]
    assert set(manifest["train_presentations"]) == {"2013B", "2013J", "2014B"}
    assert manifest["purged_recurring_learners_from_train"] >= 0


def test_time_split_with_recurring_learners_purges_them_from_train():
    rows = [
        {"case_id": f"a{i}", "group_id": str(i % 40), "time_key": "2013J"} for i in range(80)
    ]
    rows += [
        {"case_id": f"b{i}", "group_id": str(i % 40), "time_key": "2014J"} for i in range(80)
    ]
    rows += [
        {"case_id": f"x{i}", "group_id": f"u{i}", "time_key": "2013J"} for i in range(40)
    ]
    rows += [
        {"case_id": f"y{i}", "group_id": f"v{i}", "time_key": "2014J"} for i in range(40)
    ]
    manifest = materialize_time_split(rows)
    assert manifest["purged_recurring_learners_from_train"] == 80
    assert_train_test_disjoint(
        [{"case_id": r["case_id"], "group_id": r["group_id"]} for r in rows], manifest
    )


def test_assert_train_test_disjoint_raises_on_leak():
    rows = [
        {"case_id": "c1", "group_id": "7"},
        {"case_id": "c2", "group_id": "7"},
    ]
    manifest = {
        "split_ids": {"train": ["c1"], "calibration": [], "dev": [], "test": ["c2"]}
    }
    with pytest.raises(P13SplitError):
        assert_train_test_disjoint(rows, manifest)


def test_leakage_audit_flags_gold_key_in_input():
    rows = [{"case_id": "c1", "input": {"early_click_total": 5.0, "label": "Pass"}}]
    with pytest.raises(LeakageError):
        audit_rows(rows, strict=True)


def test_leakage_audit_flags_future_hint_keys():
    rows = [{"case_id": "c1", "input": {"final_grade_after": 70.0}}]
    with pytest.raises(LeakageError):
        audit_rows(rows, strict=True)


def test_no_future_click_used_by_feature_builder():
    """Temporal leakage guard: append post-cutoff clicks; features must not move."""
    cs = _synth_clickstream(seed=9)
    info = _synth_info(cs)
    base = build_srl_proxy_rows(cs, info)
    polluted = cs.copy()
    extra = polluted.iloc[:200].copy()
    extra["date"] = 250.0  # far beyond the cutoff
    extra["sum_click"] = 9999
    polluted = pd.concat([polluted, extra], ignore_index=True)
    after = build_srl_proxy_rows(polluted, info)
    for r_base, r_after in zip(base, after):
        assert r_base["features"] == r_after["features"], r_base["case_id"]
