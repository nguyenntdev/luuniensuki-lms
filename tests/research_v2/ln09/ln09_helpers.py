"""LN-09 test helpers: case builders mirroring the frozen T3 fixture schema.

Named ``ln09_helpers`` (never generic ``helpers``) to avoid cross-study
collision with other studies' helper modules.
"""
from __future__ import annotations

from typing import Any

from research_v2.contracts.types import ContractError, StudyInput

VERIFIED_EV = {"outcome": "evidence_use", "score": 0.2, "type": "source_task", "verified": True}
VERIFIED_QUIZ = {"outcome": "spatial", "score": 0.35, "type": "quiz", "verified": True}


def make_features(**overrides: Any) -> dict[str, Any]:
    """Nominal actionable case mirroring the T3 fixture schema."""
    features: dict[str, Any] = {
        "candidate_intervention": "additional_source_comparison_activity",
        "class_context": {"grade": 12, "subject": "GDĐP", "synthetic": True},
        "cohort_size": 25,
        "content": {"id": "ngo-mon", "type": "imperial-site"},
        "learner": {
            "access": "standard",
            "competencies": {"S1": 0.1, "S2": 0.2, "S3": 0.1, "S4": 0.1},
            "event_condition": "regular",
            "is_new": True,
            "profile_id": "SYN-NOVICE",
            "synthetic": True,
        },
        "learning_evidence": [dict(VERIFIED_EV), dict(VERIFIED_QUIZ)],
        "observation_age_days": 1,
        "required_signal_types": ["source_task", "quiz"],
        "seed": 20261202,
        "signals_conflict": False,
    }
    features.update(overrides)
    return features


def make_input(case_id: str = "case-nominal", features: dict[str, Any] | None = None) -> StudyInput:
    return StudyInput(
        study_id="LN-09",
        case_id=case_id,
        split_id="test",
        group_id="grp-test",
        features=features if features is not None else make_features(),
    )


def make_high_risk_no_evidence(case_id: str = "case-high-risk-no-evidence") -> StudyInput:
    """Mandatory counterexample: HIGH RISK flag, zero learning evidence.

    The learner profile shows very low competencies (a risk signal any naive
    system would act on) but there are NO logs/evidence to audit. INV-LN-09-01
    forbids inferring deficit from this absence.
    """
    return make_input(
        case_id,
        make_features(
            learning_evidence=[],
            learner={
                "access": "standard",
                "competencies": {"S1": 0.05, "S2": 0.05, "S3": 0.05, "S4": 0.05},
                "event_condition": "regular",
                "is_new": True,
                "profile_id": "SYN-NOVICE",
                "synthetic": True,
            },
        ),
    )


__all__ = [
    "make_features",
    "make_input",
    "make_high_risk_no_evidence",
    "VERIFIED_EV",
    "VERIFIED_QUIZ",
    "ContractError",
]
