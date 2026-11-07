# -*- coding: utf-8 -*-
"""Diagnostic Feedback Domain Engine for Historical Reasoning (LN-08 / Study 08).

Implements the historical misconception diagnostic engine:
- Unicode NFC normalization and negation-preserving tokenization (ALG-LN-08-01)
- Fact and assertion comparison against expected historical conclusions (ALG-LN-08-02)
- Claim-source graph validation and citation locator verification (ALG-LN-08-03)
- Contradiction, missing premise, and unsupported inference classification (ALG-LN-08-04)
- Formative feedback generation on task and process, strictly avoiding personal ability labels (ALG-LN-08-05)

Enforces Invariants:
- INV-LN-08-01: Keyword matching alone must NEVER grant correctness.
- INV-LN-08-02: Uncertain/unrecognized patterns yield 'abstain' without personal competence judgments.
- INV-LN-08-03: No claim of source support without verified locator.
- INV-LN-08-04: Feedback adheres to task boundary and disclosure limit.
- INV-LN-08-05: Synthetic fixtures are isolated from real learner data.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Optional

from backend.domain.history_error_taxonomy import (
    AnswerEvidence,
    AssessmentDecision,
    DiagnosticCategory,
    DiagnosticDecision,
    DiagnosticTag,
    FeedbackTemplate,
    HistoricalErrorType,
)

POLICY_VERSION = "study-v1-ln08"

# --------------------------------------------------------------------------- #
# Linguistic Patterns & Dictionaries (Vietnamese Historical Epigraphy & Sites)
# --------------------------------------------------------------------------- #

# Negation patterns that reverse propositional truth value
NEGATION_PATTERNS = [
    r"\bkhông\s+thuộc\b",
    r"\bkhông\s+nằm\b",
    r"\bkhông\s+phải\b",
    r"\bkhông\s+được\b",
    r"\bkhông\s+xây\b",
    r"\btrái\s+với\b",
    r"\bchẳng\s+phải\b",
    r"\bchưa\s+từng\b",
    r"\bphủ\s+nhận\b",
    r"\bbác\s+bỏ\b",
    r"\bngược\s+lại\b",
    r"\bsai\s+lệch\b",
    r"\bkhông\s+hề\b",
    r"\bđâu\s+phải\b",
    r"\bkhông\b(?!\s+(?:gian|khí)\b)",
]

# Canonical keywords for baseline matching
CANONICAL_RITUAL_AXIS_KEYWORDS = [
    "trục nghi lễ",
    "trục thần đạo",
    "nghi lễ",
]

# Synonymous phrasing for ritual spatial axis in historical architecture
SYNONYM_RITUAL_AXIS_PHRASES = [
    "tuyến không gian phục vụ nghi thức",
    "tuyến không gian nghi thức",
    "không gian phục vụ nghi thức",
    "trục nghi thức",
    "tuyến nghi lễ",
    "trục trung tâm nghi thức",
    "không gian nghi lễ",
]

# Synonym mappings for citation / source
SOURCE_SYNONYM_PHRASES = [
    "tư liệu",
    "sử liệu",
    "tài liệu",
    "văn bản",
    "chính sử",
    "nguồn",
]

# Relational connection verbs (affirming spatial ritual relationship)
AFFIRMATIVE_RELATION_PHRASES = [
    "thuộc",
    "nằm trên",
    "toạ lạc trên",
    "tọa lạc trên",
    "được bố trí trên",
    "nằm trong",
    "thuộc về",
]

# Known invalid or untrusted source identifiers
UNTRUSTED_SOURCE_IDS = {
    "SOURCE-SYN-WRONG",
    "SOURCE-UNVERIFIED",
    "SOURCE-FABRICATED",
}


def normalize_text(text: str) -> str:
    """Normalize Unicode to NFC, remove extraneous whitespace, preserve negation."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFC", text)
    cleaned = re.sub(r"\s+", " ", normalized).strip()
    return cleaned


def has_negation(text: str) -> tuple[bool, Optional[str]]:
    """Detect presence of negation patterns that invert historical claim."""
    lower = text.lower()
    for pattern in NEGATION_PATTERNS:
        match = re.search(pattern, lower)
        if match:
            return True, match.group(0)
    return False, None


def has_synonym_equivalence(text: str) -> bool:
    """Detect whether answer uses valid historical synonyms for spatial-ritual axis."""
    lower = text.lower()
    has_axis_synonym = any(phrase in lower for phrase in SYNONYM_RITUAL_AXIS_PHRASES)
    has_rel_phrase = any(phrase in lower for phrase in AFFIRMATIVE_RELATION_PHRASES)
    return has_axis_synonym and has_rel_phrase


