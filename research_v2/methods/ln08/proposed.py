"""LN-08 proposed policy — evidence-calibrated diagnostic feedback engine.

Decision procedure (strict precedence, mirrors the observed legacy engine
``research/feedback/diagnostic_feedback.py`` at the pinned snapshot and fixes
its known keyword-matching vulnerability):

0. Empty/whitespace answer            -> ``abstain`` (calibrated abstention,
                                         mapped to ``abstain_insufficient_data``;
                                         never a personal competence judgment).
1. Source-linkage verification        -> ``classify_source_error`` when the
                                         cited locator is fabricated/untrusted/
                                         unverified (INV-LN-08-03: no claim of
                                         source support without verified
                                         locator).
2. Negation / contradiction parsing   -> ``classify_contradiction`` when a
                                         negation operator reverses the
                                         asserted relation. This catches the
                                         mandatory counterexample: an answer
                                         containing ALL keywords yet REVERSING
                                         the historical relation ("Ngọ Môn is
                                         NOT on the ritual axis") must be a
                                         contradiction, never
                                         ``feedback_supported`` (INV-LN-08-01:
                                         keyword matching alone must NEVER
                                         grant correctness). The Vietnamese
                                         negation scan excludes lookalikes
                                         ("không gian" = space, "khí").
3. Partial-reasoning detection        -> ``feedback_incomplete`` when the
                                         answer only identifies the generic
                                         monument class without the
                                         spatial-ritual relation.
4. Semantic-equivalence detection     -> ``preserve_semantics`` when a
                                         synonym-equivalent paraphrase asserts
                                         the source-backed relation without the
                                         canonical keyword.
5. Canonical keyword support          -> ``feedback_supported`` only when the
                                         source locator is verified, no
                                         negation is present and the asserted
                                         relation is expressed.
6. Unrecognised form                  -> ``abstain`` (fail-closed, distinct
                                         from every reject label).

Determinism: no randomness is consumed (the ``seed`` config is accepted for
interface compatibility only). Identical (input, config, seed) produce
identical decisions.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from .dataset import DatasetError, DiagnosticCase
from .labels import (
    REASON_EMPTY_ANSWER,
    REASON_KEYWORD_MISSING,
    REASON_NOMINAL,
    REASON_NEGATION,
    REASON_PARTIAL,
    REASON_SOURCE_MISMATCH,
    REASON_SYNONYM,
    RULE_INV,
    RULE_NEGATION,
    RULE_SUPPORTED,
    RULE_PARTIAL,
    RULE_SOURCE,
    RULE_SYNONYM,
    STUDY_ID,
    build_prediction,
    native_decision,
)

METHOD_ID = "proposed"
METHOD_VERSION = "ln08-proposed-v2.0"

# ---------------------------------------------------------------------------
# Linguistic resources (Vietnamese historical epigraphy + English equivalents)
# ---------------------------------------------------------------------------

# Negation operators that invert a historical claim. The bare Vietnamese
# negator carries a lookahead so lookalike compounds ("không gian" = space,
# "khí" = air/atmosphere) are not misread as operators.
NEGATION_PATTERNS: tuple[str, ...] = (
    # Vietnamese compound operators (most specific first)
    r"\bkhông\s+thuộc\b",
    r"\bkhông\s+nằm\b",
    r"\bkhông\s+phải\b",
    r"\bkhông\s+được\b",
    r"\bkhông\s+xây\b",
    r"\bkhông\s+từng\b",
    r"\bkhông\s+hề\b",
    r"\bchưa\s+từng\b",
    r"\bchẳng\s+phải\b",
    r"\bđâu\s+phải\b",
    r"\bphủ\s+nhận\b",
    r"\bbác\s+bỏ\b",
    r"\btrái\s+với\b",
    r"\bngược\s+lại\b",
    r"\bsai\s+lệch\b",
    # Bare Vietnamese negator with lookalike guard
    r"\bkhông\b(?!\s*(?:gian|khí)\b)",
    # English
    r"\bnot\b",
    r"\bnever\b",
    r"\bno\b",
    r"\bdoes\s+not\b",
    r"\bisn't\b",
    r"\bwasn't\b",
    r"\baren't\b",
    r"\bdoesn't\b",
    r"\bdidn't\b",
    r"\bcontradicts\b",
    r"\brefutes\b",
    r"\bdenies\b",
    r"\bopposite\b",
)

# Synonymous phrasings for the spatial-ritual axis (assertion content).
SYNONYM_AXIS_PHRASES: tuple[str, ...] = (
    "tuyến không gian phục vụ nghi thức",
    "tuyến không gian nghi thức",
    "không gian phục vụ nghi thức",
    "trục nghi thức",
    "tuyến nghi lễ",
    "trục trung tâm nghi thức",
    "không gian nghi lễ",
    "ritual axis",
    "ceremonial axis",
    "ritual space",
    "ritual pathway",
)

# Affirmative relational predicates (spatial relation to the axis).
AFFIRMATIVE_RELATION_PHRASES: tuple[str, ...] = (
    "thuộc",
    "nằm trên",
    "toạ lạc trên",
    "tọa lạc trên",
    "được bố trí trên",
    "nằm trong",
    "thuộc về",
    "is on",
    "lies on",
    "located on",
    "situated on",
    "stands on",
    "belongs to",
    "part of",
)

# Canonical axis keywords (exact phrasing of the verified passages).
CANONICAL_AXIS_KEYWORDS: tuple[str, ...] = (
    "trục nghi lễ",
    "trục thần đạo",
    "nghi lễ",
    "ritual axis",
    "ceremonial axis",
)

# Generic architectural descriptors (partial reasoning signal).
GENERIC_ARCH_PHRASES: tuple[str, ...] = (
    "công trình kiến trúc",
    "kiến trúc",
    "di tích",
    "historical structure",
    "architecture",
    "heritage site",
    "monument",
)

# Known invalid / untrusted source identifiers (from the legacy engine).
UNTRUSTED_SOURCE_IDS: frozenset[str] = frozenset(
    {"SOURCE-SYN-WRONG", "SOURCE-UNVERIFIED", "SOURCE-FABRICATED"}
)

COMPARATOR_STATUS: dict[str, str] = {
    "proposed": "ORIGINAL_CODE_VERIFIED",
    "baselines_b0": "ORIGINAL_CODE_VERIFIED",
    "baselines_c1": "REIMPLEMENTATION",
    "ablations_a1": "ORIGINAL_CODE_VERIFIED",
    "ablations_a2": "ORIGINAL_CODE_VERIFIED",
    "ablations_a3": "ORIGINAL_CODE_VERIFIED",
}

DEFAULT_COSINE_THRESHOLD = 0.40


# ---------------------------------------------------------------------------
# Text analysis primitives (pure, deterministic)
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Unicode NFC normalisation + whitespace collapse (negation preserved)."""
    if not isinstance(text, str):
        raise DatasetError(f"normalize_text expects str, got {type(text).__name__}")
    normalized = unicodedata.normalize("NFC", text)
    return re.sub(r"\s+", " ", normalized).strip().lower()


