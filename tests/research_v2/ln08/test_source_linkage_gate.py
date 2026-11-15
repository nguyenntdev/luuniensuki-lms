"""Source-linkage verification: fabricated / untrusted / unverified locators.

Spec 03.F Case 3: a plausible statement with a fabricated source must be
classified_source_error. INV-LN-08-03: no claim of source support without a
verified locator.
"""
from __future__ import annotations

import pytest

from ln08_helpers import FABRICATED_SOURCE_ANSWER, make_features, policy_solve


@pytest.mark.parametrize(
    "source_id",
    ["SOURCE-FABRICATED", "SOURCE-SYN-WRONG", "SOURCE-UNVERIFIED"],
)
def test_untrusted_source_ids_are_source_errors(source_id):
    features = make_features(answer=FABRICATED_SOURCE_ANSWER, source_id=source_id)
    assert policy_solve("proposed", features) == "classify_source_error"


def test_unverified_flag_is_source_error():
    features = make_features(
        answer=FABRICATED_SOURCE_ANSWER, source_id="SOURCE-DNTL-001", verified=False
    )
    assert policy_solve("proposed", features) == "classify_source_error"


def test_a3_no_source_check_ablation_accepts_fabricated_locator():
    features = make_features(answer=FABRICATED_SOURCE_ANSWER, source_id="SOURCE-FABRICATED")
    assert policy_solve("proposed", features) == "classify_source_error"
    assert policy_solve("ablations_a3", features) == "feedback_supported"


def test_b0_and_c1_are_blind_to_fabricated_locator():
    features = make_features(answer=FABRICATED_SOURCE_ANSWER, source_id="SOURCE-FABRICATED")
    assert policy_solve("baselines_b0", features) == "feedback_supported"
    assert policy_solve("baselines_c1", features) == "feedback_supported"


def test_verified_trusted_locator_passes_the_gate():
    features = make_features(
        answer=FABRICATED_SOURCE_ANSWER, source_id="SOURCE-DNTL-001", verified=True
    )
    assert policy_solve("proposed", features) == "feedback_supported"
