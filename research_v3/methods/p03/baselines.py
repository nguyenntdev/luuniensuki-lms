"""P03 baselines (prereg comparison_family; SCIENTIFIC_EVALUATION.md section 3).

C0  direct-answer sanity control - weak by construction, never a SOTA reference.
C1  rule-based stand-in for a generic mid-competence LLM tutor.
    LABEL: simulated_proxy, NOT a real LLM. Exists to exercise the scoring
    harness; no LLM behavior is claimed from it.
C2  real LLM - BLOCKED. There is no licensed executable LLM in this
    environment; only an actually executed model with recorded id/version and
    cost may fill C2 (see pre_registration.yaml blocked_cards).
"""
from __future__ import annotations

from .policy import ABSTAIN, _answer_worthiness, _seeded_unit, MalformedSourceError
from .types import TutorDecision, TutorDecisionInput

C1_LABEL = "simulated_proxy, NOT a real LLM"


def c0_direct_answer(inp: TutorDecisionInput) -> TutorDecision:
    """Answers whenever the learner asks; never abstains; never refuses.

    Cites evidence ids only when verified sources exist (so the citation
    metric can distinguish it from the proposed policy).
    """
    evidence_ids = tuple(
        s.source_id for s in inp.sources if s.provenance_status == "verified"
    )
    if inp.wants_answer:
        return TutorDecision(
            case_id=inp.case_id,
            action="answer_with_evidence" if evidence_ids else "answer_with_evidence",
            reason_codes=("c0_direct_answer", "no_gates"),
            evidence_ids=evidence_ids,
            meta={"baseline": "C0_direct_answer"},
        )
    # Without an explicit request it mirrors a generic Q&A tutor: answer anyway.
    return TutorDecision(
        case_id=inp.case_id,
        action="answer_with_evidence",
        reason_codes=("c0_direct_answer", "no_gates"),
        evidence_ids=evidence_ids,
        meta={"baseline": "C0_direct_answer"},
    )


def c1_simulated_proxy(inp: TutorDecisionInput) -> TutorDecision:
    """Rule-based generic-tutor proxy. Deterministic per case id.

    Behavior model (declared): answers early requests ~50% of the time
    (seeded by case id), otherwise hints; never verifies provenance; abstains
    only when the retrieval pool is literally empty.
    """
    evidence_ids = tuple(
        s.source_id for s in inp.sources if s.provenance_status == "verified"
    )
    if not inp.sources:
        return TutorDecision(
            case_id=inp.case_id,
            action=ABSTAIN,
            reason_codes=("c1_simulated_proxy", "empty_retrieval_pool"),
            abstained=True,
            meta={"baseline": "C1_simulated_proxy", "label": C1_LABEL},
        )
    if inp.wants_answer and _seeded_unit(inp.case_id, "c1") < 0.5:
        return TutorDecision(
            case_id=inp.case_id,
            action="answer_with_evidence",
            reason_codes=("c1_simulated_proxy", "early_answer_granted_proxy"),
            evidence_ids=evidence_ids,
            meta={"baseline": "C1_simulated_proxy", "label": C1_LABEL},
        )
    action = "socratic_question" if inp.stage == "observation" else "hint"
    return TutorDecision(
        case_id=inp.case_id,
        action=action,
        reason_codes=("c1_simulated_proxy", "generic_scaffold_proxy"),
        evidence_ids=evidence_ids,
        meta={"baseline": "C1_simulated_proxy", "label": C1_LABEL},
    )


C2_STATUS = "BLOCKED"
C2_REASON = (
    "No licensed executable LLM in environment (2 GiB GPU, 3.2 GiB disk free, "
    "no ollama/vllm/llama-cli, no API credentials). C2 may only be claimed "
    "after an actual run with model id/version and cost recorded."
)


def c2_real_llm(inp: TutorDecisionInput) -> TutorDecision:
    """C2 is BLOCKED - this stub fails closed; it must never fabricate output."""
    raise MalformedSourceError(f"C2_real_llm is {C2_STATUS}: {C2_REASON}")


BASELINES = {
    "C0_direct_answer": c0_direct_answer,
    "C1_simulated_proxy_rulebased": c1_simulated_proxy,
}
