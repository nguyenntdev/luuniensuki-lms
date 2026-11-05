# -*- coding: utf-8 -*-
"""Source-Grounded AI Scaffolding Policy (Wave W06 / LN-04).

Implements the domain engine for Socratic AI tutoring with:
- Hint budget & fading management (observation -> evidence -> reasoning)
- Strict source verification gating (abstaining when source missing/unverified)
- Answer leakage defense (preventing direct solutions before authorized release)
- Prompt injection defense (sanitization, override & jailbreak detection)
- Deterministic fallback when AI provider is unavailable
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


POLICY_VERSION = "study-v1"

# Patterns detecting explicit requests for complete direct answers / solutions
DIRECT_ANSWER_REQUEST_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"\b(?:viết|cho|xin|tiết lộ|cung cấp)\s+(?:đáp án|lời giải|kết quả)\s+(?:hoàn chỉnh|đầy đủ|chi tiết)?\s*(?:để em chép|ngay)?\b", re.IGNORECASE),
    re.compile(r"\b(?:give me|tell me|show me|reveal)\s+(?:the\s+)?(?:full\s+)?(?:answer|solution|result)\b", re.IGNORECASE),
    re.compile(r"\b(?:chép đáp án|làm hộ em|giải hộ em)\b", re.IGNORECASE),
)

# Injection and prompt override patterns (pedagogical bypasses)
PROMPT_INJECTION_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"\b(?:bỏ qua|quên|ghi đè)\s+(?:mọi\s+)?(?:quy tắc|chỉ dẫn|hướng dẫn|lệnh|chỉ thị)\b", re.IGNORECASE),
    re.compile(r"\b(?:ignore|disregard|bypass|override)\s+(?:all\s+)?(?:rules|instructions|directives|system)\b", re.IGNORECASE),
    re.compile(r"\b(?:nội dung nguồn không quan trọng|source does not matter)\b", re.IGNORECASE),
    re.compile(r"\b(?:act as|pretend to be|đóng vai)\s+(?:dan|developer mode|unrestricted)\b", re.IGNORECASE),
)


class ScaffoldingDecision(str, Enum):
    HINT_THEN_FADE = "hint_then_fade"
    RESTRICT_LEAKAGE = "restrict_leakage"
    ABSTAIN_SOURCE_GAP = "abstain_source_gap"
    REJECT_INJECTION = "reject_injection"
    DETERMINISTIC_FALLBACK = "deterministic_fallback"
    DIRECT_ANSWER = "direct_answer"


@dataclass(frozen=True)
class ScaffoldingResult:
    decision: str
    reason_codes: list[str]
    policy_version: str = POLICY_VERSION
    answer_leakage: bool = False
    citation_integrity: bool = False
    appropriate_abstention: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "reason_codes": self.reason_codes,
            "policy_version": self.policy_version,
            "answer_leakage": self.answer_leakage,
            "citation_integrity": self.citation_integrity,
            "appropriate_abstention": self.appropriate_abstention,
            **self.details,
        }


def detect_answer_request(question: str) -> bool:
    """Check if the user is explicitly requesting a direct full answer to bypass learning."""
    if not question:
        return False
    norm = question.strip()
    return any(p.search(norm) is not None for p in DIRECT_ANSWER_REQUEST_PATTERNS)


def detect_scaffolding_injection(question: str) -> bool:
    """Check if the input attempts prompt injection, system override, or rule bypass."""
    if not question:
        return False
    norm = question.strip()
    return any(p.search(norm) is not None for p in PROMPT_INJECTION_PATTERNS)


def evaluate_scaffolding_policy(
    scenario_input: dict[str, Any],
    *,
    mode: str = "intervention",
    config: Optional[dict[str, Any]] = None,
) -> ScaffoldingResult:
    """Pure domain evaluation of source-grounded scaffolding policy.

    Modes:
      - 'baseline': Direct answer bot revealing historical solutions immediately,
                    without hint budget or source verification checks.
      - 'intervention': Full pedagogical scaffolding policy:
          1. Provider health -> deterministic_fallback if unavailable
          2. Adversarial/injection detection -> reject_injection
          3. Source verification gate -> abstain_source_gap if missing/unverified
          4. Answer release & leakage defense -> restrict_leakage if early answer request
          5. Progressive Socratic hint -> hint_then_fade
      - 'ablation': Configurable ablation testing:
          - disable_hint_budget: true -> direct answer without hint gating
          - disable_source_refusal: true -> bypass source gap check
          - disable_injection_check: true -> bypass prompt injection filter
    """
    cfg = config or {}
    question = str(scenario_input.get("question", "") or "")
    provider = scenario_input.get("provider", {})
    provider_available = provider.get("available", True) if isinstance(provider, dict) else True
    
    retrieval = scenario_input.get("retrieval", {})
    if not isinstance(retrieval, dict):
        retrieval = {}
    source_ids = retrieval.get("source_ids", [])
    source_status = retrieval.get("source_status", "unverified")
    
    task = scenario_input.get("task", {})
    if not isinstance(task, dict):
        task = {}
    answer_release_allowed = bool(task.get("answer_release_allowed", False))
    hint_level = int(task.get("hint_level", 1))

    # -------------------------------------------------------------
    # BASELINE MODE: Direct answer bot, unconstrained source release
    # -------------------------------------------------------------
    if mode == "baseline":
        is_ans_req = detect_answer_request(question)
        # Baseline directly leaks/reveals answer on request or provides direct answer
        return ScaffoldingResult(
            decision="direct_answer",
            reason_codes=["baseline_direct_answer", "no_hint_budget"],
            policy_version=POLICY_VERSION,
            answer_leakage=True if is_ans_req else False,
            citation_integrity=bool(source_ids and source_status in ("verified", "editor_reviewed")),
            appropriate_abstention=False,
            details={
                "mode": "baseline",
                "revealed_direct_answer": True,
            },
        )

    # -------------------------------------------------------------
    # ABLATION MODE
    # -------------------------------------------------------------
    if mode == "ablation":
        disable_hint_budget = cfg.get("disable_hint_budget", False)
        disable_source_refusal = cfg.get("disable_source_refusal", False)
        disable_injection_check = cfg.get("disable_injection_check", False)

        if not provider_available:
            return ScaffoldingResult(
                decision=ScaffoldingDecision.DETERMINISTIC_FALLBACK.value,
                reason_codes=["service_unavailable"],
                policy_version=POLICY_VERSION,
                answer_leakage=False,
                citation_integrity=False,
                appropriate_abstention=True,
                details={"mode": "ablation", "fallback": True},
            )

        if not disable_injection_check and detect_scaffolding_injection(question):
            return ScaffoldingResult(
                decision=ScaffoldingDecision.REJECT_INJECTION.value,
                reason_codes=["prompt_injection"],
                policy_version=POLICY_VERSION,
                answer_leakage=False,
                citation_integrity=False,
                appropriate_abstention=True,
                details={"mode": "ablation", "rejected_injection": True},
            )

        has_verified_source = bool(source_ids) and (source_status in ("verified", "editor_reviewed"))
        if not disable_source_refusal and not has_verified_source:
            return ScaffoldingResult(
                decision=ScaffoldingDecision.ABSTAIN_SOURCE_GAP.value,
                reason_codes=["unverified_context"],
                policy_version=POLICY_VERSION,
                answer_leakage=False,
                citation_integrity=False,
                appropriate_abstention=True,
                details={"mode": "ablation", "abstention": True},
            )

        if disable_hint_budget:
            # Direct answers without hint budget
            return ScaffoldingResult(
                decision="direct_answer",
                reason_codes=["ablation_direct_answer"],
                policy_version=POLICY_VERSION,
                answer_leakage=True,
                citation_integrity=has_verified_source,
                appropriate_abstention=False,
                details={"mode": "ablation", "hint_budget_disabled": True},
            )

    # -------------------------------------------------------------
    # INTERVENTION MODE: Standard rigorous scaffolding policy
    # -------------------------------------------------------------
    # Rule 1: Service availability / provider health
    if not provider_available:
        return ScaffoldingResult(
            decision=ScaffoldingDecision.DETERMINISTIC_FALLBACK.value,
            reason_codes=["service_unavailable"],
            policy_version=POLICY_VERSION,
            answer_leakage=False,
            citation_integrity=False,
            appropriate_abstention=True,
            details={
                "mode": "intervention",
                "fallback_type": "offline_deterministic_rubric",
            },
        )

    # Rule 2: Prompt injection / instruction override defense
    if detect_scaffolding_injection(question):
        return ScaffoldingResult(
            decision=ScaffoldingDecision.REJECT_INJECTION.value,
            reason_codes=["prompt_injection"],
            policy_version=POLICY_VERSION,
            answer_leakage=False,
            citation_integrity=False,
            appropriate_abstention=True,
            details={
                "mode": "intervention",
                "security_violation": "instruction_override",
            },
        )

    # Rule 3: Source verification gate (epistemic integrity)
    has_verified_source = bool(source_ids) and (source_status in ("verified", "editor_reviewed"))
    if not has_verified_source:
        return ScaffoldingResult(
            decision=ScaffoldingDecision.ABSTAIN_SOURCE_GAP.value,
            reason_codes=["unverified_context"],
            policy_version=POLICY_VERSION,
            answer_leakage=False,
            citation_integrity=False,
            appropriate_abstention=True,
            details={
                "mode": "intervention",
                "source_gap": True,
                "epistemic_status": "insufficient_verified_evidence",
            },
        )

    # Rule 4: Answer release & leakage defense (fading & scaffolding control)
    is_answer_request = detect_answer_request(question)
    if is_answer_request and not answer_release_allowed:
        return ScaffoldingResult(
            decision=ScaffoldingDecision.RESTRICT_LEAKAGE.value,
            reason_codes=["answer_request"],
            policy_version=POLICY_VERSION,
            answer_leakage=False,
            citation_integrity=True,
            appropriate_abstention=True,
            details={
                "mode": "intervention",
                "scaffold_step": "restrict_early_solution",
                "socratic_redirection": True,
            },
        )

    # Rule 5: Progressive Socratic scaffolding (observation -> evidence -> reasoning)
    return ScaffoldingResult(
        decision=ScaffoldingDecision.HINT_THEN_FADE.value,
        reason_codes=["nominal"],
        policy_version=POLICY_VERSION,
        answer_leakage=False,
        citation_integrity=True,
        appropriate_abstention=False,
        details={
            "mode": "intervention",
            "hint_level": hint_level,
            "scaffold_stage": "observation" if hint_level == 1 else "evidence" if hint_level == 2 else "reasoning",
            "cited_source_ids": source_ids,
        },
    )
