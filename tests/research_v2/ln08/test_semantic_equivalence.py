"""Semantic-equivalence: correct synonym paraphrase without exact keywords.

Spec 03.F Case 2: a correct paraphrase with NO exact canonical keyword must
be recognised as asserting the source-backed proposition (native
``preserve_semantics``, contract ``feedback_supported``) - never penalised
for keyword absence.
"""
from __future__ import annotations

from ln08_helpers import (
    SYNONYM_PARAPHRASE,
    load_t3_gold,
    load_t3_inputs,
    make_features,
    policy_solve,
)


def test_synonym_paraphrase_without_canonical_keyword_is_recognised():
    features = make_features(answer=SYNONYM_PARAPHRASE)
    # No exact canonical keyword in the paraphrase
    assert "trục nghi lễ" not in features["answer"]
    native = policy_solve("proposed", features)
    assert native in ("preserve_semantics", "feedback_supported")


def test_synonym_paraphrase_maps_to_contract_feedback_supported():
    from research_v2.methods.ln08.labels import to_contract_decision

    assert to_contract_decision("preserve_semantics") == "feedback_supported"


def test_b0_and_a1_penalise_the_correct_paraphrase():
    # The keyword-only comparators reject the synonym answer as incomplete:
    # exactly the false-rejection axis the proposed method fixes.
    features = make_features(answer=SYNONYM_PARAPHRASE)
    assert policy_solve("baselines_b0", features) == "feedback_incomplete"
    assert policy_solve("ablations_a1", features) == "feedback_incomplete"


def test_full_dataset_native_labels_match_gold():
    """Proposed policy reproduces the DIAGNOSTIC_FEEDBACK_SPEC oracle on the
    full T3 holdout (contract-mapped: preserve_semantics -> supported)."""
    from research_v2.contracts.input_masking import mask_case_input
    from research_v2.contracts.types import StudyInput
    from research_v2.methods.ln08.labels import NATIVE_TO_CONTRACT
    from research_v2.methods.ln08.proposed import predict_batch

    gold = load_t3_gold()
    inputs = [
        StudyInput("LN-08", r["case_id"], "test", r["group_id"], mask_case_input(r))
        for r in load_t3_inputs()
    ]
    preds = predict_batch(inputs, {"seed": 11})
    correct = sum(1 for p in preds if NATIVE_TO_CONTRACT[gold[p.case_id]] == p.decision)
    assert correct == len(gold) == 120
