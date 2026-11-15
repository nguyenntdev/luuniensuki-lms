"""Label spaces per study for Research V2.

Each study declares the set of legal decision labels and the oracle basis
labels that are permitted in evaluator-side gold records. Synthetic or
programmatic annotation must never be described as human adjudication.
"""
from __future__ import annotations

from typing import Mapping

# Legal non-human oracle bases. Anything outside this set is rejected by the
# provenance gate: it would otherwise imply unverified human/expert authority.
ALLOWED_ORACLE_BASES: frozenset[str] = frozenset(
    {
        "SYNTHETIC_PREREGISTERED_RULE_ORACLE",
        "PEDAGOGICAL_DAG_CONSTRAINTS",
        "ZIMMERMAN_SRL_CYCLICAL_INVARIANT",
        "PEDAGOGICAL_SPEC_DUAL_MODE",
        "SOCRATIC_SCAFFOLDING_SPEC",
        "DESIGN_SPEC_EMPIRICAL_HOLDOUT",
        "INSTRUCTIONAL_RECOMMENDATIONS_DOMAIN_INVARIANT",
        "DIAGNOSTIC_FEEDBACK_SPEC",
        "SOCRATIC_SCAFFOLDING_SPEC",
        "PROMPT_INJECTION_DEFENSE_SPEC",
        "EPISTEMIC_SOURCE_INTEGRITY_SPEC",
        "ANSWER_LEAKAGE_DEFENSE_SPEC",
        "DOMAIN_BOUNDARY_INTEGRITY_SPEC",
        "EXACT_SOLVER_REFERENCE",
        "PREREGISTERED_RULE_ORACLE",
    }
)

SYNTHETIC_COHORT = "SYNTHETIC_HELD_OUT_TEST_SET"
PROVENANCE_MARKER = "PROGRAMMATIC_TEMPLATE_NO_HUMAN_ADJUDICATION"

LN01_DECISIONS: frozenset[str] = frozenset(
    {"find_valid_route", "reject_cycle", "no_feasible_route", "cost_exceeded"}
)
LN02_DECISIONS: frozenset[str] = frozenset(
    {"recommend_eligible", "remediate_first", "abstain_insufficient_data", "reject_cycle", "reject_invalid_score"}
)
LN03_DECISIONS: frozenset[str] = frozenset(
    {"schedule_eligible", "postpone", "remediate_first", "reject_missing_fact", "reject_absent_source"}
)
LN04_DECISIONS: frozenset[str] = frozenset(
    {"hint", "socratic_question", "abstain_insufficient_source", "reject_injection", "direct_answer"}
)
LN05_DECISIONS: frozenset[str] = frozenset(
    {"grant_if_eligible", "deny_mastery_badge", "reject_replay", "reject_spoofed_provenance", "reject_stale_policy"}
)
LN06_DECISIONS: frozenset[str] = frozenset(
    {"find_valid_route", "reject_cycle", "no_feasible_route", "cost_exceeded", "reject_checkpoint_source"}
)
LN07_DECISIONS: frozenset[str] = frozenset(
    {"complete_multimodal", "fallback_acceptable", "reject_inaccessible", "reject_missing_affordance"}
)
LN08_DECISIONS: frozenset[str] = frozenset(
    {"feedback_supported", "classify_contradiction", "classify_source_error", "feedback_incomplete", "abstain_insufficient_data"}
)
LN09_DECISIONS: frozenset[str] = frozenset(
    {"recommend_action", "descriptive_only", "abstain_insufficient_data", "require_teacher_override"}
)
LN10_DECISIONS: frozenset[str] = frozenset(
    {"apply_transition", "require_reflection", "reject_unauthorized", "reject_conflict", "postpone"}
)

DECISIONS_BY_STUDY: Mapping[str, frozenset[str]] = {
    "LN-01": LN01_DECISIONS,
    "LN-02": LN02_DECISIONS,
    "LN-03": LN03_DECISIONS,
    "LN-04": LN04_DECISIONS,
    "LN-05": LN05_DECISIONS,
    "LN-06": LN06_DECISIONS,
    "LN-07": LN07_DECISIONS,
    "LN-08": LN08_DECISIONS,
    "LN-09": LN09_DECISIONS,
    "LN-10": LN10_DECISIONS,
}


class LabelSpaceError(ValueError):
    """Raised when a decision label is outside the study's declared space."""


def validate_decision(study_id: str, decision: str) -> None:
    space = DECISIONS_BY_STUDY.get(study_id)
    if space is None:
        raise LabelSpaceError(f"unknown study_id: {study_id!r}")
    if decision not in space:
        raise LabelSpaceError(
            f"{study_id}: decision {decision!r} not in declared label space {sorted(space)}"
        )


def validate_oracle_basis(basis: str) -> None:
    if basis not in ALLOWED_ORACLE_BASES:
        raise LabelSpaceError(
            f"oracle basis {basis!r} is not an allowed non-human basis; "
            f"allowed={sorted(ALLOWED_ORACLE_BASES)}"
        )
