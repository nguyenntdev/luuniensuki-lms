"""Ablation divergence: each ablation must truly change the code path and
diverge from the proposed policy on the stress cases it targets."""
from __future__ import annotations

import pytest

from research_v2.methods.ln02 import ablations, proposed
from ln02_helpers import (
    high_aggregate_missing_prerequisite_features,
    load_t3_inputs,
    make_input,
    nominal_features,
    unobserved_dimension_features,
)


def _run(predict_batch, inputs):
    return tuple(p.decision for p in predict_batch(inputs, {}))


def test_a1_diverges_on_high_aggregate_case():
    inp = make_input(features=high_aggregate_missing_prerequisite_features())
    assert proposed.predict_batch([inp], {})[0].decision == "remediate_first"
    assert ablations.predict_a1_batch([inp], {})[0].decision == "recommend_eligible"


def test_a2_diverges_on_unobserved_dimension_case():
    inp = make_input(features=unobserved_dimension_features())
    assert proposed.predict_batch([inp], {})[0].decision == "abstain_insufficient_data"
    assert ablations.predict_a2_batch([inp], {})[0].decision == "remediate_first"


def test_a3_diverges_on_single_dimension_deficit():
    """The collapsed scalar mean clears the mean threshold while the true
    required dimension S1 (0.22 < 0.6) fails -> ablation wrongly accepts."""
    inp = make_input(features=high_aggregate_missing_prerequisite_features())
    assert proposed.predict_batch([inp], {})[0].decision == "remediate_first"
    assert ablations.predict_a3_batch([inp], {})[0].decision == "recommend_eligible"


def test_a2_differs_from_a3_on_missing_required_dimension():
    inp = make_input(features=unobserved_dimension_features())
    assert ablations.predict_a2_batch([inp], {})[0].decision == "remediate_first"
    assert ablations.predict_a3_batch([inp], {})[0].decision == "abstain_insufficient_data"


def test_all_methods_agree_on_nominal_case():
    """Ablations isolate mechanisms; the nominal case must stay stable."""
    inp = make_input(features=nominal_features())
    for predict_batch in (
        proposed.predict_batch,
        ablations.predict_a1_batch,
        ablations.predict_a2_batch,
        ablations.predict_a3_batch,
    ):
        assert predict_batch([inp], {})[0].decision == "recommend_eligible"


def test_full_dataset_pairwise_divergence():
    """Every runner method produces a distinct decision vector on the frozen
    T3 dataset - no ablation is a silent no-op."""
    from research_v2.methods.ln02.baselines_b0 import predict_batch as b0
    from research_v2.methods.ln02.baselines_c1 import predict_batch as c1

    inputs = load_t3_inputs()
    vectors = {
        "proposed": _run(proposed.predict_batch, inputs),
        "b0": _run(b0, inputs),
        "c1": _run(c1, inputs),
        "a1": _run(ablations.predict_a1_batch, inputs),
        "a2": _run(ablations.predict_a2_batch, inputs),
        "a3": _run(ablations.predict_a3_batch, inputs),
    }
    names = list(vectors)
    for i, name_a in enumerate(names):
        for name_b in names[i + 1 :]:
            assert vectors[name_a] != vectors[name_b], (
                f"{name_a} and {name_b} produced identical decision vectors; "
                "the ablation/baseline is not mechanism-isolating"
            )


def test_a3_accuracy_gap_on_targeted_cases():
    """Quantify the ablation effect: a3 must accept the single-dim-deficit
    gold-style cases the proposed gate blocks (no hardcoded gold labels -
    the expectation is derived from the domain rubric in helpers)."""
    cases = [make_input(features=high_aggregate_missing_prerequisite_features(), case_id=f"gap-{i}") for i in range(3)]
    proposed_block = sum(
        1
        for p in proposed.predict_batch(cases, {})
        if p.decision == "remediate_first"
    )
    a3_accept = sum(
        1
        for p in ablations.predict_a3_batch(cases, {})
        if p.decision == "recommend_eligible"
    )
    assert proposed_block == 3
    assert a3_accept == 3
