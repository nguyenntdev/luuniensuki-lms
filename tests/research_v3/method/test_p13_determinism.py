"""P13: proxy determinism and construction invariants.

Same input frame => byte-identical feature output. Also verifies that feature
computation is a pure function (no hidden state, no RNG) and that the A2
temporal mutation is deterministic under its seed.
"""
from __future__ import annotations

import copy
import hashlib
import json

import numpy as np
import pandas as pd

from research_v3.methods.p13.srl_features import (
    C0_FEATURES,
    C1_FEATURES,
    SRL_PROXIES,
    build_srl_proxy_rows,
    mutate_temporal_order,
    srl_proxy_definitions,
    window_clicks,
)
from tests.research_v3.method.test_p13_splits_leakage import (
    _synth_clickstream,
    _synth_info,
)


def _frame_digest(rows: list[dict]) -> str:
    return hashlib.sha256(
        json.dumps(rows, sort_keys=True, default=float).encode()
    ).hexdigest()


def test_feature_builder_is_deterministic():
    cs = _synth_clickstream(seed=11)
    info = _synth_info(cs)
    r1 = build_srl_proxy_rows(cs, info)
    r2 = build_srl_proxy_rows(cs, info)
    assert _frame_digest(r1) == _frame_digest(r2)


def test_row_order_is_input_order_and_cases_unique():
    cs = _synth_clickstream(seed=12)
    info = _synth_info(cs)
    rows = build_srl_proxy_rows(cs, info)
    assert len(rows) == len(info)
    case_ids = [r["case_id"] for r in rows]
    assert len(set(case_ids)) == len(case_ids)
    # row i corresponds to info row i
    for r, (_, stu) in zip(rows, info.iterrows()):
        assert r["case_id"].endswith(
            f"{stu['code_module']}-{stu['code_presentation']}-{int(stu['id_student'])}"
        )


def test_all_required_features_present_and_finite():
    cs = _synth_clickstream(seed=13)
    info = _synth_info(cs)
    rows = build_srl_proxy_rows(cs, info)
    expected = set(SRL_PROXIES) | set(C0_FEATURES) | set(C1_FEATURES) | {"no_clicks_in_window"}
    for r in rows:
        assert set(r["features"]) == expected
        for v in r["features"].values():
            assert np.isfinite(v)


def test_zero_click_student_gets_explicit_zero_row_not_silent_drop():
    cs = _synth_clickstream(seed=14)
    info = _synth_info(cs)
    # one student whose clicks are ALL outside the window
    victim = info.iloc[0]
    cs = cs[
        ~(
            (cs["id_student"] == victim["id_student"])
            & (cs["code_presentation"] == victim["code_presentation"])
        )
    ]
    rows = build_srl_proxy_rows(cs, info)
    match = [
        r
        for r in rows
        if r["case_id"]
        == f"oulad-{victim['code_module']}-{victim['code_presentation']}-{int(victim['id_student'])}"
    ]
    assert len(match) == 1
    assert match[0]["features"]["no_clicks_in_window"] == 1.0
    assert match[0]["features"]["early_click_total"] == 0.0


def test_mutate_temporal_order_deterministic_and_destroying_order():
    cs = _synth_clickstream(seed=15)
    win = window_clicks(cs, start_day=0, end_day=60)
    m1 = mutate_temporal_order(win, seed=20261115)
    m2 = mutate_temporal_order(win, seed=20261115)
    assert m1["date"].tolist() == m2["date"].tolist()
    # per-student click mass preserved (only order changes)
    mass_before = win.groupby("id_student")["sum_click"].sum().sort_index()
    mass_after = m1.groupby("id_student")["sum_click"].sum().sort_index()
    pd.testing.assert_series_equal(mass_before, mass_after)
    # the (date -> click) pairing changes for at least one student with >1
    # event: the date multiset is preserved by design, the pairing is not.
    changed = False
    for s, grp in win.groupby("id_student"):
        if len(grp) <= 1:
            continue
        before = grp.sort_values("date")["sum_click"].tolist()
        after = m1[m1["id_student"] == s].sort_values("date")["sum_click"].tolist()
        if before != after:
            changed = True
            break
    assert changed, "mutation must re-pair dates with clicks"


def test_proxy_definitions_complete_and_flagged():
    defs = srl_proxy_definitions()
    assert set(defs["proxies"]) == set(SRL_PROXIES)
    for meta in defs["proxies"].values():
        assert meta["construct_validity"] == "proxy_only"
        assert meta["measured_construct"] is None
