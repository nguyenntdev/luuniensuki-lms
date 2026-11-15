"""Ablation divergence: each ablation must diverge exactly on its mechanism."""
from __future__ import annotations

from ln08_helpers import (
    FABRICATED_SOURCE_ANSWER,
    KEYWORD_COMPLETE_REVERSED_VI,
    PARTIAL_REASONING_ANSWER,
    SYNONYM_PARAPHRASE,
    load_t3_gold,
    load_t3_inputs,
    make_features,
    policy_solve,
)


def test_a1_keyword_only_collapses_all_mechanisms():
    # Negated answer accepted (keyword present) ...
    assert (
        policy_solve("ablations_a1", make_features(answer=KEYWORD_COMPLETE_REVERSED_VI))
        == "feedback_supported"
    )
    # ... fabricated locator accepted ...
    assert (
        policy_solve("ablations_a1", make_features(answer=FABRICATED_SOURCE_ANSWER, source_id="SOURCE-FABRICATED"))
        == "feedback_supported"
    )
    # ... synonym paraphrase rejected (keyword missing) ...
    assert (
        policy_solve("ablations_a1", make_features(answer=SYNONYM_PARAPHRASE))
        == "feedback_incomplete"
    )
    # ... partial reasoning rejected (keyword missing).
    assert (
        policy_solve("ablations_a1", make_features(answer=PARTIAL_REASONING_ANSWER))
        == "feedback_incomplete"
    )


def test_a2_diverges_only_on_negated_answers():
    features = make_features(answer=KEYWORD_COMPLETE_REVERSED_VI)
    assert policy_solve("proposed", features) == "classify_contradiction"
    assert policy_solve("ablations_a2", features) == "feedback_supported"
    # Nominal supported case is unchanged.
    nominal = make_features()
    assert policy_solve("proposed", nominal) == policy_solve("ablations_a2", nominal)


def test_a3_diverges_only_on_source_errors():
    features = make_features(answer=FABRICATED_SOURCE_ANSWER, source_id="SOURCE-FABRICATED")
    assert policy_solve("proposed", features) == "classify_source_error"
    assert policy_solve("ablations_a3", features) == "feedback_supported"
    # Nominal supported case is unchanged.
    nominal = make_features()
    assert policy_solve("proposed", nominal) == policy_solve("ablations_a3", nominal)


def test_full_dataset_divergence_counts():
    """Every ablation diverges from proposed on exactly its target stratum."""
    from research_v2.contracts.input_masking import mask_case_input
    from research_v2.contracts.types import StudyInput
    from research_v2.methods.ln08.ablations_a1 import predict_batch as a1
    from research_v2.methods.ln08.ablations_a2 import predict_batch as a2
    from research_v2.methods.ln08.ablations_a3 import predict_batch as a3
    from research_v2.methods.ln08.proposed import predict_batch as proposed
    from research_v2.methods.ln08.labels import NATIVE_TO_CONTRACT

    inputs = [
        StudyInput("LN-08", r["case_id"], "test", r["group_id"], mask_case_input(r))
        for r in load_t3_inputs()
    ]
    gold = load_t3_gold()
    proposed_preds = proposed(inputs, {"seed": 11})

    a1_preds = a1(inputs, {"seed": 11})
    a2_preds = a2(inputs, {"seed": 11})
    a3_preds = a3(inputs, {"seed": 11})

    def wrong(preds):
        return {
            p.case_id
            for p in preds
            if NATIVE_TO_CONTRACT[gold[p.case_id]] != p.decision
        }

    wrong_proposed = wrong(proposed_preds)
    wrong_a1 = wrong(a1_preds)
    wrong_a2 = wrong(a2_preds)
    wrong_a3 = wrong(a3_preds)

    # Proposed is correct on the full holdout under the contract mapping.
    assert not wrong_proposed
    # A1 (keyword-only) additionally fails negation + source + synonym strata.
    assert wrong_a1 >= wrong_a2 and wrong_a1 >= wrong_a3 and len(wrong_a1) >= 48
    # A2 fails exactly the negation stratum (24 contradiction cases).
    a2_only = wrong_a2 - wrong_a3
    assert len(a2_only) == 24
    assert all(gold[c] == "classify_contradiction" for c in a2_only)
    # A3 fails exactly the source-error stratum (24 cases).
    a3_only = wrong_a3 - wrong_a2
    assert len(a3_only) == 24
    assert all(gold[c] == "classify_source_error" for c in a3_only)


def test_ablation_reason_codes_carry_label():
    from research_v2.methods.ln08.ablations_a2 import predict_batch as a2
    from research_v2.contracts.types import StudyInput

    inp = StudyInput("LN-08", "t-abl", "test", "g", make_features(answer=KEYWORD_COMPLETE_REVERSED_VI))
    pred = a2([inp], {})[0]
    assert "a2_no_negation_parsing" in pred.reason_codes
    assert "ablation" in pred.reason_codes
