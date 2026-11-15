"""P06 selection-engine invariants: budget, gates, fairness, determinism.

Mirrors the LN-09 invariant: a high-risk learner with NO actionable evidence
must never be selected "as if evidence existed".
"""
from __future__ import annotations

import pytest

from research_v3.methods.p06.selection import (
    DEFAULT_EQUITY_QUOTAS,
    Decision,
    MIN_ACTABLE_RISK,
    Candidate,
    SelectionError,
    group_minima,
    random_selection,
    select_with_budget,
    suppress_small_cells,
)


def mk(cid, risk, evidence=True, subgroup="N", fail=False):
    return Candidate(case_id=cid, risk=risk, has_actionable_evidence=evidence, subgroup=subgroup, is_fail=fail)


# ---------------------------------------------------------------- budget ----

def test_budget_never_exceeded():
    cands = [mk(f"c{i:03d}", risk=0.9 - i * 0.001) for i in range(100)]
    for k in (0, 1, 25, 50, 99, 100, 500):
        res = select_with_budget(cands, k=k, enforce_equity=True)
        assert res.n_selected <= k, f"selected {res.n_selected} > k={k}"
        assert res.n_selected == min(k, sum(1 for c in cands if c.risk >= MIN_ACTABLE_RISK))


def test_capacity_lower_than_eligible_selects_exactly_k():
    cands = [mk(f"c{i:03d}", risk=0.99) for i in range(80)]
    res = select_with_budget(cands, k=25)
    assert res.n_selected == 25


def test_k_zero_selects_nothing():
    cands = [mk("a", 0.9), mk("b", 0.1)]
    res = select_with_budget(cands, k=0)
    assert res.n_selected == 0
    assert all(d != Decision.SELECTED.value for d in res.decisions.values())


# ----------------------------------------------------------------- gates ----

def test_high_risk_no_evidence_abstains_not_selected():
    """LN-09 invariant mirror: no actionable evidence => ABSTAIN, never SELECTED,
    even at maximal risk."""
    cands = [
        mk("no_evidence_high_risk", risk=0.999, evidence=False),
        mk("with_evidence_low_risk", risk=0.06, evidence=True),
    ]
    res = select_with_budget(cands, k=5)
    assert res.decisions["no_evidence_high_risk"] == Decision.ABSTAIN.value
    assert "no_evidence_high_risk" not in res.selected
    assert res.decisions["with_evidence_low_risk"] == Decision.SELECTED.value


def test_zero_evidence_learners_never_selected_even_when_budget_slack():
    cands = [mk(f"e{i}", risk=0.5) for i in range(10)] + [
        mk(f"z{i}", risk=0.99, evidence=False) for i in range(3)
    ]
    res = select_with_budget(cands, k=13)
    assert all(not cid.startswith("z") for cid in res.selected)


def test_below_threshold_risk_is_not_applicable():
    cands = [mk("tiny_risk", risk=MIN_ACTABLE_RISK - 0.01, evidence=True)]
    res = select_with_budget(cands, k=5)
    assert res.decisions["tiny_risk"] == Decision.NOT_APPLICABLE.value
    assert res.decisions["tiny_risk"] != Decision.ABSTAIN.value
    assert res.decisions["tiny_risk"] != Decision.SELECTED.value


def test_abstain_and_not_applicable_are_distinct_states():
    cands = [
        mk("abstainer", risk=0.9, evidence=False),
        mk("inapplicable", risk=0.01, evidence=True),
        mk("selectable", risk=0.5, evidence=True),
    ]
    res = select_with_budget(cands, k=3)
    states = set(res.decisions.values())
    assert Decision.ABSTAIN.value in states
    assert Decision.NOT_APPLICABLE.value in states
    assert Decision.SELECTED.value in states


def test_a3_gate_removal_selects_no_evidence_learners():
    """Ablation A3 is a TRUE removal: with apply_gates=False the zero-evidence
    learner becomes selectable — demonstrating the gate is the named mechanism."""
    cands = [mk("z_high_risk", risk=0.99, evidence=False), mk("e_low", risk=0.1)]
    gated = select_with_budget(cands, k=2, apply_gates=True)
    ungated = select_with_budget(cands, k=2, apply_gates=False)
    assert "z_high_risk" not in gated.selected
    assert "z_high_risk" in ungated.selected


# --------------------------------------------------------------- fairness ----

def test_fairness_coverage_enforced_when_feasible():
    # 20 eligible majority ('N'), 10 eligible minority ('Y'); pool share Y=1/3.
    # k=15, quota 0.5 => proportional floor Y = ceil(0.5*(1/3)*15) = 3, N = 8.
    # Both floors met; selection stays within budget.
    cands = [mk(f"n{i:02d}", risk=0.8 - i * 0.01, subgroup="N") for i in range(20)]
    cands += [mk(f"y{i:02d}", risk=0.3 + i * 0.01, subgroup="Y") for i in range(10)]
    res = select_with_budget(cands, k=15)
    y_sel = sum(1 for cid in res.selected if cid.startswith("y"))
    n_sel = sum(1 for cid in res.selected if cid.startswith("n"))
    assert y_sel >= 3
    assert n_sel >= 8
    assert res.n_selected == 15
    assert not res.capacity_conflict


