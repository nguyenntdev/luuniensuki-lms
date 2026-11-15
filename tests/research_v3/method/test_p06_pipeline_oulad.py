"""P06 pipeline integration on REAL OULAD (marked slow; core cells only).

Uses the actual adapter + real splits + real model; runs a reduced matrix so
the suite stays fast while still executing the full production code path.
"""
from __future__ import annotations

import numpy as np
import pytest

from research_v3.datasets.adapters.oulad import assert_no_label_in_input, load_students
from research_v3.eval.leakage import assert_disjoint_groups, audit_rows
from research_v3.eval.splitters import freeze_hash, group_split, time_split
from research_v3.experiments.p06.run_experiment import (
    KS,
    SEED,
    make_splits,
    pool_counts,
    run_arm,
    to_candidates,
    total_fails,
)
from research_v3.methods.p06.metrics import metrics_for_round
from research_v3.methods.p06.risk_model import P06RiskModel
from research_v3.methods.p06.selection import group_minima


@pytest.fixture(scope="module")
def oulad_rows():
    return load_students()


def test_real_oulad_row_count_and_labels(oulad_rows):
    assert len(oulad_rows) == 32_593
    labels = {r["label"] for r in oulad_rows}
    assert labels == {"Distinction", "Pass", "Fail", "Withdrawn"}


def test_adapter_no_label_leak_and_audit_clean(oulad_rows):
    assert_no_label_in_input(oulad_rows)
    report = audit_rows(oulad_rows, strict=False)
    assert report["duplicates"] == 0
    assert report["status"] == "PASS"


def test_group_split_no_student_overlap(oulad_rows):
    split = group_split(oulad_rows, group_key="group_id", paper_id="P06", salt="p06-v3")
    student_to_part: dict[str, str] = {}
    part_by_case = {}
    for name, ids in split.split_ids.items():
        for cid in ids:
            part_by_case[cid] = name
    for r in oulad_rows:
        cid = str(r["case_id"])
        gid = str(r["group_id"])
        if gid in student_to_part:
            assert student_to_part[gid] == part_by_case[cid], "student spans partitions"
        else:
            student_to_part[gid] = part_by_case[cid]


def test_time_split_train_before_test(oulad_rows):
    ts = time_split(oulad_rows, time_key="time_key", paper_id="P06", train_fraction=0.70)
    ordered = sorted({r["input"]["code_presentation"] for r in oulad_rows})
    train_last = max(
        r["input"]["code_presentation"] for r in oulad_rows if str(r["case_id"]) in set(ts.split_ids["train"])
    )
    test_first = min(
        r["input"]["code_presentation"] for r in oulad_rows if str(r["case_id"]) in set(ts.split_ids["test"])
    )
    assert ordered.index(train_last) <= ordered.index(test_first)


def test_time_split_deterministic_hash(oulad_rows):
    s1 = make_splits(oulad_rows)
    s2 = make_splits(oulad_rows)
    assert s1[1]["group"]["hash"] == s2[1]["group"]["hash"]


@pytest.fixture(scope="module")
def fitted_time_model(oulad_rows):
    time_parts, _, _ = make_splits(oulad_rows)
    model = P06RiskModel().fit(time_parts["train"], time_parts["calibration"])
    risks = model.predict_proba(time_parts["test"])
    return time_parts, risks


def test_real_model_test_metrics_all_arms_respect_budget(oulad_rows, fitted_time_model):
    time_parts, risks = fitted_time_model
    test_rows = time_parts["test"]
    candidates = to_candidates(test_rows, risks)
    n_fail = total_fails(candidates)
    assert n_fail > 0
    pools = {
        g: n
        for g, n in [
            (g, sum(1 for c in candidates.values() if c.subgroup == g and c.has_actionable_evidence and c.risk >= 0.05))
            for g in ("Y", "N")
        ]
    }
    for arm in ("C0", "C1", "PROPOSED", "A1", "A2", "A3", "A4"):
        for k in KS:
            minima, feas = group_minima(
                [c for c in candidates.values() if c.has_actionable_evidence and c.risk >= 0.05],
                {"Y": 0.5, "N": 0.5},
                k=k,
            )
            res = run_arm(arm, candidates, k=k, seed=SEED)
            if arm == "A2":
                # A2 removes the capacity constraint by design: k := |eligible|;
                # its invariant is precision collapse, not budget respect.
                assert res.capacity_limit >= sum(pools.values())
            else:
                assert res.n_selected <= k, f"{arm} k={k} capacity violated"
            rec = metrics_for_round(res, candidates, k=k, minima=minima, pools=pools, total_fails=n_fail)
            if arm == "A2":
                assert rec["capacity_violation"] is True  # constraint removed by design
            else:
                assert rec["capacity_violation"] is False
            if arm in ("C0", "C1", "PROPOSED") and rec["recall_at_k"] is not None:
                assert 0.0 <= rec["recall_at_k"] <= 1.0
                assert 0.0 <= rec["precision_at_k"] <= 1.0


def test_proposed_meets_equity_floor_on_real_data(oulad_rows, fitted_time_model):
    time_parts, risks = fitted_time_model
    candidates = to_candidates(time_parts["test"], risks)
    pools = pool_counts(candidates)
    for k in KS:
        minima, _ = group_minima(
            [c for c in candidates.values() if c.has_actionable_evidence and c.risk >= 0.05],
            {"Y": 0.5, "N": 0.5},
            k=k,
        )
        res = run_arm("PROPOSED", candidates, k=k, seed=SEED)
        counts = {}
        for cid in res.selected:
            g = candidates[cid].subgroup
            counts[g] = counts.get(g, 0) + 1
        for g, m in minima.items():
            assert counts.get(g, 0) >= min(m, pools.get(g, 0)), f"k={k} group={g}"
        # proportional floors must fit inside the budget
        assert sum(minima.values()) <= k


def test_real_determinism_same_risks_same_selection(oulad_rows, fitted_time_model):
    time_parts, risks = fitted_time_model
    candidates = to_candidates(time_parts["test"], risks)
    r1 = run_arm("PROPOSED", candidates, k=50, seed=SEED)
    r2 = run_arm("PROPOSED", candidates, k=50, seed=SEED)
    assert r1.selected == r2.selected


def test_zero_evidence_learners_abstain_on_real_data(oulad_rows, fitted_time_model):
    time_parts, risks = fitted_time_model
    candidates = to_candidates(time_parts["test"], risks)
    zero_ev = [c for c in candidates.values() if not c.has_actionable_evidence]
    assert zero_ev, "real OULAD test partition must contain zero-evidence learners"
    res = run_arm("PROPOSED", candidates, k=100, seed=SEED)
    for c in zero_ev:
        assert res.decisions[c.case_id] in ("ABSTAIN",)
        assert c.case_id not in res.selected