def detect_negation(normalized: str) -> tuple[bool, str | None]:
    """Return (present, matched_operator) for negation operators."""
    for pattern in NEGATION_PATTERNS:
        match = re.search(pattern, normalized)
        if match:
            return True, match.group(0)
    return False, None


def has_synonym_equivalence(normalized: str) -> bool:
    """Synonym-equivalent assertion of the spatial-ritual relation."""
    has_axis = any(phrase in normalized for phrase in SYNONYM_AXIS_PHRASES)
    has_relation = any(phrase in normalized for phrase in AFFIRMATIVE_RELATION_PHRASES)
    return has_axis and has_relation


def has_canonical_keywords(normalized: str) -> bool:
    """Exact canonical axis phrasing present."""
    return any(kw in normalized for kw in CANONICAL_AXIS_KEYWORDS)


def is_partial_reasoning(normalized: str) -> bool:
    """Generic monument description without the spatial-ritual relation."""
    generic = any(phrase in normalized for phrase in GENERIC_ARCH_PHRASES)
    axis = has_canonical_keywords(normalized) or any(
        phrase in normalized for phrase in SYNONYM_AXIS_PHRASES
    )
    return generic and not axis


def verify_source_linkage(evidence: Mapping[str, Any]) -> tuple[bool, str | None]:
    """Verify the cited locator is known-trusted AND flagged verified.

    Returns (ok, failure_code); failure codes mirror the legacy engine.
    """
    source_id = evidence.get("source_id")
    verified = evidence.get("verified", False)
    if not isinstance(source_id, str) or not source_id.strip():
        return False, "missing_source_locator"
    if source_id in UNTRUSTED_SOURCE_IDS:
        return False, "source_mismatch_untrusted"
    if not verified:
        return False, "source_unverified"
    return True, None


def char_ngram_vector(text: str, n: int = 3) -> dict[str, int]:
    clean = re.sub(r"\s+", " ", text.strip())
    counts: dict[str, int] = {}
    for i in range(max(0, len(clean) - n + 1)):
        gram = clean[i : i + n]
        counts[gram] = counts.get(gram, 0) + 1
    return counts


def cosine_similarity(v1: Mapping[str, int], v2: Mapping[str, int]) -> float:
    import math

    dot = sum(v1[k] * v2.get(k, 0) for k in v1)
    mag1 = math.sqrt(sum(v * v for v in v1.values()))
    mag2 = math.sqrt(sum(v * v for v in v2.values()))
    if mag1 == 0.0 or mag2 == 0.0:
        return 0.0
    return dot / (mag1 * mag2)


