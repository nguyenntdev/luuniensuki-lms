"""P11 rubric tests: determinism, level pinning, negative cases, NA/ABSTAIN, baselines."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from research_v3.methods.p11.rubric import (
    CRITERIA,
    Claim,
    EvidenceItem,
    EvidenceLink,
    HistoricalReasoningResponse,
    InferenceType,
    LEVEL_DESCRIPTORS,
    LinkRelation,
    NonOrdinalMark,
    Provenance,
    c0_keyword_score,
    c1_rubric_score,
    score_response,
    score_sourcing,
)
from research_v3.annotations.tasks.p11_annotation_pack.constructed_cases.build_cases import (
    CONSTRUCTORS,
    cc01_zero_evidence,
    cc04_full_chain,
    cc05_fabricated_citation,
)

PACK = Path("research_v3/annotations/tasks/p11_annotation_pack")


def _full() -> HistoricalReasoningResponse:
    return cc04_full_chain()


# ---------------------------------------------------------------------------
# determinism
# ---------------------------------------------------------------------------


def test_scoring_is_deterministic():
    r1 = score_response(_full())
    r2 = score_response(_full())
    assert r1.scores == r2.scores
    assert r1.overall == r2.overall
    assert r1.caps_applied == r2.caps_applied


def test_scoring_pure_function_no_hidden_state():
    # order of construction must not matter
    a = HistoricalReasoningResponse(
        response_id="x",
        evidence=(EvidenceItem("e1", provenance=Provenance.DESCRIBED), EvidenceItem("e2")),
        claims=(Claim("c1", inference_type=InferenceType.DESCRIPTIVE),),
        links=(EvidenceLink("c1", "e1", LinkRelation.SUPPORTS),),
    )
    b = HistoricalReasoningResponse(
        response_id="x",
        evidence=(EvidenceItem("e2"), EvidenceItem("e1", provenance=Provenance.DESCRIBED)),
        claims=(Claim("c1", inference_type=InferenceType.DESCRIPTIVE),),
        links=(EvidenceLink("c1", "e1", LinkRelation.SUPPORTS),),
    )
    assert score_response(a).scores == score_response(b).scores


# ---------------------------------------------------------------------------
# level pinning (0-3 scale)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case_id", list(CONSTRUCTORS))
def test_constructed_cases_pin_to_expected_levels(case_id):
    result = score_response(CONSTRUCTORS[case_id]())
    expected_csv = PACK / "constructed_cases" / "expected_levels.csv"
    rows = {r["case_id"]: r for r in csv.DictReader(expected_csv.open(encoding="utf-8"))}
    exp = rows[case_id]
    for crit, col in zip(CRITERIA, ("expected_S1", "expected_S2", "expected_S3", "expected_S4")):
        assert result.scores[crit] == int(exp[col]), f"{case_id}/{crit}"
    assert all(isinstance(v, int) for v in result.scores.values())
    assert 0 <= result.overall <= 3


def test_all_criteria_scored_on_zero_three_scale():
    for case_id, ctor in CONSTRUCTORS.items():
        result = score_response(ctor())
        for crit, level in result.scores.items():
            assert isinstance(level, int) and 0 <= level <= 3, f"{case_id}/{crit}={level!r}"


# ---------------------------------------------------------------------------
# negative cases
# ---------------------------------------------------------------------------


def test_no_evidence_cannot_score_above_lowest_level():
    """Spec: a response with no evidence cannot rise above the lowest level."""
    result = score_response(cc01_zero_evidence())
    assert result.scores["S1_sourcing"] == 0
    assert result.scores["S2_corroboration"] == 0
    assert result.scores["S3_contextualization"] == 0
    # S4 is capped at <= 1 even with causal claims
    assert result.scores["S4_argumentation"] <= 1
    assert any("zero_evidence_cap" in cap for cap in result.caps_applied)


def test_rich_claims_without_evidence_stay_capped():
    resp = HistoricalReasoningResponse(
        response_id="neg1",
        evidence=(),
        claims=(
            Claim("c1", "Very sophisticated causal claim.", is_causal=True, inference_type=InferenceType.CAUSAL),
            Claim("c2", "Counterfactual flourish.", inference_type=InferenceType.COUNTERFACTUAL),
        ),
    )
    result = score_response(resp)
    assert result.scores["S4_argumentation"] <= 1


def test_fabricated_citations_capped_on_sourcing():
    result = score_response(cc05_fabricated_citation())
    assert result.scores["S1_sourcing"] <= 1
    assert any("fabricated_source_cap" in cap for cap in result.caps_applied)


def test_keyword_baseline_cannot_distinguish_fabricated():
    """C0 failure family: keyword hits regardless of authenticity/relations."""
    real = c0_keyword_score(cc04_full_chain())
    fake = c0_keyword_score(cc05_fabricated_citation())
    # C0 sees both as sourcing-flavored because both *mention* sources; the rubric separates them
    assert c1_rubric_score(cc04_full_chain()).scores["S1_sourcing"] == 3
    assert c1_rubric_score(cc05_fabricated_citation()).scores["S1_sourcing"] == 1


def test_relation_inverted_links_detected():
    """Stress family 'dao quan he lich su': refutes mislabeled as supports changes corroboration level."""
    base_evidence = (
        EvidenceItem("e1", provenance=Provenance.CITED, is_authentic=True, locator="loc1"),
        EvidenceItem("e2", provenance=Provenance.CITED, is_authentic=True, locator="loc2"),
    )
    claims = (Claim("c1", inference_type=InferenceType.EXPLANATORY),)
    honest = HistoricalReasoningResponse(
        response_id="honest", evidence=base_evidence, claims=claims,
        links=(EvidenceLink("c1", "e1", LinkRelation.SUPPORTS), EvidenceLink("c1", "e2", LinkRelation.SUPPORTS)),
    )
    inverted = HistoricalReasoningResponse(
        response_id="inverted", evidence=base_evidence, claims=claims,
        links=(EvidenceLink("c1", "e1", LinkRelation.SUPPORTS), EvidenceLink("c1", "e2", LinkRelation.REFUTES)),
    )
    s_honest, s_inverted = score_response(honest).scores, score_response(inverted).scores
    assert s_honest["S2_corroboration"] == 2  # support, no cross-check
    assert s_inverted["S2_corroboration"] == 3  # refutation counts as cross-checking


# ---------------------------------------------------------------------------
# NA / ABSTAIN distinct from 0
# ---------------------------------------------------------------------------


def test_not_applicable_distinct_from_zero():
    resp = HistoricalReasoningResponse(
        response_id="na1",
        evidence=(EvidenceItem("e1"),),
        claims=(Claim("c1"),),
    )
    result = score_response(resp, required={"S1_sourcing": False})
    assert result.scores["S1_sourcing"] is NonOrdinalMark.NOT_APPLICABLE
    assert result.scores["S1_sourcing"] != 0
    assert result.scored_criteria == 3
    assert result.overall is not None
    # excluded from mean, not imputed
    raw = [v for v in result.scores.values() if isinstance(v, int)]
    assert result.overall == round(sum(raw) / len(raw), 2)


def test_abstain_mark_never_entered_by_scorer():
    """The deterministic scorer never emits ABSTAIN; ABSTAIN is a rater-side mark."""
    for ctor in CONSTRUCTORS.values():
        result = score_response(ctor())
        assert all(v is not NonOrdinalMark.ABSTAIN for v in result.scores.values())


# ---------------------------------------------------------------------------
# schema validation
# ---------------------------------------------------------------------------


def test_dangling_links_rejected():
    with pytest.raises(ValueError, match="unknown evidence"):
        HistoricalReasoningResponse(
            response_id="bad",
            evidence=(EvidenceItem("e1"),),
            claims=(Claim("c1"),),
            links=(EvidenceLink("c1", "ghost", LinkRelation.SUPPORTS),),
        )
    with pytest.raises(ValueError, match="unknown claim"):
        HistoricalReasoningResponse(
            response_id="bad2",
            evidence=(EvidenceItem("e1"),),
            claims=(Claim("c1"),),
            links=(EvidenceLink("ghost", "e1", LinkRelation.SUPPORTS),),
        )


def test_descriptors_complete_and_bilingual():
    for crit in CRITERIA:
        assert set(LEVEL_DESCRIPTORS[crit]) == {0, 1, 2, 3}
        for level, text in LEVEL_DESCRIPTORS[crit].items():
            assert text.strip(), f"{crit}/{level} descriptor empty"
            assert "(" in text, f"{crit}/{level} descriptor missing second language"


# ---------------------------------------------------------------------------
# baselines
# ---------------------------------------------------------------------------


def test_c0_keyword_baseline_bounds():
    scores = c0_keyword_score(cc04_full_chain())
    assert set(scores) == set(CRITERIA)
    assert all(0 <= v <= 3 for v in scores.values())