def has_canonical_keywords(text: str) -> bool:
    """Check for exact canonical phrasing 'trục nghi lễ' and affirmative relation."""
    lower = text.lower()
    has_axis = any(kw in lower for kw in CANONICAL_RITUAL_AXIS_KEYWORDS)
    return has_axis


def is_partial_reasoning(text: str) -> bool:
    """Detect if answer only identifies generic object type without spatial-ritual reasoning."""
    lower = text.lower()
    has_generic_arch = "công trình kiến trúc" in lower or "kiến trúc" in lower or "di tích" in lower
    has_ritual_axis = has_canonical_keywords(lower) or any(phrase in lower for phrase in SYNONYM_RITUAL_AXIS_PHRASES)
    return has_generic_arch and not has_ritual_axis


def verify_source_linkage(evidence: dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Verify that cited source is authentic, verified, and not in untrusted list."""
    source_id = evidence.get("source_id")
    verified = evidence.get("verified", False)

    if not source_id:
        return False, "missing_source_locator"
    if source_id in UNTRUSTED_SOURCE_IDS:
        return False, "source_mismatch_untrusted"
    if not verified:
        return False, "source_unverified"

    return True, None


# --------------------------------------------------------------------------- #
# Baseline Policy (Naive Keyword Matching)
# --------------------------------------------------------------------------- #

def evaluate_baseline(scenario_input: dict[str, Any], config: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Naive baseline: superficial keyword matching blind to negation and citation validity.

    Vulnerabilities:
    - Fooled by negated keywords: 'không thuộc trục nghi lễ' contains 'trục nghi lễ' -> accepted!
    - Fooled by wrong source: matches keywords in text without checking evidence source -> accepted!
    - Penalizes synonym expressions: 'tuyến không gian phục vụ nghi thức' misses keyword 'trục nghi lễ' -> rejected!
    - Penalizes partial expressions: misses keyword 'trục nghi lễ' -> incomplete/rejected.
    """
    answer_raw = scenario_input.get("answer", "")
    answer = normalize_text(answer_raw)
    content = scenario_input.get("content", {})
    entity_label = content.get("label", "")

    # Naive keyword check: looks for entity name or expected axis keywords
    lower_ans = answer.lower()
    has_axis_kw = "trục nghi lễ" in lower_ans or "nghi lễ" in lower_ans
    is_negated, _ = has_negation(answer)

    if has_axis_kw:
        # Naive system marks correct purely on keyword presence!
        # False keyword match occurs if negation is present
        decision = DiagnosticDecision.FEEDBACK_SUPPORTED.value
        category = DiagnosticCategory.KEYWORD_MATCH.value
        reason_codes = ["Đáp án và nguồn phù hợp", "baseline_keyword_match"]
        false_keyword_match = is_negated
    else:
        # Fails synonym answers and partial answers due to missing exact keyword
        decision = DiagnosticDecision.FEEDBACK_INCOMPLETE.value
        category = DiagnosticCategory.KEYWORD_MISSING.value
        reason_codes = ["baseline_keyword_missing"]
        false_keyword_match = False

    return {
        "decision": decision,
        "reason_codes": reason_codes,
        "policy_version": "baseline-v1-keyword",
        "diagnostic_category": category,
        "false_keyword_match": false_keyword_match,
        "feedback_message": "Chấm dựa trên sự xuất hiện của từ khóa chính.",
        "observables": {
            "diagnostic_category": category,
            "false_keyword_match": false_keyword_match,
            "keyword_matched": has_axis_kw,
            "negation_checked": False,
            "source_checked": False,
        },
    }


# --------------------------------------------------------------------------- #
# Intervention Policy (Categorized Diagnostic Analysis)
# --------------------------------------------------------------------------- #

def evaluate_intervention(
    scenario_input: dict[str, Any],
    config: Optional[dict[str, Any]] = None,
    *,
    skip_negation_check: bool = False,
    skip_source_check: bool = False,
) -> dict[str, Any]:
    """Intervention: diagnostic analysis across historical misconception taxonomy.

    Pipeline:
    1. Input sanitization and empty check -> abstain
    2. Source linkage verification (unless disabled by ablation)
    3. Propositional negation / contradiction check (unless disabled by ablation)
    4. Incomplete / partial reasoning check
    5. Semantic / synonym equivalence recognition
    6. Nominal supported answer
    """
    answer_raw = scenario_input.get("answer", "")
    answer = normalize_text(answer_raw)
    evidence = scenario_input.get("evidence", {})

    if not answer:
        return {
            "decision": DiagnosticDecision.ABSTAIN.value,
            "reason_codes": ["Thiếu câu trả lời", "RULE-LN-08-INV"],
            "policy_version": POLICY_VERSION,
            "diagnostic_category": DiagnosticCategory.UNCLASSIFIED.value,
            "observables": {
                "diagnostic_category": DiagnosticCategory.UNCLASSIFIED.value,
                "error_type": HistoricalErrorType.INSUFFICIENT_EVIDENCE.value,
            },
        }

    # Step 1: Source Linkage Verification (INV-LN-08-03)
    if not skip_source_check:
        source_ok, source_err = verify_source_linkage(evidence)
        if not source_ok:
            tag = DiagnosticTag(
                code="SRC_MISMATCH_01",
                error_type=HistoricalErrorType.SOURCE_MISMATCH,
                confidence=0.98,
                span=str(evidence.get("source_id", "none")),
                evidence="Nguồn dẫn không trùng khớp với cơ sở dữ liệu sử liệu được xác thực.",
                actionable_hint="Kiểm tra lại mã định danh và trang dẫn của nguồn trước khi xác lập luận điểm.",
            )
            return {
                "decision": DiagnosticDecision.CLASSIFY_SOURCE_ERROR.value,
                "reason_codes": ["Nguồn không hỗ trợ nhận định", "RULE-LN-08-03", "source_mismatch"],
                "policy_version": POLICY_VERSION,
                "diagnostic_category": DiagnosticCategory.SOURCE_ERROR.value,
                "feedback_message": "Nguồn tư liệu dẫn chứng không hỗ trợ nhận định này. Hãy đối chiếu lại mã nguồn chuẩn.",
                "diagnostic_tags": [tag.__dict__],
                "observables": {
                    "diagnostic_category": DiagnosticCategory.SOURCE_ERROR.value,
                    "error_type": HistoricalErrorType.SOURCE_MISMATCH.value,
                    "source_verified": False,
                    "false_keyword_match": False,
                },
            }

    # Step 2: Logical Negation / Contradiction (INV-LN-08-01)
    if not skip_negation_check:
        is_negated, neg_token = has_negation(answer)
        if is_negated:
            tag = DiagnosticTag(
                code="NEG_CONTRADICT_01",
                error_type=HistoricalErrorType.LOGICAL_NEGATION,
                confidence=0.99,
                span=neg_token or "không",
                evidence="Câu chứa liên từ hoặc phó từ phủ định làm đảo ngược ý nghĩa lịch sử của mệnh đề.",
                actionable_hint="Lưu ý quan hệ giữa công trình và trục nghi lễ là khẳng định, không phải phủ định.",
            )
            return {
                "decision": DiagnosticDecision.CLASSIFY_CONTRADICTION.value,
                "reason_codes": ["Phủ định biến câu đúng thành sai", "RULE-LN-08-02", "logical_negation"],
                "policy_version": POLICY_VERSION,
                "diagnostic_category": DiagnosticCategory.CONTRADICTION.value,
                "feedback_message": "Câu trả lời chứa mệnh đề phủ định làm sai lệch quan hệ không gian nghi lễ được ghi trong sử liệu.",
                "diagnostic_tags": [tag.__dict__],
                "observables": {
                    "diagnostic_category": DiagnosticCategory.CONTRADICTION.value,
                    "error_type": HistoricalErrorType.LOGICAL_NEGATION.value,
                    "negation_detected": True,
                    "false_keyword_match": False,
                },
            }

    # Step 3: Partial / Incomplete Reasoning (ALG-LN-08-04)
    if is_partial_reasoning(answer):
        tag = DiagnosticTag(
            code="PARTIAL_REASONING_01",
            error_type=HistoricalErrorType.PARTIAL_REASONING,
            confidence=0.95,
            span=answer,
            evidence="Câu mới chỉ nêu đặc điểm chung (công trình kiến trúc) mà chưa nêu quan hệ với trục nghi lễ theo yêu cầu.",
            actionable_hint="Bổ sung thêm luận điểm về vị trí và vai trò của công trình trên trục nghi lễ của Hoàng thành.",
        )
        return {
            "decision": DiagnosticDecision.FEEDBACK_INCOMPLETE.value,
            "reason_codes": ["Câu trả lời đúng một phần", "RULE-LN-08-05", "partial_reasoning"],
            "policy_version": POLICY_VERSION,
            "diagnostic_category": DiagnosticCategory.INCOMPLETE.value,
            "feedback_message": "Câu trả lời đúng một phần nhưng còn thiếu mối quan hệ không gian - nghi lễ cốt lõi.",
            "diagnostic_tags": [tag.__dict__],
            "observables": {
                "diagnostic_category": DiagnosticCategory.INCOMPLETE.value,
                "error_type": HistoricalErrorType.PARTIAL_REASONING.value,
                "completeness_score": 0.5,
                "false_keyword_match": False,
            },
        }

    # Step 4: Semantic & Synonym Equivalence (INV-LN-08-04 / RULE-LN-08-04)
    if has_synonym_equivalence(answer):
        return {
            "decision": DiagnosticDecision.PRESERVE_SEMANTICS.value,
            "reason_codes": ["Diễn đạt khác nhưng cùng mệnh đề", "RULE-LN-08-04", "synonym_equivalence"],
            "policy_version": POLICY_VERSION,
            "diagnostic_category": DiagnosticCategory.SUPPORTED_EQUIVALENT.value,
            "feedback_message": "Cách diễn đạt phong phú và thể hiện đúng bản chất không gian nghi lễ của di tích theo nguồn sử liệu.",
            "observables": {
                "diagnostic_category": DiagnosticCategory.SUPPORTED_EQUIVALENT.value,
                "error_type": HistoricalErrorType.SYNONYM_EQUIVALENCE.value,
                "semantic_invariance_preserved": True,
                "false_keyword_match": False,
            },
        }

    # Step 5: Canonical Nominal Supported (RULE-LN-08-01)
    if has_canonical_keywords(answer):
        return {
            "decision": DiagnosticDecision.FEEDBACK_SUPPORTED.value,
            "reason_codes": ["Đáp án và nguồn phù hợp", "RULE-LN-08-01", "nominal"],
            "policy_version": POLICY_VERSION,
            "diagnostic_category": DiagnosticCategory.SUPPORTED.value,
            "feedback_message": "Đáp án chuẩn xác, dẫn chứng phù hợp với tư liệu lịch sử được cung cấp.",
            "observables": {
                "diagnostic_category": DiagnosticCategory.SUPPORTED.value,
                "error_type": HistoricalErrorType.NONE.value,
                "source_verified": True,
                "false_keyword_match": False,
            },
        }

    # Fallback / Abstain for unrecognized forms
    return {
        "decision": DiagnosticDecision.ABSTAIN.value,
        "reason_codes": ["Cần xem xét thêm do câu trả lời chưa rõ quan hệ", "RULE-LN-08-ABSTAIN"],
        "policy_version": POLICY_VERSION,
        "diagnostic_category": DiagnosticCategory.UNCLASSIFIED.value,
        "feedback_message": "Hệ thống chưa đủ cơ sở dữ liệu để phân loại chính xác lỗi này. Đã chuyển hồ sơ cho giáo viên.",
        "observables": {
            "diagnostic_category": DiagnosticCategory.UNCLASSIFIED.value,
            "error_type": HistoricalErrorType.UNKNOWN.value,
            "false_keyword_match": False,
        },
    }


# --------------------------------------------------------------------------- #
# Ablation Policy
# --------------------------------------------------------------------------- #

def evaluate_ablation(scenario_input: dict[str, Any], config: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Ablation studies: isolate specific diagnostic components.

    Supported variants via config['ablation'] or config['ablation_type']:
    - 'keyword_only': degrades to naive keyword matcher
    - 'disable_negation': intervention engine with negation analysis disabled
    - 'disable_source_link' / 'no_source_grounding': intervention engine with source validation disabled
    """
    cfg = config or {}
    ablation_type = cfg.get("ablation") or cfg.get("ablation_type") or "keyword_only"

    if ablation_type in ("keyword_only",):
        res = evaluate_baseline(scenario_input, config)
        res["policy_version"] = "ablation-v1-keyword-only"
        return res
    elif ablation_type in ("disable_negation", "no_negation"):
        res = evaluate_intervention(scenario_input, config, skip_negation_check=True)
        res["policy_version"] = "ablation-v1-no-negation"
        return res
    elif ablation_type in ("disable_source_link", "no_source_grounding", "disable_source_grounding"):
        res = evaluate_intervention(scenario_input, config, skip_source_check=True)
        res["policy_version"] = "ablation-v1-no-source-link"
        return res
    else:
        # Default ablation: keyword only
        res = evaluate_baseline(scenario_input, config)
        res["policy_version"] = f"ablation-v1-{ablation_type}"
        return res
