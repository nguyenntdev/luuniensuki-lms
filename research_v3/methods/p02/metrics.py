"""P02 benchmark metrics: feasibility, optimality gap, false infeasibility,
runtime, all with exact numerators/denominators and certified-oracle deltas.

Definitions (see METHOD.md / prereg):
- feasibility_rate        : share of instances answered with a plan or a
                            PROVEN rejection matching the oracle decision.
- exact_match_rate        : share of instances whose (decision, cost) equals
                            the oracle verdict (cost compared only when the
                            oracle certifies feasibility).
- false_infeasibility     : oracle-feasible instances the solver rejected
                            (any infeasible/abstain label). MUST be 0 for
                            every exact solver; any positive count fails.
- optimality_gap          : mean over oracle-feasible instances of
                            (solver_cost - oracle_cost) / max(1, oracle_cost),
                            counting abstentions at +infinity (reported
                            separately as abstain count).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from .generator import GeneratedCase
from .problems import ABSTAIN, PlanningProblem, SolverResult

REJECT_DECISIONS = frozenset({"no_feasible_route", "cost_exceeded"})


@dataclass(frozen=True)
class SolverCell:
    solver_id: str
    n_instances: int
    exact_match: int
    feasible_found: int
    oracle_feasible: int
    false_infeasibility: int
    false_feasible: int
    abstains: int
    timeout_status: int
    optimal_status: int
    gap_numer: float  # sum of per-instance relative gaps (abstain excluded)
    gap_n: int
    gap_inf_count: int  # abstained/failed on an oracle-feasible instance
    wall_ms_total: float
    wall_ms_p95: float
    status_counts: Mapping[str, int]
    decision_counts: Mapping[str, int]

    @property
    def feasibility_rate(self) -> float | None:
        return None if self.n_instances == 0 else self.feasible_found / self.n_instances

    @property
    def exact_match_rate(self) -> float | None:
        return None if self.n_instances == 0 else self.exact_match / self.n_instances

    @property
    def mean_relative_gap(self) -> float | None:
        return None if self.gap_n == 0 else self.gap_numer / self.gap_n

    def to_dict(self) -> dict[str, Any]:
        return {
            "solver_id": self.solver_id,
            "n_instances": self.n_instances,
            "exact_match": self.exact_match,
            "exact_match_rate": self.exact_match_rate,
            "feasible_found": self.feasible_found,
            "feasibility_rate": self.feasibility_rate,
            "oracle_feasible": self.oracle_feasible,
            "false_infeasibility": self.false_infeasibility,
            "false_feasible": self.false_feasible,
            "abstains": self.abstains,
            "timeout_status": self.timeout_status,
            "optimal_status": self.optimal_status,
            "mean_relative_gap": self.mean_relative_gap,
            "gap_n": self.gap_n,
            "gap_inf_count": self.gap_inf_count,
            "wall_ms_total": round(self.wall_ms_total, 3),
            "wall_ms_p95": round(self.wall_ms_p95, 3),
            "status_counts": dict(sorted(self.status_counts.items())),
            "decision_counts": dict(sorted(self.decision_counts.items())),
        }


def _cost_of(result: SolverResult) -> int | None:
    return result.total_cost if result.decision == "find_valid_route" else None


def evaluate_cell(
    solver_id: str,
    cases: Sequence[GeneratedCase],
    results: Sequence[SolverResult],
) -> SolverCell:
    """Score one solver against certified oracle verdicts (same order)."""
    if len(cases) != len(results):
        raise ValueError("cases/results length mismatch")
    exact = feas = oracle_feas = false_inf = false_feas = abst = timeouts = optimal = 0
    gap_numer = 0.0
    gap_n = gap_inf = 0
    walls: list[float] = []
    status_counts: dict[str, int] = {}
    decision_counts: dict[str, int] = {}
    for case, res in zip(cases, results):
        if res.problem_id != case.problem.problem_id:
            raise ValueError(f"pairing mismatch at {res.problem_id}")
        walls.append(res.wall_ms)
        status_counts[res.status] = status_counts.get(res.status, 0) + 1
        decision_counts[res.decision] = decision_counts.get(res.decision, 0) + 1
        verdict = case.oracle
        oracle_feasible = verdict.decision == "find_valid_route"
        oracle_feas += int(oracle_feasible)
        if res.status == "timeout":
            timeouts += 1
        if res.status == "optimal":
            optimal += 1
        if res.decision == ABSTAIN:
            abst += 1
        if oracle_feasible:
            if res.decision == "find_valid_route":
                feas += 1
                cost = _cost_of(res)
                if cost is not None and verdict.optimum_cost is not None:
                    if cost == verdict.optimum_cost:
                        exact += 1
                    gap = (cost - verdict.optimum_cost) / max(1, verdict.optimum_cost)
                    gap_numer += gap
                    gap_n += 1
                else:  # pragma: no cover - feasible implies a cost
                    gap_inf += 1
            else:
                # REJECT on a feasible instance: the cardinal error.
                false_inf += 1
                gap_inf += 1
        else:
            # Oracle says infeasible/cost_exceeded; solver must agree.
            if res.decision == "find_valid_route":
                false_feas += 1
            elif res.decision == verdict.decision:
                exact += 1
    return SolverCell(
        solver_id=solver_id,
        n_instances=len(cases),
        exact_match=exact,
        feasible_found=feas,
        oracle_feasible=oracle_feas,
        false_infeasibility=false_inf,
        false_feasible=false_feas,
        abstains=abst,
        timeout_status=timeouts,
        optimal_status=optimal,
        gap_numer=gap_numer,
        gap_n=gap_n,
        gap_inf_count=gap_inf,
        wall_ms_total=sum(walls),
        wall_ms_p95=_p95(walls),
        status_counts=status_counts,
        decision_counts=decision_counts,
    )


def _p95(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1)))))
    return ordered[k]


def per_regime_breakdown(
    solver_id: str,
    cases: Sequence[GeneratedCase],
    results: Sequence[SolverResult],
) -> dict[str, dict[str, Any]]:
    """Metric block per budget regime (tight/mid/loose)."""
    out: dict[str, dict[str, Any]] = {}
    for regime in ("tight", "mid", "loose"):
        sub = [(c, r) for c, r in zip(cases, results) if c.regime == regime]
        if not sub:
            continue
        cell = evaluate_cell(solver_id, [c for c, _ in sub], [r for _, r in sub])
        out[regime] = cell.to_dict()
    return out


def per_family_breakdown(
    solver_id: str,
    cases: Sequence[GeneratedCase],
    results: Sequence[SolverResult],
) -> dict[str, dict[str, Any]]:
    """Metric block per topology family (family-level failure analysis)."""
    out: dict[str, dict[str, Any]] = {}
    families = sorted({c.problem.family_id for c in cases})
    for fam in families:
        sub = [(c, r) for c, r in zip(cases, results) if c.problem.family_id == fam]
        cell = evaluate_cell(solver_id, [c for c, _ in sub], [r for _, r in sub])
        out[fam] = cell.to_dict()
    return out


def paired_cost_differences(
    cases: Sequence[GeneratedCase],
    results_a: Sequence[SolverResult],
    results_b: Sequence[SolverResult],
) -> tuple[list[float], list[str], list[int | None]]:
    """Per-instance cost(A) - cost(B) on commonly feasible instances.

    Returns (diffs, group_ids, paired_flags) where paired_flags marks
    instances both solvers answered feasibly (regret-compatible pairs).
    """
    diffs: list[float] = []
    groups: list[str] = []
    flags: list[int | None] = []
    for case, ra, rb in zip(cases, results_a, results_b):
        if ra.decision == "find_valid_route" and rb.decision == "find_valid_route":
            diffs.append(float(ra.total_cost - rb.total_cost))
            groups.append(case.problem.family_id)
            flags.append(ra.total_cost - rb.total_cost)
        else:
            flags.append(None)
    return diffs, groups, flags
