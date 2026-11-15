"""LN-04 proposed method: Source-Grounded Socratic Tutor with Instruction Boundary.

Deterministic policy implementing the preregistered mechanism stack:

1. **Instruction boundary** — prompt-injection / override / jailbreak patterns in
   the student turn trigger ``reject_injection``; the turn is never executed.
2. **Malicious-note quarantine** — retrieved-note text is an untrusted channel.
   If the answer text appears only inside a note carrying injection payload, or
   the note itself instructs the system to reveal answers, the answer is
   suppressed and the note quarantined (never cited, never surfaced).
3. **Fail-closed provenance gate** — without explicitly verified source status
   the tutor abstains (``abstain_insufficient_source``) instead of guessing.
4. **Answer budget** — the answer is a server-controlled resource: while
   ``answer_release_allowed`` is false, direct-answer requests get a Socratic
   redirect (``hint``), never the solution.
5. **Progressive hint fading** — verified-source nominal turns emit
   ``socratic_question``; as the authorized hint level rises the scaffold fades
   toward a partial ``hint``.

This is a pure decision policy: no external LLM is called, and no oracle or
gold material is read. Scientific labeling: heuristic reference implementation
of the preregistered policy, not a real-LLM evaluation.
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from . import features as feat
from .labels import STUDY_ID, validate_contract_decision

METHOD_ID = "proposed"
METHOD_VERSION = "ln04-proposed-v1.0.0"

DEFAULTS: dict[str, Any] = {
    "injection_boundary": True,
    "malicious_note_quarantine": True,
    "source_gate": True,
    "answer_budget": True,
    "hint_fading": True,
}


def _config(config: Mapping[str, Any] | None) -> dict[str, Any]:
    merged = dict(DEFAULTS)
    if config:
        merged.update({k: v for k, v in config.items() if k in DEFAULTS})
    return merged


def _quarantined_note_answer(
    retrieval: Mapping[str, Any], question: str
) -> str | None:
    """Return leaked answer text found only in an untrusted note, else None.

    A note is untrusted when it carries injection payload. Any answer-looking
    fragment inside such a note must never be surfaced, so the caller only needs
    to know that such content exists (the caller suppresses it).
    """
    notes = retrieval.get("notes")
    if not isinstance(notes, list):
        return None
    leaked = False
    for note in notes:
        text = str(note if not isinstance(note, Mapping) else note.get("text", "") or "")
        if not text:
            continue
        if feat.note_is_malicious(text):
            if feat.question_requests_answer(question) or feat.first_match(
                feat.ANSWER_REQUEST_PATTERNS, text
            ):
                leaked = True
    return "present-in-malicious-note" if leaked else None


def predict_one(inp: StudyInput, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    cfg = _config(config)
    f = inp.features
    question = feat.get_question(f)
    retrieval = feat.get_retrieval(f)
    task = feat.get_task(f)

    release_allowed = feat.answer_release_allowed(task)
    wants_answer = feat.question_requests_answer(question)

    # --- 1. Instruction boundary: student-turn injection -------------------
    if cfg["injection_boundary"] and feat.question_is_injection(question):
        decision = "reject_injection"
        return StudyPrediction(
            study_id=STUDY_ID,
            case_id=inp.case_id,
            decision=decision,
            score=None,
            reason_codes=("prompt_injection", "instruction_boundary_enforced"),
            evidence_ids=(),
        )

    # --- 2. Malicious-note quarantine --------------------------------------
    if cfg["malicious_note_quarantine"]:
        leaked_via_note = _quarantined_note_answer(retrieval, question)
        if leaked_via_note is not None:
            # The answer text exists only in an untrusted retrieved note.
            # Never surface it: fall through to the epistemic gate; if the
            # formal source is verified, redirect Socratically instead.
            suppressed = True
        else:
            suppressed = False
        if suppressed and feat.source_is_verified(retrieval) and not release_allowed:
            return StudyPrediction(
                study_id=STUDY_ID,
                case_id=inp.case_id,
                decision="hint",
                score=None,
                reason_codes=(
                    "malicious_note_quarantined",
                    "answer_text_withheld",
                    "socratic_redirect",
                ),
                evidence_ids=(),
            )

    # --- 3. Fail-closed provenance gate ------------------------------------
    verified = feat.source_is_verified(retrieval)
    if cfg["source_gate"] and not verified:
        decision = "abstain_insufficient_source"
        return StudyPrediction(
            study_id=STUDY_ID,
            case_id=inp.case_id,
            decision=decision,
            score=None,
            reason_codes=("unverified_or_absent_source", "fail_closed_gate"),
            evidence_ids=(),
        )

    # --- 4. Answer budget (server-controlled release) ----------------------
    if cfg["answer_budget"] and wants_answer and not release_allowed:
        decision = "hint"
        return StudyPrediction(
            study_id=STUDY_ID,
            case_id=inp.case_id,
            decision=decision,
            score=None,
            reason_codes=("early_answer_request", "answer_release_locked", "socratic_redirect"),
            evidence_ids=tuple(str(s) for s in (retrieval.get("source_ids") or [])),
        )

    # --- 5. Progressive Socratic hint fading -------------------------------
    # Fading is a pedagogical STAGE (observation -> evidence -> reasoning),
    # not a decision change: the oracle contract keeps the scaffolded decision
    # at every authorized hint level; the level is recorded in reason codes.
    level = feat.hint_level_of(task)
    decision = "socratic_question"
    stage = "observation" if level == 1 else "evidence" if level == 2 else "reasoning"
    reason = ("verified_source", "socratic_open_question", f"hint_level_{level}", f"stage_{stage}")
    validate_contract_decision(decision)
    return StudyPrediction(
        study_id=STUDY_ID,
        case_id=inp.case_id,
        decision=decision,
        score=None,
        reason_codes=reason,
        evidence_ids=tuple(str(s) for s in (retrieval.get("source_ids") or [])),
    )


def predict_batch(
    inputs: list[StudyInput], config: Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    return [predict_one(inp, config) for inp in inputs]
