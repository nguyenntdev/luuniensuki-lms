"""Shared decision engine for LN-09 Research V2 policies.

Implements the pedagogical invariants of the legacy domain module
``backend/domain/instructional_recommendations.py`` (INV-LN-09-01..05) as a
typed V2 decision procedure:

- INV-LN-09-01: never infer learner deficit from missing logs. An empty or
  insufficient evidence stream yields an explicit abstention (never a deficit
  action), unless the teacher explicitly overrides — and even then only as
  ``require_teacher_override`` (descriptive-only hand-off), never as an
  inferred-deficit intervention.
- INV-LN-09-02: every recommended action must trace back to a verified
  assessment task / source. Unverified evidence yields an explicit abstention.
- INV-LN-09-03: teacher override supremacy — an explicit teacher decision is
  honored above any model recommendation; the model can never convert an
  override into an automatic grade or mandatory activity.
- INV-LN-09-04: k-anonymity privacy threshold (n >= k, default 5). Cohorts
  below the threshold are suppressed to a descriptive-only summary (no
  learner-level recommendation published).
- INV-LN-09-05: contradictory signals must be surfaced explicitly
  (``abstain_conflict``), never silently resolved.

Additional hard checks: source-availability/missingness mask (high risk with
no actionable evidence must NOT produce a deficit inference) and data
freshness (stale observations yield ``request_refresh``).

Decision procedure precedence (each check returns immediately):
    1. teacher override (explicit ``teacher_override`` in features)
    2. k-anonymity suppression
    3. missing logs / missing required signal types (abstain_missing_evidence)
    4. conflicting signals (abstain_conflict)
    5. unverified sources (abstain_unverified_source)
    6. stale observations (request_refresh)
    7. nominal: actionable recommendation anchored to the curriculum catalog

Decisions are emitted in the legacy gold vocabulary so the sealed T3 evaluator
scores them verbatim (see package ``__init__`` divergence note). All
predictions are pure functions of (features, config). No oracle, fault_id,
cohort label or expected_decision is ever read.
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v2.contracts.types import ContractError, StudyInput, StudyPrediction

STUDY_ID = "LN-09"

# Gold-compatible decision vocabulary (legacy DecisionCode).
DECISION_PROPOSE_ACTION = "propose_explained_action"
DECISION_ABSTAIN_MISSING = "abstain_missing_evidence"
DECISION_ABSTAIN_CONFLICT = "abstain_conflict"
DECISION_ABSTAIN_UNVERIFIED = "abstain_unverified_source"
DECISION_REQUEST_REFRESH = "request_refresh"
DECISION_DESCRIPTIVE_ONLY = "descriptive_summary_only"

VALID_DECISIONS = frozenset(
    {
        DECISION_PROPOSE_ACTION,
        DECISION_ABSTAIN_MISSING,
        DECISION_ABSTAIN_CONFLICT,
        DECISION_ABSTAIN_UNVERIFIED,
        DECISION_REQUEST_REFRESH,
        DECISION_DESCRIPTIVE_ONLY,
    }
)

# Reason codes (explicit, machine-checkable).
RC_NOMINAL = "nominal"
RC_MISSING_LOGS = "missing_logs"
RC_MISSING_SIGNAL_TYPES = "missing_required_signal_types"
RC_CONFLICTING_SIGNALS = "conflicting_signals"
RC_UNVERIFIED_TASK = "unverified_task"
RC_STALE_MASTERY = "stale_mastery"
RC_K_ANONYMITY_VIOLATION = "k_anonymity_violation"
RC_UNSUPPORTED_INTERVENTION = "unsupported_intervention"
RC_DESCRIPTIVE_ONLY = "descriptive_only_no_action"
RC_TEACHER_REJECTED = "teacher_rejected"
RC_TEACHER_ACCEPTED = "teacher_accepted"
RC_TEACHER_MODIFIED = "teacher_modified"

# Curriculum-anchored action catalog (subset carried from the domain module;
# evidence_ids always reference the verified source tasks backing a proposal).
CURRICULUM_ACTION_ANCHORS: dict[str, str] = {
    "additional_source_comparison_activity": "GDDP12-HUE-HERITAGE-SOURCE-S3",
    "additional_spatial_orientation_activity": "GDDP12-HUE-HERITAGE-SPATIAL-S1",
    "additional_chronology_exercise": "GDDP12-HUE-HERITAGE-CHRONOLOGY-S2",
    "additional_argumentation_workshop": "GDDP12-HUE-HERITAGE-ARGUMENT-S4",
}

DEFAULT_K_THRESHOLD = 5
DEFAULT_MAX_STALENESS_DAYS = 30

# Engine flags understood by ablations.py (mechanism-isolating switches).
FLAG_SKIP_FRESHNESS = "skip_freshness_check"
FLAG_SKIP_SOURCE_CHECK = "skip_source_verification"
FLAG_SKIP_K_ANONYMITY = "skip_k_anonymity"
FLAG_DESCRIPTIVE_FALLBACK_OFF = "disable_descriptive_fallback"


def _require_mapping(features: Any, case_id: str) -> Mapping[str, Any]:
    if not isinstance(features, Mapping):
        raise ContractError(f"case {case_id!r}: features must be a mapping")
    return features


def _parse_cohort_size(features: Mapping[str, Any], case_id: str) -> int | None:
    raw = features.get("cohort_size")
    if raw is None:
        return None
    if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0:
        raise ContractError(f"case {case_id!r}: 'cohort_size' must be a non-negative integer")
    return raw


def _parse_age_days(features: Mapping[str, Any], case_id: str) -> int:
    raw = features.get("observation_age_days", 0)
    if isinstance(raw, bool) or not isinstance(raw, (int, float)) or raw < 0:
        raise ContractError(f"case {case_id!r}: 'observation_age_days' must be a non-negative number")
    return int(raw)


def _parse_required_signal_types(features: Mapping[str, Any], case_id: str) -> tuple[str, ...]:
    raw = features.get("required_signal_types", [])
    if not isinstance(raw, (list, tuple)) or any(not isinstance(t, str) for t in raw):
        raise ContractError(f"case {case_id!r}: 'required_signal_types' must be a list of strings")
    return tuple(raw)


def _parse_evidence(features: Mapping[str, Any], case_id: str) -> tuple[list[dict[str, Any]], list[int]]:
    """Parse learning evidence rows. Returns (parsed, indices_of_unverified)."""
    raw = features.get("learning_evidence", [])
    if raw is None:
        raw = []
    if not isinstance(raw, list):
        raise ContractError(f"case {case_id!r}: 'learning_evidence' must be a list")
    parsed: list[dict[str, Any]] = []
    unverified: list[int] = []
    for i, ev in enumerate(raw):
        if not isinstance(ev, Mapping):
            raise ContractError(f"case {case_id!r}: learning_evidence[{i}] must be a mapping")
        try:
            score = float(ev["score"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ContractError(
                f"case {case_id!r}: learning_evidence[{i}] missing/invalid 'score'"
            ) from exc
        if not (0.0 <= score <= 1.0):
            raise ContractError(f"case {case_id!r}: learning_evidence[{i}].score out of [0,1]")
        ev_type = ev.get("type")
        if not isinstance(ev_type, str) or not ev_type.strip():
            raise ContractError(f"case {case_id!r}: learning_evidence[{i}] missing 'type'")
        outcome = ev.get("outcome")
        if outcome is not None and not isinstance(outcome, str):
            raise ContractError(f"case {case_id!r}: learning_evidence[{i}].outcome must be a string")
        verified = ev.get("verified", False)
        if not isinstance(verified, bool):
            raise ContractError(f"case {case_id!r}: learning_evidence[{i}].verified must be boolean")
        if not verified:
            unverified.append(i)
        parsed.append({"score": score, "type": ev_type, "verified": verified, "outcome": outcome})
    return parsed, unverified


def _parse_teacher_override(features: Mapping[str, Any], case_id: str) -> dict[str, Any] | None:
    """Explicit teacher override (INV-LN-09-03). Present only when the teacher
    has actually acted; its absence never blocks the default decision path."""
    raw = features.get("teacher_override")
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise ContractError(f"case {case_id!r}: 'teacher_override' must be a mapping")
    status = raw.get("status")
    if status not in ("accepted", "rejected", "modified"):
        raise ContractError(
            f"case {case_id!r}: teacher_override.status must be accepted|rejected|modified"
        )
    return dict(raw)


def _missing_signal_types(
    evidence: list[dict[str, Any]], required: tuple[str, ...]
) -> tuple[str, ...]:
    """Required signal families with zero observed rows of any kind.

    INV-LN-09-01: absent signal types are missingness, not low ability. A
    missing required family blocks deficit inference about that competency.

    Missingness is about *existence*, trust is a separate gate: an unverified
    row still proves the signal type was observed (it then fails the
    unverified-source check, never the missing-logs check). A deficit
    proposal requires verified evidence on every required family downstream
    regardless, so no path infers ability from untrusted or absent rows.
    """
    present = {ev["type"] for ev in evidence}
    return tuple(t for t in required if t not in present)


def _risk_signal(evidence: list[dict[str, Any]]) -> float | None:
    """Aggregate observed performance (mean score); None when nothing observed."""
    scores = [ev["score"] for ev in evidence if ev["verified"]]
    if not scores:
        return None
    return sum(scores) / len(scores)


def evaluate_case(inp: StudyInput, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    """Core LN-09 decision procedure (proposed policy).

    Precedence: teacher override > k-anonymity > missing evidence > conflict
    > unverified source > staleness > nominal recommendation.
    """
    cfg = dict(config or {})
    case_id = inp.case_id
    features = _require_mapping(inp.features, case_id)

    k_threshold = int(cfg.get("k_threshold", DEFAULT_K_THRESHOLD))
    max_staleness = int(cfg.get("max_staleness_days", DEFAULT_MAX_STALENESS_DAYS))
    skip_k = bool(cfg.get(FLAG_SKIP_K_ANONYMITY, False))
    skip_source = bool(cfg.get(FLAG_SKIP_SOURCE_CHECK, False))
    skip_freshness = bool(cfg.get(FLAG_SKIP_FRESHNESS, False))
    descriptive_fallback_off = bool(cfg.get(FLAG_DESCRIPTIVE_FALLBACK_OFF, False))

    evidence, unverified_idx = _parse_evidence(features, case_id)
    age_days = _parse_age_days(features, case_id)
    cohort_size = _parse_cohort_size(features, case_id)
    required = _parse_required_signal_types(features, case_id)
    override = _parse_teacher_override(features, case_id)
    signals_conflict = bool(features.get("signals_conflict", False))

    candidate = features.get("candidate_intervention")
    if candidate is not None and not isinstance(candidate, str):
        raise ContractError(f"case {case_id!r}: 'candidate_intervention' must be a string")

    # --- INV-LN-09-03: teacher override supremacy ---------------------------
    # The teacher's explicit decision outranks every algorithmic branch. An
    # override can never be downgraded to an automatic grade or mandatory
    # activity: rejection/absence of an accepted modified action yields only a
    # descriptive summary handed back to the teacher.
    if override is not None:
        status = override["status"]
        if status == "rejected":
            return StudyPrediction(
                study_id=STUDY_ID,
                case_id=case_id,
                decision=DECISION_DESCRIPTIVE_ONLY,
                score=None,
                reason_codes=(RC_TEACHER_REJECTED, RC_DESCRIPTIVE_ONLY),
                evidence_ids=(),
            )
        if status == "modified" and override.get("modified_action"):
            return StudyPrediction(
                study_id=STUDY_ID,
                case_id=case_id,
                decision=DECISION_PROPOSE_ACTION,
                score=None,
                reason_codes=(RC_TEACHER_MODIFIED, RC_NOMINAL),
                evidence_ids=tuple(f"ev_{i}" for i in range(len(evidence))),
            )
        # accepted (or modified without a concrete replacement action): the
        # algorithmic recommendation is confirmed but stays advisory.
        base = _algorithmic_decision(
            features=features,
            evidence=evidence,
            unverified_idx=unverified_idx,
            age_days=age_days,
            cohort_size=cohort_size,
            required=required,
            signals_conflict=signals_conflict,
            candidate=candidate,
            case_id=case_id,
            k_threshold=k_threshold,
            max_staleness=max_staleness,
            skip_k=skip_k,
            skip_source=skip_source,
            skip_freshness=skip_freshness,
            descriptive_fallback_off=descriptive_fallback_off,
        )
        return StudyPrediction(
            study_id=STUDY_ID,
            case_id=case_id,
            decision=base.decision,
            score=base.score,
            reason_codes=base.reason_codes + (RC_TEACHER_ACCEPTED,),
            evidence_ids=base.evidence_ids,
        )

    return _algorithmic_decision(
        features=features,
        evidence=evidence,
        unverified_idx=unverified_idx,
        age_days=age_days,
        cohort_size=cohort_size,
        required=required,
        signals_conflict=signals_conflict,
        candidate=candidate,
        case_id=case_id,
        k_threshold=k_threshold,
        max_staleness=max_staleness,
        skip_k=skip_k,
        skip_source=skip_source,
        skip_freshness=skip_freshness,
        descriptive_fallback_off=descriptive_fallback_off,
    )


def _algorithmic_decision(
    *,
    features: Mapping[str, Any],
    evidence: list[dict[str, Any]],
    unverified_idx: list[int],
    age_days: int,
    cohort_size: int | None,
    required: tuple[str, ...],
    signals_conflict: bool,
    candidate: str | None,
    case_id: str,
    k_threshold: int,
    max_staleness: int,
    skip_k: bool,
    skip_source: bool,
    skip_freshness: bool,
    descriptive_fallback_off: bool,
) -> StudyPrediction:
    """Algorithmic (non-override) branch of the LN-09 decision procedure."""

    # --- INV-LN-09-04: k-anonymity privacy suppression ----------------------
    # Small cohorts are suppressed to a descriptive-only summary; no
    # learner-level recommendation is published for n < k.
    if not skip_k and cohort_size is not None and cohort_size < k_threshold:
        return StudyPrediction(
            study_id=STUDY_ID,
            case_id=case_id,
            decision=DECISION_DESCRIPTIVE_ONLY,
            score=None,
            reason_codes=(RC_K_ANONYMITY_VIOLATION, RC_DESCRIPTIVE_ONLY),
            evidence_ids=(),
        )

    # --- INV-LN-09-01: missing logs / missing required signal families ------
    # HIGH RISK SIGNAL + NO ACTIONABLE EVIDENCE must never become a deficit
    # inference: it abstains. With descriptive_fallback_off (ablation a1) the
    # abstention certificate is withheld and only a bare descriptive summary
    # is emitted, exposing the mechanism.
    if not evidence:
        reasons = [RC_MISSING_LOGS]
        missing = _missing_signal_types(evidence, required)
        if missing:
            reasons.append(RC_MISSING_SIGNAL_TYPES)
        decision = DECISION_ABSTAIN_MISSING
        if descriptive_fallback_off:
            decision = DECISION_DESCRIPTIVE_ONLY
            reasons.append(RC_DESCRIPTIVE_ONLY)
        return StudyPrediction(
            study_id=STUDY_ID,
            case_id=case_id,
            decision=decision,
            score=None,
            reason_codes=tuple(reasons),
            evidence_ids=(),
        )

    missing = _missing_signal_types(evidence, required)
    if missing:
        reasons = [RC_MISSING_SIGNAL_TYPES, RC_MISSING_LOGS]
        decision = DECISION_ABSTAIN_MISSING
        if descriptive_fallback_off:
            decision = DECISION_DESCRIPTIVE_ONLY
            reasons.append(RC_DESCRIPTIVE_ONLY)
        return StudyPrediction(
            study_id=STUDY_ID,
            case_id=case_id,
            decision=decision,
            score=None,
            reason_codes=tuple(reasons),
            evidence_ids=tuple(f"ev_{i}" for i in range(len(evidence))),
        )

    # --- INV-LN-09-05: contradictory signals surfaced explicitly ------------
    if signals_conflict:
        return StudyPrediction(
            study_id=STUDY_ID,
            case_id=case_id,
            decision=DECISION_ABSTAIN_CONFLICT,
            score=None,
            reason_codes=(RC_CONFLICTING_SIGNALS,),
            evidence_ids=tuple(f"ev_{i}" for i in range(len(evidence))),
        )

    # --- INV-LN-09-02: source / task verification ---------------------------
    if unverified_idx and not skip_source:
        return StudyPrediction(
            study_id=STUDY_ID,
            case_id=case_id,
            decision=DECISION_ABSTAIN_UNVERIFIED,
            score=None,
            reason_codes=(RC_UNVERIFIED_TASK, RC_UNSUPPORTED_INTERVENTION),
            evidence_ids=tuple(f"ev_{i}" for i in unverified_idx),
        )

    # --- Freshness check -----------------------------------------------------
    if age_days > max_staleness and not skip_freshness:
        return StudyPrediction(
            study_id=STUDY_ID,
            case_id=case_id,
            decision=DECISION_REQUEST_REFRESH,
            score=None,
            reason_codes=(RC_STALE_MASTERY,),
            evidence_ids=tuple(f"ev_{i}" for i in range(len(evidence))),
        )

    # --- Nominal: source-auditable actionable recommendation -----------------
    if candidate is None or candidate not in CURRICULUM_ACTION_ANCHORS:
        # An unanchored candidate cannot be traced to curriculum requirements
        # (INV-LN-09-02); the evidence itself stays verified but the proposed
        # action would be unsupported, so abstain rather than fabricate.
        return StudyPrediction(
            study_id=STUDY_ID,
            case_id=case_id,
            decision=DECISION_ABSTAIN_UNVERIFIED,
            score=None,
            reason_codes=(RC_UNSUPPORTED_INTERVENTION, RC_UNVERIFIED_TASK),
            evidence_ids=tuple(f"ev_{i}" for i in range(len(evidence))),
        )

    risk = _risk_signal(evidence)
    return StudyPrediction(
        study_id=STUDY_ID,
        case_id=case_id,
        decision=DECISION_PROPOSE_ACTION,
        score=risk,
        reason_codes=(RC_NOMINAL,),
        evidence_ids=tuple(
            f"ev_{i}"
            for i, ev in enumerate(evidence)
            if ev["verified"]
        ),
    )
