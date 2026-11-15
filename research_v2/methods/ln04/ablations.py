"""LN-04 mechanism-isolating ablations of the proposed policy.

- ``ablations_a1``: no hint budget — answer-budget gate removed; direct-answer
  requests on verified sources are fulfilled directly.
- ``ablations_a2``: no source gate — fail-closed provenance check removed;
  unverified/draft/out-of-scope sources no longer trigger abstention.
- ``ablations_a3``: no injection filter — instruction-boundary removed;
  override/jailbreak turns are executed (leaking the answer channel).

Each ablation flips exactly one mechanism off; everything else is identical to
``proposed.predict_one`` so any divergence is attributable to that mechanism.
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from . import features as feat
from .proposed import DEFAULTS, _config, _quarantined_note_answer
from .labels import STUDY_ID

A1_METHOD_ID = "ablations_a1"
A2_METHOD_ID = "ablations_a2"
A3_METHOD_ID = "ablations_a3"
ABLATION_VERSION = "ln04-ablation-v1.0.0"


def _predict(
    inp: StudyInput,
    *,
    answer_budget: bool,
    source_gate: bool,
    injection_boundary: bool,
    config: Mapping[str, Any] | None = None,
) -> StudyPrediction:
    cfg = _config(config)
    cfg["answer_budget"] = answer_budget
    cfg["source_gate"] = source_gate
    cfg["injection_boundary"] = injection_boundary

    f = inp.features
    question = feat.get_question(f)
    retrieval = feat.get_retrieval(f)
    task = feat.get_task(f)
    release_allowed = feat.answer_release_allowed(task)
    wants_answer = feat.question_requests_answer(question)

    tag = "ablation"

    # Malicious-note quarantine stays ON in every ablation unless the source
    # gate is the removed mechanism; with the gate off the untrusted note is
    # the only "source", so its answer channel leaks (this is the a2 hazard).
    if cfg["malicious_note_quarantine"]:
        leaked_via_note = _quarantined_note_answer(retrieval, question)
        verified = feat.source_is_verified(retrieval)
        if leaked_via_note is not None and source_gate and verified and not release_allowed:
            return StudyPrediction(
                study_id=STUDY_ID,
                case_id=inp.case_id,
                decision="hint",
                score=None,
                reason_codes=(
                    f"{tag}_malicious_note_quarantined",
                    "answer_text_withheld",
                    "socratic_redirect",
                ),
                evidence_ids=(),
            )

    # 1. Instruction boundary (a3 removes it)
    if injection_boundary and feat.question_is_injection(question):
        return StudyPrediction(
            study_id=STUDY_ID,
            case_id=inp.case_id,
            decision="reject_injection",
            score=None,
            reason_codes=(f"{tag}_prompt_injection", "instruction_boundary_enforced"),
            evidence_ids=(),
        )

    # 2. Provenance gate (a2 removes it)
    verified = feat.source_is_verified(retrieval)
    if source_gate and not verified:
        return StudyPrediction(
            study_id=STUDY_ID,
            case_id=inp.case_id,
            decision="abstain_insufficient_source",
            score=None,
            reason_codes=(f"{tag}_unverified_or_absent_source", "fail_closed_gate"),
            evidence_ids=(),
        )

    # 3. Answer budget (a1 removes it)
    if answer_budget and wants_answer and not release_allowed:
        return StudyPrediction(
            study_id=STUDY_ID,
            case_id=inp.case_id,
            decision="hint",
            score=None,
            reason_codes=(f"{tag}_early_answer_request", "answer_release_locked", "socratic_redirect"),
            evidence_ids=tuple(str(s) for s in (retrieval.get("source_ids") or [])),
        )

    # 4. Hint fading (stage labels; matches the proposed policy contract)
    level = feat.hint_level_of(task)
    stage = "observation" if level == 1 else "evidence" if level == 2 else "reasoning"
    decision = "socratic_question"
    reason = (
        f"{tag}_verified_source",
        "socratic_open_question",
        f"hint_level_{level}",
        f"stage_{stage}",
    )
    return StudyPrediction(
        study_id=STUDY_ID,
        case_id=inp.case_id,
        decision=decision,
        score=None,
        reason_codes=reason,
        evidence_ids=tuple(str(s) for s in (retrieval.get("source_ids") or [])),
    )


def predict_one_a1(inp: StudyInput, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    """A1: no hint budget — early answers fulfilled directly on verified sources."""
    return _predict(inp, answer_budget=False, source_gate=True, injection_boundary=True, config=config)


def predict_one_a2(inp: StudyInput, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    """A2: no source gate — unverified sources no longer trigger abstention."""
    return _predict(inp, answer_budget=True, source_gate=False, injection_boundary=True, config=config)


def predict_one_a3(inp: StudyInput, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    """A3: no injection filter — override/jailbreak turns are executed."""
    return _predict(inp, answer_budget=True, source_gate=True, injection_boundary=False, config=config)


def _batch(predict_one):
    def predict_batch(
        inputs: list[StudyInput], config: Mapping[str, Any] | None = None
    ) -> list[StudyPrediction]:
        return [predict_one(inp, config) for inp in inputs]

    return predict_batch


predict_batch_a1 = _batch(predict_one_a1)
predict_batch_a2 = _batch(predict_one_a2)
predict_batch_a3 = _batch(predict_one_a3)