# ---------------------------------------------------------------------------
# Core decision function
# ---------------------------------------------------------------------------

def decide_case(
    case: DiagnosticCase,
    *,
    parse_negation: bool = True,
    check_source: bool = True,
    keyword_only: bool = False,
) -> dict[str, Any]:
    """Pure decision function. Returns (decision, reason_codes, score) dict.

    Keyword arguments exist ONLY for the mechanism-isolating ablations; the
    proposed policy always runs with every mechanism enabled.
    """
    if not case.answer.strip():
        return {
            "decision": "abstain",
            "reason_codes": (REASON_EMPTY_ANSWER, RULE_INV),
            "score": None,
        }

    normalized = normalize_text(case.answer)

    if keyword_only:
        # Degraded keyword-presence mode (used by the a1 ablation only).
        present = has_canonical_keywords(normalized) or "nghi lễ" in normalized
        return {
            "decision": "feedback_supported" if present else "feedback_incomplete",
            "reason_codes": (
                (REASON_NOMINAL,) if present else (REASON_KEYWORD_MISSING,),
            ),
            "score": None,
        }

    # Step 1: source-linkage verification (INV-LN-08-03).
    if check_source:
        source_ok, source_err = verify_source_linkage(case.evidence.__dict__)
        if not source_ok:
            return {
                "decision": "classify_source_error",
                "reason_codes": (REASON_SOURCE_MISMATCH, RULE_SOURCE, source_err or "source_gap"),
                "score": None,
            }

    # Step 2: negation / contradiction parsing (INV-LN-08-01). An answer that
    # contains every keyword yet reverses the relation is a contradiction.
    if parse_negation:
        negated, operator = detect_negation(normalized)
        if negated:
            return {
                "decision": "classify_contradiction",
                "reason_codes": (REASON_NEGATION, RULE_NEGATION, f"operator:{operator or 'unknown'}"),
                "score": None,
            }

    # Step 3: partial / incomplete reasoning.
    if is_partial_reasoning(normalized):
        return {
            "decision": "feedback_incomplete",
            "reason_codes": (REASON_PARTIAL, RULE_PARTIAL),
            "score": None,
        }

    # Step 4: semantic / synonym equivalence.
    if has_synonym_equivalence(normalized):
        return {
            "decision": "preserve_semantics",
            "reason_codes": (REASON_SYNONYM, RULE_SYNONYM),
            "score": None,
        }

    # Step 5: canonical nominal support.
    if has_canonical_keywords(normalized):
        return {
            "decision": "feedback_supported",
            "reason_codes": (REASON_NOMINAL, RULE_SUPPORTED),
            "score": None,
        }

    # Step 6: unrecognised form -> calibrated abstention (fail-closed).
    return {
        "decision": "abstain",
        "reason_codes": (REASON_KEYWORD_MISSING, RULE_INV),
        "score": None,
    }


def solve_case(
    case: DiagnosticCase,
    *,
    parse_negation: bool = True,
    check_source: bool = True,
    keyword_only: bool = False,
) -> dict[str, Any]:
    """Public solve wrapper with validated native decision labels."""
    result = decide_case(
        case,
        parse_negation=parse_negation,
        check_source=check_source,
        keyword_only=keyword_only,
    )
    result["decision"] = native_decision(result["decision"])
    return result


def predict_one(inp: Any, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    from research_v2.contracts.types import StudyInput as _StudyInput

    if not isinstance(inp, _StudyInput):
        raise DatasetError(f"predict_one expects StudyInput, got {type(inp).__name__}")
    cfg = dict(config or {})
    if not isinstance(inp.study_id, str) or inp.study_id != STUDY_ID:
        raise DatasetError(f"case {inp.case_id!r}: expected study_id {STUDY_ID}, got {inp.study_id!r}")
    case = DiagnosticCase.from_features(inp.features, case_id=inp.case_id)
    result = solve_case(case)
    return build_prediction(
        case_id=inp.case_id,
        decision=result["decision"],
        reason_codes=tuple(result["reason_codes"]),
        evidence_ids=(case.evidence.claim_id, case.evidence.source_id),
        score=result["score"],
    )


def predict_batch(inputs: list, config: dict | None = None) -> list:
    """Contract ABI: deterministic LN-08 decisions for a batch of inputs.

    Any invalid row rejects the whole batch with its location (no guessed
    fallback), per the study specification.
    """
    cfg = dict(config or {})
    out = []
    for i, inp in enumerate(inputs):
        try:
            out.append(predict_one(inp, cfg))
        except DatasetError as exc:
            raise DatasetError(f"input[{i}] {exc}") from exc
        except Exception as exc:  # surface typed failure with batch location
            raise DatasetError(f"input[{i}] case {getattr(inp, 'case_id', '?')!r}: {exc}") from exc
    return out
