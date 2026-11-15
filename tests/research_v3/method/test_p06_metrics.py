"""P06 metrics: precision/recall/NDCG, k-anonymity suppression, fairness gap."""
from __future__ import annotations

import pytest

from research_v3.methods.p06.metrics import (
    fairness_gap,
    metrics_for_round,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    subgroup_coverage,
)
from research_v3.methods.p06.selection import Candidate, SelectionResult, select_with_budget


def mk(cid, risk, evidence=True, subgroup="N", fail=False):
    return Candidate(case_id=cid, risk=risk, has_actionable_evidence=evidence, subgroup=subgroup, is_fail=fail)


def test_precision_and_recall_basic():
    cands = {
        "a": mk("a", 0.9, fail=True),
        "b": mk("b", 0.8, fail=False),
        "c": mk("c", 0.7, fail=True),
        "d": mk("d", 0.1),
    }
    assert precision_at_k(["a", "b"], cands) == 0.5
    assert recall_at_k(["a", "b"], cands, total_fails=2) == 0.5
    assert recall_at_k(["a", "c"], cands, total_fails=2) == 1.0
    assert precision_at_k([], cands) is None
    assert recall_at_k(["a"], cands, total_fails=0) is None


def test_ndcg_perfect_and_imperfect_ranking():
    cands = {
        "a": mk("a", 0.9, fail=True),
        "b": mk("b", 0.8, fail=True),
        "c": mk("c", 0.7, fail=False),
        "d": mk("d", 0.1, fail=False),
    }
    perfect = ndcg_at_k(["a", "b", "c"], cands, k=3)
    assert perfect == 1.0
    swapped = ndcg_at_k(["c", "a", "b"], cands, k=3)
    assert 0.0 < swapped < 1.0
    assert swapped < perfect


def test_ndcg_none_when_no_fails():
    cands = {"a": mk("a", 0.9, fail=False), "b": mk("b", 0.1, fail=False)}
    assert ndcg_at_k(["a"], cands, k=1) is None


def test_k_anonymity_suppression_for_n_lt_5():
    """Selected minority cell with n<5 must be suppressed (value None + reason),
    never published as a number."""
    cands = {f"n{i:02d}": mk(f"n{i:02d}", 0.8, subgroup="N") for i in range(10)}
    cands.update({f"y{i}": mk(f"y{i}", 0.7, subgroup="Y") for i in range(3)})
    res = select_with_budget(list(cands.values()), k=8, equity_quotas={"Y": 0.5, "N": 0.5})
    pools = {"N": 10, "Y": 3}
    minima = {"N": 5, "Y": 2}
    cov = subgroup_coverage(list(res.selected), cands, pools=pools, minima=minima)
    # y cell: only ~1-2 selected with minima scaled down; if n<5 => suppressed
    if cov["Y"]["n"] < 5:
        assert cov["Y"]["value"] is None
        assert cov["Y"]["reason"] == "suppressed_n_lt_5"
    # N cell with 5+ selections must NOT be suppressed
    if cov["N"]["n"] >= 5:
        assert cov["N"]["reason"] is None
        assert cov["N"]["value"] is not None


def test_fairness_gap_suppressed_cells_propagate_none():
    cov = {
        "Y": {"n": 2, "value": None, "reason": "suppressed_n_lt_5"},
        "N": {"n": 10, "value": 0.5, "reason": None},
    }
    assert fairness_gap(cov) is None


def test_fairness_gap_direction():
    assert fairness_gap({"Y": {"n": 6, "value": 0.4, "reason": None}, "N": {"n": 6, "value": 0.8, "reason": None}}) == -0.4


def test_metrics_for_round_records_capacity_violation_flag():
    cands = {f"c{i:02d}": mk(f"c{i:02d}", 0.5 + i * 0.01, subgroup="YN"[i % 2]) for i in range(20)}
    res = select_with_budget(list(cands.values()), k=5)
    rec = metrics_for_round(
        res,
        cands,
        k=5,
        minima={"Y": 3, "N": 3},
        pools={"Y": 10, "N": 10},
        total_fails=4,
    )
    assert rec["capacity_violation"] is False
    assert rec["n_selected"] == 5
    assert "wilson_ci_95" in rec["precision_ci_95"]


def test_metrics_none_on_empty_selection():
    cands = {"a": mk("a", 0.01, evidence=True)}
    res = select_with_budget(list(cands.values()), k=0)
    rec = metrics_for_round(res, cands, k=0, minima={"Y": 0, "N": 0}, pools={"Y": 0, "N": 1}, total_fails=0)
    assert rec["precision_at_k"] is None
    assert rec["recall_at_k"] is None
    assert rec["ndcg_at_k"] is None
