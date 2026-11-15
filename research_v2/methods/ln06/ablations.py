"""LN-06 mechanism-isolating ablations.

Each ablation removes exactly one mechanism from the proposed pipeline and
keeps everything else identical (same input, same budget semantics, same
label space), so any metric movement is attributable to that mechanism:

- ``a1`` (``ablations_a1``): budget check disabled. Over-budget feasible
  subsets are returned as valid routes; the sensitive metric is
  false-acceptance of infeasible-budget plans.
- ``a2`` (``ablations_a2``): prerequisite closure disabled. Coverage targets
  are selected without transitive prerequisites and no cycle certification
  runs; the sensitive metric is prerequisite violations and missed cycles.
- ``a3`` (``ablations_a3``): the LEGACY all-providers bug, reproduced on
  purpose. Subset selection must include EVERY provider of each target
  outcome (OR-as-AND), so A/B-same-outcome cases are falsely reported
  infeasible. This is the documented regression of the observed engine,
  kept only to demonstrate that the proposed fix matters.

Ablations run the genuinely modified code path (flags into ``solve_case`` or
the dedicated a3 subset oracle), not a relabelled proposed output.
"""
from __future__ import annotations

from typing import Any, Mapping

from .dataset import DatasetError, Stop, TrailCase
from .labels import REASON_ABLATION, build_prediction
from .proposed import (
    DEFAULT_EXACT_NODE_BUDGET,
    DEFAULT_EXACT_ORDER_LIMIT,
    cyclic_outcomes,
    order_route,
    solve_case,
)

STUDY_ID = "LN-06"


# ---------------------------------------------------------------------------
# A1 — budget check disabled
# ---------------------------------------------------------------------------

def a1_solve(case: TrailCase, *, node_budget: int = DEFAULT_EXACT_NODE_BUDGET) -> dict[str, Any]:
    result = solve_case(case, enforce_budget=False, node_budget=node_budget)
    result["reason_codes"] = tuple(result["reason_codes"]) + (REASON_ABLATION, "no_budget_check")
    return result


# ---------------------------------------------------------------------------
# A2 — prerequisite closure disabled
# ---------------------------------------------------------------------------

def a2_solve(case: TrailCase, *, node_budget: int = DEFAULT_EXACT_NODE_BUDGET) -> dict[str, Any]:
    result = solve_case(
        case, enforce_prerequisites=False, node_budget=node_budget
    )
    result["reason_codes"] = tuple(result["reason_codes"]) + (REASON_ABLATION, "no_prerequisite_closure")
    return result


# ---------------------------------------------------------------------------
# A3 — legacy all-providers bug (OR-as-AND over alternative providers)
# ---------------------------------------------------------------------------

def _all_providers_subset(
    stops: tuple[Stop, ...],
    available_stops: frozenset[str],
    targets: frozenset[str],
) -> tuple[tuple[str, ...], int] | None:
    """Legacy needed_stops semantics: include EVERY provider of needed outcomes.

    Mirrors the observed engine's diagnostic closure: a stop joins the needed
    set when it provides any currently-needed outcome, and its prerequisites
    join the needed outcomes. All matching providers - not one of them - are
    accumulated, so alternatives are summed instead of chosen.
    """
    by_id = {s.id: s for s in stops}
    available = set(available_stops) & set(by_id)
    needed_outcomes = set(targets)
    needed_stops: set[str] = set()
    changed = True
    while changed:
        changed = False
        for s in stops:
            if s.id in needed_stops:
                continue
            if any(p in needed_outcomes for p in s.provides):
                needed_stops.add(s.id)
                needed_outcomes |= set(s.requires)
                changed = True
    # The legacy bug: sum EVERY available provider of every needed outcome.
    for s in stops:
        if s.id in available and any(p in needed_outcomes for p in s.provides):
            needed_stops.add(s.id)
    missing = needed_stops - available
    if missing:
        return None
    if not needed_stops <= set(by_id):
        return None
    chosen = tuple(sorted(needed_stops))
    return chosen, sum(by_id[sid].cost for sid in chosen)


