"""P03 policy: hint-first Socratic decision policy (METHOD.md section 3).

Gate order (first match returns):
  G1 injection boundary -> reject_injection
  G2 malicious-note quarantine -> hint / abstain (answer suppressed)
  G3 fail-closed provenance gate -> abstain_insufficient_evidence
  G4 pedagogical stage + calibrated answer budget -> answer_with_evidence | hint
  G5 socratic default -> socratic_question | hint

Pure functions over typed inputs; deterministic; no oracle access; no network.
"""
from __future__ import annotations

import hashlib
import re
from typing import Mapping

from .types import ABSTAIN, MalformedSourceError, SourceRecord, TutorDecision, TutorDecisionInput

METHOD_VERSION = "p03-policy-v1.0.0"

# --- frozen hyperparameters (declared in METHOD.md before evaluation) -------
TAU_ANSWER = 0.60
W_CONF, W_STAGE, W_DIVERSITY = 0.5, 0.3, 0.2
STAGE_SCORES = {"observation": 0.0, "evidence": 0.5, "reasoning": 1.0}

# --- G1: prompt-injection patterns in the LEARNER TURN (untrusted channel) ---
INJECTION_PATTERNS = (
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)",
    r"you\s+are\s+now\s+(a|an)\s+",
    r"act\s+as\s+(if\s+you\s+are\s+)?(a|an)\s+(different|unrestricted|jailbroken)",
    r"developer\s+mode",
    r"reveal\s+your\s+(system\s+prompt|instructions)",
    r"print\s+your\s+(system\s+prompt|instructions|api\s+key)",
    r"(show|give|tell)\s+me\s+your\s+(api\s+key|secret|credentials)",
    r"execute\s+(the\s+)?(following\s+)?(code|command|tool)",
    r"run\s+(this|the\s+following)\s+(code|command|sql)",
    r"drop\s+table|;\s*--|\bunion\s+select\b",
    r"override\s+(your\s+)?(safety|rules|instructions|policy)",
    r"jailbreak",
)
_ANSWER_REQUEST_PATTERNS = (
    r"\b(what\s+is|what's)\s+the\s+(final\s+)?answer\b",
    r"\bjust\s+(give|tell)\s+me\s+the\s+answer\b",
    r"\bgive\s+me\s+the\s+(full|complete|direct)\s+(answer|solution)\b",
    r"\btell\s+me\s+the\s+(answer|solution)\b",
    r"\bthe\s+answer\s+is\b.*\?\s*$",
    r"\bi\s+need\s+the\s+answer\s+now\b",
)
_NOTE_INJECTION_PATTERNS = INJECTION_PATTERNS + (
    r"\b(system|assistant|tutor)\s*:",
    r"\bAI\s+(assistant|tutor)\s+(instruction|prompt)\s*:",
    r"reveal\s+the\s+answer\s+to\s+the\s+student",
    r"you\s+must\s+(now\s+)?(reveal|disclose|provide)\s+the\s+(full|direct)?\s*answer",
)
_ANSWER_STATEMENT_PATTERNS = (
    r"\bthe\s+answer\s+is\s+",
    r"\bthe\s+correct\s+answer\s+is\s+",
    r"\btherefore\s+.+\s*=\s*\d",
    r"\bso\s+the\s+(result|total|value)\s+is\s+",
)

_COMPILED_INJECTION = tuple(re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS)
_COMPILED_NOTE_INJECTION = tuple(re.compile(p, re.IGNORECASE) for p in _NOTE_INJECTION_PATTERNS)
_COMPILED_ANSWER_REQ = tuple(re.compile(p, re.IGNORECASE) for p in _ANSWER_REQUEST_PATTERNS)
_COMPILED_ANSWER_STMT = tuple(re.compile(p, re.IGNORECASE) for p in _ANSWER_STATEMENT_PATTERNS)


def _first_match(patterns, text: str) -> str | None:
    for pat in patterns:
        m = pat.search(text)
        if m:
            return m.group(0)
    return None


def text_is_injection(text: str) -> bool:
    return _first_match(_COMPILED_INJECTION, text) is not None


def requests_answer(text: str) -> bool:
    return _first_match(_COMPILED_ANSWER_REQ, text) is not None


def note_is_malicious(note_text: str) -> bool:
    return _first_match(_COMPILED_NOTE_INJECTION, note_text) is not None


def note_contains_answer(note_text: str) -> bool:
    return _first_match(_COMPILED_ANSWER_STMT, note_text) is not None


