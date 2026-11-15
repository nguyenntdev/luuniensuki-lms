"""Shared helpers for LN-06 V2 tests: case builders and policy dispatch."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research_v2.contracts.types import StudyInput, StudyPrediction  # noqa: E402
from research_v2.methods.ln06.dataset import TrailCase  # noqa: E402
from research_v2.methods.ln06.proposed import solve_case  # noqa: E402

STUDY_ID = "LN-06"


def make_case(
    stops: list[dict],
    available: list[str],
    targets: list[str],
    budget: int,
    verified: bool = True,
    travel_edges: list[dict] | None = None,
    case_id: str = "t",
) -> TrailCase:
    features: dict = {
        "stops": stops,
        "available_stops": available,
        "target_outcomes": targets,
        "time_budget_minutes": budget,
        "checkpoint_claim_verified": verified,
    }
    if travel_edges:
        features["travel_edges"] = travel_edges
    return TrailCase.from_features(features, case_id=case_id)


def make_input(case: TrailCase, features: dict | None = None) -> StudyInput:
    return StudyInput(
        study_id=STUDY_ID,
        case_id=case.case_id,
        split_id="test",
        group_id=f"{STUDY_ID}-grp-{case.case_id}",
        features=features if features is not None else dict(
            stops=[dict(id=s.id, cost=s.cost, provides=list(s.provides), requires=list(s.requires), type=s.type) for s in case.stops],
            available_stops=sorted(case.available_stops),
            target_outcomes=sorted(case.target_outcomes),
            time_budget_minutes=case.time_budget_minutes,
            checkpoint_claim_verified=case.checkpoint_claim_verified,
            travel_edges=[dict(from_=e.source, to=e.target, minutes=e.minutes) for e in case.travel_edges],
        ),
    )


AB_STOPS = [
    {"id": "A", "cost": 40, "provides": ["T"], "requires": [], "type": "alternative"},
    {"id": "B", "cost": 40, "provides": ["T"], "requires": [], "type": "alternative"},
]
# `stops` intentionally shared (not copied) so kwargs overrides of "stops" work.
AB_CASE = dict(stops=AB_STOPS, available=["A", "B"], targets=["T"], budget=50)


def policy_solve(name: str, case: TrailCase) -> dict:
    """Run any LN-06 method by its matrix id on a validated case."""
    if name == "proposed":
        return solve_case(case)
    from research_v2.methods.ln06.baselines import b0_solve, c1_solve
    from research_v2.methods.ln06.ablations import a1_solve, a2_solve, a3_solve

    return {
        "baselines_b0": b0_solve,
        "baselines_c1": c1_solve,
        "ablations_a1": a1_solve,
        "ablations_a2": a2_solve,
        "ablations_a3": a3_solve,
    }[name](case)


@pytest.fixture(scope="module")
def t3_dataset_paths():
    return (
        REPO_ROOT / "research_v2" / "data" / "ln06" / "t3_inputs.jsonl",
        REPO_ROOT / "research_v2" / "data" / "ln06" / "t3_gold.jsonl",
    )
