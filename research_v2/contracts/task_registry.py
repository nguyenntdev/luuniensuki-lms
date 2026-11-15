"""Task registry: canonical study metadata and required artifacts."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Mapping


@dataclass(frozen=True)
class StudyTask:
    study_id: str
    title: str
    mandatory_case: str
    primary_metric: str

    def to_dict(self) -> dict:
        return asdict(self)


STUDIES: Mapping[str, StudyTask] = {
    "LN-01": StudyTask(
        "LN-01",
        "Spiral Curriculum Sequence Synthesis and Constraint-Aware Path Planning",
        "two alternative providers of same outcome",
        "spiral_sequence_validity_rate",
    ),
    "LN-02": StudyTask(
        "LN-02",
        "Non-Compensatory Prerequisite-Aware Adaptive Learning",
        "high overall score but one necessary skill absent",
        "prerequisite_violation_rate",
    ),
    "LN-03": StudyTask(
        "LN-03",
        "Evidence-Grounded Dual-Mode Spaced Learning",
        "generative task before any stable fact recall",
        "invalid_generative_assignment_rate",
    ),
    "LN-04": StudyTask(
        "LN-04",
        "Source-Grounded Socratic Tutoring and Instruction Boundary Enforcement",
        "the answer appears in malicious retrieved note",
        "answer_leakage_rate",
    ),
    "LN-05": StudyTask(
        "LN-05",
        "Evidence-Gated Mastery Credentials and Anti-Replay Gamification",
        "same valid submission delivered 100 times concurrently",
        "false_mastery_award_rate",
    ),
    "LN-06": StudyTask(
        "LN-06",
        "Constrained Heritage Trail Planning with Alternative Learning Stops",
        "A/B provide same outcome at 40 min, budget 50",
        "normalized_route_utility_regret",
    ),
    "LN-07": StudyTask(
        "LN-07",
        "Cognitive-Equivalent Multimodal Heritage Learning under Resource Constraints",
        "raster has image but omits inscription needed for task",
        "task_feasibility_rate",
    ),
    "LN-08": StudyTask(
        "LN-08",
        "Evidence-Calibrated Diagnostic Feedback for Historical Reasoning",
        "contains all keywords yet reverses historical relation",
        "diagnostic_error_rate",
    ),
    "LN-09": StudyTask(
        "LN-09",
        "Source-Auditable Teacher Decision Support under Incomplete Learning Analytics",
        "high risk but no actionable evidence",
        "unsupported_action_rate",
    ),
    "LN-10": StudyTask(
        "LN-10",
        "Process-Verifiable Self-Regulated Learning with Reflection Gates",
        "two conflicting offline edits to same version",
        "unjustified_transition_rate",
    ),
}

STUDY_IDS: tuple[str, ...] = tuple(sorted(STUDIES))


def get_study(study_id: str) -> StudyTask:
    try:
        return STUDIES[study_id]
    except KeyError as exc:
        raise ValueError(f"unknown study_id: {study_id!r}") from exc
