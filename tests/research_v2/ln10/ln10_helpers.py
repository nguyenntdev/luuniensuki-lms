"""LN-10 test helpers: scenario builders for the SRL state machine.

Named ``ln10_helpers`` (never a generic ``helpers.py``) to avoid cross-study
test-module collisions in the shared pytest rootdir.
"""
from __future__ import annotations

from typing import Any

from research_v2.contracts.types import StudyInput

STUDY_ID = "LN-10"


def make_features(**overrides: Any) -> dict[str, Any]:
    """Nominal authorized revision: student owner, aligned version, rationale."""
    features: dict[str, Any] = {
        "actor": {"owns_project": True, "role": "student"},
        "project": {
            "goal": "evidence_based_conservation_proposal",
            "reflection_completed": True,
            "state": "monitoring",
            "type": "heritage_city",
            "version": 3,
        },
        "transition": {
            "action": "revise_plan",
            "expected_version": 3,
            "new_goal": "heritage_learning_campaign",
            "rationale": "Khảo sát thực địa và đối chiếu Đại Nam Nhất Thống Chí "
            "đòi hỏi tái cấu trúc giả thuyết.",
        },
    }
    features.update(overrides)
    return features


def make_input(
    features: dict[str, Any] | None = None,
    *,
    case_id: str = "t",
) -> StudyInput:
    feats = features if features is not None else make_features()
    return StudyInput(
        study_id=STUDY_ID,
        case_id=case_id,
        split_id="test",
        group_id=f"{STUDY_ID}-grp-{case_id}",
        features=feats,
    )


def conflicting_edits_features(**overrides: Any) -> dict[str, Any]:
    """Mandatory case: TWO CONFLICTING OFFLINE EDITS to the same version.

    Both edits target ``expected_version: 3`` (== current project version) but
    carry divergent payloads (different new_goal), so neither a plain CAS
    failure nor idempotent redelivery explains them: the policy must detect
    the conflict and reject/postpone, not silently apply either edit.
    """
    features = make_features(
        concurrent_edits=[
            {
                "editor": "student-a",
                "expected_version": 3,
                "action": "revise_plan",
                "new_goal": "epigraphic_comparative_catalog",
                "rationale": "Bổ sung nguồn văn khắc Hán Nôm trên Cao Đỉnh.",
            },
            {
                "editor": "student-b",
                "expected_version": 3,
                "action": "revise_plan",
                "new_goal": "monsoon_flood_resilience_plan",
                "rationale": "Phân tích ảnh viễn thám vụ lũ монsoon 2020.",
            },
        ],
    )
    features.update(overrides)
    return features


def premature_submit_features(**overrides: Any) -> dict[str, Any]:
    """Project completion with no reflection (mandatory case 2)."""
    features = make_features(
        project={
            "goal": "evidence_based_conservation_proposal",
            "reflection_completed": False,
            "state": "monitoring",
            "type": "heritage_city",
            "version": 3,
        },
        transition={
            "action": "submit",
            "expected_version": 3,
            "new_goal": "heritage_learning_campaign",
            "rationale": "Đủ checklist mốc then chốt.",
        },
    )
    features.update(overrides)
    return features


def unauthorized_actor_features(**overrides: Any) -> dict[str, Any]:
    """Forged/foreign actor without ownership (mandatory deny case)."""
    features = make_features(actor={"owns_project": False, "role": "student"})
    features.update(overrides)
    return features


def missing_rationale_features(**overrides: Any) -> dict[str, Any]:
    """Material revision with empty rationale text (mandatory case 4 cousin)."""
    features = make_features(
        transition={
            "action": "revise_plan",
            "expected_version": 3,
            "new_goal": "heritage_learning_campaign",
            "rationale": "",
        },
    )
    features.update(overrides)
    return features
