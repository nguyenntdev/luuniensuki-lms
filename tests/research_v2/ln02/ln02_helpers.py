"""Shared helpers for LN-02 method tests (oracle-free by construction).

Fixtures are hand-built from the domain rubric (spec 03/14 counterexamples),
never copied from the sealed gold file; no test imports gold material.
"""
from __future__ import annotations

import copy
from pathlib import Path

from research_v2.contracts.types import StudyInput

STUDY_ID = "LN-02"
REPO_ROOT = Path(__file__).resolve().parents[3]

COMPETENCIES = ("S1", "S2", "S3", "S4")
HEALTHY_MASTERY = {"S1": 0.8, "S2": 0.75, "S3": 0.85, "S4": 0.7}


def make_input(
    case_id: str = "case-test",
    features: dict | None = None,
    *,
    group_id: str = "grp-test",
    split_id: str = "test",
) -> StudyInput:
    return StudyInput(
        study_id=STUDY_ID,
        case_id=case_id,
        split_id=split_id,
        group_id=group_id,
        features=copy.deepcopy(features or nominal_features()),
    )


def nominal_features() -> dict:
    """Nominal learner: all dims observed and above the task thresholds."""
    return {
        "content": {"id": "motif-nominal", "type": "imperial-urn-motif"},
        "graph_edges": [["S1", "S2"]],
        "learner": {
            "competencies": dict(HEALTHY_MASTERY),
            "profile_id": "LEARNER-NOMINAL",
        },
        "mastery": dict(HEALTHY_MASTERY),
        "score_observed": 0.72,
        "target_task": {
            "id": "task-nominal",
            "prerequisites": {"S1": 0.5, "S2": 0.45},
            "target_competency": "S3",
        },
    }


def high_aggregate_missing_prerequisite_features() -> dict:
    """MANDATORY counterexample (spec 14.C.4 / 03.F Case 1).

    High overall score, three dims strong, but one *required* dimension far
    below its threshold. Non-compensatory logic must remediate.
    """
    return {
        "content": {"id": "motif-gap", "type": "imperial-urn-motif"},
        "graph_edges": [["foundation_orientation", "chronological_sequence"]],
        "learner": {
            "competencies": {"S1": 0.22, "S2": 0.82, "S3": 0.75, "S4": 0.85},
            "profile_id": "LEARNER-GAP",
        },
        "mastery": {"S1": 0.22, "S2": 0.82, "S3": 0.75, "S4": 0.85},
        "score_observed": 0.74,
        "target_task": {
            "id": "task-gap",
            "prerequisites": {"S1": 0.6, "S2": 0.4},
            "target_competency": "S3",
        },
    }


def unobserved_dimension_features() -> dict:
    """Missing temporal competency (S2) but high observed verbal score
    (spec 03.F Case 2): required dim unobserved -> calibrated abstention."""
    return {
        "content": {"id": "motif-missing", "type": "imperial-urn-motif"},
        "graph_edges": [["S1", "S3"]],
        "learner": {
            "competencies": {"S1": 0.9, "S3": 0.88, "S4": 0.84},
            "profile_id": "LEARNER-MISSING",
        },
        "mastery": {"S1": 0.9, "S3": 0.88, "S4": 0.84},
        "score_observed": 0.78,
        "target_task": {
            "id": "task-missing",
            "prerequisites": {"S2": 0.5, "S3": 0.5},
            "target_competency": "S4",
        },
    }


def cyclic_graph_features() -> dict:
    return {
        "content": {"id": "motif-cycle", "type": "imperial-urn-motif"},
        "graph_edges": [
            ["spatial_mapping", "relic_identification"],
            ["relic_identification", "spatial_mapping"],
        ],
        "learner": {"competencies": dict(HEALTHY_MASTERY)},
        "mastery": dict(HEALTHY_MASTERY),
        "score_observed": 0.7,
        "target_task": {
            "id": "task-cycle",
            "prerequisites": {"S1": 0.5},
            "target_competency": "S2",
        },
    }


def invalid_score_features() -> dict:
    features = nominal_features()
    features["score_observed"] = 1.85
    return features


def load_t3_inputs(limit: int | None = None) -> list[StudyInput]:
    """Load the frozen T3 dataset as masked StudyInputs (no gold read)."""
    path = REPO_ROOT / "research_v2" / "data" / "ln02" / "t3_inputs.jsonl"
    import json

    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            rows.append(
                StudyInput(
                    study_id=STUDY_ID,
                    case_id=row["case_id"],
                    split_id="test",
                    group_id=row["group_id"],
                    features=row["input"],
                )
            )
            if limit is not None and len(rows) >= limit:
                break
    return rows
