"""Partial-reasoning detection: generic answers are feedback_incomplete.

Spec 03.T3 stress axis: incomplete reasoning without the spatial-ritual
relation must never be scored as supported.
"""
from __future__ import annotations

from ln08_helpers import PARTIAL_REASONING_ANSWER, make_features, policy_solve


def test_generic_monument_description_is_incomplete():
    features = make_features(answer=PARTIAL_REASONING_ANSWER)
    assert policy_solve("proposed", features) == "feedback_incomplete"


def test_partial_answer_is_not_supported():
    features = make_features(answer="Điện Thái Hòa là di tích lịch sử nổi tiếng tại Cố đô Huế.")
    assert policy_solve("proposed", features) != "feedback_supported"


def test_partial_reasoning_still_requires_verified_source():
    # Source gate has precedence: a partial answer with a bad locator is a
    # source error, not merely incomplete.
    features = make_features(answer=PARTIAL_REASONING_ANSWER, source_id="SOURCE-FABRICATED")
    assert policy_solve("proposed", features) == "classify_source_error"


def test_empty_answer_abstains():
    from research_v2.methods.ln08.proposed import solve_case
    from research_v2.methods.ln08.dataset import DiagnosticCase

    case = DiagnosticCase.from_features(make_features(answer="   "), case_id="t-empty")
    result = solve_case(case)
    assert result["decision"] == "abstain"
