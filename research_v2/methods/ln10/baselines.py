"""LN-10 baselines (C0 sanity + C1 strong classical) as independent policies.

- ``baselines_b0`` (``baselines_b0`` alias, C0 SANITY_ONLY): naive linear
  checklist — ALWAYS applies the transition unconditionally. It ignores
  ownership, concurrency/conflict, reflection and rationale; two conflicting
  offline edits are silently "applied" (last-write-wins) which is exactly the
  integrity failure LN-10 targets. Deliberately vulnerable; exists to expose
  metric gaming (an always-accept must never earn perfect utility).

- ``baselines_c1`` (``baselines_c1`` alias, C1 strong classical): linear
  checklist progress tracker with a single fixed stage order. It enforces
  ownership and the plain version check (classical optimistic-concurrency
  analogue) but has NO reflection gate, NO rationale requirement and NO
  explicit two-conflicting-edits detector: when two offline edits target the
  same version it falls back to the plain CAS read and silently applies the
  first one (documented failure mode of classical checklist workflow engines,
  cf. BPMN-style rule workflow without reflective criteria).

Both share the legitimate input features, budget and native label space with
I1. Neither imports or calls the proposed decision function (independence
requirement, LN-10-14.N).
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from .dataset import (
    KNOWN_ACTIONS,
    DatasetError,
    SRLCase,
    parse_case,
)
from .labels import (
    REASON_BASELINE_AUTO_ADVANCE,
    REASON_OFFLINE_CONFLICT,
    REASON_UNAUTHORIZED_ACTOR,
    STUDY_ID,
    build_prediction,
)

COMPARATOR_STATUS = {
    "baselines_b0": "REIMPLEMENTATION",
    "baselines_c1": "REIMPLEMENTATION",
}

B0_METHOD_ID = "baselines_b0"
C1_METHOD_ID = "baselines_c1"
BASELINE_METHOD_VERSION = "ln10-baselines-v1.0"


def _validate_features(inp: StudyInput) -> SRLCase:
    try:
        return parse_case(inp.case_id, inp.features)
    except DatasetError:
        raise
    except Exception as exc:
        raise DatasetError(f"case {inp.case_id!r}: {exc}") from exc


# ---------------------------------------------------------------------------
# B0 — unchecked linear checklist: always apply (C0, SANITY_ONLY)
# ---------------------------------------------------------------------------

def b0_decide(case: SRLCase) -> dict[str, Any]:
    """B0 sanity control: auto-advance unconditionally, ignore every gate.

    Conflicting offline edits are silently ignored (the transition "wins") —
    the documented negative-control behaviour.
    """
    return {
        "decision": "allow_authorized_transition",
        "reason_codes": (REASON_BASELINE_AUTO_ADVANCE, "no_ownership_check",
                         "no_concurrency_check", "no_reflection_gate"),
        "evidence_ids": (),
        "transition_applied": True,
        "conflict_detected": False,
        "reflection_required": False,
    }


def predict_batch_b0(inputs: Iterable[StudyInput], config: Mapping[str, Any] | None = None) -> list[StudyPrediction]:
    del config  # B0 has no tunables
    preds: list[StudyPrediction] = []
    for inp in inputs:
        case = _validate_features(inp)
        result = b0_decide(case)
        preds.append(
            build_prediction(
                case_id=inp.case_id,
                decision=result["decision"],
                reason_codes=tuple(result["reason_codes"]),
                evidence_ids=tuple(result["evidence_ids"]),
                score=1.0 if result["transition_applied"] else 0.0,
            )
        )
    return preds


# ---------------------------------------------------------------------------
# C1 — linear checklist progress tracker (C1, strong classical)
# ---------------------------------------------------------------------------

def c1_decide(case: SRLCase) -> dict[str, Any]:
    """C1 strong classical: checklist order + ownership + plain CAS only.

    Classical checklist semantics (timestamp/step progress tracker):
      1. actor must be owner/staff (classical ACL),
      2. expected_version must match current version (plain compare-and-swap;
         on mismatch the FIRST recorded edit is silently applied after the
         user confirms — modelled here as applying on the *next* aligned
         attempt; for this single-shot ABI the mismatch is reported as a
         conflict, but the two-conflicting-edits case is NOT detected because
         the checklist never inspects the concurrent-edit set),
      3. unknown actions/states are auto-advanced (checklist trusts the flow).
    No reflection gate, no rationale requirement — the matched-subtask
    weakness under study.
    """
    project = case.project
    transition = case.transition

    # Ownership (classical access-control list on the checklist item).
    if not (case.actor.owns_project or case.actor.role in ("teacher", "admin", "staff")):
        return {
            "decision": "deny_transition",
            "reason_codes": (REASON_UNAUTHORIZED_ACTOR, "checklist_acl_denied"),
            "evidence_ids": (),
            "transition_applied": False,
            "conflict_detected": False,
            "reflection_required": False,
        }

    # Plain CAS: the ONLY conflict signal a checklist tracker can see.
    if (
        transition.expected_version is not None
        and project.version is not None
        and transition.expected_version != project.version
    ):
        return {
            "decision": "resolve_revision_conflict",
            "reason_codes": (REASON_OFFLINE_CONFLICT, "checklist_cas_mismatch"),
            "evidence_ids": (),
            "transition_applied": False,
            "conflict_detected": True,
            "reflection_required": False,
        }

    # Unknown actions/states are auto-advanced (no FSM, no abstain family).
    if transition.action not in KNOWN_ACTIONS or not project.state:
        return {
            "decision": "allow_authorized_transition",
            "reason_codes": (REASON_BASELINE_AUTO_ADVANCE, "checklist_auto_advance_unknown"),
            "evidence_ids": (),
            "transition_applied": True,
            "conflict_detected": False,
            "reflection_required": False,
        }

    # No reflection gate, no rationale gate, no concurrent-edit-set detector:
    # two conflicting offline edits on the same aligned version are silently
    # applied (first-write-wins) by the checklist flow.
    return {
        "decision": "allow_authorized_transition",
        "reason_codes": (REASON_BASELINE_AUTO_ADVANCE, "checklist_step_reached",
                         "no_reflection_gate", "no_concurrent_edit_detection"),
        "evidence_ids": (),
        "transition_applied": True,
        "conflict_detected": False,
        "reflection_required": False,
    }


def predict_batch_c1(inputs: Iterable[StudyInput], config: Mapping[str, Any] | None = None) -> list[StudyPrediction]:
    del config  # C1 has no tunables
    preds: list[StudyPrediction] = []
    for inp in inputs:
        case = _validate_features(inp)
        result = c1_decide(case)
        preds.append(
            build_prediction(
                case_id=inp.case_id,
                decision=result["decision"],
                reason_codes=tuple(result["reason_codes"]),
                evidence_ids=tuple(result["evidence_ids"]),
                score=1.0 if result["transition_applied"] else 0.0,
            )
        )
    return preds