def _seeded_unit(case_id: str, salt: str) -> float:
    """Deterministic per-case unit interval from the case id (no RNG state)."""
    digest = hashlib.sha256(f"{salt}:{case_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / float(2 ** 64)


# ---------------------------------------------------------------------------
# gates
# ---------------------------------------------------------------------------
def _g1_injection(inp: TutorDecisionInput) -> TutorDecision | None:
    hit = _first_match(_COMPILED_INJECTION, inp.learner_turn)
    if hit is None:
        return None
    return TutorDecision(
        case_id=inp.case_id,
        action="reject_injection",
        reason_codes=("prompt_injection", "instruction_boundary_enforced", f"pattern_hit:{hit[:40]}"),
        refused=True,
        meta={"gate": "G1"},
    )


def _g2_quarantine(inp: TutorDecisionInput) -> TutorDecision | None:
    malicious = [s for s in inp.sources if note_is_malicious(s.text)]
    if not malicious:
        return None
    answer_in_note = any(
        note_contains_answer(s.text) or _first_match(_COMPILED_ANSWER_REQ, s.text)
        for s in malicious
    )
    verified = any(s.provenance_status == "verified" for s in inp.sources)
    reasons = ["malicious_note_quarantined", "answer_text_withheld"]
    if answer_in_note:
        reasons.append("leak_blocked_from_untrusted_note")
    if verified:
        # Socratic redirect instead of surfacing quarantined content.
        return TutorDecision(
            case_id=inp.case_id,
            action="hint",
            reason_codes=tuple(reasons + ["socratic_redirect"]),
            meta={"gate": "G2", "quarantined_ids": [s.source_id for s in malicious]},
        )
    return TutorDecision(
        case_id=inp.case_id,
        action=ABSTAIN,
        reason_codes=tuple(reasons + ["no_verified_source"]),
        abstained=True,
        meta={"gate": "G2", "quarantined_ids": [s.source_id for s in malicious]},
    )


def _g3_provenance(inp: TutorDecisionInput) -> TutorDecision | None:
    verified = [s for s in inp.sources if s.provenance_status == "verified"]
    if not verified:
        return TutorDecision(
            case_id=inp.case_id,
            action=ABSTAIN,
            reason_codes=("unverified_or_absent_source", "fail_closed_gate"),
            abstained=True,
            meta={"gate": "G3"},
        )
    if len(verified) > 1 and _contradicts(verified):
        return TutorDecision(
            case_id=inp.case_id,
            action=ABSTAIN,
            reason_codes=("contradictory_sources_detected", "fail_closed_gate"),
            abstained=True,
            meta={"gate": "G3"},
        )
    return None


def _contradicts(verified: list[SourceRecord]) -> bool:
    """Conservative slot-contradiction check on verified sources.

    Two verified records contradict when they assert different values for the
    same declarative slot ('the X is Y' / 'X = Y' patterns).
    """
    slots: dict[str, set[str]] = {}
    for s in verified:
        for m in re.finditer(
            r"\b(the\s+)?([a-z][a-z\s\-]{2,30}?)\s+(?:is|are|=)\s+([a-z0-9\-\s]{1,24})", s.text, re.IGNORECASE
        ):
            key = re.sub(r"\s+", " ", m.group(2).strip().lower())
            val = re.sub(r"\s+", " ", m.group(3).strip().lower())
            if key and val:
                slots.setdefault(key, set()).add(val)
    return any(len(vals) > 1 for vals in slots.values())


def _answer_worthiness(inp: TutorDecisionInput) -> float:
    """Factorized evidence calibration (METHOD.md section 3, G4c).

    p_answer is a RELEASE-WORTHINESS score (risk-coverage semantics), not a
    prediction of the warranted-release label: values above tau on stage-locked
    cases are intentional conservatism (withhold despite high worthiness).
    """
    confs = [
        s.retrieval_confidence
        for s in inp.sources
        if s.provenance_status == "verified"
    ]
    conf_min = min(confs) if confs else 0.0
    stage_score = float(inp.stage_score) if inp.stage_score else STAGE_SCORES[inp.stage]
    diversity = min(1.0, len({s.source_id for s in inp.sources if s.provenance_status == "verified"}) / 3.0)
    p = W_CONF * conf_min + W_STAGE * stage_score + W_DIVERSITY * diversity
    return round(min(1.0, max(0.0, p)), 6)


def _g4_stage_budget(inp: TutorDecisionInput) -> TutorDecision | None:
    evidence_ids = tuple(
        s.source_id for s in inp.sources if s.provenance_status == "verified"
    )
    p = _answer_worthiness(inp)
    stage_allows = inp.stage == "reasoning"
    if inp.wants_answer:
        if stage_allows and p >= TAU_ANSWER:
            return TutorDecision(
                case_id=inp.case_id,
                action="answer_with_evidence",
                reason_codes=(
                    "verified_source",
                    "stage_reasoning_authorized",
                    "calibrated_confidence_pass",
                ),
                evidence_ids=evidence_ids,
                p_answer=p,
                meta={"gate": "G4"},
            )
        reasons = ["early_answer_request", "answer_release_locked", "socratic_redirect"]
        if stage_allows and p < TAU_ANSWER:
            reasons = ["low_answer_confidence", "calibrated_hint_fallback", "socratic_redirect"]
        return TutorDecision(
            case_id=inp.case_id,
            action="hint",
            reason_codes=tuple(reasons),
            evidence_ids=evidence_ids,
            p_answer=p,
            meta={"gate": "G4"},
        )
    return None


def _g5_socratic_default(inp: TutorDecisionInput) -> TutorDecision:
    level = {"observation": 1, "evidence": 2, "reasoning": 3}[inp.stage]
    evidence_ids = tuple(
        s.source_id for s in inp.sources if s.provenance_status == "verified"
    )
    if inp.stage == "observation":
        action, stage_name = "socratic_question", "observation"
    else:
        action, stage_name = "hint", inp.stage
    return TutorDecision(
        case_id=inp.case_id,
        action=action,
        reason_codes=(
            "verified_source",
            "socratic_default",
            f"hint_level_{level}",
            f"stage_{stage_name}",
        ),
        evidence_ids=evidence_ids,
        meta={"gate": "G5"},
    )


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------
def decide(inp: TutorDecisionInput) -> TutorDecision:
    """One deterministic decision. Raises MalformedSourceError on bad inputs."""
    if not isinstance(inp.learner_turn, str):
        raise MalformedSourceError("learner_turn must be a string")
    for gate in (_g1_injection, _g2_quarantine, _g3_provenance, _g4_stage_budget):
        out = gate(inp)
        if out is not None:
            return out
    return _g5_socratic_default(inp)


def decide_config(inp: TutorDecisionInput, config: Mapping[str, bool] | None = None) -> TutorDecision:
    """Config-gated decision used ONLY by the named ablations (A1..A5).

    Each flag removes exactly the named mechanism; defaults keep everything on.
    """
    cfg = {
        "injection_boundary": True,      # off = A5 (no action cost)
        "malicious_note_quarantine": True,  # off = A5 (no action cost)
        "uncertainty_calibration": True,  # off = A2 (no tau gate)
        "learner_stage": True,            # off = A3 (stage frozen to reasoning)
        "abstention": True,               # off = A4 (no abstain)
        "provenance_confidence": True,    # off = A1 (no conf factor)
    }
    if config:
        unknown = set(config) - set(cfg)
        if unknown:
            raise MalformedSourceError(f"unknown ablation flags {sorted(unknown)}")
        cfg.update(config)

    # A3: freeze the pedagogical stage to reasoning (no learner-stage signal).
    if not cfg["learner_stage"]:
        inp = TutorDecisionInput(
            case_id=inp.case_id,
            learner_turn=inp.learner_turn,
            sources=inp.sources,
            stage="reasoning",
            wants_answer=inp.wants_answer,
            stage_score=max(inp.stage_score, 1.0),
        )

    if cfg["injection_boundary"]:
        out = _g1_injection(inp)
        if out is not None:
            return out
    if cfg["malicious_note_quarantine"]:
        out = _g2_quarantine(inp)
        if out is not None:
            return out
    if cfg["abstention"]:
        out = _g3_provenance(inp)
        if out is not None:
            return out

    evidence_ids = tuple(
        s.source_id for s in inp.sources if s.provenance_status == "verified"
    )
    p = _answer_worthiness(inp) if cfg["provenance_confidence"] else round(
        min(1.0, W_STAGE * (float(inp.stage_score) or STAGE_SCORES[inp.stage])
            + W_DIVERSITY * min(1.0, len(evidence_ids) / 3.0) + 0.25),  # A1: stage+diversity only
        6,
    )
    if inp.wants_answer:
        if cfg["uncertainty_calibration"]:
            if inp.stage == "reasoning" and p >= TAU_ANSWER:
                return TutorDecision(
                    case_id=inp.case_id,
                    action="answer_with_evidence",
                    reason_codes=("verified_source", "stage_reasoning_authorized", "calibrated_confidence_pass"),
                    evidence_ids=evidence_ids,
                    p_answer=p,
                    meta={"gate": "G4-ablation"},
                )
            reasons = (
                ["low_answer_confidence", "calibrated_hint_fallback", "socratic_redirect"]
                if inp.stage == "reasoning"
                else ["early_answer_request", "answer_release_locked", "socratic_redirect"]
            )
            return TutorDecision(
                case_id=inp.case_id,
                action="hint",
                reason_codes=tuple(reasons),
                evidence_ids=evidence_ids,
                p_answer=p,
                meta={"gate": "G4-ablation"},
            )
        # A2: no uncertainty gate - answer whenever the stage permits.
        if inp.stage == "reasoning":
            return TutorDecision(
                case_id=inp.case_id,
                action="answer_with_evidence",
                reason_codes=("stage_reasoning_authorized", "uncertainty_gate_removed"),
                evidence_ids=evidence_ids,
                p_answer=p,
                meta={"gate": "G4-ablation-A2"},
            )
        return TutorDecision(
            case_id=inp.case_id,
            action="hint",
            reason_codes=("early_answer_request", "answer_release_locked", "socratic_redirect"),
            evidence_ids=evidence_ids,
            p_answer=p,
            meta={"gate": "G4-ablation-A2"},
        )
    return _g5_socratic_default(inp)
