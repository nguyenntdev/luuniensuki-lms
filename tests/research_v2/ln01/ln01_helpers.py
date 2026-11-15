"""LN-01 test helpers: case builders and typed-error helpers."""
from __future__ import annotations

from typing import Any

from research_v2.contracts.types import ContractError, StudyInput

VALID_ANCHORS = {
    "grade10": "GDĐP-HUE-10-ART",
    "grade11": "GDĐP-HUE-11-HISTORY",
    "grade12": "GDĐP-HUE-12-HERITAGE",
}


def make_features(**overrides: Any) -> dict[str, Any]:
    """Nominal 4-node spiral: 10 -> 10 -> 11 -> 12 with rising Bloom depth."""
    features: dict[str, Any] = {
        "nodes": [
            {"content_id": "cao-dinh", "grade": 10, "cognitive_level": 1, "objective": "motif_observation"},
            {"content_id": "cao-dinh", "grade": 10, "cognitive_level": 2, "objective": "epigraphic_comprehension"},
            {"content_id": "cao-dinh", "grade": 11, "cognitive_level": 3, "objective": "source_corroboration"},
            {"content_id": "cao-dinh", "grade": 12, "cognitive_level": 4, "objective": "heritage_evaluation"},
        ],
        "prerequisites": [[0, 1], [1, 2], [2, 3]],
        "curriculum_anchor": dict(VALID_ANCHORS),
    }
    features.update(overrides)
    return features


def make_input(case_id: str = "case-nominal", features: dict[str, Any] | None = None) -> StudyInput:
    return StudyInput(
        study_id="LN-01",
        case_id=case_id,
        split_id="test",
        group_id="grp-test",
        features=features if features is not None else make_features(),
    )


__all__ = ["make_features", "make_input", "VALID_ANCHORS", "ContractError"]