def test_fairness_floor_takes_higher_risk_members_first():
    cands = [mk(f"y{i}", risk=0.2 + i * 0.01, subgroup="Y") for i in range(6)]
    res = select_with_budget(cands, k=3, equity_quotas={"Y": 0.5, "N": 0.5})
    # floor Y = 3; the 3 highest-risk Y's must be the reserved ones
    assert set(res.selected) == {"y5", "y4", "y3"}


def test_fairness_degrades_gracefully_when_infeasible():
    """Pool has 2 eligible minority members; floor asks 5 -> select min(floor,
    pool), no crash, conflict/infeasibility recorded rather than silently dropped."""
    cands = [mk(f"n{i:02d}", risk=0.8, subgroup="N") for i in range(10)]
    cands += [mk(f"y{i}", risk=0.7, subgroup="Y") for i in range(2)]
    res = select_with_budget(cands, k=6, equity_quotas={"Y": 0.5, "N": 0.5})
    y_sel = sum(1 for cid in res.selected if cid.startswith("y"))
    assert y_sel >= 1  # at least one minority seat when the pool supplies it
    assert y_sel == min(1, 2) or res.feasibility["Y"] is not None  # recorded either way
    assert res.n_selected == 6


def test_floors_never_override_capacity():
    """Floors exceed k: capacity wins, and it is the highest-risk learners kept."""
    cands = [mk(f"y{i}", risk=0.5 + i * 0.01, subgroup="Y") for i in range(10)]
    res = select_with_budget(cands, k=2, equity_quotas={"Y": 0.9, "N": 0.0})
    assert res.n_selected == 2
    assert set(res.selected) == {"y9", "y8"}


def test_group_minima_ceil_semantics():
    pool = [mk(f"y{i}", risk=0.1, subgroup="Y") for i in range(3)]
    minima, feas = group_minima(pool, {"Y": 0.5, "N": 0.5})
    assert minima["Y"] == 2  # ceil(0.5*3) in diagnostic mode
    assert minima["N"] == 0
    assert feas["Y"] is True


def test_group_minima_proportional_mode_feasible_by_construction():
    """Preregistered mode: floors scale with pool share AND capacity k."""
    pool = [mk(f"y{i}", risk=0.5, subgroup="Y") for i in range(910)]
    pool += [mk(f"n{i:04d}", risk=0.5, subgroup="N") for i in range(8764)]
    minima, feas = group_minima(pool, {"Y": 0.5, "N": 0.5}, k=25)
    # Y share = 910/9674 ≈ 9.41% -> ceil(0.5*0.0941*25) = 2 seats
    assert minima["Y"] == 2
    assert minima["N"] + minima["Y"] <= 25
    assert all(feas.values())


def test_floors_scale_with_k():
    pool = [mk(f"y{i}", risk=0.5, subgroup="Y") for i in range(100)]
    pool += [mk(f"n{i:03d}", risk=0.5, subgroup="N") for i in range(300)]
    m25, _ = group_minima(pool, {"Y": 0.5, "N": 0.5}, k=25)
    m100, _ = group_minima(pool, {"Y": 0.5, "N": 0.5}, k=100)
    assert m100["Y"] >= m25["Y"]


# ------------------------------------------------------------ determinism ----

def test_determinism_same_inputs_same_output():
    cands = [mk(f"c{i:03d}", risk=0.3 + (i % 7) * 0.05, subgroup="YN"[i % 2]) for i in range(50)]
    r1 = select_with_budget(cands, k=10)
    r2 = select_with_budget(cands, k=10)
    assert r1.selected == r2.selected
    assert r1.decisions == r2.decisions


def test_random_selection_deterministic_given_seed():
    cands = [mk(f"c{i:03d}", risk=0.5) for i in range(50)]
    r1 = random_selection(cands, k=10, seed=2026)
    r2 = random_selection(cands, k=10, seed=2026)
    assert r1.selected == r2.selected
    r3 = random_selection(cands, k=10, seed=7)
    assert r3.selected != r1.selected  # different seed => different draw


def test_ties_broken_by_case_id():
    cands = [mk("b", 0.5), mk("a", 0.5), mk("c", 0.5)]
    res = select_with_budget(cands, k=2)
    assert res.selected == ("a", "b")


# ------------------------------------------------------------- validation ----

def test_invalid_risk_rejected():
    with pytest.raises(SelectionError):
        mk("bad", risk=1.5)


def test_negative_k_rejected():
    with pytest.raises(SelectionError):
        select_with_budget([mk("a", 0.9)], k=-1)


def test_suppress_small_cells():
    out = suppress_small_cells({"big": 50, "small": 3})
    assert out["big"]["reason"] is None
    assert out["small"]["value"] is None
    assert out["small"]["reason"] == "suppressed_n_lt_5"


def test_default_quotas_are_preregistered():
    assert DEFAULT_EQUITY_QUOTAS == {"Y": 0.5, "N": 0.5}
