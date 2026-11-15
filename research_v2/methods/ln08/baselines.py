"""LN-08 baseline policies (C0 sanity + C1 strong classical).

- ``b0`` (``baselines_b0`` alias, SANITY_ONLY): naive keyword-presence check
  against the canonical axis vocabulary. It is deliberately fooled by
  negation ("Ngọ Môn KHÔNG thuộc trục nghi lễ" contains "trục nghi lễ" ->
  accepted) and blind to citation validity (fabricated locators -> accepted).
  This is the documented vulnerability of keyword matching: INV-LN-08-01
  exists precisely because this behaviour must never grant correctness.

- ``c1`` (``baselines_c1`` alias, MATCHED_CLASSICAL, REIMPLEMENTATION):
  character-3-gram TF-IDF cosine similarity between the student answer and a
  fixed reference sentence, thresholded at 0.40 (the same classical
  construction as the observed legacy B1 ``run_ln08_b1``). It deliberately
  has NO negation parsing (a negated sentence scores high cosine similarity
  against the affirmative reference) and NO source-locator verification.
  Synonym paraphrases fall below threshold and are scored incomplete.

Both baselines share the legitimate input features, the label space and the
compute budget with the proposed policy. Neither imports the proposed
decision function (independence requirement); each performs its own analysis
over raw text.
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from .dataset import DatasetError, DiagnosticCase
from .labels import (
    REASON_KEYWORD_MATCH,
    REASON_KEYWORD_MISSING,
    RULE_SUPPORTED,
    STUDY_ID,
    build_prediction,
    native_decision,
)
from .proposed import (
    DEFAULT_COSINE_THRESHOLD,
    CANONICAL_AXIS_KEYWORDS,
    cosine_similarity,
    char_ngram_vector,
    normalize_text,
)

STUDY_ID = "LN-08"
METHOD_VERSION_B0 = "ln08-baseline-b0-keyword-v1.0"
METHOD_VERSION_C1 = "ln08-baseline-c1-tfidf-cosine-v1.0"

# Reference sentence used by the C1 cosine baseline (fixed, from the verified
# passage family; identical construction to the legacy run_ln08_b1).
REFERENCE_TEXT = "Ngọ Môn thuộc trục nghi lễ được mô tả trong nguồn sử liệu triều Nguyễn."


# ---------------------------------------------------------------------------
# B0 — keyword-presence sanity baseline
# ---------------------------------------------------------------------------

def b0_decide(case: DiagnosticCase) -> dict[str, Any]:
    """Naive keyword matching blind to negation and citation validity."""
    if not case.answer.strip():
        return {
            "decision": "abstain",
            "reason_codes": (REASON_KEYWORD_MISSING, "b0_empty_answer"),
            "score": None,
        }
    normalized = normalize_text(case.answer)
    matched = any(kw in normalized for kw in CANONICAL_AXIS_KEYWORDS) or "nghi lễ" in normalized
    # Negation is DETECTED for observability but deliberately NOT acted on:
    # the baseline accepts keyword presence regardless of polarity.
    negated = "không" in normalized or " not " in f" {normalized} "
    if matched:
        return {
            "decision": "feedback_supported",
            "reason_codes": (REASON_KEYWORD_MATCH, "b0_keyword_match"),
            "score": None,
            "false_keyword_match": negated,
        }
    return {
        "decision": "feedback_incomplete",
        "reason_codes": (REASON_KEYWORD_MISSING, "b0_keyword_missing"),
        "score": None,
    }


# ---------------------------------------------------------------------------
# C1 — TF-IDF cosine strong classical baseline
# ---------------------------------------------------------------------------

def c1_decide(case: DiagnosticCase, threshold: float = DEFAULT_COSINE_THRESHOLD) -> dict[str, Any]:
    """Char-3-gram cosine similarity vs the affirmative reference sentence.

    No negation parsing: "không thuộc trục nghi lễ" yields high similarity.
    No source verification: fabricated locators are invisible here.
    """
    if not case.answer.strip():
        return {
            "decision": "abstain",
            "reason_codes": (REASON_KEYWORD_MISSING, "c1_empty_answer"),
            "score": None,
        }
    v_ans = char_ngram_vector(normalize_text(case.answer), n=3)
    v_ref = char_ngram_vector(normalize_text(REFERENCE_TEXT), n=3)
    similarity = cosine_similarity(v_ans, v_ref)
    if similarity >= threshold:
        return {
            "decision": "feedback_supported",
            "reason_codes": ("c1_tfidf_cosine_match", RULE_SUPPORTED),
            "score": round(similarity, 6),
        }
    return {
        "decision": "feedback_incomplete",
        "reason_codes": ("c1_tfidf_cosine_low", REASON_KEYWORD_MISSING),
        "score": round(similarity, 6),
    }


# ---------------------------------------------------------------------------
# Shared ABI plumbing
# ---------------------------------------------------------------------------

def _predict(inputs: list, config: dict | None, decider) -> list:
    from research_v2.contracts.types import StudyInput as _StudyInput

    cfg = dict(config or {})
    out = []
    for i, inp in enumerate(inputs):
        if not isinstance(inp, _StudyInput):
            raise DatasetError(f"input[{i}] expects StudyInput, got {type(inp).__name__}")
        case = DiagnosticCase.from_features(inp.features, case_id=inp.case_id)
        try:
            result = decider(case, cfg)
        except DatasetError:
            raise
        except Exception as exc:
            raise DatasetError(f"input[{i}] case {inp.case_id!r}: {exc}") from exc
        result["decision"] = native_decision(result["decision"])
        out.append(
            build_prediction(
                case_id=inp.case_id,
                decision=result["decision"],
                reason_codes=tuple(result["reason_codes"]),
                evidence_ids=(case.evidence.source_id,),
                score=result.get("score"),
            )
        )
    return out


def b0_solve(case: DiagnosticCase) -> dict[str, Any]:
    return b0_decide(case)


def c1_solve(case: DiagnosticCase, threshold: float = DEFAULT_COSINE_THRESHOLD) -> dict[str, Any]:
    return c1_decide(case, threshold)


def b0_predict_one(inp: Any, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    return _predict([inp], dict(config or {}), lambda c, _cfg: b0_decide(c))[0]


def predict_batch_b0(inputs: list, config: dict | None = None) -> list:
    from research_v2.contracts.types import StudyInput as _StudyInput

    cfg = dict(config or {})
    out = []
    for i, inp in enumerate(inputs):
        if not isinstance(inp, _StudyInput):
            raise DatasetError(f"input[{i}] expects StudyInput, got {type(inp).__name__}")
        case = DiagnosticCase.from_features(inp.features, case_id=inp.case_id)
        result = b0_decide(case)
        result["decision"] = native_decision(result["decision"])
        out.append(
            build_prediction(
                case_id=inp.case_id,
                decision=result["decision"],
                reason_codes=tuple(result["reason_codes"]),
                evidence_ids=(case.evidence.source_id,),
                score=result.get("score"),
            )
        )
    return out


def c1_predict_one(inp: Any, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    cfg = dict(config or {})
    threshold = float(cfg.get("cosine_threshold", DEFAULT_COSINE_THRESHOLD))
    return _predict([inp], cfg, lambda c, _cfg: c1_decide(c, threshold))[0]


def predict_batch_c1(inputs: list, config: dict | None = None) -> list:
    cfg = dict(config or {})
    threshold = float(cfg.get("cosine_threshold", DEFAULT_COSINE_THRESHOLD))
    return _predict(inputs, cfg, lambda c, _cfg: c1_decide(c, threshold))