def a3_solve(case: TrailCase, *, node_budget: int = DEFAULT_EXACT_NODE_BUDGET) -> dict[str, Any]:
    """Reproduce the legacy false-infeasibility regression on purpose."""
    by_id = {s.id: s for s in case.stops}
    if not case.checkpoint_claim_verified:
        return {
            "decision": "reject_checkpoint_source",
            "reason_codes": (REASON_ABLATION, "a3_all_providers", "source_gap"),
            "route": (),
            "total_cost": 0,
            "dwell_cost": 0,
            "travel_cost": 0,
        }
    cyclic = cyclic_outcomes(case.stops)
    if cyclic:
        return {
            "decision": "reject_cycle",
            "reason_codes": (REASON_ABLATION, "a3_all_providers", "prerequisite_cycle"),
            "route": (),
            "total_cost": 0,
            "dwell_cost": 0,
            "travel_cost": 0,
        }
    selection = _all_providers_subset(case.stops, case.available_stops, case.target_outcomes)
    if selection is None:
        covered = {o for sid in case.available_stops if sid in by_id for o in by_id[sid].provides}
        missing = sorted(case.target_outcomes - covered)
        reason = "unreachable_outcome:" + ",".join(missing) if missing else "all_providers_over_closure"
        return {
            "decision": "no_feasible_route",
            "reason_codes": (REASON_ABLATION, "a3_all_providers", reason),
            "route": (),
            "total_cost": 0,
            "dwell_cost": 0,
            "travel_cost": 0,
        }
    chosen, dwell = selection
    ordered, travel_cost = order_route(
        chosen, by_id, case.travel_edges, exact_order_limit=DEFAULT_EXACT_ORDER_LIMIT
    )
    total = dwell + travel_cost
    if total > case.time_budget_minutes:
        return {
            "decision": "cost_exceeded",
            "reason_codes": (REASON_ABLATION, "a3_all_providers", "over_budget"),
            "route": ordered,
            "total_cost": total,
            "dwell_cost": dwell,
            "travel_cost": travel_cost,
        }
    return {
        "decision": "find_valid_route",
        "reason_codes": (REASON_ABLATION, "a3_all_providers", "nominal"),
        "route": ordered,
        "total_cost": total,
        "dwell_cost": dwell,
        "travel_cost": travel_cost,
    }


# ---------------------------------------------------------------------------
# Contract ABI
# ---------------------------------------------------------------------------

def _predict(inputs: list, config: dict | None, solver) -> list:
    from research_v2.contracts.types import StudyInput

    cfg = dict(config or {})
    out = []
    for i, inp in enumerate(inputs):
        if not isinstance(inp, StudyInput):
            raise DatasetError(f"input[{i}] expects StudyInput, got {type(inp).__name__}")
        case = TrailCase.from_features(inp.features, case_id=inp.case_id)
        try:
            result = solver(case, node_budget=int(cfg.get("exact_node_budget", DEFAULT_EXACT_NODE_BUDGET)))
        except Exception as exc:
            raise DatasetError(f"input[{i}] case {inp.case_id!r}: {exc}") from exc
        out.append(
            build_prediction(
                case_id=inp.case_id,
                decision=result["decision"],
                reason_codes=tuple(result["reason_codes"]),
                evidence_ids=tuple(result["route"]),
                score=float(result["total_cost"]),
            )
        )
    return out


def a1_predict_one(inp: Any, config: Mapping[str, Any] | None = None) -> Any:
    return _predict([inp], config, a1_solve)[0]


def a2_predict_one(inp: Any, config: Mapping[str, Any] | None = None) -> Any:
    return _predict([inp], config, a2_solve)[0]


def a3_predict_one(inp: Any, config: Mapping[str, Any] | None = None) -> Any:
    return _predict([inp], config, a3_solve)[0]


def predict_batch_a1(inputs: list, config: dict | None = None) -> list:
    return _predict(inputs, config, a1_solve)


def predict_batch_a2(inputs: list, config: dict | None = None) -> list:
    return _predict(inputs, config, a2_solve)


def predict_batch_a3(inputs: list, config: dict | None = None) -> list:
    return _predict(inputs, config, a3_solve)
