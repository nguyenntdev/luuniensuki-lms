"""P06 selection engine: eligibility, budgeted selection with equity floor,
k-anonymity suppression.

NON-CAUSAL CONTRACT: this module only *ranks and selects* learners against
realized outcomes for measurement. It must never be described as averting or
improving outcomes; OULAD is observational. See METHOD.md section 1.

Decision states are distinct (METHOD.md §2, requirement 1):
- ``SELECTED``   — in the intervention set (evidence exists, risk >= p_min)
- ``ABSTAIN``    — high/negative risk but NO actionable evidence (gate)
- ``NOT_APPLICABLE`` — evidence exists but risk below the actable threshold
- ``NOT_SELECTED``   — eligible but outside the budget
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Sequence

import math


class SelectionError(ValueError):
    """Raised when a selection violates a hard invariant."""


class Decision(str, Enum):
    SELECTED = "SELECTED"
    NOT_SELECTED = "NOT_SELECTED"
    ABSTAIN = "ABSTAIN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


#: Preregistered constants (METHOD.md §2; fixed, never learned).
MIN_ACTABLE_RISK = 0.05
K_ANONYMITY_MIN_N = 5
DEFAULT_EQUITY_QUOTAS = {"Y": 0.5, "N": 0.5}  # disability attribute
DEFAULT_COSTS: Mapping[str, float] = {"Y": 1.0, "N": 1.0}  # cost-neutral default


@dataclass(frozen=True)
class Candidate:
    """One learner in one cohort selection round."""

    case_id: str
    risk: float
    has_actionable_evidence: bool
    subgroup: str  # value of the constrained attribute, e.g. disability 'Y'/'N'
    is_fail: bool  # sealed gold; used ONLY by the evaluator, never by selection
    cost: float = 1.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.risk <= 1.0:
            raise SelectionError(f"{self.case_id}: risk {self.risk} outside [0,1]")
        if self.cost < 0:
            raise SelectionError(f"{self.case_id}: negative cost")


@dataclass(frozen=True)
class SelectionResult:
    """Outcome of one selection round with full per-learner decisions."""

    selected: tuple[str, ...]
    decisions: Mapping[str, str]
    abstained: tuple[str, ...] = field(default_factory=tuple)
    not_applicable: tuple[str, ...] = field(default_factory=tuple)
    capacity_limit: int = 0
    feasibility: Mapping[str, bool] = field(default_factory=dict)
    capacity_conflict: bool = False  # True when floors jointly exceeded k

    @property
    def n_selected(self) -> int:
        return len(self.selected)


def eligible_pool(
    candidates: Sequence[Candidate],
    *,
    apply_gates: bool = True,
) -> list[Candidate]:
    """Learners with actionable evidence AND risk >= MIN_ACTABLE_RISK.

    A learner with NO actionable evidence is never eligible (ABSTAIN), even at
    very high predicted risk: without evidence there is nothing to act on, and
    selecting them would fabricate an action (LN-09 invariant). A learner with
    evidence but tiny risk is NOT_APPLICABLE (below the actable threshold).

    ``apply_gates=False`` is ONLY for ablation A3 (true removal of the gating
    mechanism, METHOD.md §6); it must never be used for a headline arm.
    """
    pool = []
    for c in candidates:
        if apply_gates:
            if not c.has_actionable_evidence:
                continue
            if c.risk < MIN_ACTABLE_RISK:
                continue
        pool.append(c)
    return pool


def group_minima(
    pool: Sequence[Candidate],
    quotas: Mapping[str, float],
    *,
    k: int | None = None,
) -> tuple[dict[str, int], dict[str, bool]]:
    """Preregistered equity floors per subgroup and their feasibility.

    With ``k`` given (preregistered mode): proportional floors
    ``m_g = ceil(quota_g * pi_g * k)`` where ``pi_g`` is the group's share of
    the eligible pool — feasible by construction when quotas sum to <= 1.
    Without ``k`` (diagnostic mode): ``m_g = ceil(quota_g * |eligible g|)``,
    which may exceed any realistic capacity and is recorded as infeasible.

    A floor also degrades to ``min(m_g, |E_g|)`` when the pool cannot supply
    it; feasibility is reported per group.
    """
    counts: dict[str, int] = {}
    for c in pool:
        counts[c.subgroup] = counts.get(c.subgroup, 0) + 1
    total = sum(counts.values())
    minima: dict[str, int] = {}
    feasibility: dict[str, bool] = {}
    for g, quota in quotas.items():
        if k is not None and total > 0:
            pi_g = counts.get(g, 0) / total
            m = math.ceil(quota * pi_g * k)
        else:
            m = math.ceil(quota * counts.get(g, 0))
        reachable = min(m, counts.get(g, 0))
        minima[g] = reachable
        feasibility[g] = counts.get(g, 0) >= m
    return minima, feasibility


def _order_key(c: Candidate) -> tuple[float, str]:
    """Deterministic sort: risk desc, then case_id asc."""
    return (-c.risk, c.case_id)


def select_with_budget(
    candidates: Sequence[Candidate],
    *,
    k: int,
    equity_quotas: Mapping[str, float] | None = None,
    enforce_equity: bool = True,
    apply_gates: bool = True,
) -> SelectionResult:
    """Select at most ``k`` eligible learners, honoring subgroup floors.

    Exact two-phase greedy for the separable objective ``sum of selected
    risk`` under group minima (METHOD.md §2/§8): reserve each group's floor
    with its highest-risk eligible members, then fill remaining capacity by
    risk order over the whole eligible pool. Tie-breaks deterministic.

    ``apply_gates=False`` (ablation A3 only) removes the evidence/risk gates;
    every learner becomes selectable and ABSTAIN/NOT_APPLICABLE vanish.

    Hard invariants (each tested in tests/research_v3/method/test_p06_*.py):
    - never more than ``k`` selections;
    - no ineligible learner is ever selected (evidence gate respected);
    - every eligible subgroup floor is met whenever the pool allows;
    - deterministic given the same inputs.
    """
    if k < 0:
        raise SelectionError("k must be >= 0")
    quotas = dict(equity_quotas) if equity_quotas is not None else dict(DEFAULT_EQUITY_QUOTAS)

    pool = eligible_pool(candidates, apply_gates=apply_gates)
    pool_sorted = sorted(pool, key=_order_key)

    reserved: list[Candidate] = []
    feasibility: dict[str, bool] = {}
    minima: dict[str, int] = {}
    capacity_conflict = False
    if enforce_equity:
        minima, feasibility = group_minima(pool, quotas, k=k)
        # Defense-in-depth: if user quotas sum > 1, floors can jointly exceed
        # k; scale proportionally (deterministic) and record the conflict.
        total_floor = sum(minima.values())
        if total_floor > k and total_floor > 0:
            capacity_conflict = True
            minima = {
                g: min(m, int(m * k // total_floor)) for g, m in minima.items()
            }
        taken_per_group: dict[str, int] = {}
        for c in pool_sorted:
            m = minima.get(c.subgroup, 0)
            if m <= 0:
                continue
            if taken_per_group.get(c.subgroup, 0) < m:
                reserved.append(c)
                taken_per_group[c.subgroup] = taken_per_group.get(c.subgroup, 0) + 1

    # Reserved set can exceed k when floors + capacity conflict; capacity wins
    # (hard constraint) and the excess is dropped highest-risk-first so the
    # floors are infringed only where mathematically unavoidable.
    if len(reserved) > k:
        reserved = sorted(reserved, key=_order_key)[:k]
        capacity_conflict = True

    selected = list(reserved)
    chosen_ids = {c.case_id for c in selected}

    def cost_of(seq: Sequence[Candidate]) -> float:
        return sum(c.cost for c in seq)

    budget_left = k - len(selected)
    if budget_left > 0:
        for c in pool_sorted:
            if budget_left <= 0:
                break
            if c.case_id in chosen_ids:
                continue
            selected.append(c)
            chosen_ids.add(c.case_id)
            budget_left -= 1

    selected_set = set(chosen_ids)
    decisions: dict[str, str] = {}
    abstained: list[str] = []
    not_applicable: list[str] = []
    for c in candidates:
        if c.case_id in selected_set:
            decisions[c.case_id] = Decision.SELECTED.value
        elif apply_gates and not c.has_actionable_evidence:
            decisions[c.case_id] = Decision.ABSTAIN.value
            abstained.append(c.case_id)
        elif apply_gates and c.risk < MIN_ACTABLE_RISK:
            decisions[c.case_id] = Decision.NOT_APPLICABLE.value
            not_applicable.append(c.case_id)
        else:
            decisions[c.case_id] = Decision.NOT_SELECTED.value

    if len(selected) > k:
        raise SelectionError(
            f"capacity violated: selected {len(selected)} > k={k}"
        )
    if enforce_equity:
        counts: dict[str, int] = {}
        for c in selected:
            counts[c.subgroup] = counts.get(c.subgroup, 0) + 1
        # Scaled minima are feasible by construction; verify against them.
        for g, m in (minima or {}).items():
            pool_g = sum(1 for c in pool if c.subgroup == g)
            if counts.get(g, 0) < min(m, pool_g):
                raise SelectionError(
                    f"equity floor unmet for feasible group {g!r}: "
                    f"{counts.get(g, 0)} < {min(m, pool_g)}"
                )

    return SelectionResult(
        selected=tuple(c.case_id for c in selected),
        decisions=decisions,
        abstained=tuple(sorted(abstained)),
        not_applicable=tuple(sorted(not_applicable)),
        capacity_limit=k,
        feasibility=feasibility,
        capacity_conflict=capacity_conflict,
    )


def suppress_small_cells(
    counts: Mapping[str, int],
    *,
    min_n: int = K_ANONYMITY_MIN_N,
) -> dict[str, dict[str, object]]:
    """k-anonymity suppression for reported per-subgroup statistics.

    Any cell with ``n < min_n`` becomes ``{"n": n, "value": None,
    "reason": "suppressed_n_lt_5"}``; never a fabricated number.
    """
    out: dict[str, dict[str, object]] = {}
    for name, n in counts.items():
        if n < min_n:
            out[name] = {"n": int(n), "value": None, "reason": f"suppressed_n_lt_{min_n}"}
        else:
            out[name] = {"n": int(n), "value": None, "reason": None}
    return out


def random_selection(
    candidates: Sequence[Candidate],
    *,
    k: int,
    seed: int,
) -> SelectionResult:
    """C0: uniform random selection among the *eligible* pool (same gate).

    Deterministic given ``seed``. Subgroup attribute recorded but no floor
    enforced (that contrast is PROPOSED vs C1/C0 policies).
    """
    import random

    pool = eligible_pool(candidates)
    rng = random.Random(seed)
    picked = pool[:] if k >= len(pool) else rng.sample(pool, k)
    picked_ids = {c.case_id for c in picked}
    decisions: dict[str, str] = {}
    for c in candidates:
        if c.case_id in picked_ids:
            decisions[c.case_id] = Decision.SELECTED.value
        elif not c.has_actionable_evidence:
            decisions[c.case_id] = Decision.ABSTAIN.value
        elif c.risk < MIN_ACTABLE_RISK:
            decisions[c.case_id] = Decision.NOT_APPLICABLE.value
        else:
            decisions[c.case_id] = Decision.NOT_SELECTED.value
    return SelectionResult(
        selected=tuple(c.case_id for c in picked),
        decisions=decisions,
        abstained=tuple(sorted(c.case_id for c in candidates if decisions[c.case_id] == Decision.ABSTAIN.value)),
        not_applicable=tuple(sorted(c.case_id for c in candidates if decisions[c.case_id] == Decision.NOT_APPLICABLE.value)),
        capacity_limit=k,
        feasibility={},
    )
