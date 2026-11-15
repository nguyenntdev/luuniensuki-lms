"""P11 typed rubric for historical reasoning (sourcing, corroboration, contextualization, argumentation).

Deterministic scoring of DECLARED structure (evidence, claims, citation links) — not free-text NLP.
Contract doc: research_v3/methods/p11/METHOD.md (frozen before implementation).

Two distinguished non-ordinal marks (never conflated with level 0):
- NOT_APPLICABLE: criterion cannot apply (prompt did not require it)
- ABSTAIN: rater/scorer declines to judge (insufficient information); never imputed

Status: rubric + scorer are ENGINEERING artifacts. Any validity/reliability claim on real
student work is BLOCKED (P11-T12/T13/T14/T19): no human raters, no consented responses yet.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Mapping, Sequence

RUBRIC_ID = "P11_rubric_v1"
RUBRIC_VERSION = "1.0.0"

CRITERIA: tuple[str, ...] = ("S1_sourcing", "S2_corroboration", "S3_contextualization", "S4_argumentation")

MIN_LEVEL = 0
MAX_LEVEL = 3

#: Descriptors are shared with the annotation codebook; keep byte-identical text.
LEVEL_DESCRIPTORS: dict[str, dict[int, str]] = {
    "S1_sourcing": {
        0: "Không sử dụng bằng chứng nào (no evidence used).",
        1: "Dẫn ra bằng chứng nhưng không nêu nguồn (evidence asserted without provenance).",
        2: "Mô tả nguồn nhưng không trích dẫn cụ thể (provenance described but not cited).",
        3: "Trích dẫn nguồn chính/thứ cấp xác thực kèm định vị archival (cited authentic source with locator).",
    },
    "S2_corroboration": {
        0: "Chỉ dùng một hoặc không dùng bằng chứng nào (single or no evidence).",
        1: "Có ≥2 bằng chứng nhưng không gắn với luận điểm (evidence present but unlinked to claims).",
        2: "Bằng chứng được gắn hỗ trợ ít nhất một luận điểm (linked support, no cross-checking).",
        3: "Đối chiếu chéo giữa các bằng chứng, kể cả bằng chứng phản bác/giới hạn (cross-checked, incl. refuting evidence).",
    },
    "S3_contextualization": {
        0: "Không có bối cảnh (no context).",
        1: "Bối cảnh chung chung, không thời gian/không gian (generic, undated context).",
        2: "Bối cảnh có thời gian/không gian gắn với luận điểm (dated/spatial context linked to a claim).",
        3: "Bối cảnh giới hạn phạm vi/giá trị của luận điểm (context constrains claim scope).",
    },
    "S4_argumentation": {
        0: "Luận điểm không có suy luận (claim without inference).",
        1: "Suy luận mô tả (descriptive inference).",
        2: "Suy luận giải thích hỗ trợ luận điểm (explanatory inference).",
        3: "Chuỗi suy luận tường minh, xử lý phản bác hoặc phản chứng (explicit chain incl. refutation/counterfactual).",
    },
}


class Criterion(str, Enum):
    S1_SOURCING = "S1_sourcing"
    S2_CORROBORATION = "S2_corroboration"
    S3_CONTEXTUALIZATION = "S3_contextualization"
    S4_ARGUMENTATION = "S4_argumentation"


class SourceType(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    ARTIFACT = "artifact"
    ORAL = "oral"
    OTHER = "other"


class Provenance(str, Enum):
    ASSERTED = "asserted"    # no provenance given
    DESCRIBED = "described"  # source described in words, no citation
    CITED = "cited"          # explicit citation


class LinkRelation(str, Enum):
    SUPPORTS = "supports"
    REFUTES = "refutes"
    CONTEXTUALIZES = "contextualizes"


class InferenceType(str, Enum):
    NONE = "none"
    DESCRIPTIVE = "descriptive"
    EXPLANATORY = "explanatory"
    CAUSAL = "causal"
    COUNTERFACTUAL = "counterfactual"


class NonOrdinalMark(str, Enum):
    """Distinguished marks that are NOT ordinal levels."""

    NOT_APPLICABLE = "NOT_APPLICABLE"
    ABSTAIN = "ABSTAIN"


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    source_type: SourceType = SourceType.OTHER
    provenance: Provenance = Provenance.ASSERTED
    is_authentic: bool = False  # named real archive/source vs invented/fake citation
    locator: str | None = None  # stable archival page/claim id
    text: str = ""  # declared evidence text; used by C0 keyword baseline only

    def __post_init__(self) -> None:
        if not self.evidence_id:
            raise ValueError("evidence_id is required")


@dataclass(frozen=True)
class Claim:
    claim_id: str
    text: str = ""
    is_causal: bool = False
    inference_type: InferenceType = InferenceType.NONE
    #: True when the claim explicitly states its validity conditions (time/place bounded),
    #: i.e. contextualization constrains the claim — required for S3 level 3.
    scope_limited: bool = False

    def __post_init__(self) -> None:
        if not self.claim_id:
            raise ValueError("claim_id is required")


@dataclass(frozen=True)
class EvidenceLink:
    claim_id: str
    evidence_id: str
    relation: LinkRelation

    def __post_init__(self) -> None:
        if not self.claim_id or not self.evidence_id:
            raise ValueError("link must reference a claim_id and evidence_id")


@dataclass(frozen=True)
class HistoricalReasoningResponse:
    response_id: str
    evidence: tuple[EvidenceItem, ...] = ()
    claims: tuple[Claim, ...] = ()
    links: tuple[EvidenceLink, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.response_id:
            raise ValueError("response_id is required")
        evidence_ids = {e.evidence_id for e in self.evidence}
        claim_ids = {c.claim_id for c in self.claims}
        for link in self.links:
            if link.evidence_id not in evidence_ids:
                raise ValueError(
                    f"{self.response_id}: link references unknown evidence {link.evidence_id!r}"
                )
            if link.claim_id not in claim_ids:
                raise ValueError(f"{self.response_id}: link references unknown claim {link.claim_id!r}")


@dataclass(frozen=True)
class CriterionScore:
    criterion: str
    level: int | NonOrdinalMark
    rationale: str = ""


@dataclass(frozen=True)
class RubricResult:
    rubric_id: str
    rubric_version: str
    response_id: str
    scores: Mapping[str, int | NonOrdinalMark]
    rationales: Mapping[str, str]
    overall: float | None
    #: how many criteria were actually scored on the 0-3 scale (NA/ABSTAIN excluded)
    scored_criteria: int
    #: upper-bound cap applied by the zero-evidence / fabricated-source rules
    caps_applied: tuple[str, ...] = ()

    def numeric_scores(self) -> list[float]:
        """Levels on the 0-3 scale only; NA/ABSTAIN excluded, never imputed."""
        return [float(v) for v in self.scores.values() if isinstance(v, int)]


# ---------------------------------------------------------------------------
# Deterministic scoring functions (pure; same input -> same output)
# ---------------------------------------------------------------------------

_PROVENANCE_RANK: Mapping[Provenance, int] = {
    Provenance.ASSERTED: 1,
    Provenance.DESCRIBED: 2,
    Provenance.CITED: 3,
}


def _best_provenance(evidence: Sequence[EvidenceItem]) -> int:
    if not evidence:
        return 0
    return max(_PROVENANCE_RANK[e.provenance] for e in evidence)


def score_sourcing(
    response: HistoricalReasoningResponse,
    *,
    required: bool = True,
) -> CriterionScore:
    """S1 sourcing: provenance/citation quality of declared evidence."""
    caps: list[str] = []
    level: int | NonOrdinalMark
    if not required:
        return CriterionScore(Criterion.S1_SOURCING.value, NonOrdinalMark.NOT_APPLICABLE)
    if not response.evidence:
        caps.append("zero_evidence_cap_S1")
        level = 0
    else:
        level = _best_provenance(response.evidence)
        authentic_cited = [e for e in response.evidence if e.provenance is Provenance.CITED and e.is_authentic]
        if authentic_cited:
            level = 3
            if any(e.locator for e in authentic_cited):
                pass  # locator strengthens the level-3 descriptor but level already 3
        elif level == 3:
            # citations exist but none authentic -> fabricated-source cap
            caps.append("fabricated_source_cap_S1")
            level = 1
    rationale = (
        f"best provenance rank {level}" if isinstance(level, int) else "criterion not applicable"
    )
    return CriterionScore(Criterion.S1_SOURCING.value, level, "; ".join([rationale, *caps]).strip("; "))


def score_corroboration(
    response: HistoricalReasoningResponse,
    *,
    required: bool = True,
) -> CriterionScore:
    """S2 corroboration: multiple evidence, links to claims, cross-checking."""
    caps: list[str] = []
    n_ev = len(response.evidence)
    if not required:
        return CriterionScore(Criterion.S2_CORROBORATION.value, NonOrdinalMark.NOT_APPLICABLE)
    if n_ev <= 1:
        if n_ev == 1 and response.links:
            # one piece of evidence linked to a claim is still single-source: level 2 floor is not met
            caps.append("single_evidence_cap_S2")
        level = min(1, max(0, n_ev)) if n_ev else 0
        if not caps:
            caps.append("zero_evidence_cap_S2" if n_ev == 0 else "single_evidence_cap_S2")
        return CriterionScore(Criterion.S2_CORROBORATION.value, level, "; ".join(caps))

    supports = [l for l in response.links if l.relation is LinkRelation.SUPPORTS]
    refutes = [l for l in response.links if l.relation is LinkRelation.REFUTES]
    claims_supported = {l.claim_id for l in supports}
    claims_with_multi_ev = {
        l.claim_id
        for l in response.links
        if sum(1 for o in response.links if o.claim_id == l.claim_id and o.relation is not LinkRelation.CONTEXTUALIZES) >= 2
    }
    if claims_with_multi_ev and refutes:
        level = 3
    elif claims_supported:
        level = 2
    else:
        level = 1
    if n_ev >= 2 and not response.links:
        caps.append("unlinked_evidence_cap_S2")
    rationale = (
        f"n_evidence={n_ev}, supports={len(supports)}, refutes={len(refutes)}, "
        f"multi_ev_claims={len(claims_with_multi_ev)}"
    )
    return CriterionScore(Criterion.S2_CORROBORATION.value, level, "; ".join([rationale, *caps]).strip("; "))


def score_contextualization(
    response: HistoricalReasoningResponse,
    *,
    required: bool = True,
) -> CriterionScore:
    """S3 contextualization: dated/spatial context linked to inferential claims."""
    caps: list[str] = []
    if not required:
        return CriterionScore(Criterion.S3_CONTEXTUALIZATION.value, NonOrdinalMark.NOT_APPLICABLE)
    if not response.evidence:
        caps.append("zero_evidence_cap_S3")
        return CriterionScore(Criterion.S3_CONTEXTUALIZATION.value, 0, "; ".join(caps))

    inferential_claims = {
        c.claim_id
        for c in response.claims
        if c.inference_type in (InferenceType.EXPLANATORY, InferenceType.CAUSAL, InferenceType.COUNTERFACTUAL)
    }
    context_links = [l for l in response.links if l.relation is LinkRelation.CONTEXTUALIZES]
    context_on_inferential = [l for l in context_links if l.claim_id in inferential_claims]
    scope_limited_claims = {c.claim_id for c in response.claims if c.scope_limited}
    if context_on_inferential and (scope_limited_claims & inferential_claims):
        # context is attached AND the claim states its validity conditions -> constrains scope
        level = 3
    elif context_on_inferential or (scope_limited_claims & inferential_claims):
        level = 3 if scope_limited_claims & inferential_claims else 2
    elif context_links:
        level = 2
    else:
        level = 1 if response.evidence else 0
    rationale = (
        f"context_links={len(context_links)}, inferential_claims={len(inferential_claims)}"
    )
    return CriterionScore(Criterion.S3_CONTEXTUALIZATION.value, level, "; ".join([rationale, *caps]).strip("; "))


def score_argumentation(
    response: HistoricalReasoningResponse,
    *,
    required: bool = True,
    allow_handling_bonus: bool = True,
) -> CriterionScore:
    """S4 argumentation: inference depth of claims + refutation/counterfactual handling.

    `allow_handling_bonus=False` is ablation A1-adjacent mechanism removal for the
    refutation-handling mechanism (used by mutation tests, not a separate scorer).
    """
    caps: list[str] = []
    if not required:
        return CriterionScore(Criterion.S4_ARGUMENTATION.value, NonOrdinalMark.NOT_APPLICABLE)

    rank = {
        InferenceType.NONE: 0,
        InferenceType.DESCRIPTIVE: 1,
        InferenceType.EXPLANATORY: 2,
        InferenceType.CAUSAL: 2,
        InferenceType.COUNTERFACTUAL: 3,
    }
    if not response.claims:
        caps.append("zero_claim_cap_S4")
        return CriterionScore(Criterion.S4_ARGUMENTATION.value, 0, "; ".join(caps))

    if not response.evidence:
        # negative case: no evidence -> argumentation cannot exceed the lowest level
        caps.append("zero_evidence_cap_S4")
        return CriterionScore(Criterion.S4_ARGUMENTATION.value, min(1, max(rank[c.inference_type] for c in response.claims)), "; ".join(caps))

    best = max(rank[c.inference_type] for c in response.claims)
    handles = any(l.relation is LinkRelation.REFUTES for l in response.links)
    counterfactual = any(c.inference_type is InferenceType.COUNTERFACTUAL for c in response.claims)
    level = best
    if allow_handling_bonus and (handles or counterfactual) and best >= 2:
        level = 3
    rationale = f"best_inference={best}, refutation_or_counterfactual={handles or counterfactual}"
    return CriterionScore(Criterion.S4_ARGUMENTATION.value, level, "; ".join([rationale, *caps]).strip("; "))


def score_response(
    response: HistoricalReasoningResponse,
    *,
    required: Mapping[str, bool] | None = None,
    allow_handling_bonus: bool = True,
) -> RubricResult:
    """Score all four criteria deterministically.

    `required` maps criterion id -> False to mark NOT_APPLICABLE (e.g. prompt did not
    require sourcing). Missing keys default to required=True.
    """
    required = dict(required or {})
    caps: list[str] = []
    scores: dict[str, int | NonOrdinalMark] = {}
    rationales: dict[str, str] = {}

    s1 = score_sourcing(response, required=required.get(Criterion.S1_SOURCING.value, True))
    s2 = score_corroboration(response, required=required.get(Criterion.S2_CORROBORATION.value, True))
    s3 = score_contextualization(response, required=required.get(Criterion.S3_CONTEXTUALIZATION.value, True))
    s4 = score_argumentation(response, required=required.get(Criterion.S4_ARGUMENTATION.value, True), allow_handling_bonus=allow_handling_bonus)

    for cs in (s1, s2, s3, s4):
        scores[cs.criterion] = cs.level
        rationales[cs.criterion] = cs.rationale
        if "cap_" in cs.rationale:
            caps.append(f"{cs.criterion}: {cs.rationale}")

    numeric = [float(v) for v in scores.values() if isinstance(v, int)]
    overall = round(sum(numeric) / len(numeric), 2) if numeric else None
    return RubricResult(
        rubric_id=RUBRIC_ID,
        rubric_version=RUBRIC_VERSION,
        response_id=response.response_id,
        scores=scores,
        rationales=rationales,
        overall=overall,
        scored_criteria=len(numeric),
        caps_applied=tuple(caps),
    )


# ---------------------------------------------------------------------------
# Baselines (spec section 4 matrix)
# ---------------------------------------------------------------------------

_KEYWORD_FAMILIES: Mapping[str, tuple[str, ...]] = {
    "sourcing": ("nguồn", "tư liệu", "sưu tầm", "chứng cứ", "source", "document", "evidence"),
    "corroboration": ("đối chiếu", "so sánh", "xác nhận", "corroborate", "compare", "cross-check"),
    "contextualization": ("bối cảnh", "thời kỳ", "xã hội", "context", "period", "background"),
    "argumentation": ("luận điểm", "suy luận", "kết luận", "argue", "conclude", "infer", "therefore"),
}


def c0_keyword_score(response: HistoricalReasoningResponse) -> dict[str, int]:
    """C0 sanity baseline: keyword-presence scoring over declared text fields.

    Ignores structure and authenticity entirely; its expected failure family is
    keyword hits on fabricated or relation-inverted content (stress suites, spec s5).
    Returns a level 0-3 per canonical criterion id from keyword counts (0 hits -> 0, ...).
    """
    haystack = " ".join(
        [e.text for e in response.evidence]
        + [c.text for c in response.claims]
        + [response.metadata.get("prompt", "")]
    ).lower()
    family_to_criterion = {
        "sourcing": Criterion.S1_SOURCING.value,
        "corroboration": Criterion.S2_CORROBORATION.value,
        "contextualization": Criterion.S3_CONTEXTUALIZATION.value,
        "argumentation": Criterion.S4_ARGUMENTATION.value,
    }
    out: dict[str, int] = {}
    for fam, crit in family_to_criterion.items():
        hits = sum(1 for kw in _KEYWORD_FAMILIES[fam] if kw in haystack)
        out[crit] = min(3, hits)
    return out


def c1_rubric_score(response: HistoricalReasoningResponse) -> RubricResult:
    """C1 baseline: the rubric applied to declared evidence (same scorer as proposed
    minus human calibration; the calibrated link-aware variant needs raters -> BLOCKED)."""
    return score_response(response)


__all__ = [
    "RUBRIC_ID",
    "RUBRIC_VERSION",
    "CRITERIA",
    "MIN_LEVEL",
    "MAX_LEVEL",
    "LEVEL_DESCRIPTORS",
    "Criterion",
    "SourceType",
    "Provenance",
    "LinkRelation",
    "InferenceType",
    "NonOrdinalMark",
    "EvidenceItem",
    "Claim",
    "EvidenceLink",
    "HistoricalReasoningResponse",
    "CriterionScore",
    "RubricResult",
    "score_sourcing",
    "score_corroboration",
    "score_contextualization",
    "score_argumentation",
    "score_response",
    "c0_keyword_score",
    "c1_rubric_score",
]
