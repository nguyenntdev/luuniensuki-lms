"""LN-04 baselines.

- ``baselines_b0``: naive direct-answer bot — reveals full solutions on any
  request, no hint budget, no source gate, no injection defense.
- ``baselines_c1``: rule-based SIMULATED generic-LLM proxy with a soft tutor
  prompt but no injection defense and no provenance gate.

Scientific labeling (mandatory): the C1 proxy is a deterministic heuristic that
simulates the documented failure modes of an unconstrained LLM tutor. It is NOT
a real LLM, and no output of this module may be described as real-LLM
evaluation. All reason codes are prefixed ``simulated`` to make this explicit in
every persisted prediction row.
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from . import features as feat
from .labels import STUDY_ID

B0_METHOD_ID = "baselines_b0"
B0_METHOD_VERSION = "ln04-b0-direct-answer-v1.0.0"
B0_SIMULATED = False  # B0 is an explicit naive policy, not an LLM proxy claim

C1_METHOD_ID = "baselines_c1"
C1_METHOD_VERSION = "ln04-c1-simulated-llm-proxy-v1.0.0"
C1_SIMULATED = True  # heuristic proxy of a generic LLM tutor; never a real LLM


# ---------------------------------------------------------------------
# B0 — naive direct-answer bot
# ---------------------------------------------------------------------
def predict_one_b0(inp: StudyInput, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    question = feat.get_question(inp.features)
    retrieval = feat.get_retrieval(inp.features)
    wants_answer = feat.question_requests_answer(question)
    is_injection = feat.question_is_injection(question)

    # B0 has no injection defense: overrides are executed as answer requests.
    if wants_answer or is_injection:
        decision = "direct_answer"
        reasons = ["b0_full_solution_dump"]
        if is_injection:
            reasons.append("b0_no_injection_defense")
    else:
        # Even nominal turns get an ungrounded answer: B0 never scaffolds.
        decision = "direct_answer"
        reasons = ["b0_always_answer", "no_hint_budget"]

    return StudyPrediction(
        study_id=STUDY_ID,
        case_id=inp.case_id,
        decision=decision,
        score=None,
        reason_codes=tuple(reasons),
        evidence_ids=(),  # B0 cites nothing verifiable
    )


def predict_batch_b0(
    inputs: list[StudyInput], config: Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    return [predict_one_b0(inp, config) for inp in inputs]


# ---------------------------------------------------------------------
# C1 — SIMULATED generic LLM tutor proxy (soft prompt, no hard defenses)
# ---------------------------------------------------------------------
def predict_one_c1(inp: StudyInput, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    cfg = config or {}
    question = feat.get_question(inp.features)
    retrieval = feat.get_retrieval(inp.features)
    is_injection = feat.question_is_injection(question)
    wants_answer = feat.question_requests_answer(question)
    verified = feat.source_is_verified(retrieval)
    release_allowed = feat.answer_release_allowed(feat.get_task(inp.features))
    simulated = bool(cfg.get("simulated_prefix", True)) or C1_SIMULATED

    # Soft prompt is only a linguistic instruction: injection overrides it.
    if is_injection:
        decision = "direct_answer"
        reasons = ["simulated_c1_soft_prompt_overridden", "simulated_no_injection_boundary"]
    elif wants_answer and not release_allowed:
        # The soft prompt politely deflects ordinary answer requests...
        if not verified:
            # ...but without a provenance gate it still fabricates an answer.
            decision = "direct_answer"
            reasons = ["simulated_c1_ungrounded_extrapolation", "simulated_no_source_gate"]
        else:
            decision = "hint"
            reasons = ["simulated_c1_soft_redirection"]
    elif wants_answer and release_allowed and not verified:
        decision = "direct_answer"
        reasons = ["simulated_c1_ungrounded_extrapolation", "simulated_no_source_gate"]
    else:
        # Generic tutor produces hints without any verification check.
        decision = "hint"
        reasons = ["simulated_c1_generic_response"]
        if not verified:
            reasons.append("simulated_c1_no_provenance_check")

    prefix = ("simulated",) if simulated and not reasons[0].startswith("simulated") else ()
    return StudyPrediction(
        study_id=STUDY_ID,
        case_id=inp.case_id,
        decision=decision,
        score=None,
        reason_codes=tuple(prefix) + tuple(reasons),
        evidence_ids=(),
    )


def predict_batch_c1(
    inputs: list[StudyInput], config: Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    return [predict_one_c1(inp, config) for inp in inputs]
